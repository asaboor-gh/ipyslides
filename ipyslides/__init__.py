from .__version__ import __version__

version = __version__

from .core import LiveSlides
from .extended_md import parse_xmd
from .formatter import code_css

def display_markdown(markdown_file_path):
    """Parse a markdown file and display immediately. This is handy for generating document from markdown file with python code outputs.
    Runs python code blocks with header `python run source_var_name`. 
    
    You can export notebook as HTML and print it to PDF, that will be a cleaned without cells PDF document.
    Exported and printted PDF will include notebook's markdown cells.
    
    New in 1.4.6
    """
    with open(markdown_file_path, 'r') as f:
        xmd = f.read()
    parse_xmd(code_css(style='default',background='unset')) # Minimal Code style
    parse_xmd('''<style>
    div.columns { 
        width:100%;max-width:100%;
        display:inline-flex;flex-direction:row;
        column-gap:2em;height:auto;
    }
    pre, code { background:unset !important;}
    pre { padding: 0.2em !important; padding-bottom: 0.2em; margin-bottom: 0.5em; }
    @media print {
        div.input, div.output_area > div.prompt{ display:none !important; }
        img, svg, .columns, div.highlight, span {
            page-break-before: auto; 
            page-break-after: auto; 
            page-break-inside: avoid; 
        }
    }
    </style>''')
    parse_xmd(xmd, display_inline = True) # No return required

__all__ = ['LiveSlides', 'display_markdown']
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
