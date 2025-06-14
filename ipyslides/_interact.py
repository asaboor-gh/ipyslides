import sys, re, time
import traitlets
from contextlib import contextmanager, nullcontext
from datetime import datetime
from functools import wraps
from typing import Union, Callable

from ipywidgets import DOMWidget, Output, fixed
from anywidget import AnyWidget
from IPython.core.ultratb import AutoFormattedTB

from ._base.icons import Icon
from ._base._widgets import JupyTimer

_active_output = nullcontext() # will be overwritten by function calls
_active_timer = JupyTimer() # will be displayed inside Interact

def monitor(timeit: Union[bool,Callable]=False, throttle:int=None, debounce:int=None, logger:Callable[[str],None]=None):
    """Decorator that throttles and/or debounces a function, with optional logging and timing.

    - timeit: bool, if True logs function execution time.
    - throttle: int milliseconds, minimum interval between calls.
    - debounce: int milliseconds, delay before trailing call. If throttle is given, this is ignored.
    - logger: callable(str), optional logging function (e.g. print or logging.info).

    This type of call will be automatically timed:

    ```python
    @monitor
    def f(*args,**kwargs):
        pass
    ```python

    but `@monitor()` will do nothing, as no option was used.
    """
    throttle = throttle / 1000 if throttle else 0 # seconds now, but keep debounce in milliseconds

    def log(ctx, msg):
        with ctx:
            logger(msg) if callable(logger) else print(msg)

    def decorator(fn):
        if all(not v for v in [timeit, throttle,debounce]):
            return fn # optimized way to dodge default settings
        
        last_call_time = [0.0]
        last_args = [()]
        last_kwargs = [{}]
        fname = fn.__name__

        @wraps(fn)
        def wrapped(*args, **kwargs):
            now = time.time()
            last_args[0] = args
            last_kwargs[0] = kwargs
 
            def call(out):
                # print(fn, out, throttle, debounce) # debugging
                if isinstance(out, Output): # clean output as it is full call
                    out.clear_output(wait=True)

                start = time.time()
                with out:
                    fn(*last_args[0], **last_kwargs[0])
                    duration = time.time() - start
                    last_call_time[0] = time.time()
                    
                    if timeit:
                        log(nullcontext(), # want to be not overwritten above output 
                            f"\033[34m[Timed]\033[0m     {datetime.now()} | {fname!r}: " 
                            f"executed in {duration*1000:.3f} milliseconds"
                        )

            time_since_last = now - last_call_time[0]
            if throttle and time_since_last >= throttle: # no tolerance required here
                call(_active_output)
            else:
                if throttle:
                    log(_active_output, f"\033[31m[Throttled]\033[0m {datetime.now()} | {fname!r}: skipped call")

                elif debounce:
                    log(_active_output, f"\033[33m[Debounced]\033[0m {datetime.now()} | {fname!r}: reset timer")
                    # This part loses outputs (which go to jupyter logger) if we use threading.Timer os asyncio.
                    # so I created a JupyTimer for Jupyter. You may suspect we can debounce for a simple time check
                    # like in throttle, but we need to take initial args and kwargs to produce correct ouput
                    if not _active_timer.busy(): # Do not overlap
                        _active_timer.run(debounce, call, args=(_active_output,), loop=False, tol = debounce/20) # 5% tolerance
                else:
                    call(_active_output)
        return wrapped
    
    if callable(timeit): # called without parenthesis, automatically timed
        return decorator(timeit)
    return decorator


@contextmanager
def disabled(*widgets):
    "Disable widget and enable it after code block runs under it. Useful to avoid multiple clicks on a button that triggers heavy operations."
    for widget in widgets:
        if not isinstance(widget, DOMWidget):
            raise TypeError(f"Expected ipywidgets.DOMWidget, got {type(widget).__name__}")
        widget.disabled = True
        widget.add_class("Context-Disabled")
    try:
        yield
    finally:
        for widget in widgets:
            widget.disabled = False
            widget.remove_class("Context-Disabled")

# We will capture error at user defined callbacks level
_autoTB = AutoFormattedTB(mode='Context', color_scheme='Linux')

