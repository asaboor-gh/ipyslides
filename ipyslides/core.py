import sys, re
from collections import namedtuple
from contextlib import contextmanager, suppress

from IPython import get_ipython
from IPython.display import display
from IPython.utils.capture import capture_output
import ipywidgets as ipw

from .extended_md import parse_xmd, _allowed_funcs
from .source import Source
from .writers import write, iwrite
from .formatter import bokeh2html, plt2html, highlight, _HTML, serializer
from . import utils

_under_slides = {k:getattr(utils,k,None) for k in utils.__all__}

from ._base.base import BaseLiveSlides
from ._base.intro import how_to_slide, logo_svg
from ._base.scripts import multi_slides_alert
from ._base.slide import build_slide
from ._base import styles

try:  # Handle python IDLE etc.
    SHELL = get_ipython()
except:
    print("Slides only work in IPython Notebook!")
    sys.exit()
    
        
class LiveSlides(BaseLiveSlides):
    # This will be overwritten after creating a single object below!
    __name__ = 'ipyslides.core.LiveSlides' # Used to validate code in markdown, must
    def __init__(self):
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
        self.parse_xmd = parse_xmd # Parse extended markdown
        self.serializer = serializer # Serialize IPython objects to HTML
        
        with suppress(Exception): # Avoid error when using setuptools to install
            self.shell.register_magic_function(self.__slide, magic_kind='cell',magic_name='slide')
            self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name='title')
            self.shell.register_magic_function(self.notes.insert, magic_kind='line',magic_name='notes')
            self.shell.register_magic_function(self.__xmd, magic_kind='line_cell',magic_name='xmd')
            self.user_ns = self.shell.user_ns #important for set_dir
            
            # Override print function to display in order in slides
            def pprint(*args, **kwargs):
                "Displays object(s) inline with others in corrct order. args and kwargs are passed to builtin print."
                with self.capture_std() as std:
                    print(*args, **kwargs)
                std.stdout.display() # Display at the end
            
            self.shell.user_ns['pprint'] = pprint
        
        self._citations = {} # Initialize citations
        self._computed_display = False # Do not load all slides by default
        
        self._slides_dict = {} # Initialize slide dictionary, updated by user or by _on_displayed.
        self._current_slide = '0' # Initialize current slide for notes at title page
        self._reverse_mapping = {'0':'0'} # display number -> input number of slide
        
        self.__iterable = [] #self.__collect_slides() # Collect internally
        self._nslides =  0 # Real number of slides
        self._max_index = 0 # Maximum index including frames
        
        self.loading_html = self.widgets.htmls.loading #SVG Animation in it
        
        self.progress_slider = self.widgets.sliders.progress
        self.progress_slider.label = '0' # Set inital value, otherwise it does not capture screenshot if title only
        self.progress_slider.observe(self._update_content,names=['index'])
        self.markdown_callables = tuple(_allowed_funcs.split('|'))
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
        self.widgets._exec_js(multi_slides_alert)
        
        self._make_sure_title() # Should be before showing it below
        
        self.widgets.slidebox.children[0].clear_output(wait=True)
        with self.widgets.slidebox.children[0]: # title slide in both simple and computed case
            self._slides_dict['0'].show() # Instead of refreshing, we can just update the content of the title slides to avoid errors
        
        with suppress(Exception): # Does not work everywhere.
            self.widgets.inputs.bbox.value = ', '.join(str(a) for a in self.screenshot.screen_bbox) # Useful for knowing scren size
    
    def _make_sure_title(self):
        if '0' not in self._slides_dict:
            with build_slide(self, '0'):
                self.parse_xmd('\n'.join(how_to_slide), display_inline=True)
                
    @property
    def slides(self):
        return tuple(self.__iterable)
    
    @property
    def iterable(self):
        return self.__iterable 
    
    @property
    def citations(self):
        return self._citations 
    
    @property
    def _access_key(self):
        "Access key for slides number to get other things like notes, toasts, etc."
        return self._reverse_mapping.get(self._slidelabel, '') # being on safe, give '' as default

    def clear(self):
        "Clear all slides."
        self._check_computed('clear slides')
        self._make_sure_title() # Make sure title is there, before updating slides
        self._slides_dict = {'0':self._slides_dict.get('0')} # keep title page
        self._toasts = {'0':self._toasts.get('0',None) } # keep title page's toasts
        self.refresh() # Clear interface too
    
    def cite(self,key, citation = None,here = False):
        "Add citation in presentation, key should be a unique string and citation is text/markdown/HTML."
        self._check_computed('add citations')
        if here:
            return utils.textbox(citation,left='initial',top='initial') # Just write here
        self._citations[key] =  citation or self.citations.get(key,None) # Get given first
        _id = list(self._citations.keys()).index(key)
        # Return string otherwise will be on different place
        return f'<a href="#{key}"><sup id ="{key}-back" style="color:var(--accent-color);">{_id + 1}</sup></a>'
    
    def citations_html(self,title='### References'): 
        "Write all citations collected via `cite` method in the end of the presentation."    
        collection = [f'''<span id="{k}">
            <a href="#{k}-back"><sup style="color:var(--accent-color);">{i+1}</sup></a>
            {v if v else f"Set LiveSlides.citations[{k!r}] = 'citation value'"}
            </span>''' for i,(k,v) in enumerate(self._citations.items())]
        return _HTML(self.parse_xmd(title + '\n' +'<br/>'.join(collection), display_inline=False, rich_outputs = False))
    
    def write_citations(self,title='### References'):
        "Write all citations collected via `cite` method in the end of the presentation."
        self.write(self.citations_html(title = title))
        
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
        if self.shell is None or self.shell.__class__.__name__ == 'TerminalInteractiveShell':
            raise Exception('Python/IPython REPL cannot show slides. Use IPython notebook instead.')
        
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
                    ipw.HTML("""<b style='color:var(--accent-color);font-size:24px;'>IPySlides</b>"""),
                    self.widgets.toggles.timer,
                    self.widgets.htmls.notes
                ]).add_class('ExtraControls')
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
            self.widgets.outputs.slide.clear_output(wait=True)
            with self.widgets.outputs.slide:
                if self.screenshot.capturing == False:
                    self.__iterable[self._slideindex].animation.display()
                
                self.__iterable[self._slideindex].show()  # Show slide
        finally:
            self.loading_html.value = ''
            
    def __switch_slide(self,old_index, new_index): # this change is provide from _update_content
        self.widgets.slidebox.children[-1].clear_output(wait=False) # Clear last slide CSS
        with self.widgets.slidebox.children[-1]:
            if self.screenshot.capturing == False:
                self.__iterable[new_index].animation.display()
            self.__iterable[new_index]._css.display()
            
        self.widgets.slidebox.children[old_index].layout = ipw.Layout(width = '0',margin='0',opacity='0') # Hide old slide
        self.widgets.slidebox.children[old_index].remove_class('SlideArea')
        self.widgets.slidebox.children[new_index].layout = self.widgets.outputs.slide.layout
        self.widgets.slidebox.children[new_index].add_class('SlideArea')
        
    def _update_content(self,change):
        if self.__iterable and change:
            self.widgets.htmls.toast.value = '' # clear previous content of notification 
            self._display_toast() # or self.toasts._display_toast . Display in start is fine
            self.notes._display(self._slides_dict.get(self._access_key,None).notes) # Display notes first
        
            n = self.__iterable[self._slideindex].display_number if self.__iterable else 0 # keep it from slides
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
                    s.show() 
                self._slideindex = i # goto there to update display
                print(f'Pocessing... {int(self.widgets.progressbar.value)}%',end='\r') # Update loading progress bar
        else:
            self.widgets.slidebox.children = [self.widgets.outputs.slide]
            
    def refresh(self): 
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self._check_computed('refresh')
        self.__iterable = self.__collect_slides() # would be at least one title slide
        n_last = self.__iterable[-1].display_number
        self._nslides = int(n_last) # Avoid frames number
        self._max_index = len(self.__iterable) - 1 # This includes all frames
        
        # Now update progress bar
        old_label = self._slidelabel
        opts = [(f"{s.display_number}", round(100*float(s.display_number)/(n_last or 1), 2)) for s in self.__iterable]
        self.progress_slider.options = opts  # update options
        
        if old_label in list(zip(*opts))[0]: # Bring back to same slide if possible
            self._slidelabel = old_label
            
        self._update_content(True) # Force Refresh
        
    def set_slide_css(self,props_dict = {}):
        """props_dict is a dict of css properties in format {'selector': {'prop':'value',...},...}
        'selector' for slide itself should be ''.
        """
        self._slides_dict[self._current_slide].set_css(props_dict)
    
    def set_overall_animation(self, main = 'slide_h',frame = 'slide_v'):
        "Set animation for main and frame slides for all slides created after this. For individual slides, use `self.slides[index].set_animation`"
        self._slides_dict[self._current_slide].set_overall_animation(main = main, frame = frame)
    
    # defining magics and context managers
    def __slide(self,line,cell):
        """Capture content of a cell as `slide`.
            ---------------- Cell ----------------
            %%slide 1                             
            #python code here                     
        
        You can use extended markdown to create slides
            ---------------- Cell ----------------
            %%slide 2 -m
            Everything here and below is treated as markdown, not python code.
            (1.5.5+) If Markdown is separated by three underscores (___) on it's own line, multiple frames are created.
            Markdown before the first three underscores is written on all frames. This is equivalent to `@LiveSlides.frames` decorator.
        """
        line = line.strip().split() #VSCode bug to inclue \r in line
        if line and not line[0].isnumeric():
            raise ValueError(f'You should use %%slide integer >= 1 -m(optional), got {line}')
        
        slide_number = int(line[0])
        
        if '-m' in line[1:]:
            _frames = re.split(r'^___$|^___\s+$',cell,flags = re.MULTILINE) # Split on --- or ---\s+
            if len(_frames) == 1:
                with self.slide(slide_number):
                    parse_xmd(cell, display_inline = True, rich_outputs = False)
            else:
                @self.frames(slide_number, *_frames[1:])
                def create_frames(obj):
                    parse_xmd(_frames[0], display_inline = True, rich_outputs = False) # This goes with every frame
                    parse_xmd(obj, display_inline = True, rich_outputs = False)
        else:
            with self.slide(slide_number):
                self.shell.run_cell(cell)
    
    @contextmanager
    def slide(self,slide_number,props_dict = {}):
        """Use this context manager to generate any number of slides from a cell
        CSS properties from `props_dict` are applied to current slide."""
        if not isinstance(slide_number, int):
            raise ValueError(f'slide_number should be int >= 1, got {slide_number}')
        
        assert slide_number >= 0 # slides should be >= 1, zero for title slide
        if self._computed_display:
            yield # To avoid generator yied error
            self._check_computed('add slide')
        
        self._current_slide = f'{slide_number}'
        
        with build_slide(self, self._current_slide, props_dict=props_dict) as cap:
            yield cap # Useful to use later

    
    def __title(self,line,cell):
        "Turns to cell magic `title` to capture title"
        with self.slide(0):
            if '-m' in line:
                parse_xmd(cell, display_inline = True, rich_outputs = False)
            else:
                self.shell.run_cell(cell)
    
    def __xmd(self, line, cell = None):
        """Turns to cell magics `%%xmd` and line magic `%xmd` to display extended markdown. 
        Can use in place of `write` commnad for strings.
        When using `%xmd`, variables should be `{{{{var}}}}` or `\{\{var\}\}`, not `{{var}}` as IPython 
        does some formatting to line in magic. If you just need to format it in string, then `{var}` works as well.
        Inline columns are supported with ||C1||C2|| syntax."""
        if cell is None:
            return parse_xmd(line, display_inline = True, rich_outputs = False)
        else:
            return parse_xmd(cell, display_inline = True, rich_outputs = False)
            
    @contextmanager
    def title(self,props_dict = {}):
        """Use this context manager to write title.
        CSS properties from `props_dict` are applied to current slide."""
        with self.slide(0, props_dict = props_dict) as s:
            yield s # Useful to use later
    
    def frames(self, slide_number, *objs, repeat = False, frame_height = 'auto', props_dict = {}):
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
        CSS properties from `prop_dict` are applied to all slides from *objs."""
        def _frames(func = self.write): # default write if called without function
            self._check_computed('add frames')
            if not isinstance(slide_number,int):
                return print(f'slide_number expects integer, got {slide_number!r}')
            
            assert slide_number >= 1 # Should be >= 1, should not add title slide as frames
            self._current_slide = f'{slide_number}.1' # First frame

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
                with build_slide(self, f'{slide_number}.{i}', props_dict= props_dict):
                    self.write(self.format_css('.SlideArea',height = frame_height))
                    func(obj) # call function with obj
            
        return _frames 

    def __collect_slides(self):
        """Collect cells for an instance of LiveSlides."""
        self._slides_dict['0'].display_number = 0
        slides_iterable = [self._slides_dict['0']]
        
        val_keys = sorted([int(k) if k.isnumeric() else float(k) for k in self._slides_dict.keys()]) 
        str_keys = [str(k) for k in val_keys]
        _max_range = int(val_keys[-1]) + 1 if val_keys else 1
        
        nslide = 0 #start of slides - 1
        for i in range(1, _max_range):
            if i in val_keys:
                nslide = nslide + 1 #should be added before slide
                self._slides_dict[f'{i}'].display_number = nslide
                slides_iterable.append(self._slides_dict[f'{i}']) 
                self._reverse_mapping[str(nslide)] = str(i)
            
            n_ij, nframe = '{}.{}', 1
            while n_ij.format(i,nframe) in str_keys:
                nslide = nslide + 1 if nframe == 1 else nslide
                _in, _out = n_ij.format(i,nframe), n_ij.format(nslide,nframe)
                self._slides_dict[_in].display_number = float(_out)
                slides_iterable.append(self._slides_dict[_in]) 
                self._reverse_mapping[_out] = _in
                nframe = nframe + 1
            
        return tuple(slides_iterable)

# Make available as Singleton LiveSlides
_private_instance = LiveSlides() # Singleton in use namespace
# This is overwritten below to just have a singleton

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
    with ls.capture_std() as std:
        print('something')
        function_that_prints_something()
        display('Something') # Will be displayed here
        ls.write(std.stdout) # Will be written here whatever printed above this line
        
    std.stdout.display() #ls.write(std.stdout)
    ```
    In version 1.5.9+ function `pprint` is avalible in IPython namespace when LiveSlide is initialized. This displays objects in intended from rather than just text.
    > `ls.demo` and `ls.from_markdown` overwrite all previous slides.
    
    Aynthing with class name 'report-only' will not be displayed on slides, but appears in document when `ls.export.report` is called.
    This is useful to fill-in content in document that is not required in slides.
    
    > All arguments are passed to corresponding methods in `ls.settings`, so you can use those methods to change settings as well.
    """
    def __new__(cls,
                center        = True, 
                content_width = '90%', 
                footer_text   = 'IPySlides | <a style="color:blue;" href="https://github.com/massgh/ipyslides">github-link</a>', 
                show_date     = True,
                show_slideno  = True,
                logo_src      = logo_svg, 
                font_scale    = 1, 
                text_font     = 'sans-serif', 
                code_font     = 'var(--jp-code-font-family)', 
                code_style    = 'default', 
                code_lineno   = True
                ):
        "Returns Same instance each time after applying given settings. Encapsulation."
        _private_instance.__doc__ = cls.__doc__ # copy docstring
        _private_instance.settings.set_layout(center = center, content_width = content_width)
        _private_instance.settings.set_footer(text = footer_text, show_date = show_date, show_slideno = show_slideno)
        _private_instance.settings.set_logo(src = logo_src,width = 60)
        _private_instance.settings.set_font_scale(font_scale = font_scale)
        _private_instance.settings.set_font_family(text_font = text_font, code_font = code_font)
        _private_instance.settings.set_code_style(style = code_style, lineno = code_lineno)
        return _private_instance
    
    # No need to define __init__, __new__ is enough to show signature and docs
    
    
