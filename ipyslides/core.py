import sys
from collections import namedtuple
from contextlib import contextmanager, suppress

import numpy as np
from IPython import get_ipython
from IPython.display import display
from IPython.utils.capture import capture_output
import ipywidgets as ipw

from .source import Source
from .writers import write, iwrite
from .formatter import bokeh2html, plt2html, highlight
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
    
        
class _PrivateSlidesClass(BaseLiveSlides):
    """This is private class. Use `LiveSlides` instead."""
    def __init__(self):
        """This is private class. Use `LiveSlides` instead."""
        # print(f'Inside: {self.__class__.__name__}')
        super().__init__() # start Base class in start
        self.shell = SHELL
        
        for k,v in _under_slides.items(): # Make All methods available in slides
            setattr(self,k,v)
            
        self.plt2html   = plt2html
        self.bokeh2html = bokeh2html
        self.highlight  = highlight
        self.source = Source # Code source
        self.write  = write # Write IPython objects in slides
        self.iwrite = iwrite # Write Widgets/IPython in slides
        self.shell.register_magic_function(self.__slide, magic_kind='cell',magic_name='slide')
        self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name='title')
        self.user_ns = self.shell.user_ns #important for set_dir
        
        self._citations = {} # Initialize citations
        self.__slides_mode = True # Default is slides mode since it is more intuitive
        self._computed_display = False # Do not load all slides by default
        
        self.__slides_dict = {} # Initialize slide dictionary, updated by user or by _on_displayed.
        self._slides_notes = {'0': None} # Initialize notes dictionary
        self._slides_css = {} # Initialize css dictionary for each slide
        self._current_slide = '0' # Initialize current slide for notes at title page
        self._i2f_dict = {'0':'0'} # input number -> display number of slide
        self._f2i_dict = {'0':'0'} # display number -> input number of slide
        
        self.__iterable = [] #self.__collect_slides() # Collect internally
        self._nslides =  0 # Real number of slides
        self._max_index = 0 # Maximum index including frames
        
        self.loading_html = self.widgets.htmls.loading #SVG Animation in it
        
        self.progress_slider = self.widgets.sliders.progress
        self.progress_slider.observe(self.__update_content,names=['index'])
        
        # All Box of Slides
        self._box =  self.widgets.mainbox
        self._box.on_displayed(self._on_displayed) 
        self._display_box_ = ipw.VBox() # Initialize display box
    
    def _check_computed(self, what_cannot_do):
        if self._computed_display:
            raise Exception(('Can not {act} on pre-computed display. '
            'Use `.pre_compute_display(False)` to disable it and then {act}. '
            'You may enable it after that for fast loading of slides while presenting!').format(act = what_cannot_do))
    
    def _on_displayed(self, change):
        with self.widgets.outputs.renew:
            display(multi_slides_alert)
        
        self._make_sure_title()
        self.refresh() # This displays the slides 
    
    def _make_sure_title(self):
        if '0' not in self.__slides_dict:
            with capture_output() as captured:
                write(how_to_slide)
                
            self.__slides_dict['0'] = captured

    @property
    def slides(self):
        "Get slides list"
        nt = namedtuple('SLIDE','slide n')
        return tuple([nt(**d) for d in self.__iterable])
    
    @property
    def iterable(self):
        return self.__iterable  
    
    @property
    def _access_key(self):
        "Access key for slides number to get other things like notes, toasts, etc."
        return self._f2i_dict.get(self._slidelabel, '') # being on safe, give '' as default

    def clear(self):
        "Clear all slides."
        self._check_computed('clear slides')
        self._make_sure_title() # Make sure title is there, before updating slides
        self.__slides_dict = {'0':self.__slides_dict.get('0')} # keep title page
        self._slides_notes = {'0':self._slides_notes.get('0',None)} # keep title page's notes
        self._toasts = {'0':self._toasts.get('0',None) } # keep title page's toasts
        self.refresh() # Clear interface too
    
    def cite(self,key, citation,here=False):
        "Add citation in presentation, both key and citation are text/markdown/HTML."
        self._check_computed('add citations')
        if here:
            return utils.textbox(citation,left='initial',top='initial') # Just write here
        self._citations[key] = citation
        _id = list(self._citations.keys()).index(key)
        return f'<sup style="color:var(--accent-color);">{_id + 1}</sup>'
    
    def write_citations(self,title='### References'): 
        "Write all citations collected via `cite` method in the end of the presentation."    
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
    @property
    def _frameno(self):
        "Get current frame number, return 0 if not in frames in slide"
        if '.' in self._slidelabel:
            return int(self._slidelabel.split('.')[-1])
        return 0
    
    @property
    def _slideindex(self):
        "Get current slide index"
        return self.progress_slider.index
    
    @_slideindex.setter
    def _slideindex(self,value):
        "Set current slide index"
        self.progress_slider.index = value
        
    @property
    def _slidelabel(self):
        "Get current slide label"
        return self.progress_slider.label
    
    @_slidelabel.setter
    def _slidelabel(self,value):
        "Set current slide label"
        self.progress_slider.label = value
            
    def __display_slide(self):
        self.loading_html.value = styles.loading_svg
        try:
            _slide_css = self._slides_css.get(self._access_key,'') 
            if (self.print.is_printing == False) and (self._frameno < 2): # No animations while printing or frames
                _slide_css += self.settings.animation # Animation style
            
            self.widgets.outputs.slide.clear_output(wait=True)
            with self.widgets.outputs.slide:
                write(self.html('style',_slide_css)) # Write CSS first
                self.__iterable[self._slideindex]['slide'].show()  # Show slide
        finally:
            self.loading_html.value = ''
           
    def __switch_slide(self,old_index, new_index): # this change is provide from __update_content
        slide_css = self._slides_css.get(self._access_key,'') # Get CSS
        if (self.print.is_printing == False) and (self._frameno < 2): # No animations while printing or frames
            slide_css += self.settings.animation
             
        self.widgets.slidebox.children[-1].clear_output(wait=False) # Clear last slide CSS
        with self.widgets.slidebox.children[-1]:
            write(self.html('style',slide_css)) # Write CSS first to avoid style conflict  
        
        self.widgets.slidebox.children[old_index].layout = ipw.Layout(width = '0',margin='0',opacity='0') # Hide old slide
        self.widgets.slidebox.children[old_index].remove_class('SlideArea')
        self.widgets.slidebox.children[new_index].layout = self.widgets.outputs.slide.layout
        self.widgets.slidebox.children[new_index].add_class('SlideArea')
        
    def __update_content(self,change):
        if self.__iterable and change:
            self.widgets.htmls.toast.value = '' # clear previous content of notification 
            self._display_toast() # or self.toasts._display_toast . Display in start is fine
            self.notes._display(self._slides_notes.get(self._access_key,None)) # Display notes first
        
            n = self.__iterable[self._slideindex]["n"] if self.__iterable else 0 # keep it from slides
            _number = f'{n} / {self._nslides}' if n != 0 else ''
            self.settings.set_footer(_number_str = _number)
            
            if self._computed_display:
                self.__switch_slide(old_index= change['old'], new_index= change['new'])
            else:
                self.__display_slide() 
    
    def pre_compute_display(self,b = True):
        """Load all slides's display and later switch, else loads only current slide. Reset with b = False
        This is very useful when you have a lot of Maths or Widgets, no susequent calls to MathJax/Widget Manager required on slide's switch when it is loaded once."""
        self._computed_display = b
        if b:
            slides = [ipw.Output(layout=ipw.Layout(width = '0',margin='0')) for s in self.__iterable]
            self.widgets.slidebox.children = [*slides, ipw.Output(layout=ipw.Layout(width = '0',margin='0'))] # Add Output at end for style and animations
            for i, s in enumerate(self.__iterable):
                with self.widgets.slidebox.children[i]:
                    s['slide'].show() 
                self._slideindex = i # goto there to update display
                print(f'Pocessing... {int(self.widgets.progressbar.value)}%',end='\r') # Update loading progress bar
        else:
            self.widgets.slidebox.children = [self.widgets.outputs.slide]
            
    def refresh(self): 
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self._check_computed('refresh')
        self.__iterable = self.__collect_slides() # would be at least one title slide
        n_last = self.__iterable[-1]['n']
        self._nslides = int(n_last) # Avoid frames number
        self._max_index = len(self.__iterable) - 1 # This includes all frames
        
        # Now update progress bar
        old_label = self._slidelabel
        denom = n_last if n_last > 0 else 1 # in case only title slide
        opts = [(f"{s['n']}", np.round(100*s['n']/denom, 2)) for s in self.__iterable]
        self.progress_slider.options = opts  # update options
        
        if old_label in list(zip(*opts))[0]: # Bring back to same slide if possible
            self._slidelabel = old_label
            
        self.__update_content(True) # Force Refresh
        
    def __insert_slide_css(self,nframe = None,**css_props):
        "Provide CSS values with - replaced by _ e.g. font-size to font_size."
        self._check_computed('add CSS to slide')
        _css_props = {k.replace('_','-'):f"{v}" for k,v in css_props.items()} #Convert to CSS string if int or float
        _css_props = {k:v.replace('!important','').replace(';','') + '!important;' for k,v in _css_props.items()}
        props_str = ''.join([f"{k}:{v}" for k,v in _css_props.items()])
        out_str = f".SlidesWrapper, .SlideArea .block " + "{" + props_str + "}\n"
        if 'color' in _css_props:
            out_str += f".SlidesWrapper p, .SlidesWrapper>:not(div){{ color: {_css_props['color']}}}"
        
        key = f'{self._current_slide}' if nframe is None else f'{self._current_slide}.{nframe}'
        self._slides_css[key] = out_str
    
    def write_slide_css(self, **css_props):
        "Provide CSS values with - replaced by _ e.g. font-size to font_size."
        self.__insert_slide_css(nframe = None, **css_props)
    
    # defining magics and context managers
    def __slide(self,line,cell):
        """Capture content of a cell as `slide`.
            ---------------- Cell ----------------
            %%slide 1                             
            #python code here                     
        
        You can use another cell magic under it to capture cell content as you want, e.g.
            ---------------- Cell ----------------
            %%slide 2
            %%markdown
            Everything here and below is treated as markdown, not python code.
        """
        line = line.strip() #VSCode bug to inclue \r in line
        if line and not line.isnumeric():
            raise ValueError(f'You should use %%slide integer >= 1, got {line}')
        
        with self.slide(int(line)):
            self.shell.run_cell(cell)
    
    @contextmanager
    def slide(self,slide_number,**css_props):
        """Use this context manager to generate any number of slides from a cell
        `css_props` are applied to current slide. `-` -> `_` as `font-size` -> `font_size` in python."""
        if not isinstance(slide_number, int):
            raise ValueError(f'slide_number should be int >= 1, got {slide_number}')
        
        assert slide_number >= 0 # slides should be >= 1, zero for title slide
        if self._computed_display and self.__slides_mode:
            yield # To avoid generator yied error
            self._check_computed('add slide')
        
        self._current_slide = f'{slide_number}'
        with capture_output() as cap:
            self.__insert_slide_css(**css_props)
            yield
        # Now Handle What is captured
        if not self.__slides_mode:
            cap.show()
        else:
            self.__slides_dict[f'{slide_number}'] = cap 
            self.refresh()
            self._slidelabel = self._i2f_dict[f'{slide_number}'] #go to slide

    
    def __title(self,line,cell):
        "Turns to cell magic `title` to capture title"
        with self.slide(0):
            self.shell.run_cell(cell)
            
    @contextmanager
    def title(self,**css_props):
        """Use this context manager to write title.
        `css_props` are applied to current slide. `-` -> `_` as `font-size` -> `font_size` in python."""
        with self.slide(0, **css_props):
            yield
    
    def frames(self, slide_number, *objs, repeat = False, frame_height = 'auto', **css_props):
        """Decorator for inserting frames on slide, define a function with one argument acting on each obj in objs.
        You can also call it as a function, e.g. `.frames(slide_number = 1,1,2,3,4,5)()` becuase required function is `write` by defualt.
        
        ```python
        @slides.frames(1,a,b,c) # slides 1.1, 1.2, 1.3 with content a,b,c
        def f(obj):
            do_something(obj)
            
        slides.frames(1,a,b,c)() # Auto writes the frames with same content as above
        slides.frames(1,a,b,c, repeat = True)() # content is [a], [a,b], [a,b,c] from top to bottom
        slides.frames(1,a,b,c, repeat = [(0,1),(1,2)])() # two frames with content [a,b] and [b,c]
        ```
        
        **Parameters**
        
        - slide_number: (int) slide number to insert frames on. 
        - objs: expanded by * (list, tuple) of objects to write on frames. If repeat is False, only one frame is generated for each obj.
        - repeat: (bool, list, tuple) If False, only one frame is generated for each obj.
            If True, one frame are generated in sequence of ojects linke `[a,b,c]` will generate 3 frames with [a], [a,b], [a,b,c] to given in function and will be written top to bottom. 
            If list or tuple, it will be used as the sequence of frames to generate and number of frames = len(repeat).
            [(0,1),(1,2)] will generate 2 frames with [a,b] and [b,c] to given in function and will be written top to bottom or the way you write in your function.
        - frame_height: ('N%', 'Npx', 'auto') height of the frame that keeps incoming frames object at static place.
        
        No return of defined function required, if any, only should be display/show etc.
        `css_props` are applied to all slides from *objs. `-` -> `_` as `font-size` -> `font_size` in python."""
        def _frames(func = self.write): # default write if called without function
            self._check_computed('add frames')
            if not isinstance(slide_number,int):
                return print(f'slide_number expects integer, got {slide_number!r}')
            
            assert slide_number >= 1 # Should be >= 1, should not add title slide as frames
            self._current_slide = f'{slide_number}.1' # First frame

            if not self.__slides_mode:
                print(f'Showing raw form of given objects, will be displayed in slides using function {func} dynamically')
                return objs
            else:
                if repeat == True:
                    _new_objs = [objs[:i] for i in range(1,len(objs)+1)]
                elif isinstance(repeat,(list, tuple)):
                    _new_objs =[]
                    for k, seq in enumerate(repeat):
                        if not isinstance(seq,(list,tuple)):
                            raise TypeError(f'Expected list or tuple at index {k} of `repeat`, got {seq}')
                        _new_objs.append([objs[s] for s in seq])
                else:
                    _new_objs = objs
                        
                for i, obj in enumerate(_new_objs,start=1):
                    with capture_output() as cap:
                        self.write(self.format_css('.SlideArea',height = frame_height))
                        self.__insert_slide_css(nframe = i,**css_props) # insert css for all frames
                        func(obj) # call function with obj
                    self.__slides_dict[f'{slide_number}.{i}'] = cap
                    
                self.refresh() # Content change refreshes it.
                self._slidelabel = self._i2f_dict[f'{slide_number}.1'] # goto first frame always
        return _frames 
      
    def convert2slides(self,b=False):
        "Turn ON/OFF slides vs editing mode. Should be in same cell as `LiveSLides`"
        self.__slides_mode = b

    def __collect_slides(self):
        """Collect cells for an instance of LiveSlides."""
        slides_iterable = [{'slide':self.__slides_dict['0'],'n':0}]
        if not self.__slides_mode:
            return tuple(slides_iterable) # return title slide in any case
        
        val_keys = sorted([int(k) if k.isnumeric() else float(k) for k in self.__slides_dict.keys()]) 
        str_keys = [str(k) for k in val_keys]
        _max_range = int(val_keys[-1]) + 1 if val_keys else 1
        
        nslide = 0 #start of slides - 1
        for i in range(1, _max_range):
            if i in val_keys:
                nslide = nslide + 1 #should be added before slide
                slides_iterable.append({'slide':self.__slides_dict[f'{i}'],'n':nslide}) 
                self._i2f_dict[str(i)] = str(nslide)
            
            n_ij, nframe = '{}.{}', 1
            while n_ij.format(i,nframe) in str_keys:
                nslide = nslide + 1 if nframe == 1 else nslide
                _in, _out = n_ij.format(i,nframe), n_ij.format(nslide,nframe)
                slides_iterable.append({'slide':self.__slides_dict[_in],'n':float(_out)}) 
                self._i2f_dict[_in] = _out
                nframe = nframe + 1
        self._f2i_dict = {v:k for k,v in self._i2f_dict.items()}
        return tuple(slides_iterable)

