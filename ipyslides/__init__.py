from .__version__ import __version__

version = __version__

from .core import LiveSlides


def display_markdown(markdown_file_path, print_text_fonts = None, print_code_fonts = None):
    raise AttributeError("This function is deprecated. Use `LiveSlides.build_report` instead.")

__all__ = ['LiveSlides']
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
