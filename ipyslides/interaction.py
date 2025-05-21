"""
Enhanced version of ipywidgets's interact/interactive functionality.
"""

__all__ = ['interactive','interact','patched_plotly','disabled'] # other need to be explicity imported

import textwrap
import inspect 
import traitlets

from contextlib import contextmanager
from IPython.display import display
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

def _func2widget(func, mutuals):
    func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
    for p1, p2 in mutuals:
        if p1 in func_params and p2 in func_params:
            raise ValueError(f"Function {func} cannot have paramters that depend on each other, {p1!r} depends on {p2!r} ")


    out = ipw.Output()
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


def _grid_area_css(grid_css, sel):
    if not isinstance(grid_css, dict):
        raise TypeError('grid_css should be a nesetd dictionary of CSS properties.')
    return ipw.HTML(f'<style>{_build_css((sel,), grid_css)}</style>')

def _format_docs(**variables):
    def decorator(obj):
        if obj.__doc__:
            try:
                obj.__doc__ = obj.__doc__.format(**variables)
            except KeyError as e:
                raise ValueError(f"Documentation for {obj.__name__} contains unknown variable {e}") from e
            except Exception as e:
                raise ValueError(f"Failed to format docs for {obj.__name__}: {str(e)}") from e
        return obj
    return decorator

_css_info = textwrap.indent('\n**Python dictionary to CSS**\n' + _dict2css, '    ')

