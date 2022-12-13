from .__version__ import __version__

version = __version__

from .core import Slides

__all__ = ['Slides']

major, minor, patch = [int(v) for v in __version__.split('.')]
if major < 3 and minor < 3:
    print('Starting from version 2.0, there is complete rewrite of CSS for slides, so custom CSS classes may not work! See `Slides.docs()` for more info.')

if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
