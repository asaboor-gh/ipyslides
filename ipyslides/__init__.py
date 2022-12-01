from .__version__ import __version__

version = __version__

from .core import Slides

__all__ = ['LiveSlides', 'Slides']

# Backward Compatibale namespace
class LiveSlides:
    __doc__ = Slides.__doc__
    def __new__(cls,*args, **kwargs):
        #import warnings
        from .__version__ import __version__
        major,minor, patch = map(int,__version__.split('.'))
        if major >= 2:
            if minor < 2:
                print('DeprecationWarning: Name "LiveSlides" is being deprecated. Use "Slides" instead!')
            if minor >= 2:
                raise DeprecationWarning('Name "LiveSlides" is deprecated. Use "Slides" instead!')
        return Slides(*args, **kwargs)
    
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
