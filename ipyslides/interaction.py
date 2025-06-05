"""
Enhanced version of ipywidgets's interact/interactive functionality.
"""

__all__ = ['interactive','interact', 'classed', 'patched_plotly','disabled'] # other need to be explicity imported

import sys, re, textwrap
import inspect 
import traitlets

from contextlib import contextmanager, nullcontext
from collections import namedtuple

from IPython.display import display
from IPython.core.ultratb import AutoFormattedTB
from anywidget import AnyWidget

from .formatters import get_slides_instance
from .utils import _build_css, _dict2css
from ._base.icons import Icon
from ._base.widgets import ipw # patch ones required here
from ._base._widgets import _fix_init_sig, AnimationSlider

@contextmanager
def disabled(*widgets):
    "Disable widget and enable it after code block runs under it. Useful to avoid multiple clicks on a button that triggers heavy operations."
    for widget in widgets:
        if not isinstance(widget, ipw.DOMWidget):
            raise TypeError(f"Expected ipywidgets.DOMWidget, got {type(widget).__name__}")
        widget.disabled = True
        widget.add_class("Context-Disabled")
    try:
        yield
    finally:
        for widget in widgets:
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
    function render({model, el}) {
        const btn = document.createElement('button');
        el.className = 'fs-btn ips-fs';
        btn.innerHTML = '<i class="fa fa-expand"></i>';
        btn.title = 'Toggle Fullscreen';

        btn.onclick = () => {
            const parent = el.parentElement;
            if (!document.fullscreenElement || document.fullscreenElement !== parent) {
                parent.requestFullscreen()
                    .then(() => {
                        model.set('isfullscreen', true);
                        model.save_changes();
                    })
                    .catch(err => console.error('Failed to enter fullscreen:', err));
            } else {
                document.exitFullscreen()
                    .then(() => {
                        model.set('isfullscreen', false);
                        model.save_changes();
                    })
                    .catch(err => console.error('Failed to exit fullscreen:', err));
            }
            updateButtonUI(btn, parent);
        };

        document.addEventListener('fullscreenchange', () => {
            const parent = el.parentElement;
            if (!parent) return; // Exit if parent is null
            const isFullscreen = parent === document.fullscreenElement;
            model.set('isfullscreen', isFullscreen);
            model.save_changes(); 
            updateButtonUI(btn, parent);
        });

        function updateButtonUI(button, parent) {
            const isFullscreen = parent === document.fullscreenElement;
            button.querySelector('i').className = `fa fa-${isFullscreen ? 'compress' : 'expand'}`;
            if (!parent) return; // Exit if parent is null
            parent.style.background = isFullscreen ? 'var(--bg1-color, var(--jp-widgets-input-background-color, inherit))' : 'unset';
        }

        el.appendChild(btn);
    }

    export default { render };
    """
    isfullscreen = traitlets.Bool(False, read_only=True).tag(sync=True)

    def __init__(self):
        super().__init__()
        self.layout.width = 'min-content'


# We will capture error at user defined callbacks level
_autoTB = AutoFormattedTB(color_scheme='Linux')

@contextmanager
def _print_error(out):
    if out and not isinstance(out, ipw.Output):
        raise TypeError(f"out should be None or ipywidgets.Output, got {type(out)!r}")
    
    try:
        if out: out.remove_class('out-err')
        yield
    except:
        if out: 
            out.add_class('out-err').clear_output(wait=True) # clear output on error
            
        with (out or nullcontext()): # We don't want to raise it to let other callbacks run
            print('\n'.join(
                _autoTB.structured_traceback(*sys.exc_info(),tb_offset=2, number_of_lines_of_context=5)
            ))

def _func2widget(func):
    func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
    out = None # If No CSS class provided, no output widget will be created, default
    
    if klass := func.__dict__.get('_css_class', None):
        out = ipw.Output()
        out.add_class(klass)
        out._kwarg = klass # store for access later
    
    last_kws = {} # store old kwargs to avoid re-running the function if not changed
    
    def call_func(kwargs):
        if out: out.clear_output(wait=True) # clear previous output
        with (out or nullcontext()):
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in func_params}

            # Check if any parameter is a Button
            buttons = [v for v in filtered_kwargs.values() if isinstance(v, ipw.Button)]
            other_params  = {k: v for k, v in filtered_kwargs.items() if not isinstance(v, ipw.Button)}
            
            if buttons:
                if not any(btn._click_triggered for btn in buttons):
                    return # Only update if a button was clicked and skip other parameter changes
                
                with _print_error(out), disabled(*buttons): # disable buttons during function call
                    try: # error still be raised, but will be caught by _print_error, so finally is important
                        func(**filtered_kwargs) # Call the function with filtered parameters only if changed or no params
                    finally:
                        last_kws.update(filtered_kwargs) # update old kwargs to latest values
                        for btn in buttons:
                            btn._click_triggered = False # reset click trigger
                            _hint_update(btn, remove=True)
                
                return # exit after button click handling
                
            # Compare values properly by checking each parameter that is not a Button
            values_changed = any(
                k not in last_kws or other_params[k] != last_kws[k]
                for k in other_params
            )
            
            # Run function if new values, or does not have parameters or on button click
            if values_changed or not func_params: # function may not have arguments but can be run via others
                with _print_error(out):
                    func(**filtered_kwargs) # Call the function with filtered parameters only if changed or no params
            
            last_kws.update(filtered_kwargs) # update old kwargs to latest values
            
    return (call_func, out)

_general_css = {
    'display': 'grid',
    'grid-gap': '4px',
    'box-sizing': 'border-box',
    '.Refresh-Btn.Rerun:before': {
        'content': 'attr(title)',
        'padding': '0 8px',
        'color': 'red !important',
    },
    '.out-*': {
        'padding': '4px 8px',
        'display': 'grid', # outputs are not displaying correctly otherwise
    },
    '< .ips-interact': {
        '^:fullscreen > *, > *': {'margin' : 0}, # this is import for fullscreen mode to be margin-less directly
        '.widget-output.out-err': { # same error view as in JupyterLab, covers from main VBox
            'background': 'var(--jp-rendermime-error-background)',
            'margin-block': 'var(--jp-code-padding)', # have some space around to distinguish
        },
    },
    # below widget-html-content creates issue even in nested divs
    '> *, > .center > *, .widget-html-content' : { # .center is GridBox
        'min-width': '0', # Preventing a Grid Blowout by css-tricks.com
        'box-sizing': 'border-box',
    },
    '.Context-Disabled:after': { 
        **Icon('loading',color='red').css,
        'background': 'hsl(from var(--bg2-color, whitesmoke) 230 50% l)',
        'padding': '0 0.5em',
        'padding-top': '4px', # button offset sucks
    },
    '< .ips-interact > .other-area:not(:empty)': { # to distinguish other area when not empty
        'border-top': '1px inset var(--jp-border-color2, #8988)',
    },
    '.content-width-button.jupyter-button, .content-width-button .jupyter-button': {
            'width':'max-content',
            'padding-left': '8px', 'padding-right': '8px',
    },
    '> * .widget-box': {'flex-shrink': 0}, # avoid collapse of boxes,
    '.js-plotly-plot': {'flex-grow': 1}, # stretch parent, rest is autosize stuff
}

def _hint_update(btn, remove = False):
    (btn.remove_class if remove else btn.add_class)('Rerun')

def _run_callbacks(fcallbacks, kwargs, box):
    # Each callback is executed, Error in any of them don't stop other callbacks, handled in _print_error context manager
    for func in fcallbacks:
        func(box.kwargs if box else kwargs) # get latest from box due to internal widget changes

class AnyTrait(ipw.fixed):
    "Observe any trait of a widget with name trait inside interactive."
    def __init__(self,  widget, trait):
        self._widget = widget
        self._trait = trait

        if isinstance(widget, ipw.fixed): # user may be able to use it
            widget = widget.value
        
        if not isinstance(widget, ipw.DOMWidget):
            raise TypeError(f"widget expects an ipywidgets.DOMWidget even if wrapped in fixed, got {type(widget)}")
        
        if trait not in widget.trait_names():
            raise traitlets.TraitError(f"{widget.__class__} does not have trait {trait}")
        
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
                'y': 'x.value',  # observe x's value
                'fig': ipw.fixed(go.FigureWidget()),
                'btn': ipw.Button(icon='refresh', tooltip='Update Plot'),
            }}
            
        @callback # captured by out-main 
        def update_plot(self, x, fig, btn): # will need btn click to run
            fig.data = []
            fig.add_scatter(x=[0, x], y=[0, x**2])
            
        @callback('out-stats')  # creates Output widget for it
        def show_stats(self, y):
            print(f"Distance: {{np.sqrt(1 + y**2)}}")
    
    # Create and layout
    dash = MyDashboard(auto_update=True)
    dash.relayout(
        left_sidebar=dash.groups.controls,  # controls on left
        center=[(ipw.VBox(), ('fig', 'out-stats')),]  # plot and stats in a VBox explicitly
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
    - app_layout (dict): Initial layout configuration, see `relayout` method for details.
        - header: List[str | (Box, List[str])] - Top widgets
        - left_sidebar: List[str | (Box, List[str])] - Left side widgets 
        - center: List[str | (Box, List[str])] - Main content area
        - right_sidebar: List[str | (Box, List[str])] - Right side widgets
        - footer: List[str | (Box, List[str])] - Bottom widgets
    - grid_css (dict): CSS Grid properties for layout customization
        - See set_css() method for details
        - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

    **Widget Parameters** (`_interactive_params`'s returned dict):

    - Regular ipywidgets with value trait
    - Fixed widgets using ipw.fixed(widget)
    - String pattern 'widget.trait' for trait observation, 'widget' must be in kwargs or e.g. '.trait' to observe traits on this instance.
    - You can use '.fullscreen' to detect fullscreen change and do actions based on that.
    - Any DOM widget that needs display (inside fixed too). A widget and its observed trait in a single function are not allowed, such as `f(fig, v)` where `v='fig.selected'`.
    - `ipywidgets.Button` for manual updates on heavy callbacks besides global `auto_update`. Add tooltip for info on button when not synced.
    - Plotly FigureWidgets (use patched_plotly for selection support)

    **Callbacks**:   

    - Methods decorated with @callback
    - Optional CSS class via @callback('out-myclass')
    - CSS class must start with 'out-' excpet reserved 'out-main'
    - Each callback gets only needed parameters and updates happen only when relevant parameters change
    - **Output Widget Behavior**:
        - An output widget is created only if a CSS class is provided via `@callback` or `classed`.
        - If no CSS class is provided, the callback will use the main output widget, labeled as 'out-main'.
        
    **Attributes & Properties**:  

    - isfullscreen: Read-only trait to detect fullscreen change on python side. Can be observed as '.isfullscreen' in params.
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
    isfullscreen = traitlets.Bool(False, read_only=True)

    def __init__(self, auto_update=True, app_layout= None, grid_css={}):
        if not isinstance(grid_css,dict):
            raise TypeError(f"grid_css should be a dict, got {type(grid_css)}")
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
        if not self._iparams: # need to interact anyhow and also allows a no params function
            self._auto_update = False
        
        self._icallbacks = self._interactive_callbacks() # callbacks after collecting params
        if not isinstance(self._icallbacks, (list, tuple)):
            raise TypeError("_interactive_callbacks should return a tuple of functions!")
        
        if not self._icallbacks:
            raise ValueError("at least one interactive function required!")

        outputs = self._func2widgets() # build stuff, before actual interact
        super().__init__(self._run_updates, {'manual':not self._auto_update,'manual_name':''}, **self._iparams)
        
        btn = getattr(self, 'manual_button', None) # need it above later
        self.add_class('ips-interact').add_class(self._css_class)
        self.layout.position = 'relative' # contain absolute items inside
        self.layout.height = 'max-content' # adopt to inner height

        self.children += (*extras, *outputs, self._style_html) # add extra widgets to box children
        self.out.add_class("out-main")
        self.out._kwarg = "out-main" # needs to be in all widgets

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
            
            btn._kwarg = 'btn-main'
            btn.add_class('Refresh-Btn').add_class('btn-main') # btn-main for user
            btn.layout = {'width': 'max-content', 'height':'28px', 'padding':'0 24px'}
            btn.tooltip = 'Sync Outputs'
            btn.icon = 'refresh'
            try:
                btn.click() # first run to ensure no dynamic inside
            except Exception as e:
                print(f"Warning: Initial button click faild: {e}")

        self._all_widgets = {w._kwarg: w for w in self.children if hasattr(w, '_kwarg')} # save it once for sending to app layout
        self._groups = self._create_groups(self._all_widgets) # create groups of widgets for later use
        
        for func in self._icallbacks:
            self._hint_btns_update(func) # external buttons update hint
        
        if app_layout is not None:
            self._validate_layout(app_layout) # validate arguemnts first
            self.relayout(**app_layout)
        else:
            self.relayout(center=list(self._all_widgets.keys())) # add all to GridBox which is single column
    
    def __repr__(self): # it throws very big repr, so just show class name and id
        return f"<{self.__module__}.{type(self).__name__} at {hex(id(self))}>"
    
    def _validate_layout(self, app_layout):
        if not isinstance(app_layout, dict):
            raise TypeError("app_layout should be a dictionary to relayout widgets!")
        
        allowed_keys = inspect.signature(self.relayout).parameters.keys()
        for key, value in app_layout.items():
            if not key in allowed_keys:
                raise KeyError(f"keys in app_layout should be one of {allowed_keys}, got {key!r}")
            
            if value is None or key not in ["header", "footer", "center", "left_sidebar", "right_sidebar"]:
                continue  # only validate content areas, but go for all, don't retrun

            if not isinstance(value, (list, tuple)):
                raise TypeError(
                    f"{key!r} in app_layout should be a list/tuple of widget names or "
                    f"(Box_instance, [names]) tuples, got {type(value).__name__}"
                )
            
            if self._auto_update:
                value = [v for v in value if v != 'btn-main'] # avoid throwing error over button, which changes by other paramaters
            
            for i, name in enumerate(value,start=1):
                if isinstance(name,str):
                    if not name in self._all_widgets:
                        raise ValueError(
                            f"Invalid widget name {name!r} in {key!r} at position {i}. "
                            f"Valid names are: {list(self._all_widgets.keys())}")
                    continue # valid widget name, no need to check further

                if not isinstance(name, (list,tuple)):
                    raise TypeError(
                        f"Item at position {i} in {key!r} must be a widget name or "
                        f"(Box_instance, [names]) tuple, got {type(name).__name__}")
                
                if len(name) != 2:
                    raise ValueError(
                        f"Tuple at position {i} in {key!r} must have exactly 2 items: "
                        f"(Box_instance, [names]), got {len(name)} items")
                    
                box, children = name

                if not isinstance(box, ipw.Box):
                    raise TypeError(f"First item of tuple at position {i} in {key!r} must be a Box widget instance, got {type(box).__name__}")
    
                if not isinstance(children, (list,tuple)):
                    raise TypeError(
                        f"Second item of tuple at position {i} in {key!r} must be a list/tuple "
                        f"of widget names, got {type(children).__name__}")
                
                for child in children:
                    if not isinstance(child, str):
                        raise TypeError(
                            f"Widget names in tuple at position {i} in {key!r} must be strings, "
                            f"got {type(child).__name__}")
                    
                    if child not in self._all_widgets:
                        raise ValueError(
                            f"Invalid widget name {child!r} in tuple at position {i} in {key!r}. "
                            f"Valid names are: {list(self._all_widgets.keys())}")
    
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
            - Each of above must be a List[str | (Box, List[str])] of widget params names if given. Box is instance of ipywidgets.Box initialized without children.
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
        other = ipw.VBox().add_class('other-area') # this should be empty to enable CSS perfectly, unless filled below
        areas = ["header","footer", "center", "left_sidebar","right_sidebar"]

        collected = []
        for key, value in app_layout.items():
            if value and key in areas:
                collected.extend(list(value))
                box = ipw.GridBox if key == 'center' else ipw.VBox
                children = []
                for name in value:
                    if isinstance(name,str) and name in self._all_widgets:
                        children.append(self._all_widgets[name])
                    elif isinstance(name, (list,tuple)) and len(name) == 2: # already checked, but just in case
                        nested_box, childs = name
                        nested_box.children = tuple([self._all_widgets[n] for n in childs if n in self._all_widgets])
                        collected.extend(list(childs)) # avoid showing nested ones again.
                        children.append(nested_box) # add box to  main children
                    
                setattr(self._app, key, box(children, _dom_classes = (key.replace('_','-'),))) # for user CSS
            elif value: # class own traits and Layout properties
                setattr(self._app, key, value)
        
        other.children += tuple([v for k,v in self._all_widgets.items() if k not in collected])
        
        # We are adding a reaonly isfullscreen trait set through button on parent class
        fs_btn = FullscreenButton()
        fs_btn.observe(lambda c: self.set_trait('isfullscreen',c.new), names='isfullscreen') # setting readonly property
        
        self.children = (self._app, other, self._style_html, fs_btn) # button be on top to click
    
    @_format_docs(css_info = textwrap.indent(_css_info,'    ')) # one more time indent for nested method
    def set_css(self, main=None, center=None):
        """Update CSS styling for the main app layout and center grid.
        
        **Parameters**:         

        - main (dict): CSS properties for main app layout
            - Target center grid with ` > .center ` selector
            - Target widgets by their parameter names as classes
            - Use `:fullscreen` at root level of dict to apply styles in fullscreen mode
            - Use `[Button, ToggleButton, ToggleButtons].add_class('content-width-button')` to fix button widths easily.
        - center (dict): CSS properties for center grid section
            - Direct access to center grid (same as main's ` > .center `)
            - Useful for grid layout of widgets inside center area
            - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

        **CSS Classes Available**:  

        - Parameter names from _interactive_params()
        - 'btn-main' for manual update button
        - Custom 'out-*' classes from @callback decorators and 'out-main' from main output.

        **Example**:       

        ```python
        dash.set_css(
            main={{
                ':fullscreen': {{'min-height':'100vh'}}, # fullscreen mode full height by min-height
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
        _css = _build_css(('.ips-interact > .interact-app',),_general_css)

        fs_css = main.pop(':fullscreen',{}) or main.pop('^:fullscreen',{}) # both valid
        if fs_css: # fullscreen css given by user, full screen is top interact, not inside one as button is there
            _css += ('\n' + _build_css((f".{self._css_class}.widget-interact.ips-interact:fullscreen > .interact-app",), fs_css))
        
        if main:
            _css += ("\n" + _build_css((main_sl,), main))
        if center:
            _css += ("\n" + _build_css((cent_sl,), center))
        self._style_html.value = f'<style>{_css}</style>'
    
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
            # not for random dict, but intended one
            if isinstance(value, dict) and len(value) == 1 and set(value).issubset(params):
                print(f"use 'widget.trait' instead of {value}, which allows using '.trait' to observe traits on the instance")
                value = '.'.join([*value.keys(), *value.values()]) # make a str for old way to work
                print("converted to:", value)

            if isinstance(value, str) and value.count('.') == 1 and ' ' not in value: # space restricted
                name, trait_name = value.split('.')
                if name == '' and trait_name in self.trait_names():
                    params[key] = AnyTrait(self, trait_name)
                    # we don't need mutual exclusion on self, as it is not passed
                elif name in params: # extras are already cleaned widgets, otherwise params must have key under this condition
                    w = params.get(name, None)
                    if isinstance(w, ipw.fixed):
                        w = w.value # wrapper widget may be

                    # We do not want to raise error, so any invalid string can goes to Text widget
                    if isinstance(w, ipw.DOMWidget) and trait_name in w.trait_names():
                        params[key] = AnyTrait(w, trait_name)
                        self._mutuals.append((key, name))
        
        # Set _iparams after clear widgets
        self._iparams = params
        self._reset_descp(extras)
        for key, value in extras.items():
            value._kwarg = key # required for later use
            if isinstance(value, ipw.Button): # Button can only be in extras, by fixed or itself
                # Add click trigger flag and handler, callbacks using this can only be triggered by click
                value._click_triggered = False
                value.add_class('Refresh-Btn') # add class for styling
                if not value.tooltip: # will show when not synced
                    value.tooltip = 'Run Callback'
                value.on_click(lambda btn: setattr(btn, '_click_triggered', True))
                value.on_click(self.update) # after setting click trigger, update outputs
                
        return tuple(extras.values())
    
    def _reset_descp(self, extras):
        # fix description in extras, like if user pass IntSlider etc.
        for key, value in extras.items():
            if 'description' in value.traits() and not value.description \
                and not isinstance(value,(ipw.HTML, ipw.HTMLMath, ipw.Label)): # HTML widgets and Labels should not pick extra
                value.description = key # only if not given
    
    def _func2widgets(self):
        self._outputs = ()   # reference for later use
        self._fcallbacks = () #
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
            
            self._validate_func(f) # before making widget, check
            new_func, out = _func2widget(f) # converts to output widget if user set class or empty
            self._fcallbacks += (new_func,) 
            
            if out is not None:
                self._outputs += (out,)
        
        del used_classes # no longer needed
        return self._outputs # explicit
    
    def _validate_func(self, f):
        ps = inspect.signature(f).parameters
        f_ps = {k:v for k,v in ps.items()}
        has_varargs = any(param.kind == param.VAR_POSITIONAL for param in ps.values())
        has_varkwargs = any(param.kind == param.VAR_KEYWORD for param in ps.values())

        if has_varargs or has_varkwargs:
            raise TypeError(
                f"Function {f.__name__!r} cannot have *args or **kwargs in its signature. "
                "Only explicitly named keywords from interactive params are allowed."
            )

        if len(ps) == 0 and self._auto_update:
            raise ValueError(
                f"Function {f.__name__!r} must have at least one parameter when auto_update is enabled (default). "
                "Any function with no arguments can only run with global interact button click."
            )
        
        for p1, p2 in self._mutuals:
            if p1 in f_ps and p2 in f_ps:
                raise ValueError(
                    f"Function {f} cannot have paramters that depend on each other, {p1!r} depends on {p2!r} "
                    f"Use independent parameter inside callbacks as self.params.{p2} instead of passing it directly (only possible in subclass of InteractBase).")
        
        gievn_params = set(self.params._asdict())
        extra_params = set(f_ps) - gievn_params
        if extra_params:
            raise ValueError(f"Function {f.__name__!r} has parameters {extra_params} that are not defined in interactive params.")
        
    
    def _create_groups(self, widgets_dict):
        groups = namedtuple('WidgetGropus', ['controls', 'outputs', 'others'])
        controls, outputs, others = [], [], []
        for key, widget in widgets_dict.items():
            if isinstance(widget, ipw.Output):
                outputs.append(key)
            elif (isinstance(widget, ipw.ValueWidget) and 
              not isinstance(widget, (ipw.HTML, ipw.Label, ipw.HTMLMath))):
                controls.append(key)
            elif key == 'btn-main' or isinstance(widget, ipw.Button):
                controls.append(key) # run buttons always in controls
            else:
                others.append(key)
        return groups(controls=tuple(controls), outputs=tuple(outputs), others=tuple(others))
    
    def _hint_btns_update(self, func):
        func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
        # Let's observe buttons by shared value widgets in func_params
        controls = {c: self._all_widgets[c] for c in self.groups.controls if c in func_params} # filter controls by func_params
        btns = [controls[k] for k in func_params if isinstance(controls.get(k,None), ipw.Button)]
        ctrls = {k: v for k, v in controls.items() if isinstance(v, ipw.ValueWidget)} # other controls
        
        for btn in btns:
            for k,w in ctrls.items():
                def update_hint(change, button=btn): _hint_update(button) # closure
                w.observe(update_hint, names='value') # update button hint on value change
                    
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
        with _hold_running_slide_builder(), _print_error(self.out):
            if btn: # despite _print_error, self.out does not pick class out-err, no idea why
                with disabled(btn):
                    _hint_update(btn, remove=True)
                    _run_callbacks(self._fcallbacks, kwargs, self) 
            else:
                _run_callbacks(self._fcallbacks, kwargs, self) 
            

def callback(css_class = None):
    """Decorator to mark methods as interactive callbacks in InteractBase subclasses.
    
    **func**: The method to be marked as a callback.  

    - Must be defined inside a class (not nested).
    - Must be a regular method (not static/class method).
    
    **css_class**: Optional string to assign a CSS class to the callback's output widget. 

    - Must start with 'out-', but should not be 'out-main' which is reserved for main output
    - Example valid values: 'out-stats', 'out-plot', 'out-details'
    - If no css_class is provided, the callback will not create a separate output widget and will use the main output instead.
    
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
    "Use this function to assign a CSS class to a function being used in interactive, interact. to make a separate output widget."
    if not callable(func):
        raise TypeError(f"Can only function as first paramter, got {type(func).__name__}")
    
    if not isinstance(css_class, str):
        raise TypeError(f"css_class must be a string, got {type(css_class).__name__}")
    
    if not css_class.startswith('out-'):
        raise ValueError(f"css_class must start with 'out-', got {css_class!r}")
    
    if css_class == 'out-main':
        raise ValueError("out-main is reserved class for main output widget")
    
    if css_class and not re.match(r'^out-[a-zA-Z0-9-]+$', css_class):
        raise ValueError(f"css_class is not valid, must only contain letters, numbers or hyphens, got {css_class!r}")
    
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
    
    def resize_fig(fig, fs):
        fig.layout.autosize = True # plotly's figurewidget always make trouble with sizing
    
    dashboard = interactive(
        classed(update_plot, 'out-plot'),  # Assign CSS class to output, otherwise it will be captured by main output
        resize_fig, # responds to fullscreen change
        x = ipw.IntSlider(0, 0, 100),
        y = ipw.FloatSlider(0, 1),
        fig = ipw.fixed(fig),
        fs = '.isfullscreen', # detect fullscreen change on instance itself
    )
    ```

    **Parameters**:     

    - `*funcs`: One or more callback functions
    - auto_update: Update automatically on widget changes
    - app_layout: Initial layout configuration, see `relayout()` method for details
    - grid_css: CSS Grid properties for layout
        - Use `:fullscreen` at root level of dict to apply styles in fullscreen mode
        - Use `[Button, ToggleButton, ToggleButtons].add_class('content-width-button')` to fix button widths easily.
        - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).
    - `**kwargs`: Widget parameters

    **Widget Parameters**:     

    - Regular ipywidgets
    - Fixed widgets via ipw.fixed()
    - String pattern 'widget.trait' for trait observation, 'widget' must be in kwargs or '.trait' to observe traits on this instance.
    - You can use '.fullscreen' to detect fullscreen change and do actions based on that.
    - Any DOM widget that needs display (inside fixed too). A widget and its observed trait in a single function are not allowed, such as `f(fig, v)` where `v='fig.selected'`.
    - Plotly FigureWidgets (use patched_plotly)
    - `ipywidgets.Button` for manual updates on callbacks besides global `auto_update`. Add tooltip for info on button when not synced.
    

    **Widget Updates**:     

    - Functions can modify widget traits (e.g. options, min/max)
    - Order matters for dependent updates
    - Parameter-less functions run with any interaction
    - Animation widgets work even with manual updates
    - **Output Widget Behavior**:
        - Output widgets are created only if a CSS class is provided via `@callback` or `classed`.
        - If no CSS class is provided, the callback will use the main output widget labeled as 'out-main'.
    

    **CSS Classes**:      

    - Parameter names from kwargs
    - Custom 'out-*' classes from classed(), and 'out-main' class.
    - 'btn-main' for manual update button

    **Notes**:       

    - Avoid modifying global slide state
    - Use widget descriptions to prevent name clashes
    - See set_css() method for styling options
    - interactive(no_args_func_which_may_fetch_data_on_click,) is perfectly valid and run on button click.
    
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
    """Plotly's FigureWidget with two additional traits `selected` and `clicked` to observe.
    
    - selected: Dict - Points selected by box/lasso selection
    - clicked: Dict - Last clicked point (only updates when clicking different point, it should not be considered a button click)

    Each of `selected` and `clicked` dict adds a `customdata` silently which in case of plotly.expresse is restricted to be array of shape (columns, len(x))
    and in plotly.graph_objs.Figure case is not restricted but should be indexible by selected points, like an array of shape (len(x), columns) 
    (transpose of above, which is done by plotly.express internally, but not in Figure, which is inconsistant and inconvinient) is a good data 
    where x is in px.line or go.Scatter for example.

    **Note**: You may need to set `fig.layout.autoszie = True` to ensure fig adopts parent container size. 
    (whenever size changes, it may need to be set again in many cases due to some internal issues with plotly)
    """
    if getattr(fig.__class__,'__name__','') != 'FigureWidget':
        raise TypeError("provide plotly's FigureWidget")
    
    if fig.has_trait('selected') and fig.has_trait('clicked'):
        return fig # Already patched, no need to do it again
    
    fig.add_traits(selected = traitlets.Dict(), clicked=traitlets.Dict())

    def _attach_data(change):
        data = change['new']
        if data:
            if data['event_type'] == 'plotly_click': # this runs so much times
                fig.clicked = _attach_custom_data(fig, fig.clicked, data['points'])
            elif data['event_type'] == 'plotly_selected':
                fig.selected = _attach_custom_data(fig, fig.selected, data['points'])
            
    fig.observe(_attach_data, names = '_js2py_pointsCallback')
    return fig

def _attach_custom_data(fig, old, points): # fully forgiven
    if old == points: return old # why process again
    try:
        if not points or not isinstance(points, dict):
            return {}

        # Get indices safely
        ti = points.get('trace_indexes', [])
        pi = points.get('point_indexes', [])
        if not ti or not pi:
            return {**points, 'customdata':[]}

        cdata = []
        for t, p in zip(ti, pi):
            try:
                cdata.append(fig.data[t].customdata[p])
            except:
                cdata.append(None)
        points.update({'customdata': cdata})
        return points
    except:
        points['customdata'] = [None] * len(points.get('trace_indexes', []))
        return points 
