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


class ListWidget(anywidget.AnyWidget,ValueWidget):
    """List widget that displays clickable items with integer values and rich html content.
    You can observe the `value` trait to run a function on selection.
    The `options` trait is a list of items to be displayed. Each item can be an htlm string or a tuple of (value, html).
    The `description` trait is a string that will be displayed as a label above the list.

    The `value` trait is the currently selected value. If list elements are strings, the value is the index of the selected item.
    You can set `ListWidget.layout.max_height` to limit the maximum height (default 400px) of the list. The list will scroll if it exceeds this height.
    """
    _active = traitlets.Int(None, allow_none=True).tag(sync=True)
    value = traitlets.Int(None, allow_none=True).tag(sync=True)
    options = traitlets.List().tag(sync=True)
    description = traitlets.Unicode('Select an option', allow_none=True).tag(sync=True)
    
    _esm = """
    function render({model, el}) {
        el.classList.add('list-widget'); // want top level for layout settings by python
        
        function updateDescription() {
            const desc = model.get('description');
            el.dataset.description = desc || '';
            el.classList.toggle('has-description', Boolean(desc));
        }
        
        function createItem(opt, index) {
            const item = document.createElement('div');
            item.className = 'list-item';
            
            const [value, html] = Array.isArray(opt) ? opt : [index, opt];
            item.innerHTML = html;
            item.dataset.value = value;
            
            if (parseInt(value) === model.get('value')) {
                item.classList.add('selected');
            }
            
            item.addEventListener('click', () => {
                const newValue = parseInt(item.dataset.value);
                if (newValue !== model.get('value')) {
                    model.set('value', newValue);
                    model.save_changes();
                }
            });
            
            return item;
        }
        
        function updateList() {
            el.innerHTML = '';
            model.get('options').forEach((opt, index) => {
                el.appendChild(createItem(opt, index));
            });
        }
        
        updateDescription();
        updateList();
        
        model.on('change:value', () => {
            const value = model.get('value');
            model.set('_active', value); // this will show which item is selected in the list
            model.save_changes(); 
        });

        model.on('change:_active', () => { // This is apparent internal change, without setting value, not intended to be used by user
            const active = model.get('_active');
            el.childNodes.forEach(item => {
                item.classList.remove('selected');
                if (parseInt(item.dataset.value) === active) {
                    item.classList.add('selected');
                }
            });
        });
        
        model.on('change:description', updateDescription);
        model.on('change:options', updateList);
    }

    export default { render }
    """

    _css = """
    .list-widget {
        display: flex;
        flex-direction: column;
        border-radius: 4px;
        overflow-y: auto; /* user can set max height, so allow this */
        margin-block: 0.5em 0.5em;
    }
    .list-widget:hover .list-item {
        border: 1px solid var(--bg3-color, #ccc);
        margin: 0.5px; /* feels like buttons */
        border-radius: 4px;
    }
    .list-widget:hover .list-item.selected {
        border-left: 2px solid var(--accent-color, #007bff); /* show selected item */
    }
    .list-widget.has-description {
        padding-top: 1em; /* space for description font + padding */
        position: relative;
    }
    .list-widget.has-description::before {
        position: absolute;
        top: 0;
        left: 0;
        content: attr(data-description);
        align-items: center;
        font-size: 0.7em;
        padding: 0.25em 0.5em;
        color: var(--fg2-color, #333);
        display: block;
    }
    .list-item {
        align-items: center;
        padding: 0.25em 0.5em;
        cursor: pointer;
    }
    .list-item > * {
        margin-block: 0 0;
    }
    .list-item:hover {
        background: var(--bg3-color, #f5f5f5);
        font-weight: bold;
        transition: all 0.2s ease;
    }
    .list-item.selected {
        background: var(--bg3-color, #eee);
        font-weight: bold;
        border-left: 2px solid var(--accent-color, #007bff);
    }
    .list-item:active {
        transform: scale(0.99);
    }
    """  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout.max_height = '400px' # default max height

    @property
    def value_html(self):
        "Returns the HTML of the currently selected item. This is not a traitlet, just an accessor of html representation for convenience."
        if self.value is None:
            return None
        if isinstance(self.options[self.value], str):
            return self.options[self.value]
        else:
            return self.options[self.value][1]

    @traitlets.validate('options')
    def _validate_options(self, proposal):
        options = proposal['value']
        if not isinstance(options, (list,tuple)):
            raise traitlets.TraitError("Options must be a list/tuple.")
        for opt in options:
            if not isinstance(opt, (str, tuple)):
                raise traitlets.TraitError("Each option must be a string or a tuple.")
            if isinstance(opt, tuple):
                if len(opt) != 2:
                    raise traitlets.TraitError("Each tuple option must have exactly two elements.")
                if not isinstance(opt[0], int):
                    raise traitlets.TraitError("The first element of each tuple option must be an integer value.")
                if not isinstance(opt[1], str):
                    raise traitlets.TraitError("The second element of each tuple option must be a string (HTML).")
            
        return options    

    def fmt_html(self):
        from ..formatters import _inline_style
        klass = 'list-widget has-description' if self.description else 'list-widget'
        html = ''
        for i, opt in enumerate(self.options):
            if isinstance(opt, str):
                html += '<div class="list-item {}">{}</div>'.format("selected" if i == self.value else "", opt)
            elif isinstance(opt, tuple):
                html += '<div class="list-item {}">{}</div>'.format("selected" if opt[0] == self.value else "", opt[1])
        return f'''<style>{self._css}</style>
            <div class="{klass}" {_inline_style(self)} data-description="{self.description}">{html}</div>'''
            

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
    
    value = traitlets.CInt(0).tag(sync=True)          
    description = traitlets.Unicode(None, allow_none=True).tag(sync=True) 
    loop = traitlets.Bool(False).tag(sync=True)     
    nframes = traitlets.CInt(100).tag(sync=True)     
    interval = traitlets.Float(50.0).tag(sync=True) 
    playing = traitlets.Bool(False).tag(sync=True) 
    continuous_update = traitlets.Bool(True).tag(sync=True)
    cyclic = traitlets.Bool(False).tag(sync=True) 
    