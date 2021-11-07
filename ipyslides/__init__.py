__version__ = '1.0.2'


from .core import LiveSlides
from .utils import write
from .data_variables import animations

__all__ = ['initialize','init','demo']
__all__.extend(['LiveSlides', 'write'])
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
def initialize(magic_suffix = '',
               centering = True,
               dark_theme = False,
               footer_text = 'Author Name',
               show_slide_number = True,
               show_date = True,
               code_line_numbering = True,
               font_scale = 1.0,
               logo_src = '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="50" fill="blue"/>
        <text x="45%" y="45%" fill="white" font-size="4em" dominant-baseline="central" text-anchor="middle">↑</text>
        <text x="55%" y="60%" fill="white" font-size="4em" dominant-baseline="central" text-anchor="middle">↓</text></svg>''',
               animation_css = animations['slide_h'],
              ):
    """Creates insrance of `LiveSlides` with much of defualt settings enabled. 
    `magic_suffix` add value to slide's magic, e.g. if `magic_suffix='A'`, slides should be
    created using `%%slideA` magic. Other arguments are just settings of slides. 
    """
    slides = LiveSlides(animation_css=animation_css,magic_suffix=magic_suffix)
    slides.convert2slides(True)
    slides.set_font_scale(font_scale)
    slides.align8center(centering)
    slides.code_line_numbering(code_line_numbering)
    slides.set_footer(footer_text,show_date=show_date,show_slide_number=show_slide_number)
    
    if dark_theme:
        slides.setting.theme_dd.value = 'Dark'
    slides.set_logo(logo_src,width=50)
    
    with slides.slide(1):
        slides.write('# Slide 1\nOverwrite this using \n`with slide(1):`\n\t`    ...`\n or \n `%%slide 1`')
    return slides

init = initialize # Aliase
    
def demo():
    import os
    from . import _demo, utils
    
    slides = _demo.slides 
    with slides.slide(100):
        with slides.source():
            write('## This is all code to generate slides')
            write(_demo)
            write(demo)
    with slides.slide(101,background='#9ACD32'):
        with slides.source():
            slides.write_citations()
        
    slides.prog_slider.value = 0 # back to title
    return slides
