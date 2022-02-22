import sys
from collections import namedtuple
from contextlib import contextmanager

from IPython import get_ipython
from IPython.display import display
from IPython.utils.capture import capture_output
import ipywidgets as ipw

from .source import Source
from .writers import write, iwrite
from .objs_formatter import bokeh2html, plt2html
from . import utils

_under_slides = {k:getattr(utils,k,None) for k in utils.__all__}

from ._base import BaseLiveSlides, styles

try:  # Handle python IDLE etc.
    SHELL = get_ipython()
except:
    print("Slides only work in IPython Notebook!")
    sys.exit()
    
        
class LiveSlides(BaseLiveSlides):
    __instance = None # Make it singleton class
    def __new__(cls,*args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
            return cls.__instance
        else:
            print("Only one instance of slides per notebook is available!")
            
    # Singlton class can't be initialized twice, so arguments are not passed
    def __init__(self):
        """Interactive Slides in IPython Notebook. Only one instance can exist. 
        Use `display(Markdown('text'))` instead of `print` in slides or
        ```python
        with ipyslides.utils.print_context():
            print('something')
            function_that_prints_something()
        ```
        - **Example**
            ```python 
            import ipyslides as isd 
            isd.initilize() #This will generate code in same cell including this class, which is self explainatory 
            ```
        """
        super().__init__() # start Base class in start
        self.shell = SHELL
        
        for k,v in _under_slides.items(): # Make All methods available in slides
            setattr(self,k,v)
        self.plt2html = plt2html
        self.bokeh2html = bokeh2html
        self.source = Source # Code source
        self.write = write # Write IPython objects in slides
        self.iwrite = iwrite # Write Widgets/IPython in slides
            
        self.shell.register_magic_function(self.__slide, magic_kind='cell',magic_name='slide')
        self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name='title')
        self.user_ns = self.shell.user_ns #important for set_dir
        
        self._citations = {} # Initialize citations
        self.__slides_mode = False
        with capture_output() as captured:
            write('''## Create title page using `%%title` magic or `self.title()` context manager.\n> Author: Abdul Saboor\n<div>
        <h4 style="color:green;">Create Slides using <pre>%%slide</pre> or with <pre>self.slide(slide_number)</pre> context manager.</h4>
        <h4 style="color:olive;">Read instructions by clicking on left-bottom button</h4></div>
        ''')
        self.__slides_title_page = captured
        self.__slides_dict = {} # Initialize slide dictionary
        self.__dynamicslides_dict = {} # initialize dynamic slides dictionary
        
        self._slides_title_note = None #must be None, not True/False
        self._slides_notes = {} # Initialize notes dictionary
        self._current_slide = 'title' # Initialize current slide for notes at title page
        
        self.__iterable = self.__collect_slides() # Collect internally
        self.nslides = int(self.__iterable[-1]['n']) if self.__iterable else 0
        
        self.loading_html = self.widgets.htmls.loading #SVG Animation in it
        
        self.prog_slider = self.widgets.sliders.progress
        self.prog_slider.observe(self.__set_class,names=['value'])
        self.prog_slider.observe(self.__update_content,names=['value'])
        
        # All Box of Slides
        self.box =  self.widgets.mainbox
        self.__update_content(True) # First attmpt
        self.app = self.box # Alias     

    @property
    def slides(self):
        "Get slides list"
        nt = namedtuple('SLIDE','slide n notes')
        return tuple([nt(**d) for d in self.__iterable])
    
    @property
    def iterable(self):
        return self.__iterable  

    def clear(self):
        "Clear all slides."
        self.__slides_dict = {}
        self.__dynamicslides_dict = {}
        self.refresh() # Clear interface too
    
    def cite(self,key, citation,here=False):
        "Add citation in presentation, both key and citation are text/markdown/HTML."
        if here:
            return utils.textbox(citation,left='initial',top='initial') # Just write here
        self._citations[key] = citation
        _id = list(self._citations.keys()).index(key)
        return f'<sup style="color:var(--accent-color);">{_id + 1}</sup>'
    
    def write_citations(self,title='### References'):     
        collection = [f'<span><sup style="color:var(--accent-color);">{i+1}</sup>{v}</span>' for i,(k,v) in enumerate(self._citations.items())]
        return write(title + '\n' +'\n'.join(collection))      
    
    def show(self, fix_buttons = False): 
        "Display Slides. If icons do not show, try with `fix_buttons=True`."
        if not self.__slides_mode:
            return print('Set "self.convert2slides(True)", then it will work.')
        if fix_buttons:
            self.widgets.buttons.next.description = '▶'
            self.widgets.buttons.prev.description = '◀'
            self.widgets.buttons.prev.icon = ''
            self.widgets.buttons.next.icon = ''
        else: # Important as showing again with False will not update buttons. 
            self.widgets.buttons.next.description = ''
            self.widgets.buttons.prev.description = ''
            self.widgets.buttons.prev.icon = 'chevron-left'
            self.widgets.buttons.next.icon = 'chevron-right'
        self.__jlab_in_cell_display()
        return self.box
    __call__ = show
    
    def _ipython_display_(self):
        'Auto display when self is on last line of a cell'
        self.__jlab_in_cell_display()
        return display(self.box)
    
    def __jlab_in_cell_display(self): 
        # Can test Voila here too
        try: # SHould try, so error should not block it
            if 'voila' in self.shell.config['IPKernelApp']['connection_file']:
                self.widgets.sliders.width.value = 100 # This fixes dynamic breakpoint in Voila
        except: pass # Do Nothing
         
        return display(
            ipw.VBox([
                ipw.HBox([
                    ipw.HTML("""<b style='color:var(--accent-color);font-size:24px;'>IPySlides</b>"""),
                    self.widgets.toggles.display
                ]),
                self.widgets.toggles.timer,
                self.widgets.htmls.notes
            ])
        )
        
        
    def __set_class(self,change):
        "Set Opposite animation for backward navigation"
        self.widgets.slidebox.remove_class('Prev') # Safely Removes without error
        if change['new'] == self.prog_slider.max and change['old'] == 0:
            self.widgets.slidebox.add_class('Prev')
        elif (change['new'] < change['old']) and (change['old'] - change['new'] != self.prog_slider.max):
            self.widgets.slidebox.add_class('Prev')
    
    def __display_slide(self):
        self.display_toast() # or self.toasts.display_toast . Display in start is fine
        item = self.__iterable[self.prog_slider.value]
        self.notes.display(item['notes']) # Display notes first
        _number = f'{item["n"]} / {self.nslides}' if self.prog_slider.value != 0 else ''
        self.settings.set_footer(_number_str = _number)
        
        if self.print.is_printing == False: # No animations while printing
            check = round(item["n"] - int(item["n"]), 2) # Must be rounded
            if check <= 0.1: # First frame should slide only to make consistent look
                write(self.settings.animation) # Animation style
        return item['slide'].show() 
           
    def __update_content(self,change):
        if self.__slides_title_page or (self.__iterable and change):
            self.loading_html.value = styles.loading_svg
            self.widgets.outputs.slide.clear_output(wait=True)
            with self.widgets.outputs.slide:
                self.__display_slide()

            self.loading_html.value = ''       
            
        
    def refresh(self): 
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self.__iterable = self.__collect_slides()
        if self.__iterable:
            self.nslides = int(self.__iterable[-1]['n']) # Avoid frames number
            self.N = len(self.__iterable)
        else:
            self.nslides = 0
            self.N = 0
        self.prog_slider.max = self.N -1
        self.__update_content(True) # Force Refresh
        
    def write_slide_css(self,**css_props):
        "Provide CSS values with - replaced by _ e.g. font-size to font_size."
        _css_props = {k.replace('_','-'):f"{v}" for k,v in css_props.items()} #Convert to CSS string if int or float
        _css_props = {k:v.replace('!important','').replace(';','') + '!important;' for k,v in _css_props.items()}
        props_str = ''.join([f"{k}:{v}" for k,v in _css_props.items()])
        out_str = "<style>\n" + f".SlidesWrapper, .SlideArea .block " + "{" + props_str + "}\n"
        if 'color' in _css_props:
            out_str += f".SlidesWrapper p, .SlidesWrapper>:not(div){{ color: {_css_props['color']}}}"
        return write(out_str + "\n</style>") # return a write object for actual write
    
    # defining magics and context managers
    
    def __slide(self,line,cell):
        "Turns to cell magic `slide` to capture slide. Moves to this slide when executed."
        line = line.strip() #VSCode bug to inclue \r in line
        if line and not line.isnumeric():
            return print(f'You should use %%slide integer, not %%slide {line}')
        
        self._current_slide = f'{line}'
        if self.__slides_mode:
            self.shell.run_cell_magic('capture',line,cell)
            if line: #Only keep slides with line number
                self.__slides_dict[line] = self.shell.user_ns[line]
                del self.shell.user_ns[line] # delete the line from shell
                self.refresh()
        else:
            self.shell.run_cell(cell)
    
    @contextmanager
    def slide(self,slide_number,**css_props):
        """Use this context manager to generate any number of slides from a cell
        `css_props` are applied to current slide. `-` -> `_` as `font-size` -> `font_size` in python."""
        if not isinstance(slide_number,int):
            return print(f'slide_number expects integer, got {slide_number!r}')
        
        self._current_slide = f'{slide_number}'
        with capture_output() as cap:
            self.write_slide_css(**css_props)
            yield
        # Now Handle What is captured
        if not self.__slides_mode:
            cap.show()
        else:
            self.__slides_dict[f'{slide_number}'] = cap 
            self.refresh()

    
    def __title(self,line,cell):
        "Turns to cell magic `title` to capture title"
        self._current_slide = 'title'
        if self.__slides_mode:
            self.shell.run_cell_magic('capture','title_output',cell)
            self.__slides_title_page = self.shell.user_ns['title_output']
            del self.shell.user_ns['title_output'] # delete from shell
            self.refresh()
        else:
            self.shell.run_cell(cell)
            
    @contextmanager
    def title(self,**css_props):
        """Use this context manager to write title.
        `css_props` are applied to current slide. `-` -> `_` as `font-size` -> `font_size` in python."""
        self._current_slide = 'title'
        with capture_output() as cap:
            self.write_slide_css(**css_props)
            yield
        # Now Handle What is captured
        if not self.__slides_mode:
            cap.show()
        else:
            self.__slides_title_page = cap 
            self.refresh()
    
    def frames(self, slide_number, *objs, **css_props):
        """Decorator for inserting frames on slide, define a function with one argument acting on each obj in objs.
        Every `obj` is shown on it's own frame. No return of function required, if any, only should be display/show etc.
        `css_props` are applied to all slides from *objs. `-` -> `_` as `font-size` -> `font_size` in python."""
        self._current_slide = 'frames'
        def _frames(func):
            if not isinstance(slide_number,int):
                return print(f'slide_number expects integer, got {slide_number!r}')

            if not self.__slides_mode:
                print(f'Showing raw form of given objects, will be displayed in slides using function {func} dynamically')
                return objs
            else:
                _slides = []
                for obj in objs:
                    with capture_output() as cap:
                        self.write_slide_css(**css_props)
                        func(obj)
                    _slides.append(cap)
                 
                self.__dynamicslides_dict[f'd{slide_number}'] = {'objs': _slides}
                    
                self.refresh() # Content change refreshes it.
        return _frames
        
    def convert2slides(self,b=False):
        "Turn ON/OFF slides vs editing mode. Should be in same cell as `LiveSLides`"
        self.__slides_mode = b

        
    def __collect_slides(self):
        """Collect cells for an instance of LiveSlides."""
        if not self.__slides_mode:
            return [] # return empty in any case

        dynamic_slides = [k.replace('d','') for k in self.__dynamicslides_dict.keys()]
        # If slide number is mistaken, still include that. 
        all_slides = [int(k) for k in [*self.__slides_dict.keys(), *dynamic_slides]]

        try: #handle dynamic slides if empty
            _min, _max = min(all_slides), max(all_slides) + 1
        except:
            _min, _max = 0, 0
        slides_iterable,n = [], 1 # n is start of slides, no other way
        for i in range(_min,_max):
            if f'{i}' in self.__slides_dict.keys():
                notes = self._slides_notes[f'{i}'] if f'{i}' in self._slides_notes else None
                slides_iterable.append({'slide':self.__slides_dict[f'{i}'],'n':n,'notes':notes}) 
                n = n + 1
            if f'd{i}' in self.__dynamicslides_dict.keys():
                __dynamic = self.__dynamicslides_dict[f'd{i}']
                slides = [{'slide':obj,'n':float(f'{n}.{j}'),'notes':None} for j, obj in enumerate(__dynamic['objs'],start=1)]
                if len(slides) == 1:
                    slides[0]['n'] = slides[0]['n'].split('.')[0] # No float in single frame
                slides_iterable = [*slides_iterable,*slides] 
                n = n + 1
        slides_iterable =[{'slide':self.__slides_title_page,'n':0,'notes': self._slides_title_note}, *slides_iterable]
        return tuple(slides_iterable)