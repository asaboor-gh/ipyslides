"""ipyslides module to create presentations in Jupyter using Python.

You can import Slides, fsep, write, parse and fmt directly from top level.
"""


from .core import Slides, fsep, write, parse, fmt
from .__version__ import __version__

version = __version__ # add a public attribute

__all__ = ["Slides", "fsep", "fmt", "write", "parse"]
