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
    _nfs = traitlets.Dict().tag(sync=True) # frame counts per slide, for js side use
    _pfs = traitlets.Dict().tag(sync=True) # parts counts per slide, for js side use
    _fkws = traitlets.Dict().tag(sync=True) # footer kws for js side use
    _fsels = traitlets.Unicode(focus_selectors, read_only=True).tag(sync=True) # need for frontend focus management by click
    
    msg_topy = traitlets.Unicode('').tag(sync=True)
    msg_tojs = traitlets.Unicode('').tag(sync=True)

    def __init__(self, _widgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._toggles = _widgets.toggles
        self._buttons = _widgets.buttons
        self._checks = _widgets.checks
        self._loading = _widgets.htmls.loading
        self._prog = _widgets.sliders.progress
        self._theme = _widgets.theme

    @traitlets.observe("msg_topy")
    def _see_changes(self, change):
        quick_menu_was_open = self._toggles.menu.value # JS message should not result in its closing
        msg = change.new
        if not msg:
            return # Message set empty, do not waste time
        if 'SHIFT:' in msg:
            self._prog.value = self._prog.value + int(msg.lstrip('SHIFT:')) # shift by given offset
        elif msg == 'TFS': 
            self._toggles.fscreen.value = not self._toggles.fscreen.value
        elif msg == 'NEXT':
            self._buttons.next.click()
        elif msg == 'PREV':
            self._buttons.prev.click()
        elif msg == 'KSC':
            self._buttons.ksc.click()
        elif msg == 'TLSR':
            self._toggles.laser.value = not self._toggles.laser.value
        elif msg == 'TPAN':
            self._buttons.panel.click()
        elif msg == 'EDIT':
            self._buttons.source.click()
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

        elif msg in ('FS','!FS'): # This is to make sure visual state of button and slides are correct
            if msg == 'FS':
                self._toggles.fscreen.icon = 'minus'
            else:
                self._toggles.fscreen.icon = 'plus'
        elif msg == 'PRINT':
            self._buttons.print.click()
        elif msg == 'PRINT2':
            self._buttons.print2.click()
        
        if quick_menu_was_open: 
            self._toggles.menu.value = True # it might get closed by using some buttons. reset it

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

        


