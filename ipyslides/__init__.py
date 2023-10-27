from .core import Slides

# Add version to the namespace here too
version = (
    Slides._version
)  # private class attribute, instance attribute is version property
__version__ = version

__all__ = ["Slides"]


def load_ipython_extension(ipython):
    """Load the extension in IPython when someone does `%load_ext ipyslides`"""
    print(
        f"""ipyslides {version} is loaded. To get started:
          
    * Access the slides as `slides = get_slides_instance()` in current namespace  
    * Run `slides.demo()` to see a demo of some features
    * Run `slides.docs()` to see documentation
    """
    )


def unload_ipython_extension(ipython):
    pass
