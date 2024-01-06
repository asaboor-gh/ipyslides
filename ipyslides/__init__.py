from .core import Slides

# Add version to the namespace here too
version = (
    Slides._version
)  # private class attribute, instance attribute is version property
__version__ = version

__all__ = ["Slides"]
