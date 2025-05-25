"""
Enhanced version of ipywidgets's interact/interactive functionality.
"""

__all__ = ['interactive','interact', 'classed', 'patched_plotly','disabled'] # other need to be explicity imported

import re, textwrap
import inspect 
import traitlets

from contextlib import contextmanager
from collections import namedtuple

from IPython.display import display
from anywidget import AnyWidget

from .formatters import get_slides_instance
from .utils import _build_css, _dict2css
from ._base.widgets import ipw # patch ones required here
from ._base._widgets import _fix_init_sig, AnimationSlider

@contextmanager
def disabled(widget):
    "Disable widget and enable it after code block runs under it. Useful to avoid multiple clicks on a button that triggers heavy operations."
    widget.disabled = True
    widget.add_class("Context-Disabled")
    try:
        yield
    finally:
        widget.disabled = False
        widget.remove_class("Context-Disabled")

@contextmanager
def _hold_running_slide_builder():
    "Hold the running slide builder to restrict slides specific content."
    if (slides := get_slides_instance()):
        with slides._hold_running():
            yield
    else:
        yield

class FullscreenButton(AnyWidget):
    """A button widget that toggles fullscreen mode for its parent element.
    You may need to set `position: relative` on parent element to contain it inside.
    """
    
    _css = """
    .fs-btn.ips-fs {
        position: absolute; top: 2px; right: 2px;
    }
    .fs-btn.ips-fs button {
        border: none !important;
        padding: 4px;
        border-radius: 4px;
        opacity: 0.4;
        transition: opacity 0.2s;
        background: transparent;
        font-size: 16px;
        color: var(--accent-color, inherit);
    }
    .fs-btn.ips-fs button:hover {opacity:1;text-shadow:0 1px var(--bg2-color,#8988)}
    """

    _esm = """
    function render({ el }) {
        const btn = document.createElement('button');
        el.className = 'fs-btn ips-fs';
        btn.innerHTML = '<i class="fa fa-expand"></i>';
        btn.title = 'Toggle Fullscreen';

        btn.onclick = () => {
            const parent = el.parentElement; // need define inside, not avaialbe until load
            if (!document.fullscreenElement || document.fullscreenElement !== parent) {
                parent.requestFullscreen();
                parent.style.background = 'var(--bg1-color, var(--jp-widgets-input-background-color, inherit))'; // available everywhere
                btn.querySelector('i').className = 'fa fa-compress';
            } else if (document.fullscreenElement === parent) {
                document.exitFullscreen();
                parent.style.background = 'unset';
                btn.querySelector('i').className = 'fa fa-expand';
            }
        };

        // Update icon if user exits fullscreen via Esc key
        document.addEventListener('fullscreenchange', () => {
            const parent = el.parentElement; // redefine
            const isFullscreen = parent === document.fullscreenElement;
            btn.querySelector('i').className = `fa fa-${isFullscreen ? 'compress' : 'expand'}`;
            parent.style.background = isFullscreen ? 'var(--bg1-color, var(--jp-widgets-input-background-color, inherit))' : 'unset';
        });

        el.appendChild(btn);
    }
    export default { render }
    """

    def __init__(self):
        super().__init__()
        self.layout.width = 'min-content'

def _func2widget(func, mutuals):
    func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
    for p1, p2 in mutuals:
        if p1 in func_params and p2 in func_params:
            raise ValueError(
                f"Function {func} cannot have paramters that depend on each other, {p1!r} depends on {p2!r} "
                f"Use independent parameter inside callbacks as self.params.{p2} instead of passing it directly.")

    out = ipw.Output()
    if klass := func.__dict__.get('_css_class', None):
        out.add_class(klass)
        out._kwarg = klass # store for access later

    out._old_kws = {} # store old kwargs to avoid re-running the function if not changed
    out._fparams = func_params
    
    def call_func(kwargs):
        out.clear_output(wait=True) # clear previous output
        with out:
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in out._fparams}

            # Compare values properly by checking each parameter
            values_changed = any(
                k not in out._old_kws or filtered_kwargs[k] != out._old_kws[k]
                for k in filtered_kwargs
            )
            
            if values_changed or not out._fparams: # function may not have arguments but can be run via click
                func(**filtered_kwargs) # Call the function with filtered parameters only if changed or no params
            
            out._old_kws.update(filtered_kwargs) # update old kwargs to latest values
            
    out._call_func = call_func # set the function to be called when the widget is updated
    return out

