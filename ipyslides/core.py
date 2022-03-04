import sys
from collections import namedtuple
from contextlib import contextmanager

import numpy as np
from IPython import get_ipython
from IPython.display import display
from IPython.utils.capture import capture_output
import ipywidgets as ipw

from .source import Source
from .writers import write, iwrite
from .formatter import bokeh2html, plt2html
from . import utils

_under_slides = {k:getattr(utils,k,None) for k in utils.__all__}

from ._base.base import BaseLiveSlides
from ._base.intro import how_to_slide
from ._base.scripts import multi_slides_alert
from ._base import styles

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
        return cls.__instance #return each time, display will make sure single display in last call
        #else:
        #    raise Exception("Can't create more than one instance of a singleton class! Resrtart Kernel or delete previous instance.")
            
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
            
        self.plt2html   = plt2html
        self.bokeh2html = bokeh2html
        self.source = Source # Code source
        self.write  = write # Write IPython objects in slides
        self.iwrite = iwrite # Write Widgets/IPython in slides
            
        self.shell.register_magic_function(self.__slide, magic_kind='cell',magic_name='slide')
        self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name='title')
        self.user_ns = self.shell.user_ns #important for set_dir
        
        self._citations = {} # Initialize citations
        self.__slides_mode = False
        with capture_output() as self.__slides_title_page:
            write(how_to_slide)

        self.__slides_dict = {} # Initialize slide dictionary
        self._slides_title_note = None #must be None, not True/False
        self._slides_notes = {} # Initialize notes dictionary
        self._current_slide = 'title' # Initialize current slide for notes at title page
        
        self.__iterable = self.__collect_slides() # Collect internally
        self._nslides = int(self.__iterable[-1]['n']) if self.__iterable else 0 # Real number of slides
        self._max_index = 0 # Maximum index including frames
        
        self.loading_html = self.widgets.htmls.loading #SVG Animation in it
        
        self.progress_slider = self.widgets.sliders.progress
        self.progress_slider.observe(self.__update_content,names=['index'])
        
        # All Box of Slides
        self._box =  self.widgets.mainbox
        self._box.on_displayed(lambda change: self.__muti_notebook_slides_alert()) 
        self.__update_content(True) # First attmpt will only update title page
        self._display_box_ = ipw.VBox() # Initialize display box
    
    def __muti_notebook_slides_alert(self):
        " Alert for multiple slides in other notebooks, as they don't work well together."
        with self.widgets.outputs.renew:
            display(multi_slides_alert)

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
        
        return self._ipython_display_()

    
    def _ipython_display_(self):
        'Auto display when self is on last line of a cell'
        if not self.__slides_mode:
            return print('Set "self.convert2slides(True)", then it will work.')
        
        self.close_view() # Close previous views
        self._display_box_ = ipw.VBox(children=[self.__jlab_in_cell_display(), self._box]) # Initialize display box again
        return display(self._display_box_)
    
    def close_view(self):
        "Close all slides views, but keep slides in memory than can be shown again."
        self._display_box_.close() 
    
    def __jlab_in_cell_display(self): 
        # Can test Voila here too
        try: # SHould try, so error should not block it
            if 'voila' in self.shell.config['IPKernelApp']['connection_file']:
                self.widgets.sliders.width.value = 100 # This fixes dynamic breakpoint in Voila
        except: pass # Do Nothing
         
        return ipw.VBox([
                    ipw.HBox([
                        ipw.HTML("""<b style='color:var(--accent-color);font-size:24px;'>IPySlides</b>"""),
                        self.widgets.toggles.display
                    ]),
                    self.widgets.toggles.timer,
                    self.widgets.htmls.notes
                ])
            
    
    def __display_slide(self):
        self.display_toast() # or self.toasts.display_toast . Display in start is fine
        item = self.__iterable[self.progress_slider.index]
        self.notes.display(item['notes']) # Display notes first
        _number = f'{item["n"]} / {self._nslides}' if self.progress_slider.index != 0 else ''
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
        self.__iterable = self.__collect_slides() # would be at least one title slide
        n_last = self.__iterable[-1]['n']
        self._nslides = int(n_last) # Avoid frames number
        self._max_index = len(self.__iterable) - 1 # This includes all frames
        
        # Now update progress bar
        old_label = self.progress_slider.label
        denom = n_last if n_last > 0 else 1 # in case only title slide
        opts = [(f"{s['n']}", np.round(100*s['n']/denom, 2)) for s in self.__iterable]
        self.progress_slider.options = opts  # update options
        
        if old_label in list(zip(*opts))[0]: # Bring back to same slide if possible
            self.progress_slider.label = old_label
            
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
        """Capture content of a cell as `slide`.
            ---------------- Cell ----------------
            %%slide 1                             
            #python code here                     
            --------------------------------------
        
        You can use another cell magic under it to capture cell content as you want, e.g.
            ---------------- Cell ----------------
            %%slide 2
            %%markdown
            Everything here and below is treated as markdown, not python code.
            --------------------------------------
            ---------------- Cell ----------------
            %%slide 3
            %%javascript
            alert('Hello from second slide') # This will open a popup on third slide
            --------------------------------------
        """
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
        self._current_slide = f'{slide_number}.1' # First frame
        def _frames(func):
            if not isinstance(slide_number,int):
                return print(f'slide_number expects integer, got {slide_number!r}')

            if not self.__slides_mode:
                print(f'Showing raw form of given objects, will be displayed in slides using function {func} dynamically')
                return objs
            else:
                for i, obj in enumerate(objs,start=1):
                    with capture_output() as cap:
                        self.write_slide_css(**css_props)
                        func(obj)
                    self.__slides_dict[f'{slide_number}.{i}'] = cap
                    
                self.refresh() # Content change refreshes it.
        return _frames
        
    def convert2slides(self,b=False):
        "Turn ON/OFF slides vs editing mode. Should be in same cell as `LiveSLides`"
        self.__slides_mode = b

        
    def __collect_slides(self):
        """Collect cells for an instance of LiveSlides."""
        slides_iterable = [{'slide':self.__slides_title_page,'n':0,'notes': self._slides_title_note}]
        if not self.__slides_mode:
            return tuple(slides_iterable) # return title in any case
        
        val_keys = sorted([int(k) if k.isnumeric() else float(k) for k in self.__slides_dict.keys()]) 
        str_keys = [str(k) for k in val_keys]
        
        _min, _max = [int(val_keys[0]), int(val_keys[-1])] if val_keys else (0,0)
        frames = [int(v.split('.')[1]) for v in str_keys if '.' in v]
        max_frames = max(frames) if frames else 0
        
        n = 0 #start of slides
        for i in range(_min,_max + 1):
            if i in val_keys:
                n = n + 1 #should be added before slide
                notes = self._slides_notes[f'{i}'] if f'{i}' in self._slides_notes else None
                slides_iterable.append({'slide':self.__slides_dict[f'{i}'],'n':n,'notes':notes}) 
            
            for j in range(1, max_frames + 1):
                key = f'{i}.{j}'
                if key in str_keys:
                    if j == 1:
                        n = n + 1 #should be added for next frames once
                    notes = self._slides_notes[key] if key in self._slides_notes else None
                    slides_iterable.append({'slide':self.__slides_dict[key],'n':float(f'{n}.{j}'),'notes':notes}) 
            
        return tuple(slides_iterable)