from .shared_vars import __version__
__version__ = __version__

from .core import LiveSlides 

__all__ = ['LiveSlides', 'demo']
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
    
def demo():
    from . import _demo
    slides = _demo.slides 
    with slides.slide(100):
        slides.write('## This is all code to generate slides')
        slides.write(_demo)
        slides.write(demo)
    with slides.slide(101,background='#9ACD32'):
        with slides.source.context() as s:
            slides.write_citations()
        slides.write(s)
    slides.settings.theme_dd.value = 'Fancy'
    slides.progress_slider.index = 0 # back to title
    return slides