def _hint_update(btn, remove = False):
    (btn.remove_class if remove else btn.add_class)('Rerun')
    btn.button_style = '' if remove else 'warning' # for notebook outside slides, CSS not applied

def _run_callbacks(outputs, kwargs, box):
    for out in outputs:
        if hasattr(out, '_call_func'):
            out._call_func(box.kwargs if box else kwargs) # get latest from box due to internal widget changes
            

class AnyTrait(ipw.fixed):
    def __init__(self, key,  name, trait, kwargs):
        self._key = key # its own name
        self._name = name 
        self._trait = trait
        if not name in kwargs:
            raise ValueError(f"Given key {name} is not in other keyword arguments.")
        
        widget = kwargs[name]
        if isinstance(widget, ipw.fixed):
            widget = widget.value 

        if not isinstance(widget, ipw.DOMWidget):
            raise TypeError(f"Given key {name!r} is not a widget in keyword arguments.")
        
        if trait not in widget.trait_names():
            raise traitlets.TraitError(f"Parameter {name!r} does not have trait {trait!r}")
        
        # Initialize with current value first, then link
        super().__init__(value=getattr(widget,trait,None))
        traitlets.dlink((widget, trait),(self, 'value'))

def _format_docs(**variables):
    def decorator(obj):
        if obj.__doc__:
            try:
                obj.__doc__ = obj.__doc__.format(**variables)
            except Exception as e:
                raise ValueError(f"Failed to format docs for {obj.__name__}: {str(e)}") from e
        return obj
    return decorator

# ipywidgets AppLayout restricts units to px,fr,% or int, need to add rem, em
def _size_to_css(size):
    if re.match(r'\d+\.?\d*(px|fr|%|em|rem|pt)$', size):
        return size
    if re.match(r'\d+\.?\d*$', size):
        return size + 'fr'
    raise TypeError("the pane sizes must be in one of the following formats: "
        "'10px', '10fr', '10em','10rem', '10pt', 10 (will be converted to '10fr')."
        "Conversions: 1px = 1/96in, 1pt = 1/72in 1em = current font size"
        "Got '{}'".format(size))

_css_info = textwrap.indent('\n**Python dictionary to CSS**\n' + _dict2css, '    ')

