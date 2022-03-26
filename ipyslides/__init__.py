from .__version__ import __version__

version = __version__

from .core import LiveSlides
from .extended_md import parse_xmd
from .formatter import code_css

def display_markdown(markdown_file_path, print_text_fonts = None, print_code_fonts = None):
    """Parse a markdown file and display immediately. This is handy for generating document from markdown file with python code outputs.
    Runs python code blocks with header `python run source_var_name`. 
    
    You can export notebook as HTML and print it to PDF or just `Ctrl + P`, that will be a cleaned without cells PDF document.
    Exported and printed PDF will include notebook's markdown cells.
    
    If printed from exported HTML, you can give a CSS file 'custom.css' in same folder as HTML file.
    
    You can provide fonts that will be used while printing PDF. If not given, fallbacks to default fonts.
    
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
    .RTL, .RTL > * {
        text-align:right !important;
        padding: 0 12px !important; /* to avoid cuts in RTL */
        line-height: 120% !important;
    }
    .PyRepr { white-space: pre !important; }
    @media print {
        ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
        div.input, div.output_area > div.prompt{ display:none !important; }
        img, svg, span {
            page-break-before: auto; 
            page-break-after: auto; 
            page-break-inside: avoid; 
        }
        div.output_wrapper, div.output  { 
            page-break-inside: auto !important;
        }
        div.highlight { border: 1px solide gray; border-radius: 4px;}
        body *:not(.fa):not(i):not(span) {   
            font-family: __textfont__, "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" ;
        }
        body code>span { font-family: __codefont__, "SimSun-ExtB", "Cascadia Code","Ubuntu Mono", "Courier New";}
    }
    </style>'''.replace('__textfont__',f'"{print_text_fonts}"').replace('__codefont__',f'"{print_code_fonts}"'))
    
    parse_xmd(xmd, display_inline = True) # No return required

__all__ = ['LiveSlides', 'display_markdown']
      
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
    
