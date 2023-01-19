
import sys, os, json, re, textwrap
from contextlib import contextmanager, suppress
from collections import namedtuple

from IPython import get_ipython
from IPython.display import display
from IPython.utils.capture import capture_output

import ipywidgets as ipw

from .xmd import parse, extender as _extender
from .source import Source
from .writers import write, iwrite
from .formatters import bokeh2html, plt2html, highlight, _HTML, serializer, _fix_repr
from . import utils

_under_slides = {k:getattr(utils,k,None) for k in utils.__all__}

from ._base.base import BaseSlides
from ._base.intro import logo_svg, key_combs
from ._base.scripts import multi_slides_alert
from ._base.slide import Slide, _build_slide
from ._base.icons import Icon as _Icon, loading_svg
from .__version__ import __version__

try:  # Handle python IDLE etc.
    SHELL = get_ipython()
except:
    print("Slides only work in IPython Notebook!")
    sys.exit()
    

class _Citation:
    "Add citation to the slide with a unique key and value."
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
        if (_value := self._slide._app._citations.get(self._key, None)):
            return f'''<div class = "citation" id="{self._key}">
                <a href="#{self._key}-back"> 
                    <span style="color:var(--accent-color);">{self._id}. </span>
                </a>{_value}</div>'''
        else:
            return f'<div class = "warning">Set value for cited key {self._key!r} and run again to clear warning!</div>'
    
    @property
    def inline_value(self):
        if (_value := self._slide._app._citations.get(self._key, None)):
            return utils.textbox(_value.replace('<p>','',1)[::-1].replace('>p/<','',1)[::-1] , left='initial',top='initial').value
        else:
            return self.value
        