@_fix_init_sig
@_format_docs(css_info = _css_info)
class InteractBase(ipw.interactive):
    """Enhanced interactive widgets with multiple callbacks and fullscreen support.
    
    Use `interctive` function or `@interact` decorator for simpler use cases. For comprehensive dashboards, subclass this class.

    **Features**:    

    1. Multiple callback support through @callback decorator
    2. CSS Grid layout system with flexible templating
    3. Extended widget trait observation beyond just 'value'
    4. Automatic widget grouping and layout management
    5. Built-in fullscreen support
    6. Run button for manual updates

    **Basic Usage**:    

    ```python
    from ipyslides.interaction import InteractBase, callback
    import ipywidgets as ipw
    import plotly.graph_objects as go

    class MyDashboard(InteractBase):
        def _interactive_params(self):
            return {{
                'x': ipw.IntSlider(0, 0, 100),
                'y': {{'x': 'value'}},  # observe x's value
                'fig': ipw.fixed(go.FigureWidget())
            }}
            
        @callback
        def update_plot(self, x, fig): # gets out-0 class
            fig.data = []
            fig.add_scatter(x=[0, x], y=[0, x**2])
            
        @callback('out-stats')  # custom class for styling
        def show_stats(self, y):
            print(f"Distance: {{np.sqrt(1 + y**2)}}")
    
    # Create and layout
    dash = MyDashboard(auto_update=True)
    dash.relayout(
        left_sidebar=dash.groups.controls,  # controls on left
        center=['fig', 'out-stats']  # plot and stats in center
    )
    
    # Style with CSS Grid
    dash.set_css(center={{
        'grid': 'auto-flow / 1fr 2fr',
        '.fig': {{'grid-area': '1 / 2 / span 2 / 3'}},
        '.out-stats': {{'padding': '1rem'}}
    }})
    ```

    **Parameters**:      

    - auto_update (bool): Update outputs automatically on widget changes
    - app_layout (dict): Initial layout configuration
        - header: List[str] - Top widgets
        - left_sidebar: List[str] - Left side widgets 
        - center: List[str] - Main content area
        - right_sidebar: List[str] - Right side widgets
        - footer: List[str] - Bottom widgets
    - grid_css (dict): CSS Grid properties for layout customization
        - See set_css() method for details
        - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

    **Widget Parameters** (`_interactive_params`'s returned dict):

    - Regular ipywidgets with value trait
    - Fixed widgets using ipw.fixed()
    - Dict {{'widget': 'trait'}} for observing specific traits, 'widget' must be in kwargs
    - Any DOM widget that needs display
    - Plotly FigureWidgets (use patched_plotly for selection support)

    **Callbacks**:   

    - Methods decorated with @callback
    - Optional CSS class via @callback('out-myclass')
    - CSS class must start with 'out-'
    - Numerical classes (out-1, out-2) reserved for auto-assignment
    - Each callback gets only needed parameters
    - Updates happen only when relevant parameters change
        
    **Attributes & Properties**:  

    - groups: NamedTuple(controls, outputs, others) - Widget names by type
    - outputs: Tuple[Output] - Output widgets from callbacks
    - params: NamedTuple of all parameters used in this interact, including fixed widgets. 
      Can be accessed inside callbacks with self.params.<name> and change their traits other than passed to the callback.

    **Methods**:      

    - set_css(main, center): Update grid CSS
    - relayout(**kwargs): Reconfigure widget layout
        
    **Notes**:     

    - Widget descriptions default to parameter names if not set
    - Animation widgets work even with manual updates
    - Use AnimationSlider instead of ipywidgets.Play
    - Fullscreen button added automatically
    - Run button shows when updates needed

    {css_info}
    """
    def __init__(self, auto_update=True, app_layout= None, grid_css={}):
        self._auto_update = auto_update
        self._grid_css = grid_css
        self._mutuals = [] # dependent parameters 
        self._css_class = 'i-'+str(id(self))
        self._style_html = ipw.HTML()
        self._style_html.layout.position = 'absolute' # avoid being grid part
        self.set_css(main=grid_css) # after assigning above
        self._app = ipw.AppLayout().add_class('interact-app') # base one
        self._app.layout.display = 'grid' # for correct export to html, other props in set_css
        self._app.layout.position = 'relative' # contain absolute items inside
        self._app._size_to_css = _size_to_css # enables em, rem
        
        self._iparams = {} # just empty reference
        extras = self._fix_kwargs() # params are internally fixed
        if not self._iparams: # need to interact anyhow
            auto_update = False
        
        self._icallbacks = self._interactive_callbacks() # callbacks after collecting params
        if not isinstance(self._icallbacks, (list, tuple)):
            raise TypeError("_interactive_callbacks should return a tuple of functions!")
        
        if not self._icallbacks:
            raise ValueError("at least one interactive function required!")
    
        outputs = self._func2widgets() # build stuff
        super().__init__(self._run_updates, {'manual':not auto_update,'manual_name':''}, **self._iparams)
        
        btn = getattr(self, 'manual_button', None) # need it above later
        self.add_class('ips-interact').add_class(self._css_class)
        self.layout.position = 'relative' # contain absolute items inside
        self.layout.height = 'max-content' # adopt to inner height

        self.children += (*extras, *outputs, self._style_html) # add extra widgets to box children
        self.out.layout.height = '0' # We do not print stuff there, so reclaim space when error thrown
        
        for i, out in enumerate([out for out in outputs if not hasattr(out, '_kwarg')]): # user set css_class
            out.add_class(f'out-{i}')
            out._kwarg = f'out-{i}'

        for w in self.kwargs_widgets:
            c = getattr(w, '_kwarg','')
            if isinstance(w, ipw.fixed):
                w = w.value
            getattr(w, 'add_class', lambda v: None)(c) # for grid area

            # If requires click to run, animations still should work
            if btn and isinstance(w, (ipw.Play, AnimationSlider)):
                w.continuous_update = False
                w.observe(self.update, names='value')

        if btn:
            for w in self.kwargs_widgets: # should tell the button to update
                # ipywidgets' Play, Text and added Animation Sliders bypass run button, no need to trigger it
                if not isinstance(w, (ipw.Text, ipw.Play, AnimationSlider)): 
                    w.observe(lambda change: _hint_update(btn),names=['value'])
            
            btn._kwarg = 'run-button'
            btn.add_class('Refresh-Btn').add_class('run-button') # run-button for user
            btn.layout = {'width': 'max-content', 'height':'28px', 'padding':'0 24px'}
            btn.tooltip = 'Update Outputs'
            btn.icon = 'refresh'
            try:
                btn.click() # first run to ensure no dynamic inside
            except Exception as e:
                print(f"Warning: Initial button click faild: {e}")

        self._all_widgets = {w._kwarg: w for w in self.children if hasattr(w, '_kwarg')} # save it once for sending to app layout
        self._groups = self._create_groups(self._all_widgets) # create groups of widgets for later use
        
        if app_layout is not None:
            self._validate_layout(app_layout) # validate arguemnts first
            self.relayout(**app_layout)
        else:
            self.relayout(center=list(self._all_widgets.keys())) # add all to GridBox which is single column
    
    def _validate_layout(self, app_layout):
        if not isinstance(app_layout, dict):
            raise TypeError("app_layout should be a dictionary to relayout widgets!")
        
        allowed_keys = inspect.signature(self.relayout).parameters.keys()
        for key, value in app_layout.items():
            if not key in allowed_keys:
                raise KeyError(f"keys in app_layout should be one of {allowed_keys}, got {key!r}")
            
            if value is not None:
                if key in ["header","footer", "center", "left_sidebar","right_sidebar"]: # special cases
                    if self._auto_update and isinstance(value, (list, tuple)):
                        value = [v for v in value if v != 'run-button'] # avoid throwing error over button, which changes by other paramaters
                    if not isinstance(value, (list,tuple)) or not all([v in self._all_widgets for v in value]):
                        raise TypeError(f"{key!r} in app_layout should be a tuple of names of widgets from {self._all_widgets.keys()!r}, got {value!r}")
    
    def __init_subclass__(cls):
        if (not '_interactive_params' in cls.__dict__) or (not callable(cls._interactive_params)):
            raise AttributeError("implement _interactive_params(self) method in subclass, "
                "which should returns a dictionary of interaction parameters.")
        return super().__init_subclass__()
    
    def relayout(self, 
        header=None, center=None, left_sidebar=None,right_sidebar=None,footer=None,
        pane_widths=None,pane_heights=None,merge=True, 
        grid_gap=None, width=None,height=None, justify_content=None,align_items=None,
        ):
        """Configure widget layout using AppLayout structure.

        **Parameters**:  

        - Content Areas (list/tuple of widget names):
            - header: Widgets at top
            - center: Main content area (uses CSS Grid)
            - left_sidebar: Left side widgets
            - right_sidebar: Right side widgets  
            - footer: Bottom widgets
        - Grid Properties:
            - pane_widths: List[str] - Widths for [left, center, right]
            - pane_heights: List[str] - Heights for [header, center, footer]
            - grid_gap: str - Gap between grid cells
            - width: str - Overall width
            - height: str - Overall height
            - justify_content: str - Horizontal alignment
            - align_items: str - Vertical alignment

        **Size Units** (for pane_widths and pane_heights): `px`, `fr`, `%`, `em`, `rem`, `pt`. Other can be used inside set_css.

        **Example**:       

        ```python
        dash.relayout( # dash is an instance of InteractBase
            left_sidebar=dash.groups.controls,
            center=['fig', *dash.groups.outputs],
            pane_widths=['200px', '1fr', 'auto'],
            pane_heights=['auto', '1fr', 'auto'],
            grid_gap='1rem'
        )
        ```

        **Notes**:        

        - Widget names must exist in the return of _interactive_params and callbacks' classes.
        - Center area uses CSS Grid for flexible layouts
        - Other areas use vertical box layout
        """
        app_layout = {key:value for key,value in locals().items() if key != 'self'}
        self._validate_layout(app_layout)
        other = ipw.VBox([self._style_html, self.out]) # out still be there
        areas = ["header","footer", "center", "left_sidebar","right_sidebar"]

        collected = []
        for key, value in app_layout.items():
            if value and key in areas:
                collected.extend(list(value))
                box = ipw.GridBox if key == 'center' else ipw.VBox
                setattr(self._app, key, box(
                    [self._all_widgets[key] for key in value if key in self._all_widgets],
                    _dom_classes = (key.replace('_','-'),) # for user CSS
                ))
            elif value: # class own traits and Layout properties
                setattr(self._app, key, value)
        
        other.children += tuple([v for k,v in self._all_widgets.items() if k not in collected])
        self.children = (self._app, other, FullscreenButton()) # button be on top to click
    
    @_format_docs(css_info = textwrap.indent(_css_info,'    ')) # one more time indent for nested method
    def set_css(self, main=None, center=None):
        """Update CSS styling for the main app layout and center grid.
        
        **Parameters**:         

        - main (dict): CSS properties for main app layout
            - Target center grid with ` > .center ` selector
            - Target widgets by their parameter names as classes
        - center (dict): CSS properties for center grid section
            - Direct access to center grid (same as main's ` > .center `)
            - Useful for grid layout of widgets inside center area
            - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

        **CSS Classes Available**:  

        - Parameter names from _interactive_params()
        - 'run-button' for manual update button
        - 'out-0', 'out-1'... for callback outputs
        - Custom 'out-*' classes from @callback decorators

        **Example**:       

        ```python
        dash.set_css(
            main={{
                'grid-template-rows': 'auto 1fr auto',
                'grid-template-columns': '200px 1fr',
                '> .center': {{'padding': '1rem'}} # can be done with center parameter too
            }},
            center={{
                'grid': 'auto-flow / 1fr 2fr',
                '.fig': {{'grid-area': '1 / 2 / span 2 / 3'}},
                '.out-stats': {{'padding': '1rem'}}
            }}
        )
        ```

        {css_info}
        """
        if main and not isinstance(main,dict):
            raise TypeError('main should be a nesetd dictionary of CSS properties to apply to main app!')
        if center and not isinstance(center,dict):
            raise TypeError('center should be a nesetd dictionary of CSS properties to apply to central grid!')
        
        
        main_sl = f".{self._css_class}.widget-interact.ips-interact > .interact-app" # directly inside
        cent_sl = f"{main_sl} > .center"
        user_css = ''
        if main:
            user_css += _build_css((main_sl,), main)
        if center:
            user_css += ("\n" + _build_css((cent_sl,), center))
        self._style_html.value = f'<style>{user_css}</style>'
    
    def _interactive_callbacks(self):
        """Collect all methods marked as callbacks. If overridden by subclass, should return a tuple of functions."""
        funcs = []
        for name, attr in self.__class__.__dict__.items():
            if callable(attr) and hasattr(attr, '_is_interactive_callback'):
                # Bind method to instance, we can't get self.method due to traits cuaing issues
                bound_method = attr.__get__(self, self.__class__)
                # Copy CSS class from original function
                if hasattr(attr, '_css_class'):
                    bound_method.__dict__['_css_class'] = attr._css_class
                funcs.append(bound_method)
        return tuple(funcs)
    
    def _validate_params(self, params):
        if not isinstance(params, dict):
            raise TypeError(f"method `_interactive_params(self)` should return a dict of interaction parameters")
                
        for key in params:
            if not isinstance(key, str) or not key.isidentifier():
                raise ValueError(f"{key!r} is not a valid name for python variable!")
           
    def _fix_kwargs(self):
        params = self._interactive_params() # subclass defines it
        self._validate_params(params)   

        extras = {}
        for key, value in params.copy().items():
            if isinstance(value, ipw.fixed) and isinstance(value.value, ipw.DOMWidget):
                extras[key] = value.value # we need to show that widget
            elif isinstance(value,ipw.interactive):
                value.layout.grid_area = 'auto / 1 / auto / -1' # embeded interactive should be full length, unless user sets it otherwise
            elif isinstance(value, (ipw.HTML, ipw.Label, ipw.HTMLMath)):
                params[key] = ipw.fixed(value) # convert to fixed widget, these can't have user interaction available
                extras[key] = value
            elif isinstance(value, ipw.DOMWidget) and not isinstance(value,ipw.ValueWidget): # value widgets are automatically handled
                params[key] = ipw.fixed(value) # convert to fixed widget, to be passed as value
                extras[key] = value # we need to show that widget

        # All params should be fixed above before doing below
        for key, value in params.copy().items():    
            if isinstance(value, dict) and len(value) == 1:
                name, trait = next(iter(value.items()))
                params[key] = AnyTrait(key, name, trait, params)
                self._mutuals.append((key, *value.keys()))
        
        # Set _iparams after clear widgets
        self._iparams = params
        self._reset_descp(extras)
        for key, value in extras.items():
            value._kwarg = key # required for later use
        return tuple(extras.values())
    
    def _reset_descp(self, extras):
        # fix description in extras, like if user pass IntSlider etc.
        for key, value in extras.items():
            if 'description' in value.traits() and not value.description \
                and not isinstance(value,(ipw.HTML, ipw.HTMLMath, ipw.Label)): # HTML widgets and Labels should not pick extra
                value.description = key # only if not given
    
    def _func2widgets(self):
        self._outputs = ()   # reference for later use
        used_classes = {}  # track used CSS classes for conflicts 

        for f in self._icallbacks:
            if not callable(f):
                raise TypeError(f'Expected callable, got {type(f).__name__}. '
                    'Only functions accepting a subset of kwargs allowed!')
            
            # Check for CSS class conflicts
            if klass := f.__dict__.get('_css_class', None):
                if klass in used_classes:
                    raise ValueError(
                        f"CSS class {klass!r} is used by multiple callbacks: "
                        f"{f.__name__!r} and {used_classes[klass]!r}"
                    )
                used_classes[klass] = f.__name__
        
            self._outputs += (_func2widget(f, self._mutuals),) # convert to output widget
        
        del used_classes # no longer needed
        return self._outputs # explicit
    
    def _create_groups(self, widgets_dict):
        groups = namedtuple('WidgetGropus', ['controls', 'outputs', 'others'])
        controls, outputs, others = [], [], []
        for key, widget in widgets_dict.items():
            if isinstance(widget, ipw.Output):
                outputs.append(key)
            elif (isinstance(widget, ipw.ValueWidget) and 
              not isinstance(widget, (ipw.HTML, ipw.Label, ipw.HTMLMath))):
                controls.append(key)
            elif key == 'run-button':
                controls.append(key) # run button is always a control
            else:
                others.append(key)
        return groups(controls=tuple(controls), outputs=tuple(outputs), others=tuple(others))

    @property
    def outputs(self): return getattr(self, '_outputs',())

    @property
    def groups(self): 
        """NamedTuple of widget groups: controls, outputs, others."""
        if not hasattr(self, '_groups'):
            self._groups = self._create_groups(self._all_widgets)
        return self._groups
    
    @property
    def params(self):
        "NamedTuple of all parameters used in this interact, including fixed widgets. Can be access inside callbacks with self.params."
        if not hasattr(self, '_params_tuple'):
            wparams = self._iparams.copy() # copy to avoid changes
            for k, v in self._iparams.items():
                if isinstance(v, ipw.fixed) and isinstance(v.value, ipw.DOMWidget):
                    wparams[k] = v.value # only widget to expose for use, not other fixed values
            self._params_tuple = namedtuple('InteractiveParams', wparams.keys())(**wparams)
        return self._params_tuple
    
    def _run_updates(self, **kwargs):
        btn = getattr(self, 'manual_button', None)
        with _hold_running_slide_builder():
            try:
                if btn:
                    with disabled(btn):
                        _hint_update(btn, remove=True)
                        _run_callbacks(self.outputs, kwargs, self) 
                else:
                    _run_callbacks(self.outputs, kwargs, self) 
            except: # clean duplicate errors, each output has already captured their own
                self.out.outputs = ()