@contextmanager
def print_error(tb_offset=2):
    "Contextmanager to catch error and print to stderr instead of raising it to keep code executing forward."
    try:
        yield
    except:
        tb = '\n'.join(_autoTB.structured_traceback(*sys.exc_info(),tb_offset=tb_offset))
        print(tb, file=sys.stderr) # This was dead simple, but I was previously stuck with ansi2html
        # In future if need to return error, use Ansi2HTMLConverter(inline=True).convert(tb, full = False)

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

class AnyTrait(fixed):
    "Observe any trait of a widget with name trait inside interactive."
    def __init__(self,  widget, trait):
        self._widget = widget
        self._trait = trait

        if isinstance(widget, fixed): # user may be able to use it
            widget = widget.value
        
        if not isinstance(widget, DOMWidget):
            raise TypeError(f"widget expects an ipywidgets.DOMWidget even if wrapped in fixed, got {type(widget)}")
        
        if trait not in widget.trait_names():
            raise traitlets.TraitError(f"{widget.__class__} does not have trait {trait}")
        
        # Initialize with current value first, then link
        super().__init__(value=getattr(widget,trait,None))
        traitlets.dlink((widget, trait),(self, 'value'))

class Changed:
    """A class to track changes in values of params. It itself does not trigger a change. 
    Can be used as `changed = '.changed'` in params and then `changed` can be used in callbacks to check 
    some other value y as changed('y') -> True if y was changed else False. You can also test `'y' in changed`.
    This is useful to merge callbacks and execute code blocks conditionally.
    Using `if changed:` will evalutes to true if any of params is changed.
    
    ```python
    interactive(lambda a,changed: print(a,'a' in changed, changed('changed')), a = 2, changed = '.changed')
    # If a = 5 and changed from a = 6, prints '5 True False'
    # If a = 5 and did not change, prints '5 False False', so changed itself is fixed.
    ```

    In callbacks in subclasses of `InteractBase`, you can just check `self.changed('a')/'a' in self.changed` instead of adding an extra parameter.
    """
    def __init__(self, tuple_ = ()):
        self._set(tuple_)
        
    def _set(self, tuple_):
        if not isinstance(tuple_, (tuple,list)): raise TypeError("tuple expected!")
        self.__values = tuple(tuple_)
    
    def __repr__(self):
        return f"Changed({list(self.__values)})"
    
    def __call__(self, key):
        "Check name of a variable in changed variabls inside a callback."
        # We are using key, because value can not be tracked from source,
        # so in case of x = 8, y = 8, we get 8 == 8 -> True and  8 is 8 -> True, but 'x' is never 'y'.
        if not isinstance(key, str): raise TypeError(f"expects name of variable as str, got {type(key)!r}")
        if key in self.__values:
            return True
        return False
    
    def __contains__(self, key): # 'y' in changed
        return self(key)
    
    def __bool__(self): # any key changed
        return bool(self.__values)


class FullscreenButton(AnyWidget):
    """A button widget that toggles fullscreen mode for its parent element.
    You may need to set `position: relative` on parent element to contain it inside.
    """
    
    _css = """
    .fs-btn.ips-fs {
        position: absolute; top: 2px; left:2px; z-index:999;
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
        '.jp-RenderedHTML': {'padding-right':0}, # feels bad
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
    '.widget-vslider, .jupyter-widget-vslider': {'width': 'auto'}, # otherwise it spans too much area
    '.content-width-button.jupyter-button, .content-width-button .jupyter-button': {
            'width':'max-content',
            'padding-left': '8px', 'padding-right': '8px',
    },
    '> * .widget-box': {'flex-shrink': 0}, # avoid collapse of boxes,
    '.js-plotly-plot': {'flex-grow': 1}, # stretch parent, rest is autosize stuff
    '.columns':{
        'width':'100%',
        'max-width':'100%',
        'display':'inline-flex',
        'flex-direction':'row',
        'column-gap':'0.2em',
        'height':'auto',
        'box-sizing':'border-box !important',
        '> *': {'box-sizing':'border-box !important',}
    }, # as einteract now support vtack, this is good here
}
