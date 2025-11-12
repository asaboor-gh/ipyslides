"""ipyslides module to create presentations in Jupyter using Python.

You can import Slides, fsep, write, xmd and fmt directly from top level.
"""


from .core import Slides, fmt, esc, xmd, write
from .__version__ import __version__

fsep = Slides.fsep  # frame separator for convenience

version = __version__ # add a public attribute

__all__ = ["Slides", "fsep", "fmt", "esc", "write", "xmd"]
