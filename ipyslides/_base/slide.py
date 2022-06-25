"""Slide Object, should not be instantiated directly"""
import time
from contextlib import contextmanager
from ipywidgets import Output, Layout

from IPython.display import display
from IPython.utils.capture import capture_output

from . import styles
from ..utils import colored, html

class Slide:
    _animations = {'main':'','frame':''}
    _alert = colored('Print Warning: Use "pprint" function or "capture_std" contextmanager to display printed strings in order!', fg = 'red', bg = 'white')
    def __init__(self, app, captured_output, props_dict = {}):
        self._widget = Output(layout = Layout(height='auto',margin='auto',overflow='auto',padding='0.2em 2em'))
        self._app = app
        self._contents = captured_output.outputs
        if captured_output.stdout:
            display(self._alert)
            
        self._extra_outputs = {'start': [], 'end': []}
        self._css = html('style','')
        self.slide_number = None # This should be set in the LiveSlide class
        self.display_number = None # This should be set in the LiveSlides
        self._index = None # This should be set in the LiveSlides
        self.set_css(props_dict, notify = False)
        
        self.notes = '' # Should be update by Notes and LiveSlides calssess
        self.set_overall_animation()
        self._animation = None
        self._markdown = '' # Should be update by Markdown and LiveSlides calssess
        self._toast = None # Update from BaseLiveSlides
        self._has_widgets = False # Update in build_slide function
        
    def __repr__(self):
        md = f'{self.markdown[:15]}...' if self.markdown else ''
        return f'Slide(slide_number = {self.slide_number}, key = {self.display_label!r}, index = {self._index}, markdown = {md!r})'
    
    def update_display(self):
        "Update display of this slide."
        self._widget.clear_output()
        with self._widget:
            display(*self.contents)
    
    @contextmanager
    def append(self):
        "Contextmanager to append objects to this slide. Use with 'with' statement. Only most recent appended object(s) are displayed."
        return self.insert(index = -1)
    
    @contextmanager
    def insert(self, index):
        "Contextmanager to insert new content at given index. If index is -1, just appends at end. Only most recent inserted object(s) are displayed."
        if index < -1:
            raise ValueError(f'expects non-negative index or -1 to append at end, got {index}')
        
        with capture_output() as captured:
            yield
        
        outputs = captured.outputs
        if captured.stdout:
            display(self._alert)
            
        if index == 0:
            self._extra_outputs['start'] = outputs
        elif index == -1:
            self._extra_outputs['end'] = outputs
        else:
            if index >= len(self._contents):
                raise IndexError('Index {} out of range for slide with {} objects'.format(index, len(self._contents)))
            self._extra_outputs[f'{index}'] = outputs
        
        self._app._slidelabel = self.display_label # Go there
        self.update_display()
    
    def reset(self):
        "Reset all appended/prepended/inserted objects."
        self._extra_outputs = {'start': [], 'end': []}
        self._app._slidelabel = self.display_label # Go there
        self.update_display() 

    @property
    def toast(self):
        return self._toast
    
    @property
    def display_label(self):
        return str(self.display_number)
    
    @property
    def css(self):
        return self._css
    
    @property
    def index(self):
        return self._index
    
    @property
    def markdown(self):
        return self._markdown
    
    @property
    def animation(self):
        return self._animation or html('style', 
            (self._animations['frame'] 
             if '.' in self.display_label
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
        if self._app._slidelabel != self.display_label:
            self._app._slidelabel = self.display_label # Go there to see effects
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
            if self._app._slidelabel != self.display_label:
                self._app._slidelabel = self.display_label # Go there to see effects
            else:
                self._app.widgets.outputs.slide.clear_output(wait = True)
                with self._app.widgets.outputs.slide:
                    display(self.animation, self._css)
        else:
            self._animation = None # It should be None, not ''
            
    def _rebuild_all(self):
        "Update all slides in optimal way."
        self._app._iterable = self._app._collect_slides()
        n_last = self._app._iterable[-1].display_number
        self._app._nslides = int(n_last) # Avoid frames number
        self._app._max_index = len(self._app._iterable) - 1 # This includes all frames
        
        # Now update progress bar
        opts = [(f"{s.display_number}", round(100*float(s.display_number)/(n_last or 1), 2)) for s in self._app._iterable]
        self._app.progress_slider.options = opts  # update options
        # Update Slides after progress bar is updated
        self._app.widgets.slidebox.children = [it._widget for it in self._app._iterable]
        self._app._slidelabel = self.display_label # Go there after refreshing
        
        for i, s in enumerate(self._app._iterable):
            s._index = i # Update index
            if s._has_widgets:
                s.update_display() # Refresh all slides with widgets only, other data is not lost

        
@contextmanager
def build_slide(app, slide_number_str, props_dict = {}):
    "Use as contextmanager in LiveSlides class to create slide"
    with capture_output() as captured:
        if slide_number_str in app._slides_dict:
            _slide = app._slides_dict[slide_number_str]
        else:
            _slide = Slide(app, captured, props_dict)
            _slide.slide_number = slide_number_str
            app._slides_dict[slide_number_str] = _slide
            setattr(_slide, 'new', True) # To indictae for rebuilding
            
        yield _slide
        
    _slide._contents = captured.outputs
    app._slidelabel = _slide.display_label # Go there to see effects
    _slide.update_display() # Update Slide, it will not come to this point if has same code
    
    for k in [p for ps in _slide.contents for p in ps.data.keys()]:
        if k.startswith('application'): # Widgets in this slide
            _slide._has_widgets = True
            break # No need to check other widgets if one exists
    
    if captured.stdout:
        display(_slide._alert)
    
    if hasattr(_slide, 'new'):
        _slide._rebuild_all()
        delattr(_slide, 'new')
    
        
    
    