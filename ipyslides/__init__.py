from .__version__ import __version__

version = __version__

from .core import Slides
from . import parsers

__all__ = ['LiveSlides', 'Slides','parsers']

# Backward Compatibale namespace
class LiveSlides:
    __doc__ = Slides.__doc__
    def __new__(cls,*args, **kwargs):
        import warnings
        from .__version__ import __version__
        major,minor, patch = map(int,__version__.split('.'))
        if major >= 2:
            if minor < 5:
                warnings.warn('Name "Slides" is being deprecated. Use "Slides" instead!')
            if minor >= 5:
                raise DeprecationWarning('Name "Slides" is deprecated. Use "Slides" instead!')
        return Slides(*args, **kwargs)
    
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