# Make available as Singleton LiveSlides
_private_instance = _PrivateSlidesClass() # Singleton in use namespace
class LiveSlides:
    """Interactive Slides in IPython Notebook. Only one instance can exist. 
    
    **Example**
    ```python 
    import ipyslides as isd 
    ls = isd.LiveSlides() 
    ls.demo() # Load demo slides
    ls.from_markdown(...) # Load slides from markdown files
    ```
    
    Instead of builtin `print` in slides use following to display printed content in correct order.
    ```python
    with ls.print_context():
        print('something')
        function_that_prints_something()
    ```
    
    > `ls.demo` and `ls.from_markdown` overwrite all previous slides.
    
    > All arguments are passed to corresponding methods in `ls.settings`, so you can use those methods to change settings as well.
    """
    def __new__(cls,
                center        = True, 
                content_width = '90%', 
                footer_text   = 'IPySlides | <a style="color:blue;" href="https://github.com/massgh/ipyslides">github-link</a>', 
                show_date     = True,
                show_slideno  = True,
                logo_src      = None, 
                font_scale    = 1, 
                text_font     = 'sans-serif', 
                code_font     = 'var(--jp-code-font-family)', 
                code_style    = 'default', 
                code_lineno   = True, 
                animation     = 'slide_h'):
        "Returns Same instance each time after applying given settings. Encapsulation."
        _private_instance.settings.set_layout(center = center, content_width = content_width)
        _private_instance.settings.set_footer(text = footer_text, show_date = show_date, show_slideno = show_slideno)
        _private_instance.settings.set_logo(src = logo_src)
        _private_instance.settings.set_font_scale(font_scale = font_scale)
        _private_instance.settings.set_font_family(text_font = text_font, code_font = code_font)
        _private_instance.settings.set_code_style(style = code_style)
        _private_instance.settings.code_lineno(b = code_lineno)
        _private_instance.settings.set_animation(name = animation)
        return _private_instance
    
    # No need to define __init__, __new__ is enough to show signature and docs
    
