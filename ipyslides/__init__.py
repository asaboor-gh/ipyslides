from IPython.core.magic import Magics, magics_class, cell_magic
from . import data_variables as dv

# __slides_mode = False
# __slides_dict = {}
#__dynamicslides_dict = {}
 
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
            
def initialize():
    ipython = get_ipython()
    ipython.register_magics(SlidesMagics)
    ipython.set_next_input(dv.title_page)
    
def add(slide_number):
    if not isinstance(slide_number,int):
        return print(f'slide_number expects integer, got {slide_number!r}')
    ipython = get_ipython()
    ipython.set_next_input(f"%%slide {slide_number}\n", replace=True)
    
def add_after(slide_number):
    if not isinstance(slide_number,int):
        return print(f'slide_number expects integer, got {slide_number!r}')
    ipython = get_ipython()
    ipython.set_next_input(f"%%dynamicslides {slide_number}\n", replace=True)
    
def build(): #Set Next full input
    ipython = get_ipython()
    if not '__slides_mode' in ipython.user_ns.keys() or not ipython.user_ns['__slides_mode']:
        return print('Set "__slides_mode = True" in top cell and run again.')
    pass
    
    
