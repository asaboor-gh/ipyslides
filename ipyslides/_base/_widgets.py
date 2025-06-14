import uuid
import time
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
    "Avoid showing extra kwargs by having a class attribute _no_kwargs"
    params = [inspect.Parameter(key, inspect.Parameter.KEYWORD_ONLY, default=value) 
        for key, value in cls.class_own_traits().items() if not key.startswith('_')] # avoid private
    
    if not hasattr(cls,'_no_kwargs'):
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
    """List widget is a flexible widget that displays clickable items with integer indices and rich html content.
    
    - `options`: List[Any], each item can be any python object.
    - `description`: str, will be displayed as a label above the list.
    - `value`: Any, currently selected value. 
    - `transform`: Callable, function such that transform(item) -> str, for each item in options.
    - `html`: str, HTML representation of the currently selected item through transform.

    You can set `ListWidget.layout.max_height` to limit the maximum height (default 400px) of the list. The list will scroll if it exceeds this height.
    """
    _options    = traitlets.List(read_only=True).tag(sync=True) # will by [(index, obj),...]
    description = traitlets.Unicode('Select an option', allow_none=True).tag(sync=True)
    transform   = traitlets.Callable(None, allow_none=True,help="transform(value) -> str")
    index       = traitlets.Int(None, allow_none=True).tag(sync=True)
    options     = traitlets.List() # only on backend
    value       = traitlets.Any(None, allow_none=True,read_only=True) # only backend
    html        = traitlets.Unicode('',read_only=True, help="html = transform(value)")  # This is only python side
    
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

    def __init__(self, *args, **kwargs):
        if kwargs.get("transform",None) is None: # default transform set
            from ..formatters import htmlize
            self.transform = htmlize
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
        
        if not isinstance(self.transform(options[0]), str):
            raise TypeError("tranform function should return a str")
        
        self.set_trait('_options', [(i, self.transform(op)) for i, op in enumerate(options)])
        return options  

    @traitlets.validate('transform')
    def _validate_func(self, proposal):
        func = proposal['value']
        if self.options and not isinstance(self.transform(self.options[0]), str):
            raise TypeError("tranform function should return a str")
        return func

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
    .animation-slider.slider-hidden input,
    .animation-slider.slider-hidden .widget-readout {
        display: none !important;
    }
    """
    
    value = traitlets.CInt(0).tag(sync=True)          
    description = traitlets.Unicode(None, allow_none=True).tag(sync=True) 
    loop = traitlets.Bool(False).tag(sync=True)     
    nframes = traitlets.CInt(100).tag(sync=True)     
    interval = traitlets.Float(50.0).tag(sync=True) 
    playing = traitlets.Bool(False).tag(sync=True) 
    continuous_update = traitlets.Bool(True).tag(sync=True)
    cyclic = traitlets.Bool(False).tag(sync=True) 

    @traitlets.validate("nframes")
    def _ensure_min_frames(self, proposal):
        value = proposal["value"]
        if not isinstance(value, int):
            raise TypeError(f"nframes should be integere, got {type(value)!r}")
        
        if value < 2:
            raise ValueError(f"nframes > 1 should hold, got {value}")
        return value
        
@_fix_init_sig
class JupyTimer(traitlets.HasTraits):
    """A widget that provides timer functionality in Jupyter Notebook without threading/blocking.
    
    This widget allows you to run a function at specified intervals, with options for 
    looping and control over the timer's state (play/pause/loop). You can change function too by using `run()` again.
    
    The timer widget must be displayed before calling `run()` to take effect.

    ```python
    timer = JupyTimer(description="My Timer")
    display(timer) # must be displayed before running a function to work correctly

    def my_func(msg):
        print(f"Timer tick: {msg}")
        if timer.nticks > 9:
            timer.pause()

    # Run after 1000ms (1 second)
    if not timer.busy(): # executing function or looping
        timer.run(1000, my_func, args=("Hello!",))

    # For continuous execution, run every 1000ms, 10 times as set in my_func
    timer.run(1000, my_func, args=("Loop!",), loop=True)
    ```

    - Automatically displays in Jupyter, but to acces the associated widget you can use `.widget` method.
    - Use `.widget(minimal = True)` if you want to hide GUI, but still needs to be displayed to work.
    - Call attempts during incomplete interval are skipped. You can alway increase `tol` value to fix unwanted skipping.
    - This is not a precise timer, it includes processing overhead, but good enough for general tracking.
    """
    _value = traitlets.CInt(0).tag(sync=True)  
    _callback = traitlets.Tuple((None, (), {}))     
    description = traitlets.Unicode(None, allow_none=True).tag(sync=True) 
    nticks = traitlets.Int(0, read_only=True)

    def __init__(self, description = None):
        super().__init__()
        self._animator = AnimationSlider(nframes=2) # fixed 2 frames make it work
        traitlets.dlink((self._animator,'value'),(self,'_value'))
        traitlets.link((self,'description'),(self._animator,'description'))
        self.set_trait('description', description) # user set
        self._running = False # executing function
        self._delay = self._animator.interval # check after this much time (ms)
        self._last_called = 0
        self._animator.observe(lambda c: setattr(self, '_last_called', time.time()), 'playing')
    
    def __dir__(self): 
        return "busy clear description elapsed loop nticks pause play run widget".split()
    
    def _repr_mimebundle_(self,**kwargs): # display
        return self._animator._repr_mimebundle_(**kwargs)
    
    @traitlets.observe("_value")
    def _do_call(self, change):
        func, args, kwargs = self._callback

        if ready := self.elapsed >= self._delay:
            self.set_trait("nticks",self.nticks + 1) # how many time intervals passed overall
            
        if func and ready and not self._running: # We need to avoid overlapping calls
            try:
                self._running = True # running call
                func(*args, **kwargs)
            finally:
                self._running = False # free now
                self._last_called = time.time()
    
    @property
    def elapsed(self) -> float:
        """Returns elapsed time since last function call completed in milliseconds.

        If `loop = True`, total time elapsed since start would be approximated as:
            `self.elapsed + self.nticks * interval` (milliseconds)
        """
        return (time.time() - self._last_called) * 1000 # milliseconds
    
    def play(self) -> None: 
        """Start or resume the timer.
        
        If a function was previously set using `run()`, it will be executed at 
        the specified interval. If no function is set, the timer will still run
        but won't execute anything.
        """
        self._animator.playing = True
    
    def pause(self) -> None: 
        """Pause the timer without clearing the underlying function.
        
        The function set by `run()` is preserved and will resume execution when
        `play()` is called again.
        """
        self._animator.playing = False

    def loop(self, b:bool) -> None:
        "Toggle looping programmatically."
        self._animator.loop = b

    def run(self, interval, func, args = (), kwargs = {},loop = False, tol = None) -> None:
        """Set up and start a function to run at specified intervals.
        
        - interval : int. Time between function calls in milliseconds.
        - func : callable. The function to execute.
        - args : tuple, optional. Positional arguments to pass to the function.
        - kwargs : dict, optional. Keyword arguments to pass to the function.
        - loop : bool, optional
            - If True, the function will run repeatedly until paused.
            - If False, the function will run once after `interval` time and stop.
        - tol : int (milliseconds), we check for next execution after `interval - tol`, default is `0.05*interval`.

        **Notes**:

        - The timer widget must be displayed before calling `run()`.
        - Calling `run()` will stop any previously running timer.
        - The first function call occurs after the specified interval.
        """
        if tol is None:
            tol = 0.05*float(interval) # default is 5%
        
        if not (0 < tol < interval):
            raise ValueError("0 < tol < interval should hold!")
        
        if not callable(func): raise TypeError("func should be a callable to accept args and kwargs")
        self.clear()
        self._animator.interval = float(interval) # type casting to ensure correct types given
        self._animator.loop = bool(loop) 
        self._delay = interval - float(tol) # break time to check next, ms
        self._callback = (func, tuple(args), dict(kwargs))
        self.play()

    def widget(self, minimal=False) -> ValueWidget:
        "Get the associated displayable widget. If minimal = True, the widget's size will be visually hidden using zero width and height."
        if minimal:
            self._animator.layout = dict(width='0',height='0',max_width='0',max_height='0')
        return self._animator
    
    def clear(self):
        "Clear function and reset playing state."
        self.set_trait("nticks",0)
        self.pause()
        self._callback = (None, (), {})
        self._last_called = time.time() # seconds

    def busy(self) -> bool:
        """Use this to test before executing next `run()` to avoid overriding.
        
        Returns True:

        - If function is executing right now
        - If loop was set to True, technically it's alway busy.
        
        Otherwise False.
        """
        return bool(self._animator.loop or self._running)
