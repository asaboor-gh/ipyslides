__version__ = '0.0.2'

from IPython.core.magic import Magics, magics_class, cell_magic
from . import data_variables as dv

# __slides_mode = False
# __slides_dict = {}
# __dynamicslides_dict = {}
 
@magics_class
class SlidesMagics(Magics):
    @cell_magic 
    def slide(self,line,cell):
        if line and not line.isnumeric():
            return print(f'You should use %%slide integer, not %%slide {line}')
        if '__slides_mode' in self.shell.user_ns.keys() and self.shell.user_ns['__slides_mode']:
            self.shell.run_cell_magic('capture',line,cell)
            if line: #Only keep slides with line number
                self.shell.user_ns['__slides_dict'][line] = self.shell.user_ns[line]
                del self.shell.user_ns[line]
        else:
            self.shell.run_cell(cell)
    
    @cell_magic
    def dynamicslides(self,line,cell):
        if line and not line.isnumeric():
            return print(f'You should use %%dynamicslides integer, not %%dynamicslides {line}')
        if '__slides_mode' in self.shell.user_ns.keys() and self.shell.user_ns['__slides_mode']:
            key = 'd' + line if line else line #Only keep slides with line number
            self.shell.run_cell_magic('capture',key,cell)
            if key:  
                self.shell.user_ns['__dynamicslides_dict'][key] = self.shell.user_ns[key]
                del self.shell.user_ns[key]
        else:
            self.shell.run_cell(cell)

    
def load_magics():
    get_ipython().register_magics(SlidesMagics)
    
def __filter_cell_code(remove_tag):
    current_cell_code = get_ipython().get_parent()['content']['code'].splitlines()
    return '\n'.join([line for line in current_cell_code if remove_tag not in line])
            
def initialize():
    ipython = get_ipython()
    ipython.register_magics(SlidesMagics)
    code_after = __filter_cell_code('initialize')
    ipython.set_next_input(f'{code_after}\n\n{dv.title_page}', replace= True)
    
def insert(slide_number):
    if not isinstance(slide_number,int):
        return print(f'slide_number expects integer, got {slide_number!r}')
    code_after = __filter_cell_code('insert')
    get_ipython().set_next_input(f"%%slide {slide_number}\n" + code_after, replace=True)
    
def insert_after(slide_number):
    if not isinstance(slide_number,int):
        return print(f'slide_number expects integer, got {slide_number!r}')
    
    code_after = __filter_cell_code('insert_after')
    code_after += f'\n\n#Below variable should be list or tuple on which func in LiveSlides act\n__dynamicslides_dict["d{slide_number}"] = []'
    get_ipython().set_next_input(code_after, replace=True)
    
def build(): #Set Next full input
    ipython = get_ipython()
    if not '__slides_mode' in ipython.user_ns.keys() or not ipython.user_ns['__slides_mode']:
        return print('Set "__slides_mode = True" in top cell and run all cells below again.')
    else:
        code_after = __filter_cell_code('build')
        ipython.set_next_input(code_after + "\n"+ dv.build_cell, replace=True)

def insert_style():
    get_ipython().set_next_input(dv.style_html, replace=True)
    
    
