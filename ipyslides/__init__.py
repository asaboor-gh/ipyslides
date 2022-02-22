from .shared_vars import __version__
__version__ = __version__

import os
from .core import LiveSlides 
from .writers import write

__all__ = ['initialize','init','demo']
__all__.extend(['LiveSlides', 'write'])
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
def __parse_md_file(md_file):
    "Parse a Markdown file to put in slides and returns text for title and each slide."
    with open(md_file,'r') as f:
        lines = f.readlines()
        breaks = [-1] # start, will add +1 next
        for i,line in enumerate(lines):
            if line and line.strip() =='---':
                breaks.append(i)
        breaks.append(len(lines)) # Last one
        
        ranges = [range(j+1,k) for j,k in zip(breaks[:-1],breaks[1:])]
        return [''.join(lines[x.start:x.stop]) for x in ranges]
        
    
def initialize(markdown_file=None,
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
               animation = 'slide',
              ):
    """Creates insrance of `LiveSlides` with much of defualt settings enabled. 
    You can create slides from a `markdown_file` as well. Slides separator should be --- (three dashes) in start of line.
    _________ Markdown File Content __________
    # Talk Title
    ---
    # Slide 1 
    ---
    # Slide 2
    ___________________________________________
    This will create two slides along with title page.
    """
    slides = LiveSlides()
    slides.convert2slides(True)
    slides.settings.set_font_scale(font_scale)
    slides.settings.align8center(centering)
    slides.settings.code_line_numbering(code_line_numbering)
    slides.settings.set_footer(footer_text,show_date=show_date,show_slide_number=show_slide_number)
    slides.settings.set_animation(animation)
    slides.settings.theme_dd.value = 'Dark' if dark_theme else 'Fancy'
    slides.settings.set_logo(logo_src,width=50)
    
    with slides.slide(1):
        slides.write('# Slide 1\nOverwrite this using \n`with slide(1):`\n\t`    ...`\n or \n `%%slide 1`')
    # Replace content if markdown file given
    if markdown_file and os.path.isfile(markdown_file):
        chunks = __parse_md_file(markdown_file)
        slides.from_markdown = chunks # Set attribute to access it
        with slides.title():
            write(chunks[0])
        for i,chunk in enumerate(chunks[1:],start=1):
            with slides.slide(i):
                write(chunk)
    return slides

init = initialize # Aliase
    
def demo():
    from . import _demo
    slides = _demo.slides 
    with slides.slide(100):
        write('## This is all code to generate slides')
        write(_demo)
        write(demo)
    with slides.slide(101,background='#9ACD32'):
        with slides.source.context() as s:
            slides.write_citations()
        write(s)
    slides.settings.theme_dd.value = 'Fancy'
    slides.progress_slider.value = 0 # back to title
    return slides
