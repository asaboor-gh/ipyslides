"""
An enhance version of ipywidgets' interactive. 
It provides additional widgets like ListWidget and AnimationSlider
"""

__all__ = [
    'InteractBase','callback', 'interactive','interact', 'patched_plotly',
    'ListWidget', 'AnimationSlider', 'Output'
]

from ipyslides.interaction import (
    InteractBase, 
    callback, 
    interact, 
    interactive,
    patched_plotly)
from ipyslides._base._widgets import ListWidget, AnimationSlider
from ipyslides._base.widgets import Output # patched one