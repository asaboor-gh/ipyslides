"""
An enhanced version of ipywidgets' interactive functionality for Jupyter notebooks.

This module provides extended interactive capabilities including:

**Core Components**:

- InteractBase: Base class for creating interactive dashboard applications
- interact/interactive: wrapper functions for creating simple interactive widgets
- callback: Decorator for widget event callbacks to be used in subclasses of InteractBase
- monitor: Decorator to monitor general functions. All of its parameters are in callback too,
    but it is does not require function to satisfy being a callback.


**Custom Widgets**:

- ListWidget: Widget for list-based interactions that can hold any python object.
- AnimationSlider: Widget for animation controls
- Output: Modified output widget for display management

**Utilities**:

- patched_plotly: Modified plotly integration with added traits `selected` and `clicked`.
- plt2html: Convert matplotlib plots to HTML format.

Use this module to create rich interactive visualizations and user interfaces
in Jupyter notebooks with minimal boilerplate code.

This module is a wrapper around the `ipyslides.interaction` modulde.
"""

__all__ = [
    'InteractBase','callback', 'monitor', 'print_error', 'interactive','interact', 'patched_plotly', 'plt2html',
    'ListWidget', 'AnimationSlider', 'TimerWidget', 'Output', 
]

from ipyslides.interaction import (
    InteractBase, 
    callback, 
    monitor,
    interact, 
    interactive,
    print_error,
    patched_plotly)
from ipyslides._base._widgets import ListWidget, AnimationSlider, TimerWidget
from ipyslides._base.widgets import Output # patched one
from ipyslides.formatters import plt2html

def classed(*args,**kwargs):
    raise DeprecationWarning("You can use @callback on pure functions too, so classed is no more required")