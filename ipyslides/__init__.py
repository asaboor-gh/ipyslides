from .__version__ import __version__

version = __version__

from .core import LiveSlides 
from . import parsers

__all__ = ['LiveSlides', 'parsers']

        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
