"""ipyslides module to create presentations in Jupyter using Python.

You can import Slides, write, xmd, pause and fmt directly from top level.
"""


from .core import Slides, fmt, esc, xmd, write
from .__version__ import __version__

PAGE = Slides.PAGE  # legacy page delimiter kept for compatibility
pause = Slides.pause  # pause delimiter
PART = Slides.PART  # deprecated alias of pause

version = __version__ # add a public attribute

__all__ = ["Slides", "PAGE", "pause", "PART", "fmt", "esc", "write", "xmd"]
