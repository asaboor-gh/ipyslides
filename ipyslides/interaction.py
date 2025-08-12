"""
Enhanced version of ipywidgets's interact/interactive functionality.
Use as interactive/@interact or subclass InteractBase. 
"""

__all__ = ['interactive','interact', 'monitor', 'patched_plotly','disabled','print_error'] # other need to be explicity imported

import re, textwrap
import inspect 
import traitlets

from contextlib import contextmanager, nullcontext
from collections import namedtuple
from types import FunctionType
from typing import List, Callable, Dict, Union, Tuple

from IPython.display import display
from ipywidgets import DOMWidget, Box # for clean type annotation

from .formatters import get_slides_instance
from .utils import _build_css, _dict2css
from ._base.widgets import ipw # patch ones required here
from ._base._widgets import _fix_init_sig, AnimationSlider
from ._interact import (
    AnyTrait, Changed, FullscreenButton, 
    monitor, print_error, disabled, patched_plotly, 
    _format_docs, _size_to_css, _general_css
)
from . import _interact as _need_output

_css_info = textwrap.indent('\n**Python dictionary to CSS**\n' + _dict2css, '    ')

@contextmanager
def _hold_running_slide_builder():
    "Hold the running slide builder to restrict slides specific content."
    if (slides := get_slides_instance()):
        with slides._hold_running():
            yield
    else:
        yield

def _func2widget(func, change_tracker):
    func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
    out = None # If No CSS class provided, no output widget will be created, default
    
    if klass := func.__dict__.get('_css_class', None):
        out = ipw.Output()
        out.add_class(klass)
        out._kwarg = klass # store for access later
        
    last_kws = {} # store old kwargs to avoid re-running the function if not changed
    
    def call_func(kwargs):
        old_ctx = _need_output._active_output
        if out:
            out.clear_output(wait=True) # clear previous output
            _need_output._active_output = out # to get it for debounce in monitor

        with (out or nullcontext()):
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in func_params}

            # Check if any parameter is a Button, and skip them
            buttons = [v for v in filtered_kwargs.values() if isinstance(v, ipw.Button)]
            
            # Any parameter which is widget does not change identity even if underlying data changes.
            # For example, Plotly's FigureWidget relies on underlying data for ==, which can make `new_fig != old_fig`
            # evaluate to True even when `new_fig is old_fig`. This can trigger unnecessary function calls during active
            # selections, which cannot be removed from the Python side (unfortunately). 
            # Checking identity is a mess later together with == and in, we can just exclude them here, widget is supposed to have a static identity
            other_params  = {k: v for k, v in filtered_kwargs.items() if not isinstance(v, ipw.DOMWidget)}
            
            if buttons:
                if not any(btn.clicked for btn in buttons):
                    return # Only update if a button was clicked and skip other parameter changes
                
                with print_error(), disabled(*buttons): # disable buttons during function call
                    try: # error still be raised, but will be caught by print_error, so finally is important
                        func(**filtered_kwargs) # Call the function with filtered parameters only if changed or no params
                    finally:
                        last_kws.update(filtered_kwargs) # update old kwargs to latest values
                
                return # exit after button click handling
                
            # Compare values properly by checking each parameter that is not a Widget (should already be same object)
            # Not checking identity here to take benifit of mutations like list/dict content
            values_changed = [k for k, v in other_params.items() 
                if (k not in last_kws) or (v != last_kws[k]) 
            ] # order of checks matters
            
            # Run function if new values, or does not have parameters or on button click
            if values_changed or not func_params: # function may not have arguments but can be run via others
                change_tracker._set(values_changed)
                with print_error():
                    func(**filtered_kwargs) # Call the function with filtered parameters only if changed or no params
            
            change_tracker._set([])
            last_kws.update(filtered_kwargs) # update old kwargs to latest values
            _need_output._active_output = old_ctx
    
    return (call_func, out)


def _hint_update(btn, remove = False):
    (btn.remove_class if remove else btn.add_class)('Rerun')

def _run_callbacks(fcallbacks, kwargs, box):
    # Each callback is executed, Error in any of them don't stop other callbacks, handled in print_error context manager
    _need_output._active_output = box.out if box else nullcontext() # default, unless each func sets and resets
    try:
        for func in fcallbacks:
            func(box.kwargs if box else kwargs) # get latest from box due to internal widget changes
    finally:
        _need_output._active_output = nullcontext()


