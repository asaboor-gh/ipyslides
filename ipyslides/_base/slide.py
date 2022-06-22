"""Slide Object, should not be instantiated directly"""

from contextlib import contextmanager, suppress

from IPython.display import display
from IPython.utils.capture import capture_output

from . import styles
from ..utils import raw, colored, html

class Slide:
    _animations = {'main':'','frame':''}
    _alert = colored('Print Warning: Use "pprint" function or "capture_std" contextmanager to display strings in order!', fg = 'red', bg = 'white')
    def __init__(self, app, captured_output, props_dict = {}):
        self.app = app
        self._outputs = captured_output.outputs
        if captured_output.stdout:
            self._outputs.insert(0, self._alert + raw(captured_output.stdout))
            
        self._extra_outputs = {'start': [], 'end': []}
        self._css = html('style','')
        self.set_css(props_dict)
        self.slide_number = None # This should be set in the LiveSlide class
        self.display_number = None # This should be set in the LiveSlides
        
        self.notes = '' # Should be update by Notes and LiveSlides calssess
        self.set_overall_animation()
        self.animation = None
        
    def __repr__(self):
        return f'Slide(slide_number = {self.slide_number}, display_number = {self.display_number})'
    
    @contextmanager
    def append(self):
        with self.insert(-1):
            yield
    
    @contextmanager
    def prepend(self):
        with self.insert(0):
            yield
    
    @contextmanager
    def insert(self, index):
        with capture_output() as captured:
            yield
        
        outputs = captured.outputs
        if captured.stdout:
            self._outputs.insert(0, self._alert + raw(captured.stdout))
            
        if index == 0:
            self._extra_outputs['start'] = outputs
        elif index == -1:
            self._extra_outputs['end'] = outputs
        else:
            if index >= len(self._outputs):
                raise IndexError('Index {} out of range for slide with {} objects'.format(index, len(self._outputs)))
            self._extra_outputs[f'{index}'] = outputs
    
    def reset(self):
        "Reset all appended/prepended/inserted objects."
        self._extra_outputs = {'start': [], 'end': []}
    
    @property
    def display_label(self):
        return str(self.display_number)
    
    def show(self):
        middle_outputs = [[out] for out in self._outputs] # Make list for later flattening
        shift = 0
        for k, v in self._extra_outputs.items():
            if k not in ['start', 'end']:
                middle_outputs.insert(int(k) + shift, v)
                shift += 1
                
        middle_outputs = [o for out in middle_outputs for o in out] # Flatten list
        
        _outputs = self._extra_outputs['start'] + middle_outputs + self._extra_outputs['end']
        if self.app._computed_display == False:
            _outputs.insert(0, self._css)
        return display(*_outputs)
    
    def set_css(self,props_dict):
        """props_dict is a dict of css properties in format {'selector': {'prop':'value',...},...}
        'selector' for slide itself should be ''.
        """
        if not isinstance(props_dict, dict):
            raise TypeError("props_dict must be a dict in format {'selector': {'prop':'value',...},...}")
        
        for k, v in props_dict.items():
            if not isinstance(v, dict):
                raise TypeError('Value for selector {} should be a dict of {"prop":"value",...}, got {}'.format(k,v))
        _all_css = ''
        for k, v in props_dict.items():
            _css = f'.SlideArea {k} {{\n'
            _css += '\n'.join([f'{q}:{p}!important;' for q, p in v.items()])
            _all_css += _css + '\n}'
            
            if k.strip() == '':
                for q,p in v.items():
                    if 'background' in q:
                        _all_css = f'.SlidesWrapper {{\n{q}:{p}!important;}}' 
            
        self._css = html('style', _all_css)
        with suppress(BaseException): # Fist time there is no label, so avoid it
            if self.app._slidelabel != self.display_label:
                self.app._slidelabel = self.display_label # Go back to set css
            else:
                if self.app._computed_display:
                    self.app.widgets.slidebox.children[-1].clear_output(wait = True)
                    with self.app.widgets.slidebox.children[-1]:
                        display(self._css)
                else:
                    self.app._update_content(True) # For Single Slides
        
    def set_overall_animation(self, main = 'slide_h',frame = 'slide_v'):
        "Set animation for all slides created after using this function."
        if main:
            self.__class__._animations['main'] = styles.animations[main]
        if frame:
            self.__class__._animations['frame'] = styles.animations[frame]
    
    def set_animation(self, name):
        "Set animation of this slide."
        if name:
            self.animation = html('style',styles.animations[name])
            
@contextmanager
def build_slide(app, slide_number_str, props_dict = {}):
    "Use as contextmanager in LiveSlides class to create slide"
    with capture_output() as captured:
        _slide = Slide(app, captured, props_dict)
        yield _slide
        
    _slide._outputs = captured.outputs
    _slide.slide_number = slide_number_str
    _slide.animation = _slide.animation or html('style', 
            (_slide._animations['frame'] 
             if '.' in slide_number_str 
             else _slide._animations['main'])
            )
    
    if captured.stdout:
        _slide._outputs.insert(0, _slide._alert + raw(captured.stdout))
        
    app._slides_dict[slide_number_str] = _slide
    app.refresh() # Make Slides first then go there
    app._slidelabel = _slide.display_label
    
    