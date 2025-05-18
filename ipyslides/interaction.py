"""
Enhanced version of ipywidgets's interact/interactive functionality.
"""

__all__ = ['interactive','interact','patched_plotly','disabled']

import textwrap
import inspect 
import traitlets

from contextlib import contextmanager
from IPython.display import display
from .formatters import get_slides_instance
from .utils import _build_css, _dict2css
from ._base.widgets import ipw # patch ones required here

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
        - Top level properties are applied to grid itself, like ` grid_css = {'grid': 'auto-flow / 1fr 2fr'} ` makes two columns of 33% and 67% width.
        - Children of grid are given classes with same names as their keyword argument, and outputs created by `funcs` have classes `out-0, out-1,...`.
            So if a keyword argument is `fig` and you also wants to style first output, provide 
            ` grid_css = {'grid-template-columns': '1fr 2fr', 'out-0': {'height': '200px',...}, '.fig': {'grid-area': '1 / 2 / span 5 / -1'}} `
            which will put `fig` in write column and 5 other widgets in left and rest below.
        - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

    **kwargs**

    - Additional interactive widgets/ abbreviations for controls, passed to the function as values or widgets.
        See [ipywidgets.interact](https://ipywidgets.readthedocs.io/en/latest/examples/Using%20Interact.html#using-interact) docs.

    - Additional controls, widgets, and their traits other than just `value` are allowed.
        - Pass any widget like plotly's `FigureWidget` and observe selections using a function.
        - Pass subclasses of `ValueWidget` using `ipywidgets.fixed` if you are observing a trait other than `value`.
        - A dictionary with single item ` {'keyword':'trait'} ` can be used to observe a trait from a widget you passed into `kwargs` directly of  by `fixed`.
            Example: `interactive(..., x = fixed(IntSlider()), y = {'x': 'min'}` lets you observe minimum value of slider assigned to `x`.
        - Use `patched_plotly` from this module to observe `selected` and `clicked` traits automatically.


    **Usage Example**

    ```python
    import ipywidgets as ipw
    import plotly.graph_objects as go

    @slides.interact(
        lambda y: print(y), # prints x.min as y picks that attribute
        fig = go.FigureWidget(), 
        x= ipw.fixed(ipw.IntSlider()), 
        y = {'x':'min'}, 
        z = 10,  
        grid_css={'grid': auto-flow / 1fr 2fr', '.fig': {'grid-area': '5 / 1 / auto / -1'}}, 
        )
    def plot(fig:go.FigureWidget, x, z): # adding type hint allows auto-completion inside function
        x.min = z # change value widgets traits conditionally if they were passed as fixed
        x.max = z + 50
        fig.data = []
        fig.add_trace(go.Scatter(x=[1,2,3], y=[0, z, 1 - z**2], mode='lines+markers'))
    ```

    **Note**

    - Avoid modifying the global slide state, as changes will affect all slides.
    - Supports `Slides.AnimationSlider` for animations when `auto_update=True`.
    - If you need a widget in kwargs with same name as other keyword araguments, 
      use description to set it to avoid name clash, e.g. `Slides.interact(f, x=5, y= ipywidgets.IntSlider(description='auto_update'))`.
    """
    if not funcs:
        raise ValueError("at least one interactive function required!")
    
    box, btn, outputs, klass = None, None, [], 'i-'+str(id([])) # just general but unique

    def inner(**kwargs):
        with _hold_running_slide_builder():
            if btn:
                with disabled(btn):
                    _hint_update(btn, remove=True)
                    _run_callbacks(outputs, kwargs, box) 
            else:
                _run_callbacks(outputs, kwargs, box) 
            
    if not kwargs: # need to interact anyhow
        auto_update = False

    extras = {}
    for key, value in kwargs.copy().items():
        if isinstance(value, ipw.fixed) and isinstance(value.value, ipw.DOMWidget):
            extras[key] = value.value # we need to show that widget
        elif isinstance(value,ipw.interactive):
            value.layout.grid_area = 'auto / 1 / auto / -1' # embeded interactive should be full length, unless user sets it otherwise
        elif isinstance(value, (ipw.HTML, ipw.Label, ipw.HTMLMath)):
            kwargs[key] = ipw.fixed(value) # convert to fixed widget, these can't have user interaction available
            extras[key] = value
        elif isinstance(value, ipw.DOMWidget) and not isinstance(value,ipw.ValueWidget): # value widgets are automatically handled
            kwargs[key] = ipw.fixed(value) # convert to fixed widget, to be passed as value
            extras[key] = value # we need to show that widget
    
    # fix description in extras, like if user pass IntSlider etc.
    for key, value in extras.items():
        if 'description' in value.traits() and not value.description \
            and not isinstance(value,(ipw.HTML, ipw.HTMLMath, ipw.Label)): # HTML widgets and Labels should not pick extra
            value.description = key # only if not given

    # Now fix object that observe traits of others
    mutuals = []
    for key, value in kwargs.copy().items():
        if isinstance(value, dict) and len(value) == 1:
            for name, trait in value.items():
                kwargs[key] = AnyTrait(key, name, trait, kwargs)
                mutuals.append((key, *value.keys()))
        
    outputs = ()      
    for f in funcs:
        if not callable(f):
            raise TypeError('Only functions accepting a subset of kwargs can be passed as args!')
        
        outputs += (_func2widget(f, mutuals),) # convert to output widget

    box = ipw.interactive(inner,{'manual':not auto_update,'manual_name':''}, **kwargs)
    btn = getattr(box, 'manual_button', None) # need it above later
    box.add_class('on-refresh').add_class('widget-gridbox').remove_class('widget-vbox').add_class(klass)
    box.layout.display = 'grid' # for exporting to HTML correctly
    box.layout.flex_flow = 'row wrap' # for exporting to HTML correctly 

    box.children += tuple(extras.values()) # add extra widgets to box children
    box.children += outputs # add outputs after extra widgets by kwargs
    box.children += (_grid_area_css(grid_css, f".{klass}.widget-interact.on-refresh"),) # Add html at end
    box.outputs = outputs # store outputs for later use

    box.out.add_class('widget-output').add_class('out-0') # need this for exporting to HTML correctly

    for i, out in enumerate(outputs):
        out.add_class(f'out-{i+1}') # 0 for main

    for w in box.kwargs_widgets:
        c = getattr(w, '_kwarg','')
        if isinstance(w, ipw.fixed):
            w = w.value
        getattr(w, 'add_class', lambda v: None)(c) # for grid area

    if btn:
        for w in box.kwargs_widgets: # should tell the button to update
            w.observe(lambda change: _hint_update(btn),names=['value'])
        
        btn.add_class('Refresh-Btn')
        btn.layout = {'width': 'max-content', 'height':'28px', 'padding':'0 24px',}
        btn.tooltip = 'Update Outputs'
        btn.icon = 'refresh'
        btn.click() # first run to ensure no dynamic inside
    
    return box


def interact(*funcs, auto_update=True, grid_css={}, **kwargs):
    """

    - You can use this inside columns using delayed display trick, like hl`write('First column', C2)` where hl`C2 = Slides.hold(Slides.interact, f, x = 5) or Slides.interactive(f, x = 5)`.
    - You can also use this under `Slides.capture_content` to display later in a specific place.
    """
    def inner(func):
        return display(interactive(func, *funcs, auto_update = auto_update, grid_css = grid_css, **kwargs))
    return inner

_css_info = textwrap.indent('\n**Python dictionary to CSS**\n' + _dict2css, '    ')
interact.__doc__ = interactive.__doc__ + interact.__doc__ + _css_info # additional docstring
interactive.__doc__ = interactive.__doc__ + _css_info


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


