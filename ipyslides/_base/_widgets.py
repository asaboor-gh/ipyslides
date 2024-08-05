import uuid
import traitlets
import anywidget

from pathlib import Path
from IPython.display import display


class InteractionWidget(anywidget.AnyWidget):
    _esm =  Path(__file__).with_name('js') / 'interaction.js'
    _uid = traitlets.Unicode(str(uuid.uuid1()), read_only=True).tag(sync=True) # need for frontend display purporse
    _colors = traitlets.Dict().tag(sync=True) # for export
    
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
            self._prog.value = int(msg.lstrip('SHIFT:')) + self._prog.value
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
        elif msg == 'EDIT':
            self._buttons.source.click()
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
    """
    _esm = """
    function render({ model, el }) {
    el.classList.add("jupyter-widgets", "widget-html-content"); // for consistent view
    let div = document.createElement("div");
    div.classList.add("jp-RenderedHTMLCommon","custom-html","jp-mod-trusted");
    function set_html() {
        div.innerHTML = model.get("value");
    }
    el.tabIndex = -1; // need for clickable events
    el.onclick = (event) => {
        event.stopPropagation();
        if (el.classList.contains("clickable-div")) { // only if there, but register onclick anyhow, it does not work otherwise
            model.set("click_state", ((model.get("click_state") + 1) % 2)); // 0 or 1
            model.save_changes();
        };
    };
    model.on("change:value", set_html);
    set_html();
    el.appendChild(div);  
    }
    export default { render }
    """
    _css = """
    .jp-RenderedHTMLCommon.custom-html *:not(code,span, hr) {
       padding:0.1em;
       line-height:1.5; /* make text clearly readable on presentation */
    } 
    .clickable-div > .custom-html { cursor: pointer; }
    .clickable-div > .custom-html:hover, .clickable-div > .custom-html:focus {
        background: var(--bg3-color, rgba(100, 100, 111, 0.2)) !important;
    }
    """
    value = traitlets.Unicode('').tag(sync=True)
    click_state = traitlets.Int(0).tag(sync=True)

    def __init__(self, value = '', click_handler=None, **kwargs):
        kwargs['value'] = value # value set by kwargs
        if click_handler is not None:
            if not callable(click_handler):
                raise TypeError("click_handler should be a function that accepts a change of widget's `click_state` trait.")
            
            self.observe(click_handler, names='click_state')
        super().__init__(**kwargs)

    def __format__(self, spec):
        "This is needed to merge content of this widget into another one properly when used in formatting."
        return f'{self.value:{spec}}'
    
    def __repr__(self):
        return f'<{self.__module__}.HtmlWidget at {hex(id(self))}>'
    
    def observe(self, handler, names = traitlets.All, type="change"):
        "observe traits. `click_state` traits should be observed explicity!"
        if "click_state" in str(names): # only observe clicks explicity
            self.add_class('clickable-div') # only on demand
            
        return super().observe(handler, names=names, type = type)
    
    def display(self):
        "Display this HTML object with oldest metadata."
        return display(self, metadata= {'text/html':self.value}) # metadata to direct display
        

class NotesWidget(anywidget.AnyWidget):
    _esm = Path(__file__).with_name('js') / 'notes.js'
    value = traitlets.Unicode('').tag(sync=True)
    popup = traitlets.Bool(False).tag(sync=True)

    