import uuid
import traitlets
import sysconfig
import anywidget

from pathlib import Path
from IPython.display import display

def _hot_reload_dev_only(file):
    path = Path(__file__).with_name('js') / file
    egg_path = Path(sysconfig.get_paths()["purelib"]) / 'ipyslides.egg-link'
    if egg_path.exists(): # Package installed as editable
        return path # Developers
    return path.read_text() # Normal users 


class InteractionWidget(anywidget.AnyWidget):
    _esm =  _hot_reload_dev_only("interaction.js")
    _uid = traitlets.Unicode(str(uuid.uuid1()), read_only=True).tag(sync=True) # need for frontend display purporse

    msg_topy = traitlets.Unicode('').tag(sync=True)
    msg_tojs = traitlets.Unicode('').tag(sync=True)

    def __init__(self, _widgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._toggles = _widgets.toggles
        self._buttons = _widgets.buttons
        self._checks = _widgets.checks
        self._toast_html = _widgets.htmls.toast
        self._prog = _widgets.sliders.progress
        self._deactivate = _widgets._deactivate

    @traitlets.observe("msg_topy")
    def _see_changes(self, change):
        quick_menu_was_open = self._toggles.menu.value # JS message should not result in its closing
        msg = change.new
        if not msg:
            return # Message set empty, do not waste time
        if 'SHIFT:' in msg:
            new_index = int(msg.lstrip('SHIFT:')) + self._prog.index
            self._prog.index = max(0, new_index) if new_index < self._prog.index else min(new_index,len(self._prog.options) - 1)
        elif msg == 'TFS': 
            self._toggles.fscreen.value = not self._toggles.fscreen.value
        elif msg == 'NEXT':
            self._buttons.next.click()
        elif msg == 'PREV':
            self._buttons.prev.click()
        elif msg == 'HOME':
            self._buttons.home.click()
        elif msg == 'END':
            self._buttons.end.click()
        elif msg == 'TLSR':
            self._toggles.laser.value = not self._toggles.laser.value
        elif msg == 'ZOOM':
            self._toggles.zoom.value = not self._toggles.zoom.value
        elif msg == 'TPAN':
            self._buttons.setting.click()
        elif msg == 'SCAP':
            self._buttons.capture.click()
        elif msg == 'EDIT':
            self._buttons.source.click()
        elif msg == 'TVP' and not self._toggles.window.disabled:
            self._toggles.window.value = not self._toggles.window.value
        elif msg == 'NOVP': # Other than voila, no viewport button
            self._toggles.window.disabled = True
            self._toggles.window.layout.display = 'none'
        elif msg == 'LOADED':
            if self._checks.notes.value: # Notes window already there
               self._checks.notes.value = False # closes unlinked window
               self._checks.notes.value = True # opens new linked window

            self.msg_tojs = 'SwitchView' # Trigger view

            if hasattr(self,'_sync_args'):
                self.msg_tojs = f'SYNC:ON:{self._sync_args["interval"]}'

        elif msg in ('FS','!FS'): # This is to make sure visual state of button and slides are correct
            if msg == 'FS':
                self._toggles.fscreen.icon = 'minus'
            else:
                self._toggles.fscreen.icon = 'plus'
        elif msg == 'KSC':
            self._toast_html.value = 'KSC'
        elif msg == 'RACTIVE': # Remove active states for intro
            self._deactivate()
        
        if quick_menu_was_open: 
            self._toggles.menu.value = True # it might get closed by using some buttons. reset it

        self.msg_topy = "" # Reset for successive simliar changes
    
    @traitlets.observe("msg_tojs")
    def _reset(self, change):
        self.msg_tojs = "" # Reset for successive simliar changes


class HtmlWidget(anywidget.AnyWidget):
    """This introduces a trait 'click_state' which would be toggled between 0 and 1 on each click.
    You can either have a function for click or mimic a double click as well.
    """
    _esm = """
    export function render({ model, el }) {
    el.classList.add("jupyter-widgets", "widget-html-content"); // for consistent view
    let div = document.createElement("div");
    div.classList.add("jp-RenderedHTMLCommon","custom-html","jp-mod-trusted");
    function set_html() {
        div.innerHTML = model.get("value");
    }
    el.tabIndex = -1; // need for clickable events
    el.onclick = (event) => {
        model.set("click_state", ((model.get("click_state") + 1) % 2)); // 0 or 1
        model.save_changes();
    };
    model.on("change:value", set_html);
    set_html();
    el.appendChild(div);  
    }
    """
    _css = """
    .jp-RenderedHTMLCommon.custom-html *:not(code,span, hr) {
       padding:0.1em;
       line-height:150%; /* make text clearly readable on presentation */
    } 
    .clickable-div > .custom-html { cursor: pointer; }
    .clickable-div > .custom-html:hover, .clickable-div > .custom-html:focus {
        background: var(--hover-bg, rgba(100, 100, 111, 0.2)) !important;
    }
    """
    value = traitlets.Unicode('').tag(sync=True)
    click_state = traitlets.Int(0).tag(sync=True)

    def __init__(self, value, *args, click_pointer = False, **kwargs):
        kwargs['value'] = value # initial value set by kwargs
        if click_pointer:
            self.add_class('clickable-div')
        super().__init__(*args, **kwargs)

    def __format__(self, spec):
        "This is needed to merge content of this widget into another one properly when used in formatting."
        return f'{self.value:{spec}}'
    
    def display(self):
        "Display this HTML object."
        return display(self, metadata= {'text/html':self.value}) # metadata to direct display
        

class NotesWidget(anywidget.AnyWidget):
    _esm = _hot_reload_dev_only('notes.js')
    value = traitlets.Unicode('').tag(sync=True)
    popup = traitlets.Bool(False).tag(sync=True)

    