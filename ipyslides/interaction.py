"""
Enhanced version of ipywidgets's interact/interactive functionality.
"""
import inspect 

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

def _func2widget(func):
    func_params = {k:v for k,v in inspect.signature(func).parameters.items()}

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


def interactive(_f, *args, auto_update=True, grid_areas={}, grid_columns=None, grid_height=None, output_height=None, **kwargs):
    """Creates an interactive widget layout using ipywidgets, tailored for ipyslides. Add type hints to function for auto-completion inside function.
    
    **Parameters**:

    - `args`: Positional widgets displayed below the output widget, passed to calling function as widgets unlike values from kwargs.
        - These widgets may include some controls like sliders, dropdowns, etc. which will add an extra button to refresh the output 
          when `auto_update = True`, otherwise there will be already a button to refresh the output.
        - You can embed `interactive` itself inside `args` to create a nested interactive layout, hence interacting with multiple functions like a highly flexible application.
        - You can also include functions that take a subset of parameters from the main function and return output widgets. These will be updated when their corresponding variables change.
    - `auto_update`: Defaults to False if no kwargs are provided, requiring click to update in absence of any other control widgets.
    - `grid_areas`: A mapping from indices of args widgets to CSS `grid-area` properties for custom layout.
        - Values are strings specifying grid positioning: `"row-start / column-start / row-end / column-end"`.
        - Example: ` {0: 'auto / 1 /span 2 / 2', 1: '1 / 3 / 2 / 4'} ` places the first `args` widget at the left in its automatic row in 
          two columns span, the second in first row, third column, and others in the next available grid areas.
        - You can set grid area to any widget with attributes, e.g. `interactive().children[index].layout.grid_area = '1 / 1 / 2 / 2'`.
    - `grid_columns`: Defines CSS `grid-template-columns` to control column widths, e.g. `"1fr 2fr"` for two columns with different widths.
    - `grid_height`: Sets the height of the grid layout, e.g. `"300px"` to limit visible area of the grid.
    - `output_height`: Sets output widget height to prevent flickering.
    - `kwargs`: Additional interactive widgets/ abbreviations for controls, passed to the function as values.
    **Usage Example**:
    ```python
    import plotly.graph_objects as go
    @Slides.interact(go.FigureWidget(), x=5, grid_areas={0: 'auto / 1 / span 3 / 3'})
    def plot(fig:go.FigureWidget, x): # adding type hint allows auto-completion inside function
        fig.data = []
        fig.add_trace(go.Scatter(x=[1,2,3], y=[x, x+1, x+2], mode='lines+markers'))
        print(f'Plotting {x}')
    ```

    **Note**:

    - Avoid modifying the global slide state, as changes will affect all slides.
    - Supports `Slides.AnimationSlider` for animations when `auto_update=True`.
    - If you need a widget in kwargs with same name as other keyword araguments, 
      use description to set it to avoid name clash, e.g. `Slides.interact(f, x=5, y= ipywidgets.IntSlider(description='grid_height'))`.
    """
    def hint_update(btn, remove = False):
        (btn.remove_class if remove else btn.add_class)('Rerun')
        btn.button_style = '' if remove else 'warning' # for notebook outside slides, CSS not applied

    f_kws = {k:v for k,v in inspect.signature(_f).parameters.items()} # store once for all cases
    
    def run_args_callbacks(args, kwargs):
        for new, (key, old) in zip(args, f_kws.items()):
            f_kws[key] = new # update with new values from args, args may be changed by user, no example though
        f_kws.update(kwargs) # update with latest values from kwargs

        for arg in args:
            if hasattr(arg, '_call_func'):
                arg._call_func(f_kws)

    
    def inner(**kwargs):
        with _hold_running_slide_builder():
            if (btn := getattr(inner, 'btn', None)):
                with disabled(btn):
                    _f(*args, **kwargs)
                    hint_update(btn, remove=True)
                    run_args_callbacks(args, kwargs) # run args callback if any      
            else:
                _f(*args, **kwargs)
                run_args_callbacks(args, kwargs) # run args callback if any

    new_args = []      
    for arg in args:
        if not isinstance(arg, ipw.DOMWidget) and not callable(arg):
            raise TypeError('Only displayable widgets or functions can be passed as args, which can be controlled by kwargs widgets inside through function!')
        if isinstance(arg,ipw.interactive):
            arg.layout.grid_area = 'auto / 1 / auto / -1' # embeded interactive should be full length, unless user sets it otherwise

        if callable(arg):
            new_args.append(_func2widget(arg)) # convert to output widget
        else:
            new_args.append(arg)
    
    args = tuple(new_args) # avoid accidental modification when setting args_widgets

    if not kwargs: # need to interact anyhow
        auto_update = False

    box = ipw.interactive(inner,{'manual':not auto_update,'manual_name':''}, **kwargs)
    box.add_class('on-refresh').add_class('widget-gridbox').remove_class('widget-vbox')
    box.layout.grid_template_columns = grid_columns or ''
    box.layout.display = 'grid' # for exporting to HTML correctly
    box.layout.flex_flow = 'row wrap' # for exporting to HTML correctly
    box.layout.height = str(grid_height or '') 
    box.children += args
    # Add function output widgets to box children
    box.args_widgets = args
    box.out.add_class('widget-output') # need this for exporting to HTML correctly
    box.out.layout.height = str(output_height or '') #avoid flickering, handle None case
    box.out.layout.grid_area = 'auto / 1 / auto / -1' # should be full width even outside slides
    
    for key, value in grid_areas.items():
        if not isinstance(key,int):
            raise TypeError(f"key should be integer to index args, got {type(key)}")
        
        if args: # let it raise index error below
            args[key].layout.grid_area = value # set grid area for args widgets
    
    args_value_widgets = [w for w in args 
        if (isinstance(w, ipw.ValueWidget) and not isinstance(w, ipw.widget_string._String)) # HTML, Label etc. excluded, Text, Textarea are special cases
        or isinstance(w, (ipw.Text,ipw.Textarea))] # only if controls are there but not HTML widgets
    if (btn := getattr(box, 'manual_button', None)):
        inner.btn = box.manual_button
        for w in [*box.kwargs_widgets, *args_value_widgets]: # both kwargs and args widgets should tell the button to update
            w.observe(lambda change: hint_update(btn),names=['value'])
        
        btn.add_class('Refresh-Btn')
        btn.layout = {'width': 'max-content', 'height':'28px', 'padding':'0 24px',}
        btn.tooltip = 'Update Outputs'
        btn.icon = 'refresh'
        btn.click() # first run to ensure no dynamic inside
    
    elif args_value_widgets: 
        btn = ipw.Button(description='', tooltip='Update Outputs', icon='refresh',
            layout={'width': 'max-content', 'padding':'0 24px', 'height':'28px'}).add_class('Refresh-Btn')
        
        for w in args_value_widgets: # only args widgets are left unsynced in this case
            w.observe(lambda change: hint_update(btn),names=['value'])
        
        @box.out.capture(clear_output=True,wait=True)
        def on_click(b):
            with disabled(btn): # here we don't need to hold the slide builder, as we will not be inside it
                inner(**box.kwargs) # pick latest values from kwargs
                hint_update(btn, remove=True) 
                run_args_callbacks(box.args_widgets, box.kwargs)

        btn.on_click(on_click)
        box.children += (btn,) # add at last for any args widgets to work
        btn.click() # first run to ensure no dynamic inside
    return box


def interact(*args, auto_update=True, grid_areas={}, grid_columns=None, grid_height=None, output_height=None, **kwargs):
    """
    ::: note-tip
        - You can use this inside columns using delayed display trick, like hl`write('First column', C2)` where hl`C2 = Slides.hold(Slides.interact, f, x = 5) or Slides.interactive(f, x = 5)`.
        - You can also use this under `Slides.capture_content` to display later in a specific place.
    """
    def inner(func):
        return display(interactive(func, *args, auto_update = auto_update, grid_areas = grid_areas, grid_columns = grid_columns, 
            grid_height=grid_height, output_height = output_height, **kwargs))
    return inner

interact.__doc__ = interactive.__doc__ + interact.__doc__ # additional docstring