@_fix_init_sig
@_format_docs(css_info = _css_info)
class InteractBase(ipw.interactive):
    """Base class for creating interactive widgets with multiple callbacks and grid layout support.
    
    This class extends ipywidgets.interactive to provide:

    1. Multiple callback support through @callback decorator
    2. CSS Grid layout system
    3. Trait observation other than just value of widgets returned by `_interactive_params` method defined on subclass.
        - Pass any widget like plotly's `FigureWidget` and observe selections using a function.
        - Pass subclasses of `ValueWidget` using `ipywidgets.fixed` if you are observing a trait other than `value`.
        - A dictionary with single item ` {{'keyword':'trait'}} ` can be used to observe a trait from a widget you passed into `kwargs` directly or  by `fixed`.
        - Use `patched_plotly` from this module to observe `selected` and `clicked` traits automatically.
    
    To use, subclass and implement the required method:

    ```python
    import ipywidgets as ipw
    from ipyslides.interaction import InteractBase, callback

    class MyInteractive(InteractBase):
        def _interactive_params(self):
            return {{
                'x': ipw.IntSlider(0, 0, 100),
                'y': {{'x': 'value'}},  # observe x's value
                'fig': ipw.fixed(go.FigureWidget())
            }}
            
        @callback
        def update_plot(self, x, y, fig):
            fig.data = []
            fig.add_scatter(x=[0, x], y=[0, y])
            
        @callback 
        def show_stats(self, x, y):
            print(f"Distance: {{np.sqrt(x**2 + y**2)}}")
    
    mi = MyInteractive()
    mi.set_css(...) # from another cell later
    ```
    
    **Parameters:**
    
    auto_update : bool, default True

    - If True, updates outputs automatically when any widget value changes.
    - If False, adds a refresh button that must be clicked to update.
    
    grid_css : dict, default {{}}

    - Children of grid are given classes with same names as their keyword argument, and outputs created by `funcs` have classes `out-0, out-1,...`.
    - CSS Grid layout properties, see [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/). Example:
    
    ```python
    grid_css = {{
        'grid': 'auto-flow / 1fr 2fr',  # Two columns
        '.fig': {{'grid-area': '1 / 2 / span 2 / 3'}},  # Widget layout
        '.out-0': {{'height': '300px'}}  # Output styling
    }}
    ```
    
    **Methods:**
    
    set_grid_css(grid_css)
        Update grid layout CSS after initialization
    
    **Tip:** For a quick dashboard without subclassing, use `interactive` and `@interact` which wrap same functionality.
    
    **Notes:**
    
    - Widgets are collected from `_interactive_params()` method defined in subclass
    - Callbacks are collected from methods decorated with @callback
    - Each callback gets only the parameters it needs
    - Updates happen only when relevant parameters change
    - CSS Grid provides flexible layout control
    - Despite requiring a click with `auto_update=False`, you can still observe a widget trait with your own observer function.
    - Use `ipyslides.interaction.AnimationSlider` instead of `ipywidgets.Play` for a better experience.

    {css_info}
    """

    def __init__(self, auto_update=True, grid_css={}):
        self._auto_update = auto_update
        self._grid_css = grid_css
        self._mutuals = [] # dependent parameters 
        self._css_class = 'i-'+str(id(self))
        self._style_html = _grid_area_css(grid_css, f".{self._css_class}.widget-interact.on-refresh") 
        self._style_html.layout.position = 'absolute' # avoid being grid part
        
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
        self.add_class('on-refresh').add_class('widget-gridbox').remove_class('widget-vbox').add_class(self._css_class)
        self.layout.display = 'grid' # for exporting to HTML correctly
        self.layout.flex_flow = 'row wrap' # for exporting to HTML correctly 
        self.layout.position = 'relative' # contain absolute items inside
        self.children += (*extras, *outputs, self._style_html) # add extra widgets to box children
        
        self.out.add_class('widget-output').add_class('out-0') # need this for exporting to HTML correctly
        for i, out in enumerate(outputs):
            out.add_class(f'out-{i+1}') # 0 for main

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
                w.observe(lambda change: _hint_update(btn),names=['value'])
        
            btn.add_class('Refresh-Btn')
            btn.layout = {'width': 'max-content', 'height':'28px', 'padding':'0 24px',}
            btn.tooltip = 'Update Outputs'
            btn.icon = 'refresh'
            try:
                btn.click() # first run to ensure no dynamic inside
            except Exception as e:
                print(f"Warning: Initial button click faild: {e}")
    
    def __init_subclass__(cls):
        if (not '_interactive_params' in cls.__dict__) or (not callable(cls._interactive_params)):
            raise AttributeError("implement _interactive_params(self) method in subclass, "
                "which should returns a dictionary of interaction parameters.")
        return super().__init_subclass__()
    
    @_format_docs(css_info = _css_info)
    def set_grid_css(self, grid_css):
        """CSS selectors are classes from names in return of _interactive_params and .out-0, .out-1... from callbacks widgets.
        {css_info}
        """
        self._style_html.value = _grid_area_css(grid_css, f".{self._css_class}.widget-interact.on-refresh").value
    
    def _interactive_callbacks(self):
        """Collect all methods marked as callbacks. If overridden by subclass, should return a tuple of functions."""
        funcs = []
        for name, attr in self.__class__.__dict__.items():
            if callable(attr) and hasattr(attr, '_is_interactive_callback'):
                # Bind method to instance, we can't get self.method due to traits cuaing issues
                bound_method = attr.__get__(self, self.__class__)
                funcs.append(bound_method)
        return tuple(funcs)
    
    def _fix_kwargs(self):
        params = self._interactive_params() # subclass defines it
        if not isinstance(params, dict):
            raise TypeError(f"method `_interactive_params(self)` should return a dict of interaction parameters")
                
        for key in params:
            if not isinstance(key, str) or not key.isidentifier():
                raise ValueError(f"{key!r} is not a valid name for python variable!")
                    
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

        # fix description in extras, like if user pass IntSlider etc.
        for key, value in extras.items():
            if 'description' in value.traits() and not value.description \
                and not isinstance(value,(ipw.HTML, ipw.HTMLMath, ipw.Label)): # HTML widgets and Labels should not pick extra
                value.description = key # only if not given
        return tuple(extras.values())
    
    def _func2widgets(self):
        self._outputs = ()   # reference for later use   
        for f in self._icallbacks:
            if not callable(f):
                raise TypeError(f'Expected callable, got {type(f).__name__}. '
                    'Only functions accepting a subset of kwargs allowed!')
        
            self._outputs += (_func2widget(f, self._mutuals),) # convert to output widget
        return self._outputs # explicit

    @property
    def outputs(self): return getattr(self, '_outputs',())
    
    def _run_updates(self, **kwargs):
        btn = getattr(self, 'manual_button', None)
        with _hold_running_slide_builder():
            if btn:
                with disabled(btn):
                    _hint_update(btn, remove=True)
                    _run_callbacks(self.outputs, kwargs, self) 
            else:
                _run_callbacks(self.outputs, kwargs, self) 

def callback(func):
    """Decorator to mark methods as interactive callbacks in InteractBase subclasses.
    
    func: The method to be marked as a callback.
        Must be defined inside a class (not nested).
        Must be a regular method (not static/class method).
    
    See example usage in docs of InteractBase.
            
    Returns: The decorated method itself.
    """
    if not callable(func):
        raise TypeError(f"@callback can only decorate functions, got {type(func).__name__}")
    
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

