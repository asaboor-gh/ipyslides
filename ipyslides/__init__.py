"""ipyslides module to create presentations in Jupyter using Python.

You can import Slides, write, xmd, PAGE, PART and fmt directly from top level.
"""


from .core import Slides, fmt, esc, xmd, write
from .__version__ import __version__

fsep = Slides.fsep  # frame separator for convenience
PAGE = Slides.PAGE  # page delimiter for top level convenience
PART = Slides.PART  # part delimiter

version = __version__ # add a public attribute

__all__ = ["Slides", "fsep", "PAGE", "PART", "fmt", "esc", "write", "xmd"]
