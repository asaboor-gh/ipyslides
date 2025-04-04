import uuid
import traitlets
import anywidget

from pathlib import Path
from IPython.display import display
from ipywidgets import ValueWidget


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
        self._theme = _widgets.theme

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
        elif msg == 'JUPYTER' and not ('Jupyter' in self._theme.options):
            self._theme.options = ['Jupyter', *self._theme.options] 
            self._theme.value = 'Jupyter' # enable it
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
            self._colors = {} # Reset for getting latest colors
            self.msg_tojs = "SetColors"
            self._run_func = func # called when javascript sets colros
        else:
            func() # Direct call


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

    let old_classes = model.get("_dom_classes"); // Anywidget removed previous function, need to store
    model.on("change:_dom_classes", () => { // Anywidget does not work here
        const nc = model.get("_dom_classes");
        for (let c of old_classes) {
            if (el.classList.contains(c) && nc.indexOf(c) === -1) {
                el.classList.remove(c);
            };
        };
        old_classes = nc; // for next change
        for (let k of nc) {
            if (!el.classList.contains(k)) {
                el.classList.add(k);
            };
        };
    });

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


class AnimationSlider(anywidget.AnyWidget, ValueWidget):
    """This is a simple slider widget that can be used to control the animation with an observer function.

    You need to provide parameters like `nframes` and `interval` (milliseconds) to control the animation. 
    The `value` trait can be observed to get the current frame index.
    The `cyclic` trait can be set to `True` to make the animation cyclic and only works when loop mode is ON.

    ```python
    from plotly.graph_objects import FigureWidget

    fig = FigureWidget()
    fig.add_scatter(y=[1, 2, 3, 4, 5])
    widget = slides.AnimationSlider() # assuming slides is the instance of Slides app

    def on_change(change):
        value = change['new']
        fig.data[0].color = f'rgb({int(value/widget.nframes*100)}, 100, 100)' # change color based on frame index

    widget.observe(on_change, names='value')
    display(widget, fig) # display it in the notebook
    ```

    This widget can be passed to `ipywidgets.interactive` as keyword argument to create a dynamic control for the animation.

    ```python
    from ipywidgets import interact

    @interact(frame=widget)
    def show_frame(frame):
        print(frame)
    ```
    """
    _esm = _esm = Path(__file__).with_name('js') / 'animator.js'
    _css = """
    .animation-slider button {background: transparent; color: inherit;} 
    .animation-slider input[type="range"] {outline: none;}
    .animation-slider button:hover > i,
    .animation-slider button:focus > i,
    .animation-slider button:active {
        scale: 1.25;
        transition: scale 200ms ease;
    }
    .animation-slider button:active {scale: 1.25;}
    .animation-slider button .fa.fa-rotate-left.inactive {opacity: 0.25 !important;}
    """
    
    value = traitlets.Int(0).tag(sync=True)          
    description = traitlets.Unicode(None, allow_none=True).tag(sync=True) 
    loop = traitlets.Bool(False).tag(sync=True)     
    nframes = traitlets.Int(100).tag(sync=True)     
    interval = traitlets.Float(50.0).tag(sync=True) 
    playing = traitlets.Bool(False).tag(sync=True) 
    continuous_update = traitlets.Bool(True).tag(sync=True)
    cyclic = traitlets.Bool(False).tag(sync=True) 
    