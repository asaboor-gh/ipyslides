"""Slide Object, should not be instantiated directly"""

import typing
import sys
from contextlib import contextmanager
from ipywidgets import Output, Layout, Button


from IPython.display import display
from IPython.utils.capture import capture_output
from IPython.core.ultratb import FormattedTB


from . import styles
from ..utils import html, _format_css, _sub_doc, _css_docstring

class _EmptyCaptured: outputs = [] # Just as placeholder for initialization

class _LiveRichOutput:
    def __init__(self, func, slide):
        self._func = func
        self._slide = slide
        self._last_outputs = []
        self._error_outputs = []
        self._raise_error = True
        
        try: # Initail error in cell to verify code is correct
            with capture_output():
                self._func()
        except Exception as e:
            raise Exception(f'{e}')
        
    @property
    def outputs(self):
        "Executes given function and returns its output as list of outputs."
        old = self._slide._app._running_slide
        self._slide._app._running_slide = self._slide
        try:
            with capture_output() as captured:
                self._func()
                
            self._last_outputs = captured.outputs
            
        except:
            if self._raise_error:
                wdgts = self.error_handler() # should capture outside
                with capture_output() as err_captured:
                    display(*wdgts)
                    
                self._error_outputs = err_captured.outputs
                     
        finally:
            self._slide._app._running_slide = old # should go back
            
        if self._error_outputs: 
            return self._last_outputs + self._error_outputs
        return self._last_outputs
    
    def error_handler(self):
        btn = Button(description = '✕ Clear Error and Keep Last Successful Output', layout = Layout(width='auto'))
        
        def remove_error_outputs(btn):
            self._raise_error = False 
            try:
                self._error_outputs = []
                self._slide.update_display() # This clears up things, but not in cellbox mode, see that
            finally:
                self._raise_error = True
        
        ftb = FormattedTB(color_scheme='Neutral')  
        tb = ftb.structured_traceback(*sys.exc_info())  
        
        out = Output()
        with out:
            self._slide._app.builtin_print('Note: Clearing error only works in full app mode.\n' + '-'*80)
            self._slide._app.builtin_print(ftb.stb2text(tb)) # Always use builtin print to show correct traceback
        
        btn.on_click(remove_error_outputs)
        return btn, out