@_format_docs(css_info = _css_info)
def interactive(*funcs, auto_update=True, grid_css={}, **kwargs):
    """
    An enhanced interactive widget based on `ipywidgets.interactive`, tailored for ipyslides. 
    
    **Parameters**

    - `*funcs`: callable
        Provide one or more function that can accept a subset of `**kwargs`. These are converted to output widgets which you can access through `outputs` attribute
        and main output widget through `out` attribute. You can change traits of `**kwargs` widgets from these functions on demand, like setting dynmaic options to a dropdown.
        Add type hints to parameters for auto-completion inside function. Functions that change widgets traits should be listed first, so other functions can pick the latest trait values. 
        Each function only runs when any of its parameters values are changed, thus only required part of GUI is updated. A function with no parameters runs with any other interaction.
    - `auto_update`: Defaults to False if no kwargs are provided, requiring click to update in absence of any other control widgets.
    - `grid_css`: A nested dictionary to apply CSS properties to grid and its children. See below for structure of dictionary.
        - Top level properties are applied to grid itself, like ` grid_css = {{'grid': 'auto-flow / 1fr 2fr'}} ` makes two columns of 33% and 67% width.
        - Children of grid are given classes with same names as their keyword argument, and outputs created by `funcs` have classes `out-0, out-1,...`.
            So if a keyword argument is `fig` and you also wants to style first output, provide 
            ` grid_css = {{'grid-template-columns': '1fr 2fr', 'out-0': {{'height': '200px',...}}, '.fig': {{'grid-area': '1 / 2 / span 5 / -1'}}}} `
            which will put `fig` in write column and 5 other widgets in left and rest below.
        - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

    **kwargs**

    - Additional interactive widgets/ abbreviations for controls, passed to the function as values or widgets.
        See [ipywidgets.interact](https://ipywidgets.readthedocs.io/en/latest/examples/Using%20Interact.html#using-interact) docs.

    - Additional controls, widgets, and their traits other than just `value` are allowed.
        - Pass any widget like plotly's `FigureWidget` and observe selections using a function.
        - Pass subclasses of `ValueWidget` using `ipywidgets.fixed` if you are observing a trait other than `value`.
        - A dictionary with single item ` {{'keyword':'trait'}} ` can be used to observe a trait from a widget you passed into `kwargs` directly or  by `fixed`.
            Example: `interactive(..., x = fixed(IntSlider()), y = {{'x': 'min'}}` lets you observe minimum value of slider assigned to `x`.
        - Use `patched_plotly` from this module to observe `selected` and `clicked` traits automatically.


    **Usage Example**

    ```python
    import ipywidgets as ipw
    import plotly.graph_objects as go
    from ipyslides.interaction import interactive, interact

    @interact( # or interactive function
        lambda y: print(y), # prints x.min as y picks that attribute
        fig = go.FigureWidget(), 
        x= ipw.fixed(ipw.IntSlider()), 
        y = {{'x':'min'}}, 
        z = 10,  
        grid_css={{'grid': auto-flow / 1fr 2fr', '.fig': {{'grid-area': '5 / 1 / auto / -1'}}}}, 
        )
    def plot(fig:go.FigureWidget, x, z): # adding type hint allows auto-completion inside function
        x.min = z # change value widgets traits conditionally if they were passed as fixed
        x.max = z + 50
        fig.data = []
        fig.add_trace(go.Scatter(x=[1,2,3], y=[0, z, 1 - z**2], mode='lines+markers'))
    ```

    **Note**

    - Avoid modifying the global slide state, as changes will affect all slides.
    - If you need a widget in kwargs with same name as other keyword araguments, 
      use description to set it to avoid name clash, e.g. `Slides.interact(f, x=5, y= ipywidgets.IntSlider(description='auto_update'))`.

    {css_info}
    """
    class Interactive(InteractBase): # Encapsulating
        def _interactive_params(self): return kwargs # Must be overriden in subclass
        def _interactive_callbacks(self): return funcs # funcs can be provided by @callback decorated methods or optionally ovveriding it
    return Interactive(auto_update=auto_update,grid_css=grid_css)
    
@_format_docs(other=interactive.__doc__)
def interact(*funcs, auto_update=True, grid_css={}, **kwargs):
    """{other}

    **Tips:**

    - You can use this inside columns using delayed display trick, like hl`write('First column', C2)` where hl`C2 = Slides.hold(Slides.interact, f, x = 5) or Slides.interactive(f, x = 5)`.
    - You can also use this under `Slides.capture_content` to display later in a specific place.
    """
    def inner(func):
        return display(interactive(func, *funcs, auto_update = auto_update, grid_css = grid_css, **kwargs))
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


