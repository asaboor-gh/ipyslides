"""
An enhanced version of ipywidgets' interactive functionality for Jupyter notebooks.

This module provides extended interactive capabilities including:

**Core Components**:

- InteractBase: Base class for creating interactive dashboard applications
- interact/interactive: wrapper functions for creating simple interactive widgets
- callback: Decorator for widget event callbacks to be used in subclasses of InteractBase
- monitor: Decorator to monitor general functions. All of its parameters are in callback too,
    but it is does not require function to satisfy being a callback.
- JupyTimer: A widget to observe a function inside Jupyter withought blocking/threading.
    The debounce parameter in `monitor` is working based on it.


**Custom Widgets**:

- ListWidget: Widget for list-based interactions that can hold any python object.
- AnimationSlider: Widget for animation controls
- Output: Modified output widget for display management

**Utilities**:

- patched_plotly: Modified plotly integration with added traits `selected` and `clicked`.
- plt2html: Convert matplotlib plots to HTML format.
- html: Any python object (except widgets) serializable in ipyslides works, including extended markdown.
- hstack: Show objects in columns converted in same manner as `html`.
- vstack: Show objects vertically stacked converted in same manner as `html`.

Use this module to create rich interactive visualizations and user interfaces
in Jupyter notebooks with minimal boilerplate code.

This module is a wrapper around the `ipyslides.interaction` modulde.
"""

__all__ = [
    'InteractBase','callback', 'monitor', 'print_error', 'interactive','interact', 
    'patched_plotly', 'plt2html', 'hstack', 'vstack', 'html',
    'ListWidget', 'AnimationSlider', 'JupyTimer', 'Output', 
]

from contextlib import suppress

from ipywidgets import DOMWidget, HBox, VBox
from ipyslides.interaction import (
    InteractBase, 
    callback, 
    monitor,
    interact, 
    interactive,
    print_error,
    patched_plotly)
from ipyslides._base._widgets import ListWidget, AnimationSlider, JupyTimer
from ipyslides._base.widgets import Output # patched one
from ipyslides.formatters import plt2html
from ipyslides.utils import as_html_widget as _html

def _set_sizes(sizes, children, name):
    if not isinstance(sizes, (list, tuple)):
            raise TypeError(f'{name}s should be a list or tuple of sizes, got {type(sizes)}')
        
    if len(sizes) != len(children):
        raise ValueError(f"Argument '{name}s' must have same length as 'objs', got {len(sizes)} and {len(children)}")
        
    for s in sizes:
        if not isinstance(s, (int, float)):
            raise TypeError(f'{name} should be an int or float, got {type(s)}')
        
    total = sum(sizes)
    return [s/total*100 for s in sizes]

def hstack(objs: list, widths: list=None, **layout_props):
    """Stack widget representation of objs in columns with optionally setting widths (relative integers). Returns a widget.
    
    Any python object serializable in ipyslides works, including widgets and extended markdown.
    layout_props are applied to container widget's layout.
    """
    children = [_html(obj) if not isinstance(obj, DOMWidget) else obj for obj in objs]
    if widths is not None:
        widths = _set_sizes(widths, children, 'width')
        for w, child in zip(widths, children):
            with suppress(BaseException): # some widgets like plotly don't like to set dimensions this way
                child.layout.min_width = "0px" # avoids overflow
                child.layout.flex = f"{w} 1"
                child.layout.width = f"{w}%" 

    return HBox(children=children, layout = layout_props)

def vstack(objs: list, heights: list=None, **layout_props):
    """Stack widget representation of objs vertically with optionally setting heights (relative integers). Returns a widget.
    
    Any python object serializable in ipyslides package works, including widgets and extended markdown.
    layout_props are applied to container widget's layout. Set height of container to apply heights on children.
    """
    children = [_html(obj) if not isinstance(obj, DOMWidget) else obj for obj in objs]
    if heights is not None:
        heights = _set_sizes(heights, children, 'height')
        for h, child in zip(heights, children):
            with suppress(BaseException): # some widgets like plotly don't like to set dimensions this way
                child.layout.min_height = "0px" # avoids overflow
                child.layout.flex = f"{h} 1"
                child.layout.height = f"{h}%"

    return VBox(children=children, layout=layout_props)


def html(obj, **layout_props):
    """Convert obj to html representation. Returns a widget.
    
    Any python object (except widgets) serializable in ipyslides works, including extended markdown.
    layout_props are applied to html widget's layout.
    """
    out = _html(obj)
    out.layout = layout_props
    return out