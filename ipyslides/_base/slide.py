"""Slide Object, should not be instantiated directly"""

import typing
from contextlib import contextmanager
from ipywidgets import Output, Layout


from IPython.display import display
from IPython.utils.capture import capture_output


from . import styles
from ..utils import html, _HTML

class Slide:
    "New in 1.7.0"
    _animations = {'main':'','frame':''}
    def __init__(self, app, captured_output, props_dict = {}):
        self._widget = Output(layout = Layout(height='auto',margin='auto',overflow='auto',padding='0.2em 2em'))
        self._app = app
        self._contents = captured_output.outputs
            
        self._extra_outputs = {'start': [], 'end': []}
        self._css = html('style','')
        self._number = None # This should be set in the LiveSlide class
        self._label = None # This should be set in the LiveSlides
        self._index = None # This should be set in the LiveSlides
        self.set_css(props_dict, notify = False)
        
        self.notes = '' # Should be update by Notes and LiveSlides calss
        self.set_overall_animation()
        self._animation = None
        self._markdown = '' # Should be update by LiveSlides
        self._cell_code = '' # Should be update by LiveSlides 
        self._from_cell = False # Update in build slides
        self._toast = None # Update from BaseLiveSlides
        self._has_widgets = False # Update in _build_slide function
        self._citations = {} # Added from LiveSlides
        self._frames = [] # Added from LiveSlides
        
    def __repr__(self):
        return f'Slide(number = {self._number}, label = {self.label!r}, index = {self._index})'
    
    def update_display(self, go_there = True):
        "Update display of this slide."
        if go_there:
            self.clear_display(wait = True) # Clear and go there, wait to avoid blinking
        else:
            self._widget.clear_output(wait = True) # Clear, but don't go there
            
        with self._widget:
            display(*self.contents)
            
            
            if self._citations and (self._app._citation_mode == 'footnote'):
                html('hr').display()
                
                for citation in self._citations.values():
                    citation.html.display()
        
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
        
        with capture_output() as captured:
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
        Give a dictionary as {0: 'Markdown',..., -1:'Markdown'}.
        
        New in 1.7.7"""
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
    def toast(self):
        return self._toast
    
    @property
    def label(self):
        return self._label
    
    @property
    def citations(self):
        return self._citations
    
    @property
    def css(self):
        return self._css
    
    @property
    def index(self):
        return self._index
    
    @property
    def markdown(self):
        return getattr(self, '_markdown', '') # Not All Slides have markdown
    
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
        return tuple(self._extra_outputs['start'] + middle_outputs + self._extra_outputs['end']) 
    
    @property
    def source(self):
        "Return source code of this slide, markdwon or python."
        return self._get_source()
    
    def _get_source(self, name = None):
        if self._from_cell and self._cell_code:
            return self._app.source.from_string(self._cell_code, language = 'python', name = name)
        elif self._from_cell and self._markdown:
            return self._app.source.from_string(self._markdown, language = 'markdown', name = name)
        else:
            return self._app.source.from_string('Source of a slide only exits if it is created (most recently) using `from_markdown` or `%%slide` magic\n'
                'For `@LiveSlide.frames` and `with LiveSlides.slide` contextmanager, use `with LiveSlides.source.context`  to capture source.',
                language = 'markdown')
    
    def show(self):
        self.update_display() # Needs to not discard widgets there
        return display(self._widget)
    
    def set_css(self,props_dict, notify = True):
        """props_dict is a dict of css properties in format {'selector': {'prop':'value',...},...}
        'selector' for slide itself should be '' or 'slide'.
        """
        if not isinstance(props_dict, dict):
            raise TypeError("props_dict must be a dict in format {'selector': {'prop':'value',...},...}")
        
        for k, v in props_dict.items():
            if not isinstance(v, dict):
                raise TypeError('Value for selector {} should be a dict of {"prop":"value",...}, got {}'.format(k,v))
        _all_css = ''
        for k, v in props_dict.items():
            _css = ''
            if k.strip() in ('', 'slide', '.slide'):
                _css += f'.SlidesWrapper {{\n'
            else:
                _css += f'.SlideArea {k} {{\n'
                
            _css += ('\n'.join([f'{q}:{p}!important;' for q, p in v.items()]) + '\n}\n')
            _all_css += _css # Append to all css
            
        self._css = html('style', _all_css)
        
        # See effect of changes
        if self._app._slidelabel != self.label:
            self._app._slidelabel = self.label # Go there to see effects
        else:
            self._app.widgets.outputs.slide.clear_output(wait = True)
            with self._app.widgets.outputs.slide:
                display(self.animation, self._css)
        
    def set_overall_animation(self, main = 'slide_h',frame = 'slide_v'):
        "Set animation for all slides."
        if main:
            self.__class__._animations['main'] = styles.animations[main]
        else:
            self.__class__._animations['main'] = ''
            
        if frame:
            self.__class__._animations['frame'] = styles.animations[frame]
        else:
            self.__class__._animations['frame'] = ''
            
    def set_animation(self, name):
        "Set animation of this slide."
        if name:
            self._animation = html('style',styles.animations[name])
            # See effect of changes
            if self._app._slidelabel != self.label:
                self._app._slidelabel = self.label # Go there to see effects
            else:
                self._app.widgets.outputs.slide.clear_output(wait = True)
                with self._app.widgets.outputs.slide:
                    display(self.animation, self._css)
        else:
            self._animation = None # It should be None, not ''
            
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
def _build_slide(app, slide_number_str, props_dict = {}, from_cell = False, is_frameless = True):
    "Use as contextmanager in LiveSlides class to create slide. New in 1.7.0"
    # We need to overwrite previous frame/slides if they exist to clean up residual slide numbers if they are not used anymore
    old_slides = list(app._slides_dict.values()) # Need if update is required later, values decide if slide is changed
        
    with capture_output() as captured:
        if slide_number_str in app._slides_dict:
            _slide = app._slides_dict[slide_number_str] # Use existing slide is better as display is already there
            if _slide._frames and is_frameless: # If previous has frames but current does not, construct new one at this position
                _slide = Slide(app, captured, props_dict)
                _slide._number = slide_number_str
                app._slides_dict[slide_number_str] = _slide
        else:
            _slide = Slide(app, captured, props_dict)
            _slide._number = slide_number_str
            app._slides_dict[slide_number_str] = _slide
    
        yield _slide
    
    _slide._from_cell = from_cell # Need to determine code source
    if not from_cell:
        _slide._cell_code = '' # Clear cell code but not Markdown
        
    _slide._contents = captured.outputs
    
    for k in [p for ps in _slide.contents for p in ps.data.keys()]:
        if k.startswith('application'): # Widgets in this slide
            _slide._has_widgets = True
            break # No need to check other widgets if one exists
    # Append before updating slides
    append_print_warning(captured= captured, append_to= _slide._contents)
    
    app._slidelabel = _slide.label # Go there to see effects
    _slide.update_display() # Update Slide, it will not come to this point if has same code
    
    if old_slides != list(app._slides_dict.values()): # If there is a change in slides
        _slide._rebuild_all() # Rebuild all slides
        del old_slides # Delete old slides
        
def append_print_warning(captured, append_to):
    "Append print warning to outputs of a capture."
    if captured.stdout.replace('\x1b[2K','').strip(): # Only if there is output after removing \x1b[2K, IPython has something unknown
        append_to.append(_HTML('<div class="PyRepr Error">Use `pprint` or `LiveSlides.capture_std` '
        'contextmanager \nto see print output on slide in desired order!\n'
        '---------------------------------------------------------------------------\n'
        + captured.stdout + '</div>'))
        

    
        
    
    