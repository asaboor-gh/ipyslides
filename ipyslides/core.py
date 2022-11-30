
import os, sys, re, textwrap
from contextlib import contextmanager, suppress

from IPython import get_ipython
from IPython.display import display
from IPython.utils.capture import capture_output

import ipywidgets as ipw

from .extended_md import parse_xmd, _special_funcs, extender as _extender
from .source import Source
from .writers import write, iwrite
from .formatter import bokeh2html, plt2html, highlight, _HTML, serializer
from . import utils

_under_slides = {k:getattr(utils,k,None) for k in utils.__all__}

from ._base.base import BaseSlides
from ._base.intro import how_to_slide, logo_svg, key_combs
from ._base.scripts import multi_slides_alert
from ._base.slide import Slide, _build_slide

try:  # Handle python IDLE etc.
    SHELL = get_ipython()
except:
    print("Slides only work in IPython Notebook!")
    sys.exit()
    

class _Citation:
    "Add citation to the slide with a unique key and value. New in 1.7.0"
    def __init__(self, slide, key):
        self._slide = slide
        self._key = key
        self._id = '?'
        self._slide._citations[key] = self # Add to slide's citations
        
    def __repr__(self):
        return f"Citation(key = {self._key!r}, id = {self._id!r}, slide_label = {self._slide.label!r})"
    
    def __format__(self, spec):
        return f'{self.value:{spec}}'
    
    
    def _repr_html_(self):
        "HTML of this citation"
        return self.value
        
    @property
    def value(self):
        _value = self._slide._app._citations_dict.get(self._key, f'Set citation for key {self._key!r} using slides.set_citations or [{self._key}]:&#96;citation text&#96; in markdown.')
        return f'''<span class = "citation" id="{self._key}">
            <a href="#{self._key}-back"> 
                <sup style="color:var(--accent-color);">{self._id}</sup>
            </a>{_value}</span>'''
        
        
