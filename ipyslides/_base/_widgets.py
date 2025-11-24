import uuid
import traitlets
import inspect
import anywidget

from pathlib import Path
from dashlab.utils import _fix_init_sig, _fix_trait_sig

jupyter_colors = { # used in styles.py and interaction.js
    'fg1':'--jp-content-font-color0',
    'fg2':'--jp-content-font-color3',
    'fg3':'--jp-content-font-color2',
    'bg1':'--jp-layout-color0',
    'bg2':'--jp-cell-editor-background',
    'bg3':'--jp-layout-color2',
    'accent':'--jp-brand-color1',
    'pointer':'--jp-error-color1',
}

# used to set focusable elements for click-to-focus feature in _layout_css.py and interaction.js
focus_selectors = ":is(img, svg, video, canvas, .focus-self, .focus-child > *:not(.no-focus), .plot-container.plotly)"

class InteractionWidget(anywidget.AnyWidget):
    _esm =  Path(__file__).with_name('static') / 'interaction.js'
    _css =  Path(__file__).with_name('static') / 'interaction.css'
    _uid = traitlets.Unicode(str(uuid.uuid1()), read_only=True).tag(sync=True) # need for frontend display purporse
    _colors = traitlets.Dict(jupyter_colors).tag(sync=True) # for export
    _parts = traitlets.Dict().tag(sync=True) # parts data for each slide, for js side use
    _fkws = traitlets.Dict().tag(sync=True) # footer kws for js side use
    _fsels = traitlets.Unicode(focus_selectors, read_only=True).tag(sync=True) # need for frontend focus management by click
    
    msg_topy = traitlets.Unicode('').tag(sync=True)
    msg_tojs = traitlets.Unicode('').tag(sync=True)

    def __init__(self, _widgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._buttons = _widgets.buttons
        self._checks = _widgets.checks
        self._loading = _widgets.htmls.loading
        self._prog = _widgets.sliders.progress
        self._theme = _widgets.theme
        self._menu = _widgets._ctxmenu

    @traitlets.observe("msg_topy")
    def _see_changes(self, change):
        msg = change.new
        if not msg:
            return # Message set empty, do not waste time
        if 'SHIFT:' in msg:
            self._prog.value = self._prog.value + int(msg.lstrip('SHIFT:')) # shift by given offset
        elif msg == 'CCTX':
            self._menu.hide() # close context menu
        elif 'CTX:' in msg:
            # Context menu requested at given coordinates
            coords = msg.lstrip('CTX:').split(',')
            if len(coords) == 2:
                try:
                    xPerc = round(float(coords[0]),2)
                    yPerc = round(float(coords[1]),2)
                    self._menu.show(xPerc, yPerc)
                except:
                    pass
        elif msg == 'NEXT':
            self._buttons.next.click()
        elif msg == 'PREV':
            self._buttons.prev.click()
        elif msg == 'KSC':
            self._menu.select('ksc')
        elif msg == 'TLSR':
            self._menu.select('laser', lambda old: not old) # toggle
        elif msg == 'TPAN':
            self._toggle_panel(self._menu)
        elif "Draw:" in msg:
            self._menu.ws.drawer.toggle(False if "OFF" in msg else True) # toggle drawing board
        elif msg == 'EDIT':
            self._menu.select('source')
        elif msg == 'JUPYTER' and not ('Jupyter' in self._theme.options):
            self._theme.options = ['Jupyter', *self._theme.options] 
            self._theme.value = 'Jupyter' # enable it
        elif msg == 'LOADED':
            if self._checks.notes.value: # Notes window already there
               self._checks.notes.value = False # closes unlinked window
               self._checks.notes.value = True # opens new linked window

            self.msg_tojs = 'SwitchView' # Trigger view
        elif msg == 'CleanView':
            # Clear loading splash and other stuff
            self._loading.value = ""
            self._loading.layout.display = "none"
        elif msg in ('FS','!FS'): # Fullscreen change notice from JS
            self._on_fs_change(self._menu, True if msg == 'FS' else False)
        elif msg == 'PRINT':
            self._buttons.print.click()
        
        self.msg_topy = "" # Reset for successive simliar changes
    
    @traitlets.observe("msg_tojs")
    def _reset(self, change):
        self.msg_tojs = "" # Reset for successive simliar changes
    
    @traitlets.observe("_colors")
    def _run_on_change(self, change):
        if change.new and hasattr(self, '_run_func'):
            self._run_func()
            delattr(self, '_run_func')

    def _try_exec_with_fallback(self, func):
        if self._theme.value == "Jupyter":
            self._colors = jupyter_colors # Reset for getting latest colors from these keys
            self.msg_tojs = "SetColors"
            self._run_func = func # called when javascript sets colros
        else:
            func() # Direct call
    
    def _on_fs_change(self, ctx, value):
        ctx.update_state('fscreen', value) # make icons consistent
        if value:
            ctx.ws.mainbox.add_class('FullScreen')
        else:
            ctx.ws.mainbox.remove_class('FullScreen')   
    
    def _toggle_panel(self, ctx):
        closed = not ctx.ws.panelbox.is_open()
        ctx.ws.panelbox.toggle(closed) # show/hide panel


@_fix_trait_sig
class NotesWidget(anywidget.AnyWidget):
    _esm = Path(__file__).with_name('static') / 'notes.js'
    value = traitlets.Unicode('').tag(sync=True)
    popup = traitlets.Bool(False).tag(sync=True)
    

@_fix_init_sig
class LaserPointer(anywidget.AnyWidget):
    _esm = Path(__file__).with_name('static') / 'laser.js'
    _css = Path(__file__).with_name('static') / 'laser.css'
    active = traitlets.Bool(False).tag(sync=True)

        


