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

# used to set focusable elements for click-to-focus feature in _layout.py and interaction.js
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
        self.ws = _widgets # keep reference to widgets
        super().__init__(*args, **kwargs)
        self.prog = _widgets.sliders.progress
        self._menu = _widgets._ctxmenu
        self._callbacks = {
            'CCTX': self._menu.hide, # close context menu
            'NEXT': self.ws.buttons.next.click,
            'PREV': self.ws.buttons.prev.click,
            'PRINT': self.ws.buttons.print.click,
        }

    @traitlets.observe("msg_topy")
    def _see_changes(self, change):
        msg = change.new
        if not msg:
            return # Message set empty, do not waste time
        
        if msg.startswith('menu:'):
            self._menu.select(msg.split(':')[1]) # select menu option
        elif msg in self._callbacks:
            self._callbacks[msg]() # call the callback
        elif 'SHIFT:' in msg:
            self.prog.value = self.prog.value + int(msg.lstrip('SHIFT:')) # shift by given offset 
        elif 'CTX:' in msg:
            # Context menu requested at given coordinates
            coords = msg.lstrip('CTX:').split(',')
            if len(coords) == 2:
                try:
                    xPerc = round(float(coords[0]),2)
                    yPerc = round(float(coords[1]),2)
                    self._menu.show(xPerc, yPerc)
                except: pass
        elif "Draw:" in msg:
            self._menu.ws.drawer.toggle(False if "OFF" in msg else True) # toggle drawing board
        elif msg == 'JUPYTER' and not ('Jupyter' in self.ws.theme.options):
            self.ws.theme.options = ['Jupyter', *self.ws.theme.options] 
            self.ws.theme.value = 'Jupyter' # enable it
        elif msg == 'LOADED':
            if self.ws.checks.notes.value: # Notes window already there
               self.ws.checks.notes.value = False # closes unlinked window
               self.ws.checks.notes.value = True # opens new linked window

            self.msg_tojs = 'SwitchView' # Trigger view
        elif 'mode-' in msg: # layout mode changes
            self._menu._on_mode_change(msg)
        
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
        if self.ws.theme.value == "Jupyter":
            self._colors = jupyter_colors # Reset for getting latest colors from these keys
            self.msg_tojs = "SetColors"
            self._run_func = func # called when javascript sets colros
        else:
            func() # Direct call 

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

        


