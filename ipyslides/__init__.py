"""ipyslides module to create presentations in Jupyter using Python.

You can import Slides, write, Output and fmt directly from top level.
"""


from .core import Slides, Output, write, fmt



# Add version to the namespace here too
version = (
    Slides._version
)  # private class attribute, instance attribute is version property
__version__ = version

__all__ = ["Slides", "Output", "fmt", "write"]
