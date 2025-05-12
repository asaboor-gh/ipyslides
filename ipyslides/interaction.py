"""
Enhanced version of ipywidgets's interact/interactive functionality.
"""
import inspect 
import traitlets

from contextlib import contextmanager
from IPython.display import display
from .formatters import get_slides_instance
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
    
    def call_func(kwargs):
        out.clear_output(wait=True) # clear previous output
        with out:
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in func_params}

            # Compare values properly by checking each parameter
            values_changed = any(
                k not in out._old_kws or filtered_kwargs[k] != out._old_kws[k]
                for k in filtered_kwargs
            )
            
            if values_changed:
                func(**filtered_kwargs) # Call the function with filtered parameters only if changed
            
            out._old_kws.update(filtered_kwargs) # update old kwargs to latest values
            
    out._call_func = call_func # set the function to be called when the widget is updated
    return out

def _hint_update(btn, remove = False):
    (btn.remove_class if remove else btn.add_class)('Rerun')
    btn.button_style = '' if remove else 'warning' # for notebook outside slides, CSS not applied

def _run_callbacks(outputs, kwargs, box, rerun=True):
    for out in outputs:
        if hasattr(out, '_call_func'):
            out._call_func(kwargs)
    
    # This only changes the outputs where functions have made internal changes to other widgets, and is necessary
    if box and rerun: # Pick new kwargs update from box
        _run_callbacks(outputs, box.kwargs, box, rerun=False)


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
        super().__init__(value=None)
        traitlets.dlink((widget, trait),(self, 'value'))


def _grid_areas_css(grid_areas, klass):
    css = '\n' # we are doing this because some widgets like plotly have different meaning for layout
    for key, value in grid_areas.items():
        if not isinstance(key,(int, str)):
            raise TypeError(f"key should be integer or string to index children of interactive, got {type(key)}")
        
        if isinstance(key,int):
            css += (f'.{klass} > nth-child({key}) {{ grid-area : {value}; }}' + '\n')
        else:
            css += (f'.{klass} > .{key} {{ grid-area : {value}; }}' + '\n')
    return ipw.HTML(f'<style>{css}</style>')
        


