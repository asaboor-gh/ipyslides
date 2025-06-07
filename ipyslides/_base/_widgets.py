import uuid
import traitlets
import inspect
import anywidget

from pathlib import Path
from ipywidgets import ValueWidget


def _fix_init_sig(cls):
    # widgets ruin signature of subclass, let's fix it
    cls.__signature__ = inspect.signature(cls.__init__)
    return cls

def _fix_trait_sig(cls):
    params = [inspect.Parameter(key, inspect.Parameter.KEYWORD_ONLY, default=value) 
        for key, value in cls.class_own_traits().items() if not key.startswith('_')] # avoid private
    params.append(inspect.Parameter('kwargs', inspect.Parameter.VAR_KEYWORD)) # Inherited widgets traits
    cls.__signature__ = inspect.Signature(params)
    return cls


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

@_fix_trait_sig
class ListWidget(anywidget.AnyWidget,ValueWidget):
    """List widget that displays clickable items with integer values and rich html content.
    
    The `options` trait is a list of items to be displayed. Each item can be any python object.
    The `description` trait is a string that will be displayed as a label above the list.

    The `value` trait is the currently selected value. 
    The `html` trait returns the HTML representation of the currently selected item.
    You can give `transform` function that accepts a value and return html string. Default is automatically transformed to html.
    You can set `ListWidget.layout.max_height` to limit the maximum height (default 400px) of the list. The list will scroll if it exceeds this height.
    """
    _options = traitlets.List(read_only=True).tag(sync=True) # will by [(index, obj),...]
    description = traitlets.Unicode('Select an option', allow_none=True).tag(sync=True)
    index = traitlets.Int(None, allow_none=True).tag(sync=True)
    options = traitlets.List() # only on backend
    value = traitlets.Any(None, allow_none=True,read_only=True) # only backend
    html = traitlets.Unicode('',read_only=True)  # This is only python side
    
    _esm = """
    function render({model, el}) {
        el.classList.add('list-widget'); // want top level for layout settings by python
        
        function updateDescription() {
            const desc = model.get('description');
            el.dataset.description = desc || '';
            el.classList.toggle('has-description', Boolean(desc));
        }
        
        function createItem(opt) {
            const item = document.createElement('div');
            item.className = 'list-item';
            
            const [index, html] = opt; // Always expects a tuple (index, html)
            item.innerHTML = html;
            item.dataset.index = index; // Use index for identification
            
            if (index === model.get('index')) {
                item.classList.add('selected');
            }
            
            item.addEventListener('click', () => {
                const newIndex = parseInt(item.dataset.index);
                if (newIndex !== model.get('index')) {
                    model.set('index', newIndex); // Update index on click
                    model.save_changes();
                }
            });
            
            return item;
        }
        
        function updateList() {
            el.innerHTML = ''; // Clear the list
            model.get('_options').forEach((opt) => {
                el.appendChild(createItem(opt));
            });
        }

        function updateSelected(index) {
            el.childNodes.forEach(item => {
                item.classList.remove('selected');
                if (parseInt(item.dataset.index) === index) {
                    item.classList.add('selected');
                }
            });
        }
        
        updateDescription();
        updateList();

        model.on('change:index', () => { // This is apparent internal change, without setting index, not intended to be used by user
            const index = model.get('index');
            updateSelected(index);
        });
        
        model.on('change:description', updateDescription);
        model.on('change:_options', updateList);

        // Intercept custom messages from the backend
        model.on('msg:custom', (msg) => {
            if (msg?.active >= 0) { // Mock active, not changing index, for TOC list
                updateSelected(msg.active); 
            }
        });
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

    def __init__(self, transform = None, *args, **kwargs):
        if callable(transform):
            self._transform = transform
        else:
            from ..formatters import htmlize
            self._transform = htmlize

        super().__init__(*args, **kwargs)
        self.layout.max_height = '400px' # default max height

    @traitlets.validate('index')
    def _set_value_html(self,proposal):
        index = proposal['value']
        if index is None:
            self.set_trait('html','')
            self.set_trait('value',None)
            return index 
        
        _max = len(self.options) - 1
        if isinstance(index, int) and 0 <= index <= _max :
            self.set_trait('html',self._options[index][1]) # second item is html
            self.set_trait('value',self.options[index]) 
            return index
        else:
            raise ValueError(f"index should be None or integer in bounds [0, {_max}], got {index}")

    @traitlets.validate('options')
    def _validate_options(self, proposal):
        options = proposal['value']
        if not isinstance(options, (list,tuple)):
            raise traitlets.TraitError("Options must be a list/tuple.")
        
        if not options: 
            self.set_trait('_options', options) # adjust accordingly, set_trait for readonly
            return options  # allow empty list
        
        if not isinstance(self._transform(options[0]), str):
            raise TypeError("tranform given at initialization should be like map(transform, options) -> (str,...)")
        
        self.set_trait('_options', [(i, self._transform(op)) for i, op in enumerate(options)])
        return options    

    def fmt_html(self):
        from ..formatters import _inline_style
        klass = 'list-widget has-description' if self.description else 'list-widget'
        html = ''
        for i, opt in self._options:
            html += '<div class="list-item {}">{}</div>'.format("selected" if i == self.index else "", opt)
        return f'''<style>{self._css}</style>
            <div class="{klass}" {_inline_style(self)} data-description="{self.description}">{html}</div>'''
            

@_fix_trait_sig
class NotesWidget(anywidget.AnyWidget):
    _esm = Path(__file__).with_name('js') / 'notes.js'
    value = traitlets.Unicode('').tag(sync=True)
    popup = traitlets.Bool(False).tag(sync=True)


@_fix_trait_sig
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
    