class Slides(BaseSlides):
    # This will be overwritten after creating a single object below!
    def __init__(self):
        super().__init__() # start Base class in start
        self.shell = SHELL
        
        for k,v in _under_slides.items(): # Make All methods available in slides
            setattr(self,k,v)
        
        self.backtick = '&#96;'
        self.extender   = _extender
        self.plt2html   = plt2html
        self.bokeh2html = bokeh2html
        self.highlight  = highlight
        self.source = Source # Code source
        self.write  = write # Write IPython objects in slides
        self.iwrite = iwrite # Write Widgets/IPython in slides
        self.parse_xmd = parse_xmd # Parse extended markdown
        self.serializer = serializer # Serialize IPython objects to HTML
        
        with suppress(Exception): # Avoid error when using setuptools to install
            self.widgets._notebook_dir = self.shell.starting_dir # This is must after shell is defined
            self.shell.register_magic_function(self.__slide, magic_kind='cell',magic_name='slide')
            self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name='title')
            self.shell.register_magic_function(self.__xmd, magic_kind='line_cell',magic_name='xmd')
            self.shell.user_ns['__Slides_Instance__'] = self
            self.user_ns = self.shell.user_ns #important for set_dir
            
        # Override print function to display in order in slides
        if self.shell.__class__.__name__ in ('ZMQInteractiveShell','Shell'): # Shell for Colab
            import builtins
            self.builtin_print = builtins.print # Save original print function otherwise it will throw a recursion error
            def print(*args, **kwargs):
                """Prints object(s) inline with others in corrct order. args and kwargs are passed to builtin `print`.
                If `file` argument is not `sys.stdout`, then print is passed to given file."""

                if 'file' in kwargs and kwargs['file'] != sys.stdout: # User should be able to redirect print to file
                    return self.builtin_print(*args, **kwargs)

                with capture_output() as captured:
                    self.builtin_print(*args, **kwargs)

                return self.raw(captured.stdout,className = 'CustomPrint').display() # Display at the end
                # CustomPrint is used to avoid the print to be displayed when `with suppress_stdout` is used.
            
            builtins.print = print
        
        self._citation_mode = 'global' # One of 'global', 'inline', 'footnote'
            
        self._slides_dict = {} # Initialize slide dictionary, updated by user or by _on_load_and_refresh.
        self._reverse_mapping = {'0':'0'} # display number -> input number of slide
        self._citations_dict = {} # Initialize citations dictionary, updated by user or by set_citations.
        self._iterable = [] #self._collect_slides() # Collect internally
        self._nslides =  0 # Real number of slides
        self._max_index = 0 # Maximum index including frames
        self._running_slide = None # For Notes, citations etc in markdown, controlled in Slide class
        
        self.progress_slider = self.widgets.sliders.progress
        self.progress_slider.label = '0' # Set inital value, otherwise it does not capture screenshot if title only
        self.progress_slider.observe(self._update_content,names=['index'])
        
        # All Box of Slides
        self._box =  self.widgets.mainbox
        self._on_load_and_refresh() # Load and browser refresh handling
        self._display_box_ = ipw.VBox() # Initialize display box
    
    @property
    def xmd_syntax(self):
        "Special syntax for markdown."
        return _HTML(self.parse_xmd(textwrap.dedent('''
        ## Extended Markdown
        Extended syntax for markdown is constructed to support almost full presentation from Markdown.
        
        **Following syntax works only under currently buidling `slide` or `frame`:**
        
        - alert`notes&#96;This is slide notes&#96;`  to add notes to current slide
        - alert`cite&#96;key&#96;` to add citation to current slide
        - alert`[key]:&#96;citation content&#96;` to add citation value, use these at start, so can be access in alert`cite&#96;key&#96;`
        - alert`citations&#96;citations title&#96;`  to add citations at end if `citation_mode = 'global'`.
        - alert`include&#96;markdown_file.md&#96;` to include a file in markdown format. Useful to have citations in a separate file. (2.0.6+)
        - alert`section&#96;section text&#96;` to add a section that will appear in the table of contents. (2.1.7+).
        - alert`toc&#96;Table of content header text&#96;` to add a table of contents. Run at last again to collect all. (2.1.7+).
        - Triple dashes `---` is used to split markdown text in slides inside `from_markdown(start, file_or_str)` function.
        - Double dashes `--` is used to split markdown text in frames. (1.8.9+)
        
        **Other syntax can be used everywhere like under `%%slides int -m`, in `write/iwrite/format_html/parse_xmd/from_markdown` functions:**\n
        - Variables can be replaced with their HTML value (if possible) using \{\{variable\}\} syntax.
        - Two side by side columns can be added inline using alert`|&#124; Column A |&#124; Column B |&#124;` sytnax.
        - Block multicolumns are made using follwong syntax, column separtor is tiple plus `+++`: 
        ```markdown     
         ```multicol widthA widthB
         Column A
         +++
         Column B
         ```
        ```
        
        - Python code blocks can be exectude by syntax 
        ```markdown
         ```python run source {.CSS_className}
         my_var = 'Hello'
         ```
        ```
        and source then can be emded with \{\{source\}\} syntax and also \{\{my_var\}\} will show 'Hello'.
        
        - A whole block of markdown can be CSS-classed using syntax
        ```markdown
         class`Block-yellow`
         ### This is Header 3
         <hr/>
         Some **bold text**
         ^^^
        ```
        gives
        class`Block-yellow`
        ### This is Header 3
        <hr/>
        Some **bold text**
        ^^^
        OR 
        ```markdown
        ::: Block-yellow
            ### This is Header 3
            <hr/>
            Some **bold text**
        ```
        gives same thing as above. 
        ::: Note 
            You can also look at [customblocks](https://github.com/vokimon/markdown-customblocks) 
            extension to make nested blocks with classes. It is added as dependency and can be used to build nested html blocks.
            
        ::: Block-red 
            - You can use `Slides.extender` to extend additional syntax using Markdown extensions such as 
                [markdown extensions](https://python-markdown.github.io/extensions/) and 
                [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/)
            - You can serialize custom python objects to HTML using `Slides.serializer` function. Having a 
                `__format__` method in your class enables to use \{\{object\}\} syntax and `_repr_html_` method enables it to use inside `write` function.
        
        - Other options include:
        
        color[blue]`color[blue]&#96;text&#96;`, color[yellow_skyblue]`color[yellow_skyblue]&#96;text&#96;`, ''') + '\n' + ', '.join(f'alert`{k}&#96;{v}&#96;`' for k,v in _special_funcs.items()),
        display_inline = False
        ))
        
    def _on_load_and_refresh(self):
        self.widgets._exec_js(multi_slides_alert)
        if self._max_index == 0: # prevent overwrite
            with suppress(BaseException):
                with _build_slide(self, '0') as s:
                    self.parse_xmd('\n'.join(how_to_slide), display_inline=True)
                with _build_slide(self, '1') as s:
                    self.parse_xmd('# Keys Combinations' + key_combs, display_inline=True)
                with _build_slide(self, '2') as s:
                    self.xmd_syntax.display()
            
            self._slideindex = 0 # Go to title slide
        
        with suppress(BaseException): # Does not work everywhere.
            self.widgets.inputs.bbox.value = ', '.join(str(a) for a in self.screenshot.screen_bbox) # Useful for knowing scren size

    
    def __repr__(self):
        repr_all = ',\n    '.join(repr(s) for s in self._iterable)
        return f'Slides(\n    {repr_all}\n)'
    
    def __iter__(self): # This is must have for exporting
        return iter(self._iterable)
    
    def __len__(self):
        return len(self._iterable)
    
    def __getitem__(self, key):
        "Get slide by index or key(written on slide's bottom)."
        if isinstance(key, int):
            return self._iterable[key]
        elif isinstance(key, str):
            frame = None
            if '.' in key:
                key, frame = key.split('.')
            
            if key in self._reverse_mapping:
                _slide = self._slides_dict[self._reverse_mapping[key]]
                if frame:
                    _slide = _slide.frames[int(frame) - 1]
                return _slide
            else:
                raise KeyError(f'Key {key} not found.')
        elif isinstance(key, slice):
            return self._iterable[key.start:key.stop:key.step]
        
        raise KeyError("Slide could be accessed by index, slice or key, got {}".format(key))
    
    @property
    def notebook_dir(self):
        "Get notebook directory."
        return self.shell.starting_dir
    
    @property
    def assets_dir(self):
        "Get assets directory."
        return self.widgets.assets_dir # Creates automatically
    
    @property
    def current(self):
        "Access current visible slide and use operations like insert, set_css etc."
        return self._iterable[self._slideindex]
    
    @property
    def running(self):
        "Access slide currently being built. Useful inside frames decorator."
        return self._running_slide
    
    @property
    def citations(self):
        "Get All citations as a tuple that can be passed to `write` function."
        # Need to filter unique keys across all slides
        if self._citation_mode == 'global':
            _all_citations = {}
            for slide in self[:]:
                _all_citations.update(slide._citations)
            
            return tuple(sorted(_all_citations.values(), key=lambda x: x._id))
        
        return ("No citations in 'inline' or 'footnote' mode",)
    
    def clear(self):
        "Clear all slides."
        self._slides_dict = {} # Clear slides
        self._citations_dict = {} # Clear citations as well
        with _build_slide(self, '0'):
            with suppress(BaseException): # Create a clean title page with no previous toasts/css/animations etc.
                self.parse_xmd('# Title Page', display_inline=True)
        
        self.refresh() # Clear interface again may be not needed, but it is not that costly.
        
    
    def cite(self, key):
        """Add citation in presentation, key should be a unique string and citation is text/markdown/HTML.
        Citations corresponding to keys used can be created by `.set_citations ` method.
        Citation can be accessed by alert`Slides.citations` property and can be passed to `write` function.
        
        **New in 1.7.2**      
        In Markdown (under `%%slide int -m` or in `from_markdown`), citations can be created by using alert`cite&#96;key&#96;` syntax and 
        can be set using alert`[key]:&#96;citationtext&#96;` syntax. If citation_mode is global, they can be shown using alert`citations&#96;citation title&#96;` syntax.
        
        """
        if not self._running_slide:
            raise RuntimeError('Citations can be added only inside a slide constructor!')
        
        if self._citation_mode == 'inline':
            return utils.textbox(self._citations_dict.get(key,f'Set citation for key {key!r} using `.set_citations`'),left='initial',top='initial').value # Just write here
        
        this_slide = self._running_slide
        _cited = _Citation(slide = this_slide, key = key)
        self._citations_dict[key] = self._citations_dict.get(key, f'Set citation for key {key!r}.') # This to ensure single run shows citation
        
        # Set _id for citation
        if self._citation_mode == 'footnote':
            _cited._id = str(list(this_slide._citations.keys()).index(key) + 1) # Get index of key
        else:
            prev_keys = list(self._citations_dict.keys())
                    
            if key in prev_keys:
                _cited._id = str(prev_keys.index(key) + 1)
            else:
                _cited._id = str(len(prev_keys)) 
             
        # Return string otherwise will be on different place
        return f'''<a href="#{key}" class="HiddenCitation">
                <sup id ="{key}-back" style="color:var(--accent-color);">{_cited._id}</sup>
                <span>{self._citations_dict[key]}</span></a>'''
    
    def set_citations(self, citations_dict):
        "Set citations in presentation. citations_dict should be a dict of {key:value,...}"
        self._citations_dict.update({key:self.parse_xmd(value, display_inline=False, rich_outputs = False
                        ).replace('<p>','',1)[::-1].replace('>p/<','',1)[::-1] # Only replace first <p>
                for key, value in citations_dict.items()})
        
        if self._citation_mode == 'footnote':
            for slide in self[:]:
                if slide.citations:
                    slide.update_display()
        else:
            self.notify('Citations updated, please rerun the slides with references to see effect.')
        
    def section(self,text):
        """Add section to presentation that will appear in table of contents. 
        In markdown, section can be created by using alert`%%section&#96;section text&#96;` syntax.
        Sections can be collected using &#96;Slides.toc&#96; property or can be written in markdown using alert`toc&#96;title&#96;` syntax."""
        self.running._section = text
    
    @property 
    def toc(self):
        """Returns dictionary of table of contents in form {'slide_label':'section_text',...} 
        whose keys/values can be passed to write command with desired format. 
        Run the slide containing alert`Slides.toc` at end as well to see all contents."""
        return {it._label:it._section for it in self._iterable if it._section if it._section}
    
    def goto_button(self, slide, text,**kwargs):
        """"
        TODO: Add docstring
        TODO: Add slide number instead of slide object.
        Think to return or display, left, right text etc.
        """
        button = ipw.Button(description=text,**kwargs)
        def on_click(btn):
            slide._app.progress_slider.index = slide.index

        button.on_click(on_click)
        return display(button)
    
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
    def _slideindex(self):
        "Get current slide index"
        return self.progress_slider.index
    
    @_slideindex.setter
    def _slideindex(self,value):
        "Set current slide index"
        with suppress(BaseException): # May not be ready yet
            self.progress_slider.index = value
        
    @property
    def _slidelabel(self):
        "Get current slide label"
        return self.progress_slider.label
    
    @_slidelabel.setter
    def _slidelabel(self,value):
        "Set current slide label"
        with suppress(BaseException): # May not be ready yet
            self.progress_slider.label = value
            
    def _switch_slide(self,old_index, new_index): # this change is provide from _update_content
        self.widgets.outputs.slide.clear_output(wait=False) # Clear last slide CSS
        with self.widgets.outputs.slide:
            if self.screenshot.capturing == False:
                self._iterable[new_index].animation.display()
            self._iterable[new_index].css.display()
        
        if (old_index + 1) > len(self.widgets.slidebox.children):
            old_index = new_index # Just safe
            
        self.widgets.slidebox.children[old_index].layout = ipw.Layout(width = '0',margin='0',opacity='0') # Hide old slide
        self.widgets.slidebox.children[old_index].remove_class('SlideArea')
        self.widgets.slidebox.children[new_index].add_class('SlideArea') # First show then set layout
        self.widgets.slidebox.children[new_index].layout = self.settings._slide_layout 
        
    def _update_content(self,change):
        if self._iterable and change:
            self.widgets.htmls.toast.value = '' # clear previous content of notification 
            self._display_toast() # or self.toasts._display_toast . Display in start is fine
            self.notes._display(self.current.notes) # Display notes first
        
            _number = f'{self.current.label} / {self._nslides}' if self.current.label != '0' else ''
            self.settings.set_footer(_number_str = _number)
            
            self._switch_slide(old_index= change['old'], new_index= change['new']) 
    
            
    def refresh(self): 
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self._iterable = self._collect_slides() # would be at least one title slide
        if not self._iterable:
            self.progress_slider.options = [('0',0)] # Clear options
            self.widgets.slidebox.children = [] # Clear older slides
            return None
        
        n_last = float(self._iterable[-1].label)
        self._nslides = int(n_last) # Avoid frames number
        self._max_index = len(self._iterable) - 1 # This includes all frames
        self.notify('Refreshing display of slides...')
        # Now update progress bar
        opts = [(s.label, round(100*float(s.label)/(n_last or 1), 2)) for s in self._iterable]
        self.progress_slider.options = opts  # update options
        # Update Slides
        #slides = [ipw.Output(layout=ipw.Layout(width = '0',margin='0')) for s in self._iterable]
        self.widgets.slidebox.children = [it._widget for it in self._iterable]
        for i, s in enumerate(self._iterable):
            s.update_display() 
            s._index = i # Update index
            self._slideindex = i # goto there to update display
        
        self._slideindex = 0 # goto first slide after refresh
    
    def delete(self, slide_number):
        "Delete slide or all frames by `slide_number` with which it was created. It reappear if its source code is run again."
        if not isinstance(slide_number, int):
            raise TypeError('slide_number must be an integer, even for frames.')
        number = str(slide_number)
        self._slides_dict = {k:v for k,v in self._slides_dict.items() if not k.startswith(number)} # Delete all frames too
        self.refresh()
        
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
            **New in 1.7.2**    
            Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        
        (1.8.9+) If Markdown is separated by two dashes (--) on it's own line, multiple frames are created.
        Markdown before the first three underscores is written on all frames. This is equivalent to `@Slides.frames` decorator.
        """
        line = line.strip().split() #VSCode bug to inclue \r in line
        if line and not line[0].isnumeric():
            raise ValueError(f'You should use %%slide integer >= 1 -m(optional), got {line}')
        
        # NOTE: DO NOT bypass creating new slides with same old markdown, some varibale
        #      may be changed in any of the cells.
        
        slide_number_str = line[0] # First argument is slide number
        
        if '-m' in line[1:]:
            _frames = re.split(r'^--$|^--\s+$',cell, flags= re.DOTALL | re.MULTILINE) # Split on --- or ---\s+
            if len(_frames) > 1:
                _frames = [_frames[0] + '\n' + obj for obj in _frames[1:]]
                
            @self.frames(int(slide_number_str), *_frames)
            def make_slide(_frame):
                #s.clear_display(wait = True) # It piles up otherwise due to replacements
                parse_xmd(_frame, display_inline = True, rich_outputs = False)
                self._running_slide._markdown = _frame # Update markdown, # cell_code will be automatuically cleared in `self.frames`
            
        else: # Run even if already exists as it is user choice in Notebook, unlike markdown which loads from file
            with _build_slide(self, slide_number_str, from_cell = True) as s:
                self.shell.run_cell(cell) #  Enables citations etc.
            
            s._cell_code = cell # Update cell code
            s._markdown = '' # Reset markdown
                   
    
    @contextmanager
    def slide(self,slide_number,props_dict = {}):
        """Use this context manager to generate any number of slides from a cell
        CSS properties from `props_dict` are applied to current slide."""
        if not isinstance(slide_number, int):
            raise ValueError(f'slide_number should be int >= 1, got {slide_number}')
        
        assert slide_number >= 0 # slides should be >= 1, zero for title slide
        
        with _build_slide(self, f'{slide_number}', props_dict=props_dict, from_cell = False) as s:
            yield s # Useful to use later
        
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
            if not isinstance(slide_number,int):
                return print(f'slide_number expects integer, got {slide_number!r}')
            
            assert slide_number >= 0 # Should be >= 0

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
                
            if len(_new_objs) > 100: # 99 frames + 1 main slide
                raise ValueError(f'Maximum 99 frames are supported, found {len(_new_objs)} frames!')
           
            # build_slide returns old slide with updated display if exists.
            with _build_slide(self, f'{slide_number}', props_dict= props_dict, from_cell = False, is_frameless = False) as this_slide:
                self.write(self.format_css('.SlideArea',height = frame_height))
                func(_new_objs[0]) # Main slide content
            
            _new_objs = _new_objs[1:] # Fisrt one is already written
            
            NFRAMES_OLD = len(this_slide._frames) # old frames
            
            new_frames = []
            for i, obj in enumerate(_new_objs): # New frames
                if i >= NFRAMES_OLD: # Add new frames
                    new_slide = Slide(self, slide_number, props_dict= props_dict)
                else: # Update old frames
                    new_slide = this_slide._frames[i] # Take same frame back
                
                new_frames.append(new_slide)
                
                with new_slide._capture(assign = True) as captured:
                    self.write(self.format_css('.SlideArea',height = frame_height))
                    func(obj)
                
                new_slide._from_cell = False
                new_slide._cell_code = ''    
                
                
            this_slide._frames = new_frames
            
            if len(this_slide._frames) != NFRAMES_OLD:
                this_slide._rebuild_all() # Rebuild all slides as frames changed
            
            # Update All displays
            for s in this_slide._frames:
                s.update_display()
            
        return _frames 

    def _collect_slides(self):
        """Collect cells for an instance of Slides."""
        slides_iterable = []
        if '0' in self._slides_dict:
            self._slides_dict['0']._label = '0'
            slides_iterable = [self._slides_dict['0']]
        
        val_keys = sorted([int(k) if k.isnumeric() else float(k) for k in self._slides_dict.keys()]) 
        _max_range = int(val_keys[-1]) + 1 if val_keys else 1
        
        nslide = 0 #start of slides - 1
        for i in range(1, _max_range):
            if i in val_keys:
                nslide = nslide + 1 #should be added before slide
                self._slides_dict[f'{i}']._label = f'{nslide}'
                slides_iterable.append(self._slides_dict[f'{i}']) 
                self._reverse_mapping[str(nslide)] = str(i)
                
                # Read Frames
                frames = self._slides_dict[f'{i}'].frames
                for j, frame in enumerate(frames, start=1):
                    jj = f'{j}' if len(frames) < 10 else f'{j:02}' # 99 frames max
                    frame._label = f'{nslide}.{jj}' # Label for frames
                    slides_iterable.append(frame)
            
        return tuple(slides_iterable)
    
    def create(self, *slide_numbers, props_dict ={}):
        "Create empty slides with given slide numbers. If a slide already exists, it remains same. This is faster than creating one slide each time."
        new_slides = False
        for slide_number in slide_numbers:
            if f'{slide_number}' not in self._slides_dict:
                with capture_output() as captured:
                    self.write(f'### Slide-{slide_number}')
                
                self._slides_dict[f'{slide_number}'] = Slide(self, slide_number, captured_output=captured, props_dict= props_dict)
                new_slides = True
        
        if new_slides:
            self.refresh() # Refresh all slides
        
        return tuple([self._slides_dict[f'{slide_number}'] for slide_number in slide_numbers])
    
    def glassmorphic(self, image_src, opacity=0.75, blur_radius=50):
        "Adds glassmorphic effect to the background. `image_src` can be a url or a local image path. `opacity` and `blur_radius` are optional. (2.0.1+)"
        return self.settings.set_glassmorphic(image_src, opacity = opacity, blur_radius = blur_radius)

# Make available as Singleton Slides
_private_instance = Slides() # Singleton in use namespace
# This is overwritten below to just have a singleton

class Slides:
    __doc__ = textwrap.dedent("""
    Interactive Slides in IPython Notebook. Only one instance can exist. 
    
    All arguments are passed to corresponding methods in `slides.settings`, so you can use those methods to change settings as well.
    
    To suppress unwanted print from other libraries/functions (2.1.0+), use:
    ```python
    with slides.suppress_stdout():
        some_function_that_prints() # This will not be printed
        print('This will not be printed either')
        display('Something') # This will be printed
    ```
    
    > `slides.demo` and `slides.docs` overwrite all previous slides.
    
    Aynthing with class name 'report-only' will not be displayed on slides, but appears in document when `slides.export.report` is called.
    This is useful to fill-in content in document that is not required in slides.
    
    Starting with 1.8, you can provide extensions at initialization time as a list to arguments `extensions`. See [PyMdownx](https://facelessuser.github.io/pymdown-extensions/extensions/arithmatex/) for useful extensions. `'pymdownx.arithmatex'` is a recommended extension to load Maths faster.
    
    """) + how_to_slide[0]
    def __new__(cls,
                citation_mode = 'global',
                center        = True, 
                content_width = '90%', 
                footer_text   = 'IPySlides | <a style="color:blue;" href="https://github.com/massgh/ipyslides">github-link</a>', 
                show_date     = True,
                show_slideno  = True,
                logo_src      = logo_svg, 
                font_scale    = 1, 
                text_font     = 'STIX Two Text', 
                code_font     = 'var(--jp-code-font-family)', 
                code_style    = 'default', 
                code_lineno   = True,
                extensions    = []
                ):
        "Returns Same instance each time after applying given settings. Encapsulation."
        _private_instance.__doc__ = cls.__doc__ # copy docstring
        
        if citation_mode not in ['global', 'inline', 'footnote']:
            raise ValueError(f'citation_mode must be one of "global", "inline", "footnote" but got {citation_mode}')
        
        _private_instance.extender.extend(extensions)
        _private_instance._citation_mode = citation_mode
        _private_instance.settings.set_layout(center = center, content_width = content_width)
        _private_instance.settings.set_footer(text = footer_text, show_date = show_date, show_slideno = show_slideno)
        _private_instance.settings.set_logo(src = logo_src,width = 60)
        _private_instance.settings.set_font_scale(font_scale = font_scale)
        _private_instance.settings.set_font_family(text_font = text_font, code_font = code_font)
        _private_instance.settings.set_code_style(style = code_style, lineno = code_lineno)
        return _private_instance
    
    # No need to define __init__, __new__ is enough to show signature and docs
    