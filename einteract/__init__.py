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
    'patched_plotly', 'plt2html', 'stack', 'hstack', 'vstack', 'html',
    'ListWidget', 'AnimationSlider', 'JupyTimer', 'Output', 
]

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
from ipyslides.utils import stack as _stack, as_html_widget as _html

def stack(objs: list, sizes: list=None, vertical: bool=False, css_class: str=None,**css_props):
    """Stack html representation of objs in columns or rows with optionally setting sizes. Returns a widget.
    
    Any python object (except widgets) serializable in ipyslides works, including extended markdown.
    """
    return _stack(objs, sizes=sizes, vertical=vertical, css_class=css_class, **css_props).as_widget()

def hstack(objs: list, widths: list=None):
    """Stack html representation of objs in columns with optionally setting widths. Returns a widget.
    
    Any python object (except widgets) serializable in ipyslides works, including extended markdown.
    """
    return _stack(objs, sizes=widths, vertical=False).as_widget()

def vstack(objs: list, heights: list=None):
    """Stack html representation of objs vertically. Returns a widget.
    
    Any python object (except widgets) serializable in ipyslides package works, including extended markdown.
    """
    return _stack(objs, sizes=heights, vertical=True).as_widget()

def html(obj):
    """Convert obj to html representation. Returns a widget.
    
    Any python object (except widgets) serializable in ipyslides works, including extended markdown.
    """
    return _html(obj)