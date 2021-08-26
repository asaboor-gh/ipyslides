__version__ = '0.8.0'

__all__ = ['initialize','initial_code']
from .core import LiveSlides, get_cell_code, display_cell_code
from .utils import write, fmt2cols, plt2html, plotly2html, print_context
__all__.extend(['LiveSlides', 'get_cell_code', 'display_cell_code',
                'write', 'fmt2cols', 'plt2html', 'plotly2html', 'print_context'])

initial_code = '''import ipyslides as isd
from ipyslides.utils import write, plt2html, print_context, fmt2cols

from ipyslides.core import  LiveSlides, display_cell_code, get_cell_code
ls = LiveSlides() # This registers %%slide and %%title magics as bonus

# Note: For LiveSlides('A'), use %%slideA, %%titleA, LiveSlides('B'), use %%slideB, %%titleB
# so that they do not overwite each other's slides.

ls.convert2slides(False) #Set this to True for Slides output
ls.set_footer('Author: Abdul Saboor')
ls.align8center(True) # Set False to align top-left corner

with ls.title():
    write('# Title Page')
    
for i in range(1,5):
    with ls.slide(i):
        write(f'## Slide {i} Title')

ls.show() #Use this only once in case you use Voila. 
#Create slides with %%slide, insert_after now, will be updated on cell run.
'''            
def initialize():
    try:
        ipython = get_ipython()
        current_cell_code = get_ipython().get_parent()['content']['code'].splitlines()
        code_after = '\n'.join([line for line in current_cell_code if 'initialize' not in line])
        ipython.set_next_input(f'{code_after}\n{initial_code}', replace= True)
    except:
        print('Copy lines below in a cell and execute\n',initial_code)
        
        
if __name__ == '__main__':
    print('Use this package in Jupyter notebook!')
