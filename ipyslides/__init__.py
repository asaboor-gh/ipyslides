__version__ = '0.6.0'

from IPython.core.magic import Magics, magics_class, cell_magic
from . import data_variables as dv

from .core import display_cell_code, get_cell_code, MultiCols
from .utils import write
multicols = MultiCols #Aliasing
__all__ = ['initialize', 'insert_title', 'insert', 'insert_after', 'build',
           'display_cell_code','get_cell_code','MultiCols','multicols']
 
@magics_class
class SlidesMagics(Magics):
    @cell_magic 
    def slide(self,line,cell):
        line = line.strip() #VSCode bug to inclue \r in line
        if line and not line.isnumeric():
            return print(f'You should use %%slide integer, not %%slide {line}')
        if '__slides_mode' in self.shell.user_ns.keys() and self.shell.user_ns['__slides_mode']:
            self.shell.run_cell_magic('capture',line,cell)
            if line: #Only keep slides with line number
                self.shell.user_ns['__slides_dict'] = self.shell.user_ns.get('__slides_dict',{}) #make Sure to get it form shell
                self.shell.user_ns['__slides_dict'][line] = self.shell.user_ns[line]
                del self.shell.user_ns[line] # delete the line from shell
        else:
            self.shell.run_cell(cell)

    
def load_magics():
    get_ipython().register_magics(SlidesMagics)
    
def convert2slides(b=False):
    "Turn ON/OFF slides vs editing mode. Should be in a cell above title and slides."
    shell = get_ipython()
    # Initialize slides collectors but don't overwite to avoid losing already done cells
    shell.user_ns['__dynamicslides_dict'] = shell.user_ns.get('__dynamicslides_dict',{})
    shell.user_ns['__slides_dict'] = shell.user_ns.get('__slides_dict',{})
    shell.user_ns['__slides_mode'] = b
    
def __filter_cell_code(remove_tag):
    current_cell_code = get_ipython().get_parent()['content']['code'].splitlines()
    return '\n'.join([line for line in current_cell_code if remove_tag not in line])
            
def initialize():
    ipython = get_ipython()
    ipython.register_magics(SlidesMagics)
    code_after = __filter_cell_code('initialize')
    ipython.set_next_input(f'{code_after}\n\n{dv.title_page}', replace= True)

def write_title(*colums,width_percents=None):
    "Write title page, supports multicolumns and inline HTML in markdown of each column." 
    shell = get_ipython()
    mode = shell.user_ns.get('__slides_mode',False)
    if mode:
        shell.user_ns['__slides_title_page'] = {'args':colums, 'kwargs':{'width_percents':width_percents}} 
    else:
        write(*colums,width_percents=width_percents)

def insert(slide_number):
    if not isinstance(slide_number,int):
        return print(f'slide_number expects integer, got {slide_number!r}')
    code_after = __filter_cell_code('insert')
    get_ipython().set_next_input(f"%%slide {slide_number}\n" + code_after, replace=True)
    
def insert_after(slide_number,*objs):
    """Creates as many dynamic slides as many number of `objs` are.
    Any object which is handled by function `display_item` at end or have a method `show` is valid."""
    if not isinstance(slide_number,int):
        return print(f'slide_number expects integer, got {slide_number!r}')
    shell = get_ipython()
    shell.user_ns['__dynamicslides_dict'] = shell.user_ns.get('__dynamicslides_dict',{}) #make Sure to get it form shell
    shell.user_ns['__dynamicslides_dict'][f'd{slide_number}'] = objs
    if not shell.user_ns['__slides_mode']:
        print('Showing raw form of given objects, will be displayed in slides using `display_item` function dynamically')
        return objs
    
def build(): #Set Next full input
    ipython = get_ipython()
    if not '__slides_mode' in ipython.user_ns.keys() or not ipython.user_ns['__slides_mode']:
        return print('Set "convert2slides(True)" in top cell and run all cells below again.')
    else:
        code_after = __filter_cell_code('build')
        ipython.set_next_input(code_after + "\n"+ dv.build_cell, replace=True)

    
    