# We need to link useful traits to set from outside, these will be linked from inside
# But these raise error if tried to set from __init__, only linked in there
_useful_traits =  [
    'pane_widths','pane_heights','merge', 'width','height',
    'grid_gap', 'justify_content','align_items'
]
# for validation
_pmethods = ['set_css','relayout','update']
_pattrs = ['groups','outputs','params', 'changed','isfullscreen']
_omethods = ["_interactive_params"]

class InteractMeta(type):
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)

        # Identify the first meaningful base class (skip 'object')
        primary_base = ([base for base in bases if base is not object] or [None])[0]

        # Check protected methods and attributes
        for attr in [*_pmethods,*_pattrs, *_useful_traits]:
            if attr in namespace and primary_base and hasattr(primary_base, attr):
                raise TypeError(f"Class '{name}' cannot override '{attr}'.")

        # Check mandatory methods
        for method_name in _omethods:
            if method_name not in namespace:
                raise TypeError(f"Class '{name}' must override '{method_name}'.")

# Need to avoid conflict with metaclass of interactive, so build a composite metaclass
_metaclass = type("InteractiveMeta", (InteractMeta, type(ipw.interactive)), {})

def _add_traits(cls):
    for name in _useful_traits:
        setattr(cls, name, ipw.AppLayout.class_traits()[name])
    return cls