class Slides(BaseSlides):
    # This will be overwritten after creating a single object below!
    def __init__(self):
        super().__init__() # start Base class in start
        self.shell = SHELL
        
        for k,v in _under_slides.items(): # Make All methods available in slides
            setattr(self,k,v)
        
        if not os.path.isdir(self.assets_dir):
            os.makedirs(self.assets_dir) # It should be present to load resources
        
        self.extender   = _extender
        self.plt2html   = plt2html
        self.bokeh2html = bokeh2html
        self.highlight  = highlight
        self.source = Source # Code source
        self.icon = _Icon # Icon is useful to add many places
        self.write  = write 
        self.iwrite = iwrite # will be discarded at some point
        self.parse = parse # Parse extended markdown
        self.serializer = serializer # Serialize IPython objects to HTML
        
        self._remove_post_run_callback() # Remove post_run_cell callback before this and at end
        self._post_run_enabled = True # Enable post_run_cell event than can be hold by skip_post_run_cell context manager
        with suppress(Exception): # Avoid error when using setuptools to install
            self.widgets._notebook_dir = self.shell.starting_dir # This is must after shell is defined
            self.shell.register_magic_function(self._slide, magic_kind='cell',magic_name='slide')
            self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name='title')
            self.shell.register_magic_function(self.__xmd, magic_kind='line_cell',magic_name='xmd')
            self.shell.user_ns['get_slides_instance'] = lambda: self
            
        # Override print function to display in order in slides
        if self.shell.__class__.__name__ in ('ZMQInteractiveShell','Shell'): # Shell for Colab
            import builtins
            self.builtin_print = builtins.print # Save original print function otherwise it will throw a recursion error
            def print(*args, **kwargs):
                """Prints object(s) inline with others in corrct order. args and kwargs are passed to builtin `print`.
                ::: note
                    - If `file` argument is not `sys.stdout`, then print is passed to given file.
                    - If oustide slides, then print is same as builtin `print`."""

                if 'file' in kwargs and kwargs['file'] != sys.stdout: # User should be able to redirect print to file
                    return self.builtin_print(*args, **kwargs)
                elif self.running or getattr(self,'_in_proxy', False):
                    with capture_output() as captured:
                        self.builtin_print(*args, **kwargs)

                    # custom-print is used to avoid the print to be displayed when `with suppress_stdout` is used.
                    return self.raw(captured.stdout,className = 'custom-print').display() # Display at the end
                else:
                    self.builtin_print(*args, **kwargs) # outside slides should behave same as before
            
            builtins.print = print
        
        self._citation_mode = 'global' # One of 'global', 'inline', 'footnote'
            
        self._slides_dict = {} # Initialize slide dictionary, updated by user or by _on_load_and_refresh.
        self._reverse_mapping = {'0':'0'} # display number -> input number of slide
        self._iterable = [] #self._collect_slides() # Collect internally
        self._nslides =  0 # Real number of slides
        self._max_index = 0 # Maximum index including frames
        self._running_slide = None # For Notes, citations etc in markdown, controlled in Slide class
        self._next_number = 0 # Auto numbering of slides should be only in python scripts
        
        self._citations = {} # Initialize citations dictionary
        with self.set_dir(self.assets_dir): # Set assets directory
            self._set_citations_from_file('citations.json') # Load citations from file if exists
        
        self.progress_slider = self.widgets.sliders.progress
        self.progress_slider.label = '0' # Set inital value, otherwise it does not capture screenshot if title only
        self.progress_slider.observe(self._update_content,names=['index'])
        self.widgets.buttons.refresh.on_click(self._update_dynamic_content)
        
        # All Box of Slides
        self._box =  self.widgets.mainbox 
        self._on_load_and_refresh() # Load and browser refresh handling
        self._display_box = None # Initialize
        self.set_overlay_url(url = None) # Set overlay url for initial information
        self._remove_post_run_callback() # Remove post_run_cell callback at end of init, otherwise it appears during import
    
    @contextmanager
    def skip_post_run_cell(self):
        """Context manager to skip post_run_cell event.""" 
        self._remove_post_run_callback()
        old = self._post_run_enabled
        self._post_run_enabled = False
        try:
            yield
        finally:
            self._post_run_enabled = old # Restore user prefrence
            if self._post_run_enabled: # If user wants to enable post_run_cell event
                self.shell.events.register('post_run_cell', self._post_run_cell)
        
    def _remove_post_run_callback(self):
        with suppress(Exception):
            self.shell.events.unregister('post_run_cell', self._post_run_cell)
    
    def run_cell(self, cell, **kwargs):
        """Run cell and return result. This is used to run cell without post_run_cell event."""
        with self.skip_post_run_cell():
            return self.shell.run_cell(cell, **kwargs)
                
    def _post_run_cell(self, result):
        if result.error_before_exec or result.error_in_exec:
            return # Do not display if there is an error
        if self._post_run_enabled:
            return self.show() # Display after cell is executed only when enabled
                     
    
    def _on_load_and_refresh(self):
        self.widgets._exec_js(multi_slides_alert)
        if self._max_index == 0: # prevent overwrite
            self._add_clean_title()
            
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
    
    def __del__(self):
        for k,v in globals():
            if isinstance(v,Slides):
                del globals()[k]
        
        for k,v in locals():
            if isinstance(v,Slides):
                del locals()[k]
    
    def navigate_to(self,index):
        "Programatically Navigate to slide by index."
        self._slideindex = index
        
    @property
    def version(self):
        "Get Slides version."
        return __version__

    @version.setter
    def version(self, value):
        raise AttributeError('Cannot set version.')
        
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
        "Access current visible slide and use operations like set_css etc."
        return self._iterable[self._slideindex]
    
    @property
    def running(self):
        "Access slide currently being built. Useful inside frames decorator."
        return self._running_slide
    
    def verify_running(self, error_msg = ''):
        "Verify if slide is being built, otherwise raise error."
        if self.running is None:
            raise RuntimeError(error_msg or 'This operation is only allowed under slide constructor.')
    
    def citations(self, func):
        """Decorator to get all citations as a tuple that can be passed to given `func` function. and update dynamically.
        `func` must accept a single argument which will be tuple of citations.
        """
        def _citations_handler():
            if self._citation_mode == 'global':  
                _all_citations = {}
                for slide in self[:]:
                    _all_citations.update(slide._citations)
                    
                return func(tuple(sorted(_all_citations.values(), key=lambda x: int(x._id))))

            raise RuntimeError("Citations are not writable in 'inline' or 'footnote' mode. They appear on slide automatically.")
        
        return self._dynamic_private(_citations_handler, tag = '_cited', hide_refresher = True)
    
    def _add_clean_title(self):
        with suppress(BaseException), self.skip_post_run_cell(): # Otherwise it will trigger cell events during __init__
            with _build_slide(self, '0') as s:
                self.parse(f'''
                    # Title Page 
                    ::: align-center
                        color[teal]`Author: Abdul Saboor`
                        
                        👈🏻 **Read more instructions in left panel**''',
                display_inline = True)  
                self.details(self.parse(key_combs, display_inline = False), 'Keyboard Shortcuts').display()
                
        self.refresh() # cleans up initialization setup       
    
    def clear(self):
        "Clear all slides. This will also clear resources including citations, sections."
        self._slides_dict = {} # Clear slides
        _ = [self.__dict__.pop(s, None) for s in getattr(self, '_links_dict', {})] # clear slides attributes
        self.set_citations({}) # Clears citations from disk too
        self._next_number = 0 # Reset slide number to 0, because user will overwrite title page.
        self._add_clean_title() # Add clean title page without messing with resources.
        
        
    def cite(self, key):
        """Add citation in presentation, key should be a unique string.
        Citations corresponding to keys used can be created by ` Slides.set_citations ` method.
        Citation can be written by alert`Slides.citations` decorator.
        
        ::: note
            You should set resources in start if using python script or voila, otherwise they will not be updated.
        """
        self.verify_running('Citations can be added only inside a slide constructor!')
        _cited = _Citation(slide = self.running, key = key)
        
        if self._citation_mode == 'inline':
            return _cited.inline_value # Just write here
        
        # Set _id for citation
        if self._citation_mode == 'footnote':
            _cited._id = str(list(self.running._citations.keys()).index(key) + 1) # Get index of key from unsorted ones
        else:
            prev_keys = list(self._citations.keys())
                    
            if key in prev_keys:
                _cited._id = str(prev_keys.index(key) + 1)
            else:
                _cited._id = str(len(prev_keys))
        
        if self._citation_mode == 'global':
            for s in self[:]:
                if getattr(s, '_cited', False) and s != self.running: # self will be updated at end
                    s.update_display(go_there = False)
                    
        # Return string otherwise will be on different place
        return f'''<a href="#{key}" class="citelink">
        <sup id ="{key}-back" style="color:var(--accent-color);">{_cited._id}</sup>
        </a>''' + (_cited.value.replace('citation', 'citation hidden',1) if self._citation_mode == 'global' else '') # will be hidden by default
    
    def set_citations(self, citations = None, file = None):
        """Set citations from dictionary or file. 
        `file` should be a JSON file with citations keys and values.
        
        ::: note
            - You should set citations in start if using python script or voila, otherwise they may not be updated.   
            - Citations are replaced with new ones.
        """
        if citations is not None:
            if isinstance(citations, dict):
                self._citations = {
                    key: self.parse(value, display_inline=False, rich_outputs = False) for key, value in citations.items()
                }
                
                if self._citation_mode == 'footnote':
                    for slide in self[:]:
                        if slide.citations:
                            slide.update_display()
            else:
                raise TypeError(f'citations should be a dict, got {type(citations)}')
        
        
        if file is not None:
            if citations is not None:
                raise RuntimeError('Cannot set citations from file and dictionary at the same time!')
            
            if isinstance(file, str):
                self._set_citations_from_file(file)
            
        # Here write resources to file in assets
        with self.set_dir(self.assets_dir):
            with open('citations.json', 'w') as f:
                json.dump(self._citations, f, indent=4)
                
        # Update citations in all slides
        for slide in self[:]:
            if getattr(slide, '_cited', False):
                slide.update_display()        
                
    def _set_citations_from_file(self, filename):
        "Load resources from file if present."
        if os.path.isfile(filename):
            with open(filename,'r') as f:
                self._citations = json.load(f) # set, not update, avoid cluttering
                
    def section(self,text):
        """Add section key to presentation that will appear in table of contents. 
        Sections can be written as table of contents by alert` Slides.toc ` decorator.
        """
        self.verify_running('Sections can be added only inside a slide constructor!')
        
        self.running._section = text # assign before updating toc
        
        for s in self[:]:
            if getattr(s, '_toced', False) and s != self.running: # self will be built of course at end
                s.update_display(go_there = False)
    
    def toc(self, func):
        """Decorator to add dynamic table of contents to slides which get updated on each new section and refresh/update_display.
        `func` should take one argument which is the tuple of sections."""
        def _toc_handler():
            sections = []
            this_index = self[:].index(self.running) if self.running in self[:] else self.running.number # Monkey patching index, would work on next run
            for slide in self[:this_index]:
                if slide._section:
                    sections.append(self.html('div', slide._section, style='',className='toc-item prev'))

            if self.running._section:
                sections.append(self.html('div', self.running._section, style='',className='toc-item this'))
                
            elif sections:
                sections[-1] = _HTML(sections[-1].value.replace('toc-item prev','toc-item this'))

            for slide in self[this_index+1:]:
                if slide._section:
                    sections.append(self.html('div', slide._section, style='',className='toc-item next'))
            
            return func(tuple(sections))
           
        return self._dynamic_private(_toc_handler, tag = '_toced', hide_refresher = True)
        
    
    def _goto_button(self, slide_number, text,text_before = '', extra_func=None, **kwargs):
        "See docs of `goto_button`. This is internal function to return button box. extra_func is a function to be called on click after going to slide."
        if not isinstance(slide_number, (int,float,str)): # keep string for internal use only
            raise TypeError('Slide number should be an integer or float for accessing frames!')
        
        button = ipw.Button(description=text,**kwargs).add_class('goto-button')
        def on_click(btn):
            try:
                ss = str(slide_number)
                if '.' in ss:
                    s,f = ss.split('.')
                    slide = self._slides_dict[s].frames[int(f)-1]
                else:
                    slide = self._slides_dict[ss]
                
                self.progress_slider.index = slide.index # let it throw error if slide does not exist
                if callable(extra_func): # Call extra function if given after chnaging slides, no need for user
                    extra_func()
                    
            except:
                self.notify(f'Failed to jump to slide {slide_number!r}, it may not exist yet!')

        button.on_click(on_click)
        
        html_before = ipw.HTML(_fix_repr(text_before)).add_class('goto-html')
        return ipw.HBox([html_before,button],layout=ipw.Layout(align_items='center')).add_class('goto-box')
    
    def goto_button(self, slide_number, text,text_before = '', **kwargs):
        """"Jump to slide_number when clicked. give slide_number as integer of float like 1, 3.1 etc.   
        `text` is the text to be displayed on button.    
        `text_before` additional text (will be parsed) on left of the Button. It is useful because button will not show up in sceenshot.        
        `kwargs` are passed to `ipywidgets.Button` function.          
        **Note:** This button has a CSS classes nested as 'goto-box' > ('goto-html','goto-button') 
        that can be used to style it under each slide separately."""
        return display(self._goto_button(slide_number, text,text_before = text_before, **kwargs))
        
    def show(self): 
        "Display Slides."
        return self._ipython_display_()
    
    def _ipython_display_(self):
        'Auto display when self is on last line of a cell'
        if self.shell is None or self.shell.__class__.__name__ == 'TerminalInteractiveShell':
            raise Exception('Python/IPython REPL cannot show slides. Use IPython notebook instead.')
        
        self._remove_post_run_callback() # Avoid duplicate display
        self._update_toc() # Update toc before displaying app to include all sections
        self._update_dynamic_content() # Update dynamic content before displaying app
        self.close_view() # Close previous views
        self._display_box = ipw.VBox(children=[self._box,self._notes_view]) # Initialize display box again
        return display(self._display_box) # Display slides
    
    def close_view(self):
        "Close slides/cell view, but keep slides in memory than can be shown again."    
        if hasattr(self,'_display_box') and self._display_box is not None:
            self._display_box.close() # Clear display that removes CSS things there
    
    @property
    def _notes_view(self): 
        return ipw.Box([self.widgets.htmls.notes]).add_class('NotesView') 
    
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
    
    @property
    def _sectionindex(self):
        "Get current section index"
        if self.current._section:
            return self.current.index
        else:
            idxs = [s.index for s in self[:self.current.index] if s._section] # Get all section indexes before current slide
            return idxs[-1] if idxs else 0 # Get last section index
                
            
    def _switch_slide(self,old_index, new_index): # this change is provide from _update_content
        self.widgets.outputs.slide.clear_output(wait=False) # Clear last slide CSS
        with self.widgets.outputs.slide:
            self.html('style',f'''.TOC .toc-item.s{self._sectionindex} {{font-weight:bold;border-right: 4px solid var(--primary-fg);}}
            .TOC .toc-item {{border-right: 4px solid var(--secondary-bg);}}'''
            ).display()
        
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
        if self.progress_slider.index == 0: # First slide
            self._box.add_class('InView-Title').remove_class('InView-Last').remove_class('InView-Other')
        elif self.progress_slider.index == (len(self.progress_slider.options) -1): # Last slide
            self._box.add_class('InView-Last').remove_class('InView-Title').remove_class('InView-Other')
        else:
            self._box.remove_class('InView-Title').remove_class('InView-Last').add_class('InView-Other')
        
        if self._iterable and change:
            self.notes._display(self.current.notes) # Display notes first
            self.widgets.htmls.toast.value = '' # clear notification content if any defined by on_load
        
            number = f'{self.current.label} / {self._nslides}' if self.current.label != '0' else ''
            self.settings._update_footer(number_str = number) # Update footer privately
            
            self._switch_slide(old_index= change['old'], new_index= change['new']) 
            self.current.run_on_load() # Run on_load setup after switching slide
            
    def refresh(self): 
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self._iterable = self._collect_slides() # would be at least one title slide
        if not self._iterable:
            self.progress_slider.options = [('0',0)] # Clear options
            self.widgets.slidebox.children = [] # Clear older slides
            _ = [self.__dict__.pop(s, None) for s in getattr(self, '_links_dict', {})] # clear slides attributes
            return None
        
        n_last = float(self._iterable[-1].label)
        self._nslides = int(n_last) # Avoid frames number
        self._max_index = len(self._iterable) - 1 # This includes all frames
        
        # Now update progress bar
        opts = [(s.label, round(100*float(s.label)/(n_last or 1), 2)) for s in self._iterable]
        self.progress_slider.options = opts  # update options
        # Update Slides
        self.widgets.slidebox.children = [it._widget for it in self._iterable]
        for i, s in enumerate(self._iterable):
            s._index = i # Update index
            
        self._update_dynamic_content(None) # Update dynamic content including widgets
        
        # This is useful for readily available objects with slides instead of indexing.
        old_links = getattr(self,'_links_dict', {})
        _ = [self.__dict__.pop(s, None) for s in old_links] # Remove old links
        self._links_dict = {f's{item.label}'.replace('.','_'): item for item in self._iterable if item.label}
        self.__dict__.update(self._links_dict) # Add new links      
    
    def proxy(self,text):
        """Place a proxy placeholder in your slide and returns it's `handle`. This is useful when you want to update the placeholder later.
        Use `Slides.proxies[index].capture` or `handle.capture` contextmanager to update the placeholder.
        """
        self.verify_running('proxy placeholder can only be used in a slide constructor!')
        return self.running._proxy_private(text)
    
    @property
    def proxies(self):
        "Returns all placeholder proxies accross all slides."
        _phs = []
        for s in self._iterable:
            _phs.extend(s.proxies)
        return tuple(_phs)
    
    # defining magics and context managers
    def _slide(self,line,cell):
        """Capture content of a cell as `slide`.
            ---------------- Cell ----------------
            %%slide 1                             
            #python code here                     
        
        You can use extended markdown to create slides
            ---------------- Cell ----------------
            %%slide 2 -m
            Everything here and below is treated as markdown, not python code.
            ::: note-info  
                Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        ::: note
            If Markdown is separated by two dashes (--) on it's own line, multiple frames are created.
            Markdown before the first (--) separator is written on all frames.
        """
        line = line.strip().split() #VSCode bug to inclue \r in line
        if line and not line[0].isnumeric():
            raise TypeError(f'You should use %%slide integer >= 1 -m(optional), got {line}')
        
        slide_number_str = line[0] # First argument is slide number
        
        if '-m' in line[1:]:
            _frames = re.split(r'^--$|^--\s+$',cell, flags= re.DOTALL | re.MULTILINE) # Split on --- or ---\s+
            if len(_frames) > 1:
                _frames = [_frames[0] + '\n' + obj for obj in _frames[1:]]
                
            @self.frames(int(slide_number_str), *_frames)
            def make_slide(_frame, idx):
                self.running.set_source(_frame, 'markdown')  # Update source beofore running content to make it available to user inside markdown too
                parse(_frame, display_inline = True, rich_outputs = False)
            
        else: # Run even if already exists as it is user choice in Notebook, unlike markdown which loads from file
            with _build_slide(self, slide_number_str) as s:
                s.set_source(cell, 'python') # Update cell source beofore running
                self.run_cell(cell) #  
            
    
    @contextmanager
    def slide(self,slide_number):
        """Use this context manager to generate any number of slides from a cell. It is equivalent to `%%slide` magic."""
        if not isinstance(slide_number, int):
            raise ValueError(f'slide_number should be int >= 1, got {slide_number}')
        
        if slide_number < 0: # zero for title slide
            raise ValueError(f'slide_number should be int >= 1, got {slide_number}')
        
        with _build_slide(self, f'{slide_number}') as s, self.source.context(auto_display = False, depth = 4) as c: # depth = 4 to source under context manager
            s.set_source(c.raw, 'python') # Update cell source befor yielding
            yield s # Useful to use later
        
    def __title(self,line,cell):
        "Turns to cell magic `title` to capture title"
        return self._slide('0 -m' if '-m' in line else '0',cell)
    
    def __xmd(self, line, cell = None):
        """Turns to cell magics `%%xmd` and line magic `%xmd` to display extended markdown. 
        Can use in place of `write` commnad for strings.
        When using `%xmd`, variables should be `{{{{var}}}}` or `\{\{var\}\}`, not `{{var}}` as IPython 
        does some formatting to line in magic. If you just need to format it in string, then `{var}` works as well.
        Inline columns are supported with ||C1||C2|| syntax."""
        if cell is None:
            return parse(line, display_inline = True, rich_outputs = False)
        else:
            return parse(cell, display_inline = True, rich_outputs = False)
            
    @contextmanager
    def title(self):
        """Use this context manager to write title. It is equivalent to `%%title` magic."""
        with self.slide(0) as s, self.source.context(auto_display = False, depth = 4) as c: # depth = 4 to source under context manager
            s.set_source(c.raw, 'python') # Update cell source befor yielding to make available inside context manager
            yield s # Useful to use later
        
    @contextmanager
    def _loading_private(self, btn):
        btn.icon = 'minus'
        btn.disabled = True # Avoid multiple clicks
        self.widgets.htmls.loading.style.display = 'block'
        self.widgets.htmls.loading.value = loading_svg
        try:
            yield
        finally:
            btn.icon = 'plus'
            btn.disabled = False
            self.widgets.htmls.loading.value = ''
            self.widgets.htmls.loading.style.display = 'none'
        
    
    def _update_dynamic_content(self, btn = None):
        with self._loading_private(self.widgets.buttons.refresh):
            for slide in self[:]:
                if any([getattr(slide, attr, False) for attr in ('_has_widgets', '_toced', '_cited')]):
                    slide.update_display(go_there = False)
                # Update dynamic content in slide
                for dp in slide._dproxies.values(): 
                    dp.update_display()
    
    def frames(self, slide_number, *objs, repeat = False, frame_height = 'auto'):
        """Decorator for inserting frames on slide, define a function with two arguments acting on each obj in objs and current frame index.
        You can also call it as a function, e.g. `.frames(slide_number = 1,1,2,3,4,5)()` becuase it can write by defualt.
        
        ```python
        @slides.frames(1,a,b,c) # slides 1.1, 1.2, 1.3 with content a,b,c
        def f(obj, idx):
            do_something(obj)
            if idx == 0: # Main Slide
                print('This is main slide')
            else:
                print('This is frame', idx)
            
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
        def _frames(func = lambda obj, idx:self.write(obj)): # default write if called without function
            if not isinstance(slide_number,int):
                return print(f'slide_number expects integer, got {slide_number!r}')
            
            if slide_number < 0: # title slide is 0 
                raise ValueError(f'slide_number should be >= 1, got {slide_number!r}')
            
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
            with _build_slide(self, f'{slide_number}', is_frameless = False) as this_slide:
                self.write(self.format_css({'.SlideArea': {'height': frame_height}}))
                func(_new_objs[0],0) # Main slide content
            
            _new_objs = _new_objs[1:] # Fisrt one is already written
            
            NFRAMES_OLD = len(this_slide._frames) # old frames
            
            new_frames = []
            for i, obj in enumerate(_new_objs): # New frames
                if i >= NFRAMES_OLD: # Add new frames
                    new_slide = Slide(self, slide_number)
                else: # Update old frames
                    new_slide = this_slide._frames[i] # Take same frame back
                    new_slide.set_source('','') # Clear old source
                    
                new_frames.append(new_slide)
                
                with new_slide._capture() as captured:
                    self.write(self.format_css({'.SlideArea': {'height': frame_height}}))
                    func(obj,i+1) # i+1 as main slide is 0
                
                
            this_slide._frames = new_frames
            
            if len(this_slide._frames) != NFRAMES_OLD:
                this_slide._rebuild_all() # Rebuild all slides as frames changed
            
            # Update All displays
            for s in this_slide._frames:
                s.update_display() # This call is much important, otherwise content of many slides do not show
                # Remove duplicate sections/notes if any
                if s._section == this_slide._section:
                    s._section = None
                if s._notes == this_slide._notes:
                    s._notes = ''
            
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
        
        if len(slides_iterable) <= 1: self._box.add_class('SingleSlide')
        else: self._box.remove_class('SingleSlide')
        
        return tuple(slides_iterable)
    
    def _update_toc(self):
        tocs_dict = {s._section:s for s in self._iterable if s._section}
        children = children = [
            ipw.HBox([
                self.widgets.buttons.home,
                self.widgets.buttons.end,
                self.widgets.buttons.toc
            ]),
            self.widgets.htmls.tochead
        ]
        
        if not tocs_dict:
            children.append(ipw.HTML(_fix_repr('No sections found!, create sections with alert`Slides.section` method'
                    ' or alert`section\`key\``')))
        else:
            for i,(sec,slide) in enumerate(tocs_dict.items(), start = 1):
                slide_number = f"{slide._number}.{slide._label.split('.')[1]}" if '.' in slide._label else slide._number
                text_before = _fix_repr(f'color[var(--accent-color)]`{i}.` {sec}') + f"<p>{slide._label}</p>"
                extra_func = lambda: self.widgets.buttons.toc.click()
                p_btn = self._goto_button(slide_number,'', text_before= text_before,extra_func=extra_func)
                children.append(p_btn.add_class('toc-item').add_class(f's{slide._index}')) # class for dynamic CSS
                
        self.widgets.tocbox.children = children
        
    def create(self, *slide_numbers):
        "Create empty slides with given slide numbers. If a slide already exists, it remains same. This is much faster than creating one slide each time."
        new_slides = False
        for slide_number in slide_numbers:
            if f'{slide_number}' not in self._slides_dict:
                with capture_output() as captured:
                    self.write(f'### Slide-{slide_number}')
                
                self._slides_dict[f'{slide_number}'] = Slide(self, slide_number, captured_output=captured)
                new_slides = True
        
        if new_slides:
            self.refresh() # Refresh all slides
        
        return tuple([self._slides_dict[f'{slide_number}'] for slide_number in slide_numbers])
    
    
    def AutoSlides(self):
        """Returns a named tuple `AutoSlides(title,slide,frames, from_markdown)` if run from inside a
        python script. Functions inside this tuple replace main functions while removing the 'slide_number' paramater.
        Useful to handle auto numbering of slides inside a sequntially running script. Call at top of script before adding slides.
        ::: note-warning
            Returns None in Jupyter's context and it is not useful there due to lack of sequence.
        
        ```python
        import ipyslides as isd
        slides = isd.Slides() 
        auto = slides.AutoSlides()
        ```
        Use `auto.title`, `auto.slide` contextmanagers, `auto.frames` decorator and `auto.from_markdown` 
        function without thinking about what should be slide number.
        """
        if self._called_from_notenook('AutoSlides'):
            return None
        
        auto = namedtuple('AutoSlides',['title','slide','frames','from_markdown'])
        def slide(): return self.slide(self._next_number) 
        def frames(*objs, repeat=False, frame_height='auto'): return self.frames(self._next_number,*objs, repeat = repeat, frame_height = frame_height)
        def from_markdown(file_or_str, trusted = False): return self.from_markdown(self._next_number,file_or_str, trusted = trusted)
        return auto(self.title,slide,frames, from_markdown)
    
    def set_overlay_url(self, url = None):
        """Sets url in a persistent overlay iframe. Useful to load external sites like drawing pads or even files on jupyter/localhost server.
        You can load a notebook file there by passing url like `http://localhost:{port}{server}{path/to/file.ipynb}`.
        
        > Some sites may not allow loading inside an iframe.
        
        You can find open source drawing programs online to use here, or install e.g. `jupyterlab-drawio` extension to load in iframe.
        """
        if url and isinstance(url, str):
            if not url.strip():
                raise ValueError('Empty string is not a valid url')
            
            if not os.path.isfile(url):
                from urllib.parse import urlparse
                scheme, netloc, path, *others = urlparse(url) # to check if it is a valid url/filepath
                if not all([scheme, netloc or path]):
                    raise ValueError(f'Invalid url: {url!r}')
            
            _html = self.html('div',[self.html('span',url), self.iframe(url,height='100%')])
            self.widgets.htmls.overlay.value= _html.value
               
            if self._called_from_notenook('set_overlay_url') and not getattr(self.current,'_on_load',None):
                self.settings.btn_overlay.value = True # Do not open panel during presentation by on_load function, otherwise immediately open it
            
        elif url is None:
            _html = self.html('div',[
                self.html('span','About this overlay'),
                self.html('div',[
                    self.doc(self.set_overlay_url,'Slides')
                    ], className = 'block')
                ])
            self.widgets.htmls.overlay.value= _html.value # Set overlay to blank and give docs info
        else:
            raise TypeError(f'url must be a valide string or None, got {url!r}')
    
        
# Make available as Singleton Slides
_private_instance = Slides() # Singleton in use namespace
# This is overwritten below to just have a singleton

class Slides:
    _version = _private_instance.version # This is for initial use, and will be overwritten by property version
    __doc__ = textwrap.dedent("""
    Interactive Slides in IPython Notebook. Only one instance can exist. 
    
    All arguments are passed to corresponding methods in submodules, that you can tweak later as well.
    
    To suppress unwanted print from other libraries/functions, use:
    ```python
    with slides.suppress_stdout():
        some_function_that_prints() # This will not be printed
        print('This will not be printed either')
        display('Something') # This will be printed
    ```
    ::: note-tip
        - Run `slides.demo()` to see a demo of some features.
        - Run `slides.docs()` to see documentation.
        - Instructions in left settings panel are always on your fingertips.
        - Creating slides in a batch using `Slides.create` is much faster than adding them one by one.
    
   """)
    def __new__(cls,
                citation_mode   = 'global',
                center          = True, 
                content_width   = '90%', 
                footer_text     = 'IPySlides | <a style="color:blue;" href="https://github.com/massgh/ipyslides">github-link</a>', 
                show_date       = True,
                show_slideno    = True,
                logo_src        = logo_svg, 
                font_scale      = 1, 
                text_font       = 'STIX Two Text', 
                code_font       = 'var(--jp-code-font-family)', 
                code_style      = 'default', 
                code_lineno     = True,
                main_animation  = 'flow',
                frame_animation = 'slide_v',
                show_always     = True,
                extensions      = []
                ):
        "Returns Same instance each time after applying given settings. Encapsulation."
        _private_instance.__doc__ = cls.__doc__ # copy docstring
        
        if citation_mode not in ['global', 'inline', 'footnote']:
            raise ValueError(f'citation_mode must be one of "global", "inline", "footnote" but got {citation_mode}')
        
        _private_instance.extender.extend(extensions)
        _private_instance._citation_mode = citation_mode
        _private_instance.settings.show_always(show_always)
        
        _private_instance.settings.set(
            layout      = dict(center = center, content_width = content_width),
            footer      = dict(text = footer_text, show_date = show_date, show_slideno = show_slideno),
            logo        = dict(src = logo_src,width = 60),
            font_scale  = dict(font_scale = font_scale),
            font_family = dict(text_font = text_font, code_font = code_font),
            code_style  = dict(style = code_style, lineno = code_lineno),
        )
        
        with suppress(BaseException): # Avoid error if no slides exist
            _private_instance.settings.set_animation(main = main_animation, frame = frame_animation)
        return _private_instance
    
    # No need to define __init__, __new__ is enough to show signature and docs
    