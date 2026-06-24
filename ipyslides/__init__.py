"""ipyslides module to create presentations in Jupyter using Python.

You can import Slides, write, xmd, pause and fmt directly from top level.
"""


from .core import Slides, fmt, esc, xmd, write, demo, docs
from .__version__ import __version__

pause = Slides.pause  # pause delimiter
version = __version__ # add a public attribute

__all__ = ["Slides", "demo", "docs", "pause", "fmt", "esc", "write", "xmd"]