def interactive(*funcs, auto_update=True, grid_areas={}, grid_columns=None, grid_height=None, output_heights={}, **kwargs):
    """An enhanced interactive widget based on `ipywidgets.interactive`, tailored for ipyslides. 
    
    **Parameters**:

    - `*funcs`: callable
        Provide one or more function that can accept a subset of `**kwargs`. These are converted to output widgets which you can access through `outputs` attribute
        and main output widget through `out` attribute. You can change traits of `**kwargs` widgets from these functions on demand, like setting dynmaic options to a dropdown.
        Add type hints to parameters for auto-completion inside function.
    - `auto_update`: Defaults to False if no kwargs are provided, requiring click to update in absence of any other control widgets.
    - `grid_areas`: A mapping from indices/keyword of children of interactive to CSS `grid-area` properties for custom layout.
        - Values are strings specifying grid positioning: `"row-start / column-start / row-end / column-end"`.
        - Example: ` {0: 'auto / 1 /span 2 / 2', 'out_1': '1 / 3 / 2 / 4'} ` places the first widget at the left in its automatic row in 
          two columns span, the 'out_1' (output widget created by first function) in first row, third column, and others in the next available grid areas.
        - You can set grid area to any widget with attributes, e.g. `interactive().children[index].layout.grid_area = '1 / 1 / 2 / 2'` later.
    - `grid_columns`: Defines CSS `grid-template-columns` to control column widths, e.g. `"1fr 2fr"` for two columns with different widths.
    - `grid_height`: Sets the height of the grid layout, e.g. `"300px"` to limit visible area of the grid.
    - `output_heights`: Sets output widgets height to prevent flickering, provide a dictionary for indexing main output and outputs created by each function (in that order) with integer keys and string values.
    
    **`kwargs`**: 
        Additional interactive widgets/ abbreviations for controls, passed to the function as values or widgets.
        See [ipywidgets.interact](https://ipywidgets.readthedocs.io/en/latest/examples/Using%20Interact.html#using-interact) docs.

        Additional controls, widgets, and their traits other than just `value` are allowed.

        - Pass any widget like plotly's `FigureWidget` and observe selections using a function.
        - Pass subclasses of `ValueWidget` using `ipywidgets.fixed` if you are observing a trait other than `value`.
        - A dictionary with single item `{'keyword':'trait'}` can be used to observe a trait from a widget you passed into `kwargs` directly of  by `fixed`.
            Example: `interactive(..., x = fixed(IntSlider()), y = {'x': 'min'}` lets you observe minimum value of slider assigned to `x`.


    **Usage Example**:
    ```python
    import ipywidgets as ipw
    import plotly.graph_objects as go

    @slides.interact(
        lambda y: print(y), # prints x.min as y picks that attribute
        fig = go.FigureWidget(), 
        x= ipw.fixed(ipw.IntSlider()), 
        y = {'x':'min'}, 
        z = 10,  
        grid_areas={'fig': '5 / 1 / auto / -1'}, 
        grid_columns='1fr 2fr')
    def plot(fig:go.FigureWidget, x, z): # adding type hint allows auto-completion inside function
        x.min = z # change value widgets traits conditionally if they were passed as fixed
        x.max = z + 50
        fig.data = []
        fig.add_trace(go.Scatter(x=[1,2,3], y=[0, z, 1 - z**2], mode='lines+markers'))
    ```

    **Note**:

    - Avoid modifying the global slide state, as changes will affect all slides.
    - Supports `Slides.AnimationSlider` for animations when `auto_update=True`.
    - If you need a widget in kwargs with same name as other keyword araguments, 
      use description to set it to avoid name clash, e.g. `Slides.interact(f, x=5, y= ipywidgets.IntSlider(description='grid_height'))`.
    """
    if not funcs:
        raise ValueError("at least one interactive function required!")
    
    box, btn, outputs, klass = None, None, [], 'i'+str(id([])) # just general but unique
    def inner(**kwargs):
        display(_grid_areas_css(grid_areas, klass))
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
        if 'description' in value.traits() and not value.description:
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
    box.layout.grid_template_columns = grid_columns or ''
    box.layout.display = 'grid' # for exporting to HTML correctly
    box.layout.flex_flow = 'row wrap' # for exporting to HTML correctly 
    box.layout.height = grid_height or ''

    box.children += tuple(extras.values()) # add extra widgets to box children
    box.children += outputs # add outputs after extra widgets by kwargs
    box.outputs = outputs # store outputs for later use

    box.out.add_class('widget-output').add_class('main').add_class('out_0') # need this for exporting to HTML correctly
    box.out.layout.grid_area = 'auto / 1 / auto / -1' # should be full width even outside slides 

    for i, out in enumerate(outputs):
        out.add_class(f'out_{i+1}') # 0 for main

    for w in box.kwargs_widgets:
        if isinstance(w, ipw.fixed):
            w, c = w.value, getattr(w, '_kwarg','')
        getattr(w, 'add_class', lambda v: None)(c) # for grid area
    
    for key, value in output_heights.items():
        if not isinstance(key, int):
            raise TypeError(f"key should be integer to index main output and other outputs created by funcs, got {type(key)}")
        if key == 0:
            box.out.layout.height = value 
        else:
            outputs[key + 1].layout.height = value

    if btn:
        for w in box.kwargs_widgets: # should tell the button to update
            w.observe(lambda change: _hint_update(btn),names=['value'])
        
        btn.add_class('Refresh-Btn')
        btn.layout = {'width': 'max-content', 'height':'28px', 'padding':'0 24px',}
        btn.tooltip = 'Update Outputs'
        btn.icon = 'refresh'
        btn.click() # first run to ensure no dynamic inside
    
    return box


def interact(*funcs, auto_update=True, grid_areas={}, grid_columns=None, grid_height=None, output_heights={}, **kwargs):
    """
    ::: note-tip
        - You can use this inside columns using delayed display trick, like hl`write('First column', C2)` where hl`C2 = Slides.hold(Slides.interact, f, x = 5) or Slides.interactive(f, x = 5)`.
        - You can also use this under `Slides.capture_content` to display later in a specific place.
    """
    def inner(func):
        return display(interactive(func, *funcs, auto_update = auto_update, grid_areas = grid_areas, grid_columns = grid_columns, 
            grid_height=grid_height, output_heights = output_heights, **kwargs))
    return inner

interact.__doc__ = interactive.__doc__ + interact.__doc__ # additional docstring