def callback(css_class = None):
    """Decorator to mark methods as interactive callbacks in InteractBase subclasses.
    
    **func**: The method to be marked as a callback.  

    - Must be defined inside a class (not nested).
    - Must be a regular method (not static/class method).
    
    **css_class**: Optional string to assign a CSS class to the callback's output widget.  

    - Must start with 'out-'
    - Cannot be numerical like 'out-1', 'out-2' as these are reserved for automatic assignment
    - Example valid values: 'out-stats', 'out-plot', 'out-details'
    
    **Usage**:                  

    - Inside a subclass of InteractBase, decorate methods with @callback and @callback('out-important') to make them interactive.
    - See example usage in docs of InteractBase.

    **Returns**: The decorated method itself.
    """  
    def decorator(func):
        if not callable(func):
            raise TypeError(f"@callback can only decorate functions, got {type(func).__name__}")
        
        nonlocal css_class # to be used later
        if isinstance(css_class, str):
            func = classed(func, css_class) # assign CSS class if provided
        
        qualname = getattr(func, '__qualname__', '')
        if not qualname:
            raise RuntimeError("@callback can only be used on named functions")
        
        if qualname.count('.') != 1:
            raise RuntimeError(
                f"@callback must be used on instance methods only, got {qualname!r}.\n"
                "Make sure:\n"
                "1. Method is defined directly in class (not nested)\n"
                "2. Not using it on standalone functions\n"
                "3. Not using it on static/class methods"
            )
        
        if isinstance(func, (staticmethod, classmethod)):
            raise TypeError("@callback cannot be used with @staticmethod or @classmethod")
        
        func._is_interactive_callback = True
        
        return func

    # Handle both @callback and @callback('out-myclass') syntax
    if callable(css_class):
        return decorator(css_class)
    return decorator