class Slide:
    "Slide object, should not be instantiated directly by user."
    _animations = {'main':'flow','frame':'slide_v'}
    _overall_css = html('style','')
    def __init__(self, app, number, captured_output = _EmptyCaptured):
        self._widget = Output(layout = Layout(height='auto',margin='auto',overflow='auto',padding='0.2em 2em'))
        self._app = app
        self._contents = captured_output.outputs
            
        self._extra_outputs = {'start': [], 'end': []}
        self._css = html('style','')
        self._number = number if isinstance(number, str) else str(number) 
        self._label = None # This should be set in the Slides
        self._index = None # This should be set in the Slides
        
        self._notes = '' # Should be update by Notes and Slides calss
        self._animation = None
        self._source = {'text': '', 'language': ''} # Should be update by Slides
        self._has_widgets = False # Update in _build_slide function
        self._citations = {} # Added from Slides
        self._frames = [] # Added from Slides
        self._section = None # Added from Slides

        
    def set_source(self, text, language):
        "Set source code for this slide."
        self._source = {'text': text, 'language': language}
    
    def _dynamic_private(self, func, tag = None):  
        "Add dynamic content to this slide which updates on refresh/update_display etc. func takes no arguments." 
        lro = _LiveRichOutput(func, self)
        
        if isinstance(tag, str): # To keep track what kind of dynamic content it is
            setattr(self, tag, True)
            
        return display(html('pre','This gets updated on refresh/update_display'), metadata = {'LiveRichOutput': lro})
        
    def _on_load_private(self, func):
        try: # check if code is correct
            with capture_output():
                func()
        except Exception as e:
            raise Exception(f'{e}')
        self._on_load = func # This will be called in main app
        
    def __repr__(self):
        return f'Slide(number = {self._number}, label = {self.label!r}, index = {self._index})'
    
    @contextmanager
    def _capture(self, assign = True):
        "Capture output to this slide."
        self._app._running_slide = self
        if assign:
            self._app._next_number = int(self._number) + 1
            self._notes = '' # Reset notes
            self._citations = {} # Reset citations
            self._extra_outputs = {'start': [], 'end': []} # Reset extra outputs
            self._section = None # Reset sec_key
            if hasattr(self,'_on_load'):
                del self._on_load # Remove on_load function
        
        try:
            self._app._remove_post_run_callback() # Remove before capturing
            with capture_output() as captured:
                yield captured
            
            if captured.stderr:
                raise RuntimeError(f'Error in building {self}: {captured.stderr}')
            
            # If no error, then add callback keeping the user preference
            if self._app._post_run_enabled:
                self._app.shell.events.register('post_run_cell', self._app._post_run_cell)
            
        finally:
            self._app._running_slide = None
            self._app._cell_slides.append(self) # Add to slides in current cell
            
            if assign:
                self._contents = captured.outputs  
        
        
    def update_display(self, go_there = True):
        "Update display of this slide."
        if go_there:
            self.clear_display(wait = True) # Clear and go there, wait to avoid blinking
        else:
            self._widget.clear_output(wait = True) # Clear, but don't go there
        
        with self._widget:
            display(*self.contents)

            if self._citations and (self._app._citation_mode == 'footnote'):
                html('hr/').display()
                self._app.write(self.citations)
        
        # Update corresponding CSS and Animation
        self._app.widgets.outputs.slide.clear_output(wait=False) # Clear last slide CSS
        with self._app.widgets.outputs.slide:
            self.animation.display()
            self.css.display()
        
        # This foreces hard refresh of layout, without it, sometimes CSS is not applied correctly
        if 'SlideArea' in self._widget._dom_classes: # Only if slide is present there.
            self._widget.remove_class('SlideArea') 
            self._widget.add_class('SlideArea')
    
    def clear_display(self, wait = False):
        "Clear display of this slide."
        self._app._slidelabel = self.label # Go there to see effects
        self._widget.clear_output(wait = wait)
        
    
    @contextmanager
    def append(self):
        "Contextmanager to append objects to this slide. Use with 'with' statement. Only most recent appended object(s) are displayed."
        return self.insert(index = -1)
    
    @contextmanager
    def insert(self, index: int):
        "Contextmanager to insert new content at given index. If index is -1, just appends at end. Only most recent inserted object(s) are displayed."
        if index < -1:
            raise ValueError(f'expects non-negative index or -1 to append at end, got {index}')
        
        with self._capture(assign = False) as captured:
            yield 
        
        outputs = captured.outputs
        
        if index == 0:
            self._extra_outputs['start'] = outputs
        elif index == -1:
            self._extra_outputs['end'] = outputs
        else:
            if index >= len(self._contents):
                raise IndexError('Index {} out of range for slide with {} objects'.format(index, len(self._contents)))
            self._extra_outputs[f'{index}'] = outputs
        
        self._app._slidelabel = self.label # Go there
        self.update_display()
        
    def insert_markdown(self, index_markdown_dict: typing.Dict[int, str]) -> None:
        """Insert multiple markdown objects (after being parsed) at given indices on slide at once.
        Give a dictionary as {0: 'Markdown',..., -1:'Markdown'}."""
        if not isinstance(index_markdown_dict, dict):
            raise TypeError(f'expects dict as {{index: "Markdown",...}}, got {type(index_markdown_dict)}')
        for index, markdown in index_markdown_dict.items():
            if not isinstance(index, int):
                raise TypeError(f'expects int as index, got {type(index)}')
            
            with self.insert(index):
                self._app.parse_xmd(markdown, display_inline = True)
    
    def reset(self):
        "Reset all appended/prepended/inserted objects."
        self._extra_outputs = {'start': [], 'end': []}
        self._app._slidelabel = self.label # Go there
        self.update_display() 
    
    @property
    def frames(self):
        return tuple(self._frames)

    @property
    def parent(self):
        if '.' in self._label:
            return self._app._slides_dict[self._number] # Return parent slide, _number is string
        
    
    @property
    def notes(self):
        return self._notes
    
    @property
    def label(self):
        return self._label
    
    @property
    def number(self):
        return int(self._number) # Return as int
    
    @property
    def citations(self):
        return tuple(sorted(self._citations.values(), key=lambda x: int(x._id)))
    
    @property
    def css(self):
        return self._overall_css + self._css # Add overall CSS but self._css should override it
    
    @property
    def index(self):
        return self._index
    
    @property
    def markdown(self):
        return self._source['text'] if self._source['language'] == 'markdown' else '' # Not All Slides have markdown
    
    @property
    def animation(self):
        return self._animation or html('style', 
            (self._animations['frame'] 
             if '.' in self.label
             else self._animations['main'])
            )
    
    @property
    def contents(self):
        middle_outputs = [[out] for out in self._contents] # Make list for later flattening
        shift = 0
        for k, v in self._extra_outputs.items():
            if k not in ['start', 'end']:
                middle_outputs.insert(int(k) + shift, v)
                shift += 1
                
        middle_outputs = [o for out in middle_outputs for o in out] # Flatten list
        all_outputs = self._extra_outputs['start'] + middle_outputs + self._extra_outputs['end']
        updated_outputs = []
        for out in all_outputs:
            if 'LiveRichOutput' in out.metadata:
                updated_outputs.extend(out.metadata['LiveRichOutput'].outputs) # Unpack LiveRichOutput as it can have many outputs
            else:
                updated_outputs.append(out)
                
        return tuple(updated_outputs) 
    
    def get_source(self, name = None):
        "Return source code of this slide, markdwon or python or None if no source exists."
        if self._source['text']:
            return self._app.source.from_string(**self._source, name = name)
        else:
            return self._app.source.from_string('Source of a slide only exits if it is NOT created (most recently) using @Slides.frames decorator\n',language = 'markdown')
    
    def show(self):
        self.update_display() # Needs to not discard widgets there
        return display(self._widget)
    
    def _set_overall_css(self, css_dict={}):
        self.__class__._overall_css = html('style','') # Reset overall CSS
        old_slide_css = self._css # Save old slide CSS without overall CSS
        self.set_css(css_dict = css_dict) # Set this slide's CSS
        self.__class__._overall_css = self.css # Set overall CSS from this slide's CSS, self.css takes both
        self._css = old_slide_css # Restore old slide CSS
    
    @_sub_doc(css_docstring = _css_docstring)
    def set_css(self,css_dict = {}):
        """Attributes at the root level of the dictionary will be applied to the slide.  
        use `ipyslides.Slides.settings.set_css` to set CSS for all slides at once.
        {css_docstring}"""
        self._css = _format_css(css_dict, allow_root_attrs = True)
        
        # See effect of changes
        if not self._app.running: # Otherwise it has side effects
            if self._app._slidelabel != self.label:
                self._app._slidelabel = self.label # Go there to see effects
            else:
                self._app.widgets.outputs.slide.clear_output(wait = False)
                with self._app.widgets.outputs.slide:
                    display(self.animation, self._css)
        
    def _set_overall_animation(self, main = 'slide_h',frame = 'slide_v'):
        "Set animation for all slides."
        if main is None:
            self.__class__._animations['main'] = ''
        elif main in styles.animations:
            self.__class__._animations['main'] = styles.animations[main]
        else:
            raise ValueError(f'Animation {main!r} not found. Use None to remove animation or one of {tuple(styles.animations.keys())}')
            
        if frame is None:
            self.__class__._animations['frame'] = ''
        elif frame in styles.animations:
            self.__class__._animations['frame'] = styles.animations[frame]
        else:
            raise ValueError(f'Animation {frame!r} not found. Use None to remove animation or one of {tuple(styles.animations.keys())}')
            
    def set_animation(self, name):
        "Set animation of this slide. Provide None if need to stop animation."
        if name is None:
            self._animation = html('style', '')
        elif isinstance(name,str) and name in styles.animations:
            self._animation = html('style',styles.animations[name])
            # See effect of changes
            if not self._app.running: # Otherwise it has side effects
                if self._app._slidelabel != self.label:
                    self._app._slidelabel = self.label # Go there to see effects
                else:
                    self._app.widgets.outputs.slide.clear_output(wait = False)
                    with self._app.widgets.outputs.slide:
                        display(self.animation, self._css)
        else:
            self._animation = None # It should be None, not '' or don't throw error here
            
    def _rebuild_all(self):
        "Update all slides in optimal way when a new slide is added."
        self._app._iterable = self._app._collect_slides()
        n_last = float(self._app._iterable[-1].label)
        self._app._nslides = int(n_last) # Avoid frames number
        self._app._max_index = len(self._app._iterable) - 1 # This includes all frames
        
        # Now update progress bar
        opts = [(s.label, round(100*float(s.label)/(n_last or 1), 2)) for s in self._app._iterable]
        self._app.progress_slider.options = opts  # update options
        # Update Slides after progress bar is updated
        self._app.widgets.slidebox.children = [it._widget for it in self._app._iterable]
        self._app._slidelabel = self.label # Go there after setting children
        
        # Update display for slides with widgets
        for i, s in enumerate(self._app._iterable):
            s._index = i # Update index of slide for __repr__
            if s._has_widgets:
                s.update_display(go_there =  False) # Refresh all slides with widgets only, other data is not lost
        

