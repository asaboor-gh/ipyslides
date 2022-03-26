from .__version__ import __version__
__version__ = __version__

from .core import LiveSlides
from .extended_md import parse_xmd

def display_markdown(markdown_file_path):
    """Parse a markdown file and display immediately. 
    Runs python code blocks with header `python run source_var_name`. 
    
    New in 1.4.6
    """
    with open(markdown_file_path, 'r') as f:
        md_str = f.read()
    parse_xmd(md_str, display_inline = True) # No return required

__all__ = ['LiveSlides', 'parse_xmd', 'display_markdown']
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