def classed(func, css_class):
    "Use this function to assign a CSS class to a function being used in interactive, interact."
    if not callable(func):
        raise TypeError(f"Can only function as first paramter, got {type(func).__name__}")
    
    if not isinstance(css_class, str):
        raise TypeError(f"css_class must be a string, got {type(css_class).__name__}")
    
    if not css_class.startswith('out-'):
        raise ValueError(f"css_class must start with 'out-', got {css_class!r}")
    
    if css_class and re.match(r'out-\d+', css_class):
        raise ValueError(f"css_class cannot be numerical like 'out-1', 'out-2', got {css_class!r}")
    
    func.__dict__['_css_class'] = css_class # set on __dict__ to avoid issues with bound methods
    return func


@_format_docs(css_info = _css_info)
def interactive(*funcs, auto_update=True, app_layout=None, grid_css={}, **kwargs):
    """Enhanced interactive widget with multiple callbacks, grid layout and fullscreen support.

    This function is used for quick dashboards. Subclass `InteractBase` for complex applications.
    
    **Features**:    

    - Multiple function support with selective updates
    - CSS Grid layout system
    - Extended widget trait observation
    - Dynamic widget property updates
    - Built-in fullscreen support

    **Basic Usage**:    

    ```python
    from ipyslides.interaction import interactive, classed
    import ipywidgets as ipw
    import plotly.graph_objects as go
    
    fig = go.FigureWidget()
    
    def update_plot(x, y, fig):
        fig.data = []
        fig.add_scatter(x=[0, x], y=[0, y])
    
    dashboard = interactive(
        classed(update_plot, 'out-plot'),  # Assign CSS class to output, otherwise it will be out-0
        x=ipw.IntSlider(0, 0, 100),
        y=ipw.FloatSlider(0, 1),
        fig=ipw.fixed(fig)
    )
    ```

    **Parameters**:     

    - `*funcs`: One or more callback functions
    - auto_update: Update automatically on widget changes
    - app_layout: Initial layout configuration, see `relayout()` method for details
    - grid_css: CSS Grid properties for layout
        - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).
    - `**kwargs`: Widget parameters

    **Widget Parameters**:     

    - Regular ipywidgets
    - Fixed widgets via ipw.fixed()
    - Dict {{'widget': 'trait'}} for trait observation, 'widget' must be in kwargs
    - Plotly FigureWidgets (use patched_plotly)

    **Widget Updates**:     

    - Functions can modify widget traits (e.g. options, min/max)
    - Order matters for dependent updates
    - Parameter-less functions run with any interaction
    - Animation widgets work even with manual updates

    **CSS Classes**:      

    - Parameter names from kwargs
    - 'out-0', 'out-1'... for unnamed outputs
    - Custom 'out-*' classes from classed()
    - 'run-button' for manual update button

    **Notes**:       

    - Avoid modifying global slide state
    - Use widget descriptions to prevent name clashes
    - See set_css() method for styling options
    
    {css_info}
    """
    class Interactive(InteractBase): # Encapsulating
        def _interactive_params(self): return kwargs # Must be overriden in subclass
        def _interactive_callbacks(self): return funcs # funcs can be provided by @callback decorated methods or optionally ovveriding it
    return Interactive(auto_update=auto_update,app_layout=app_layout, grid_css=grid_css)
    
@_format_docs(other=interactive.__doc__)
def interact(*funcs, auto_update=True,app_layout=None, grid_css={}, **kwargs):
    """{other}

    **Tips**:    

    - You can use this inside columns using delayed display trick, like hl`write('First column', C2)` where hl`C2 = Slides.hold(Slides.interact, f, x = 5) or Slides.interactive(f, x = 5)`.
    - You can also use this under `Slides.capture_content` to display later in a specific place.
    """
    def inner(func):
        return display(interactive(func, *funcs, auto_update = auto_update, app_layout=app_layout, grid_css = grid_css, **kwargs))
    return inner


def patched_plotly(fig):
    "Plotly's FigureWidget with two additional traits `selected` and `clicked` to observe."
    if getattr(fig.__class__,'__name__','') != 'FigureWidget':
        raise TypeError("provide plotly's FigureWidget")
    fig.add_traits(selected = traitlets.Dict(), clicked=traitlets.Dict())

    def _attach_data(change):
        data = change['new']
        if data:
            if data['event_type'] == 'plotly_selected':
                fig.selected = data['points']
            if data['event_type'] == 'plotly_click':
                fig.clicked = data['points']
            
    fig.observe(_attach_data, names = '_js2py_pointsCallback')
    return fig


