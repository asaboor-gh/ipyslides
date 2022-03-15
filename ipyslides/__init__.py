from .shared_vars import __version__
__version__ = __version__

from .core import LiveSlides
IPySlides  = LiveSlides # alias

__all__ = ['LiveSlides','IPySlides']
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