@_add_traits
@_fix_init_sig
@_format_docs(css_info = _css_info)
class InteractBase(ipw.interactive, metaclass = _metaclass):
    """Enhanced interactive widgets with multiple callbacks and fullscreen support.
    
    Use `interctive` function or `@interact` decorator for simpler use cases. For comprehensive dashboards, subclass this class.

    **Features**:    

    1. Multiple callback support through `@callback` decorator
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
        def show_stats(self, x, y):
            if 'y' in self.changed: # detect if y was changed
                print(f"Distance: {{np.sqrt(1 + y**2)}}")
            else:
                print(x)
    
    # Create and layout
    dash = MyDashboard(auto_update=True)
    dash.relayout(
        left_sidebar=dash.groups.controls,  # controls on left
        center=[(ipw.VBox(), ('fig', ipw.HTML('Showing Stats'), 'out-stats')),]  # plot and stats in a VBox explicitly
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
        - header: List[str | DOMWidget | (Box, List[str | DOMWidget])] - Top widgets
        - left_sidebar: List[str | DOMWidget | (Box, List[str | DOMWidget])] - Left side widgets 
        - center: List[str | DOMWidget | (Box, List[str | DOMWidget])] - Main content area
        - right_sidebar: List[str | DOMWidget | (Box, List[str | DOMWidget])] - Right side widgets
        - footer: List[str | DOMWidget | (Box, List[str | DOMWidget])] - Bottom widgets
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
        - You can have multiple buttons in a single callback and check `btn.clicked` attribute to run code based on which button was clicked.
    - Plotly FigureWidgets (use patched_plotly for selection support)

    **Callbacks**:   

    - Methods decorated with `@callback`. Run in the order of definition.
    - Optional CSS class via `@callback('out-myclass')`
    - Decorate with @monitor to check execution time, kwargs etc.
    - CSS class must start with 'out-' excpet reserved 'out-main'
    - Each callback gets only needed parameters and updates happen only when relevant parameters change
    - **Output Widget Behavior**:
        - An output widget is created only if a CSS class is provided via `@callback`.
        - If no CSS class is provided, the callback will use the main output widget, labeled as 'out-main'.
        
    **Attributes & Properties**:  

    - changed: Read-only trait to detect which parameters of a callback changed:
        - By providing `changed = '.changed'` in parameters and later in callback by checking `changed('param') -> Bool`.
        - Directly access `self.changed` in a subclass and use `changed('param') -> Bool` / `'param' in self.changed`. Useful to merge callback.
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
    changed = traitlets.Instance(Changed, default_value=Changed(), read_only=True) # tracks parameters values changed, but fixed itself

    def __init__(self, auto_update:bool=True, app_layout:dict= None, grid_css:dict={}) -> None:
        # I tried to resolve dependent parameters in a func many ways like setting mock validate, notify_change, set, etc.
        # But each time app misbehaves, so I leave it on user for a function like func(x = widget, y = 'x.trait') 
        # and expected they should not se x.trait = value in same function, to avoid recursion issue.
        self.__css_class = 'i-'+str(id(self))
        self.__style_html = ipw.HTML()
        self.__style_html.layout.position = 'absolute' # avoid being grid part
        self.__app = ipw.AppLayout().add_class('interact-app') # base one
        self.__app.layout.display = 'grid' # for correct export to html, other props in set_css
        self.__app.layout.position = 'relative' # contain absolute items inside
        self.__app._size_to_css = _size_to_css # enables em, rem
        self.__other = ipw.VBox().add_class('other-area') # this should be empty to enable CSS perfectly, unless filled below
        self.update = self.__update # needs avoid checking in metaclass, but restric in subclasses, need before setup
        self.__setup(auto_update, app_layout, grid_css)
        
        # do not add traits in __init__, unknow errors arise, just link
        for name in _useful_traits:
            traitlets.link((self, name),(self.__app,name))

    def __setup(self, auto_update, app_layout, grid_css):
        if not isinstance(grid_css,dict):
            raise TypeError(f"grid_css should be a dict, got {type(grid_css)}")
        
        self.set_css(main = grid_css)
        self.__auto_update = auto_update
        self._outputs = ()
        self.__iparams = {} # just empty reference
        extras = self.__fix_kwargs() # params are internally fixed
        if not self.__iparams: # need to interact anyhow and also allows a no params function
            self.__auto_update = False
        
        self.__icallbacks = self._registered_callbacks() # callbacks after collecting params
        if not isinstance(self.__icallbacks, (list, tuple)):
            raise TypeError("_registered_callbacks should return a tuple of functions!")
        outputs = self.__func2widgets() # build stuff, before actual interact
        super().__init__(self.__run_updates, {'manual':not self.__auto_update,'manual_name':''}, **self.__iparams)
        
        btn = getattr(self, 'manual_button', None) # need it above later
        self.add_class('ips-interact').add_class(self.__css_class)
        self.layout.position = 'relative' # contain absolute items inside
        self.layout.height = 'max-content' # adopt to inner height

        self.children += (*extras, *outputs, self.__style_html) # add extra widgets to box children
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
            btn.add_traits(clicked=traitlets.Bool(False, read_only=True)) # just completeness for global button too
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

        self.__all_widgets = self.__order_widgets(btn) # save it once for sending to app layout
        self._groups = self.__create_groups(self.__all_widgets) # create groups of widgets for later use
        
        for func in self.__icallbacks:
            self.__hint_btns_update(func) # external buttons update hint
        
        if app_layout is not None:
            self.__validate_layout(app_layout) # validate arguemnts first
            self.relayout(**app_layout)
        else:
            self.relayout(center=list(self.__all_widgets.keys())) # add all to GridBox which is single column
    
    def __order_widgets(self, manual_btn=None):
        _kw_map = {w._kwarg: w for w in self.children if hasattr(w, '_kwarg')}
        # 1) params in declared order
        ordered = {name:_kw_map[name] for name in self.__iparams.keys() if name in _kw_map}
        # 2) Manual button (if any) comes after params
        if manual_btn:
            ordered['btn-main'] = manual_btn
        # 3) outputs in registration order
        ordered.update({out._kwarg: out for out in self._outputs if hasattr(out, '_kwarg')})
        # 4) main output
        ordered["out-main"] = self.out
        # 5) anything else with _kwarg not yet included
        ordered.update({name: w for name, w in _kw_map.items() if name not in ordered})
        return ordered
    
    def __repr__(self): # it throws very big repr, so just show class name and id
        return f"<{self.__module__}.{type(self).__name__} at {hex(id(self))}>"

    def __validate_layout(self, app_layout):
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
            
            if self.__auto_update:
                value = [v for v in value if v != 'btn-main'] # avoid throwing error over button, which changes by other paramaters
            
            for i, name in enumerate(value,start=1):
                if isinstance(name,str):
                    if not name in self.__all_widgets:
                        raise ValueError(
                            f"Invalid widget name {name!r} in {key!r} at position {i}. "
                            f"Valid names are: {list(self.__all_widgets.keys())}")
                    continue # valid widget name, no need to check further

                if isinstance(name, ipw.DOMWidget):
                    continue # Allow widgets in layout other than just from params

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
                    if not isinstance(child, (str, ipw.DOMWidget)):
                        raise TypeError(
                            f"Widget names in tuple at position {i} in {key!r} must be strings or widgets, "
                            f"got {type(child).__name__}")
                    
                    if isinstance(child, str) and child not in self.__all_widgets:
                        raise ValueError(
                            f"Invalid widget name {child!r} in tuple at position {i} in {key!r}. "
                            f"Valid names are: {list(self.__all_widgets.keys())}")
    
    def relayout(self, 
        header: List[Union[str, DOMWidget,Tuple[Box, List]]] = None, 
        center: List[Union[str, DOMWidget,Tuple[Box, List]]] = None, 
        left_sidebar: List[Union[str, DOMWidget,Tuple[Box, List]]] = None,
        right_sidebar: List[Union[str, DOMWidget,Tuple[Box, List]]] = None,
        footer: List[Union[str, DOMWidget,Tuple[Box, List]]] = None,
        pane_widths: Tuple[float, float, float] = None, 
        pane_heights: Tuple[float, float, float] = None,
        merge: bool = True, 
        grid_gap: str = None, 
        width: str = None,
        height: str = None, 
        justify_content: str = None,
        align_items: str = None,
        ) -> None:
        """Configure widget layout using AppLayout structure.

        **Parameters**:  

        - Content Areas (list/tuple of widget names):
            - header: Widgets at top
            - center: Main content area (uses CSS Grid)
            - left_sidebar: Left side widgets
            - right_sidebar: Right side widgets  
            - footer: Bottom widgets
            - Each of above must be a List[str | DOMWidget | (Box, List[str | DOMWidget])] of widget params names if given. 
                - Box is instance of ipywidgets.Box() initialized without children.
                - Support of any widget other than just params in layout enables flexible and rich dashboards.
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
        self.__validate_layout(app_layout)
        areas = ["header","footer", "center", "left_sidebar","right_sidebar"]

        collected = []
        for key, value in app_layout.items():
            if value and key in areas:
                collected.extend(list(value))
                box = ipw.GridBox if key == 'center' else ipw.VBox
                children = []
                for name in value:
                    if isinstance(name,str) and name in self.__all_widgets:
                        children.append(self.__all_widgets[name])
                    elif isinstance(name, ipw.DOMWidget): # any random widget is allowed in layout
                        children.append(name)
                    elif isinstance(name, (list,tuple)) and len(name) == 2: # already checked, but just in case
                        nested_box, childs = name
                        nested_box.children = tuple([self.__all_widgets[n] if n in self.__all_widgets else n for n in childs])
                        collected.extend([c for c in childs if isinstance(c, str)]) # avoid showing nested ones again.
                        children.append(nested_box) # add box to  main children
                    
                self.__app.set_trait(key, box(children, _dom_classes = (key.replace('_','-'),))) # for user CSS
            elif value: # class own traits and Layout properties are linked here
                self.set_trait(key, value) 
        
        self.__other.children += tuple([v for k,v in self.__all_widgets.items() if k not in collected])
        
        # We are adding a reaonly isfullscreen trait set through button on parent class
        fs_btn = FullscreenButton()
        fs_btn.observe(lambda c: self.set_trait('isfullscreen',c.new), names='isfullscreen') # setting readonly property
        self.children = (self.__app, self.__other, self.__style_html, _need_output._active_timer.widget(True), fs_btn)
    
    @_format_docs(css_info = textwrap.indent(_css_info,'    ')) # one more time indent for nested method
    def set_css(self, main:dict=None, center:dict=None) -> None:
        """Update CSS styling for the main app layout and center grid.
        
        **Parameters**:         

        - main (dict): CSS properties for main app layout
            - Target center grid with ` > .center ` selector
            - Target widgets by their parameter names as classes
            - Use `:fullscreen` at root level of dict to apply styles in fullscreen mode
            - Use `[Button, ToggleButton(s)].add_class('content-width-button')` to fix button widths easily.
        - center (dict): CSS properties for center grid section
            - Direct access to center grid (same as main's ` > .center `)
            - Useful for grid layout of widgets inside center area
            - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).

        **CSS Classes Available**:  

        - Parameter names from _interactive_params()
        - 'btn-main' for manual update button
        - Custom 'out-*' classes from `@callback` decorators and 'out-main' from main output.

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
        return self._set_css(main=main, center=center)

    def _set_css(self, main, center): # in ipyvasp I needed ovveriding it, user can, but call super()._set_css for sure
        if main and not isinstance(main,dict):
            raise TypeError('main should be a nesetd dictionary of CSS properties to apply to main app!')
        if center and not isinstance(center,dict):
            raise TypeError('center should be a nesetd dictionary of CSS properties to apply to central grid!')
        
        main_sl = f".{self.__css_class}.widget-interact.ips-interact > .interact-app" # directly inside
        cent_sl = f"{main_sl} > .center"
        _css = _build_css(('.ips-interact > .interact-app',),_general_css)

        fs_css = main.pop(':fullscreen',{}) or main.pop('^:fullscreen',{}) # both valid
        if fs_css: # fullscreen css given by user, full screen is top interact, not inside one as button is there
            _css += ('\n' + _build_css((f".{self.__css_class}.widget-interact.ips-interact:fullscreen > .interact-app",), fs_css))
        
        if main:
            _css += ("\n" + _build_css((main_sl,), main))
        if center:
            _css += ("\n" + _build_css((cent_sl,), center))
        self.__style_html.value = f'<style>{_css}</style>'
    
    def _interactive_params(self) -> Dict:
        "Implement this in subclass to provide a dictionary for creating widgets and observers."
        raise NotImplementedError("implement _interactive_params(self) method in subclass, "
            "which should returns a dictionary of interaction parameters.")
    
    def _registered_callbacks(self) -> List[Callable]:
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
    
    def __validate_params(self, params):
        if not isinstance(params, dict):
            raise TypeError(f"method `_interactive_params(self)` should return a dict of interaction parameters")
                
        for key in params:
            if not isinstance(key, str) or not key.isidentifier():
                raise ValueError(f"{key!r} is not a valid name for python variable!")
 
    def __fix_kwargs(self):
        params = self._interactive_params() # subclass defines it
        self.__validate_params(params)   

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
        
        for key, value in extras.items():
            value._kwarg = key # required for later use
            if isinstance(value, ipw.Button): # Button can only be in extras, by fixed or itself
                # Add click trigger flag and handler, callbacks using this can only be triggered by click
                value.add_traits(clicked=traitlets.Bool(False, read_only=True)) # useful to detect which button pressed in callbacks
                value.add_class('Refresh-Btn') # add class for styling
                value.on_click(self.update) # after setting clicked, update outputs on click
                if not value.tooltip: # will show when not synced
                    value.tooltip = 'Run Callback'

        # All params should be fixed above before doing below
        for key, value in params.copy().items(): 
            # not for random dict, but intended one
            if isinstance(value, dict) and len(value) == 1 and set(value).issubset(params):
                print(f"use 'widget.trait' instead of {value}, which allows using '.trait' to observe traits on the instance")
                value = '.'.join([*value.keys(), *value.values()]) # make a str for old way to work
                print("converted to:", value)

            if isinstance(value, str) and value.count('.') == 1 and ' ' not in value: # space restricted
                name, trait_name = value.split('.')
                if name == '' and trait_name in self.trait_names() and not trait_name.startswith('_'): # avoid privates
                    if trait_name == 'changed':
                        params[key] = ipw.fixed(self.changed) # need this without triggering callback
                    else:
                        params[key] = AnyTrait(self, trait_name)
                    # we don't need mutual exclusion on self, as it is not passed
                elif name in params: # extras are already cleaned widgets, otherwise params must have key under this condition
                    w = params.get(name, None)
                    if isinstance(w, ipw.fixed):
                        w = w.value # wrapper widget may be

                    # We do not want to raise error, so any invalid string can goes to Text widget
                    if isinstance(w, ipw.DOMWidget) and trait_name in w.trait_names():
                        params[key] = AnyTrait(w, trait_name)

        # Set __iparams after clear widgets
        self.__iparams = params
        
        # Tag parameter widgets with their names so we can order later
        for key, val in self.__iparams.items():
            w = val.value if isinstance(val, ipw.fixed) else val
            if isinstance(w, ipw.DOMWidget):
                w._kwarg = key
                
        self.__reset_descp(extras)
        return tuple(extras.values())
    
    def __update(self, *args):
        btn = args[0] if args and isinstance(args[0],ipw.Button) else None # if triggered by click on a button
        try:
            self.__app.add_class("Context-Loading")
            if btn: btn.set_trait('clicked', True) # since read_only
            super().update(*args) # args are ignored anyhow but let it pass
        finally:
            self.__app.remove_class("Context-Loading")
            if btn:
                btn.set_trait('clicked', False)
                _hint_update(btn, remove=True)
    
    def __reset_descp(self, extras):
        # fix description in extras, like if user pass IntSlider etc.
        for key, value in extras.items():
            if 'description' in value.traits() and not value.description \
                and not isinstance(value,(ipw.HTML, ipw.HTMLMath, ipw.Label)): # HTML widgets and Labels should not pick extra
                value.description = key # only if not given
    
    def __func2widgets(self):
        self._outputs = ()   # reference for later use
        callbacks = [] # collecting processed callback
        used_classes = {}  # track used CSS classes for conflicts 
        seen_funcs = set() # track for any duplicate function

        for f in self.__icallbacks:
            if not callable(f):
                raise TypeError(f'Expected callable, got {type(f).__name__}. '
                    'Only functions accepting a subset of kwargs allowed!')
            
            if f in seen_funcs:
                raise ValueError(f"Duplicate callback detected {f.__name__!r}")

            seen_funcs.add(f)
            
            # Check for CSS class conflicts
            if klass := f.__dict__.get('_css_class', None):
                if klass in used_classes:
                    raise ValueError(
                        f"CSS class {klass!r} is used by multiple callbacks: "
                        f"{f.__name__!r} and {used_classes[klass]!r}"
                    )
                used_classes[klass] = f.__name__
            
            self.__validate_func(f) # before making widget, check
            new_func, out = _func2widget(f, self.changed) # converts to output widget if user set class or empty
            callbacks.append(new_func) 
            
            if out is not None:
                self._outputs += (out,)
        
        self.__icallbacks = tuple(callbacks) # set back
        del used_classes, seen_funcs, callbacks # no longer needed
        return self._outputs # explicit
    
    def __validate_func(self, f):
        ps = inspect.signature(f).parameters
        f_ps = {k:v for k,v in ps.items()}
        has_varargs = any(param.kind == param.VAR_POSITIONAL for param in ps.values())
        has_varkwargs = any(param.kind == param.VAR_KEYWORD for param in ps.values())

        if has_varargs or has_varkwargs:
            raise TypeError(
                f"Function {f.__name__!r} cannot have *args or **kwargs in its signature. "
                "Only explicitly named keywords from interactive params are allowed."
            )

        if len(ps) == 0 and self.__auto_update:
            raise ValueError(
                f"Function {f.__name__!r} must have at least one parameter when auto_update is enabled (default). "
                "Any function with no arguments can only run with global interact button click."
            )
        
        gievn_params = set(self.params._asdict())
        extra_params = set(f_ps) - gievn_params
        if extra_params:
            raise ValueError(f"Function {f.__name__!r} has parameters {extra_params} that are not defined in interactive params.")
        
    def __create_groups(self, widgets_dict):
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
    
    def __hint_btns_update(self, func):
        func_params = {k:v for k,v in inspect.signature(func).parameters.items()}
        # Let's observe buttons by shared value widgets in func_params
        controls = {c: self.__all_widgets[c] for c in self.groups.controls if c in func_params} # filter controls by func_params
        btns = [controls[k] for k in func_params if isinstance(controls.get(k,None), ipw.Button)]
        ctrls = {k: v for k, v in controls.items() if isinstance(v, ipw.ValueWidget)} # other controls
        
        for btn in btns:
            for k,w in ctrls.items():
                def update_hint(change, button=btn): _hint_update(button) # closure
                w.observe(update_hint, names='value') # update button hint on value change
               
    @property
    def outputs(self) -> tuple: return self._outputs

    @property
    def groups(self) -> namedtuple: 
        """NamedTuple of widget groups: controls, outputs, others."""
        if not hasattr(self, '_groups'):
            self._groups = self.__create_groups(self.__all_widgets)
        return self._groups
    
    @property
    def params(self) -> namedtuple:
        "NamedTuple of all parameters used in this interact, including fixed widgets. Can be access inside callbacks with self.params."
        if not hasattr(self, '_params_tuple'):
            wparams = self.__iparams.copy() # copy to avoid changes
            for k, v in self.__iparams.items():
                if isinstance(v, ipw.fixed) and isinstance(v.value, ipw.DOMWidget):
                    wparams[k] = v.value # only widget to expose for use, not other fixed values
            self._params_tuple = namedtuple('InteractiveParams', wparams.keys())(**wparams)
        return self._params_tuple
    
    def __run_updates(self, **kwargs):
        btn = getattr(self, 'manual_button', None)
        with _hold_running_slide_builder(), print_error():
            if btn: 
                with disabled(btn):
                    _hint_update(btn, remove=True)
                    _run_callbacks(self.__icallbacks, kwargs, self) 
            else:
                _run_callbacks(self.__icallbacks, kwargs, self) 
        

def callback(css_class:str = None, *, timeit:bool = False, throttle:int = None, debounce:int = None, logger:Callable = None) -> Callable:
    """Decorator to mark methods as interactive callbacks in InteractBase subclasses or for interactive funcs.
    
    **func**: The method to be marked as a callback.  

    - Must be defined inside a class (not nested) or a pure function in module.
    - Must be a regular method (not static/class method).
    
    **css_class**: Optional string to assign a CSS class to the callback's output widget. 

    - Must start with 'out-', but should not be 'out-main' which is reserved for main output
    - Example valid values: 'out-stats', 'out-plot', 'out-details'
    - If no css_class is provided, the callback will not create a separate output widget and will use the main output instead.

    Other keyword arguments are passed to `monitor`

    - timeit: bool, if True logs function execution time.
    - throttle: int milliseconds, minimum interval between calls.
    - debounce: int milliseconds, delay before trailing call. If throttle is given, this is ignored.
    - logger: callable(str), optional logging function (e.g. print or logging.info).

    **Usage**:                  

    - Inside a subclass of InteractBase, decorate methods with `@callback` and `@callback('out-important')` to make them interactive.
    - See example usage in docs of InteractBase.

    **Returns**: The decorated method itself.
    """  
    def decorator(func):
        if not isinstance(func, FunctionType):
            raise TypeError(f"@callback can only decorate functions, got {type(func).__name__}")
    
        # get a new function after monitor and then apply attributes
        func = monitor(timeit=timeit,throttle=throttle,debounce=debounce,logger=logger)(func)
        
        nonlocal css_class # to be used later
        if isinstance(css_class, str):
            func = _classed(func, css_class) # assign CSS class if provided
        
        qualname = getattr(func, '__qualname__', '')
        if not qualname:
            raise Exception("@callback can only be used on named functions")
        
        if qualname.count('.') == 1:
            if len(inspect.signature(func).parameters) < 1:
                raise Exception(f"{func.__name__!r} cannot be transformed into a bound method!")
            func._is_interactive_callback = True # for methods in class

        return func

    # Handle both @callback and @callback('out-myclass') syntax
    if callable(css_class):
        return decorator(css_class)
    return decorator

def _classed(func, css_class):
    # callable and str already check in callback
    if not css_class.startswith('out-'):
        raise ValueError(f"css_class must start with 'out-', got {css_class!r}")
    if css_class == 'out-main':
        raise ValueError("out-main is reserved class for main output widget")
    if css_class and not re.match(r'^out-[a-zA-Z0-9-]+$', css_class):
        raise ValueError(f"css_class is not valid, must only contain letters, numbers or hyphens, got {css_class!r}")
    func.__dict__['_css_class'] = css_class # set on __dict__ to avoid issues with bound methods
    return func

@_format_docs(css_info = _css_info)
def interactive(*funcs:List[Callable], auto_update:bool=True, app_layout:dict=None, grid_css:dict={}, **kwargs):
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
    from ipyslides.interaction import interactive, callback, monitor
    import ipywidgets as ipw
    import plotly.graph_objects as go
    
    fig = go.FigureWidget()
    
    @callback('out-plot', timeit=True)  # check execution time
    def update_plot(x, y, fig):
        fig.data = []
        fig.add_scatter(x=[0, x], y=[0, y])
    
    def resize_fig(fig, fs):
        fig.layout.autosize = False # double trigger
        fig.layout.autosize = True # plotly's figurewidget always make trouble with sizing
    
    # Above two functions can be merged since we can use changed detection
    @monitor  # check execution time
    def respond(x, y, fig , fs, changed):
        if 'fs' in changed: # or changed('fs')
            fig.layout.autosize = False # double trigger
            fig.layout.autosize = True
        else:
            fig.data = []
            fig.add_scatter(x=[0, x], y=[0, y])
    
    dashboard = interactive(
        update_plot,
        resize_fig, # responds to fullscreen change
        # respond, instead of two functions
        x = ipw.IntSlider(0, 0, 100),
        y = ipw.FloatSlider(0, 1),
        fig = ipw.fixed(fig),
        changed = '.changed', # detect a change in parameter
        fs = '.isfullscreen', # detect fullscreen change on instance itself
    )
    ```

    **Parameters**:     

    - `*funcs`: One or more callback functions
    - auto_update: Update automatically on widget changes
    - app_layout: Initial layout configuration, see `relayout()` method for details
    - grid_css: CSS Grid properties for layout
        - Use `:fullscreen` at root level of dict to apply styles in fullscreen mode
        - Use `[Button, ToggleButton(s)].add_class('content-width-button')` to fix button widths easily.
        - See [CSS Grid Layout Guide](https://css-tricks.com/snippets/css/complete-guide-grid/).
    - `**kwargs`: Widget parameters

    **Widget Parameters**:     

    - Regular ipywidgets
    - Fixed widgets via ipw.fixed()
    - String pattern 'widget.trait' for trait observation, 'widget' must be in kwargs or '.trait' to observe traits on this instance.
    - You can use '.fullscreen' to detect fullscreen change and do actions based on that.
    - You can use `changed = '.changed'` to detect which parameters of a callback changed by checking `changed('param') -> Bool` in a callback.
    - Any DOM widget that needs display (inside fixed too). A widget and its observed trait in a single function are not allowed, such as `f(fig, v)` where `v='fig.selected'`.
    - Plotly FigureWidgets (use patched_plotly)
    - `ipywidgets.Button` for manual updates on callbacks besides global `auto_update`. Add tooltip for info on button when not synced.
        - You can have multiple buttons in a single callback and check `btn.clicked` attribute to run code based on which button was clicked.

    **Widget Updates**:     

    - Functions can modify widget traits (e.g. options, min/max)
    - Order matters for dependent updates
    - Parameter-less functions run with any interaction
    - Animation widgets work even with manual updates
    - **Output Widget Behavior**:
        - Output widgets are created only if a CSS class is provided via `@callback`.
        - If no CSS class is provided, the callback will use the main output widget labeled as 'out-main'.
    

    **CSS Classes**:      

    - Parameter names from kwargs
    - Custom 'out-*' classes from `@callback`, and 'out-main' class.
    - 'btn-main' for manual update button

    **Notes**:       

    - Avoid modifying global slide state
    - Use widget descriptions to prevent name clashes
    - See set_css() method for styling options
    - interactive(no_args_func,) is perfectly valid and run on button click to do something like fetch latest data from somewhere.
    
    {css_info}
    """
    class Interactive(InteractBase): # Encapsulating
        def _interactive_params(self): return kwargs # Must be overriden in subclass
        def _registered_callbacks(self): return funcs # funcs can be provided by @callback decorated methods or optionally ovveriding it
        def __dir__(self): # avoid clutter of traits for end user on instance
            return ['set_css','relayout','groups','outputs','params','isfullscreen','changed', 'layout', *_useful_traits] 
    return Interactive(auto_update=auto_update,app_layout=app_layout, grid_css=grid_css)
    
@_format_docs(other=interactive.__doc__)
def interact(*funcs:List[Callable], auto_update:bool=True,app_layout:dict=None, grid_css:dict={}, **kwargs) -> None:
    """{other}

    **Tips**:    

    - You can use this inside columns using delayed display trick, like code`write('First column', C2)` where code`C2 = Slides.hold(Slides.ei.interact, f, x = 5) or Slides.ei.interactive(f, x = 5)`.
    - You can also use this under `Slides.capture_content` to display later in a specific place.
    """
    def inner(func):
        return display(interactive(func, *funcs, auto_update = auto_update, app_layout=app_layout, grid_css = grid_css, **kwargs))
    return inner