@contextmanager
def _build_slide(app, slide_number_str, is_frameless = True):
    "Use as contextmanager in Slides class to create slide."
    # We need to overwrite previous frame/slides if they exist to clean up residual slide numbers if they are not used anymore
    old_slides = list(app._slides_dict.values()) # Need if update is required later, values decide if slide is changed
        
    if slide_number_str in app._slides_dict:
        _slide = app._slides_dict[slide_number_str] # Use existing slide is better as display is already there
        _slide.set_source('','') # Reset old source
        if _slide._frames and is_frameless: # If previous has frames but current does not, construct new one at this position
            _slide = Slide(app, slide_number_str)
            app._slides_dict[slide_number_str] = _slide
    else:
        _slide = Slide(app, slide_number_str)
        app._slides_dict[slide_number_str] = _slide 
            
    with _slide._capture(assign = True) as captured:  
        yield _slide
    
    for k in [p for ps in _slide.contents for p in ps.data.keys()]:
        if k.startswith('application'): # Widgets in this slide
            _slide._has_widgets = True
            break # No need to check other widgets if one exists
    
    app._slidelabel = _slide.label # Go there to see effects
    _slide.update_display() # Update Slide, it will not come to this point if has same code

    if old_slides != list(app._slides_dict.values()): # If there is a change in slides
        _slide._rebuild_all() # Rebuild all slides
        del old_slides # Delete old slides

        

    
        
    
    