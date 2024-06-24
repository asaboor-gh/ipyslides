"""Slide Object, should not be instantiated directly"""

import sys, time
from contextlib import contextmanager, suppress
from ipywidgets import Layout, Button, HBox

from IPython.display import display
from IPython.core.ultratb import FormattedTB


from . import styles
from .widgets import Output # not from ipywidget
from ..utils import XTML, html, alert, _format_css, _sub_doc, _css_docstring
from ..writer import _fmt_html
from ..xmd import capture_content
from ..source import Code as code

def _expand_objs(outputs, context):
    "Put columns and exportable widgets inline with rich outputs in a given context."
    new_outputs = []
    for out in outputs:
        if hasattr(out, 'metadata') and ('COLUMNS' in out.metadata): # may be Writer object there without metadata
            new_outputs.append(context._columns[out.metadata['COLUMNS']])
        elif hasattr(out, 'metadata') and 'Exp4Widget' in out.metadata:
            other_context = context if hasattr(context, '_exportables') else context._slide # Proxy also has exportables
            new_outputs.append(other_context._exportables[out.metadata['Exp4Widget']])
        else:
            new_outputs.append(out)
    return new_outputs

class DynamicRefresh:
    "DynamicRefresh is a display for a function that is executed when refresh button is clicked. Should not be instantiated directly."
    def __init__(self, func, slide):
        if slide._app.in_dproxy: # raise this also because dictionary size get changed during iteration if nested
            raise Exception('Dynamically refreshable content cannot be written inside another same type!')
        
        self._func = func
        self._slide = slide
        self._btn = Button(icon= 'plus',layout= Layout(width='24px',height='24px'),tooltip='Refresh dynamic content').add_class('Sfresh-Btn').add_class('Menu-Item')
        self._box = HBox(children=[self._btn], layout =Layout(width='100%',height='auto')).add_class('Sfresh-Box')
        self._last_outputs = []
        self._error_outputs = []
        self._raise_error = True
        self._columns = {}
        
        self._idx = str(len(self._slide._dproxies))
        self._slide._dproxies[self._idx] = self
        
        self._slide._app._in_dproxy = self
        try: # Initail error in cell to verify code is correct
            with capture_content() as cap:
                self._func()
            if cap.stderr: raise Exception(cap.stderr)
        finally:
            self._slide._app._in_dproxy = None
        
        self._btn.on_click(self._on_click)
    
    def _ipython_display_(self):            
        self._box.children = [self._btn] # First time Output get captured on slide, so avoid it
        display(self._box, metadata = self.metadata)
        
    def _on_click(self, btn):
        out = Output(layout = Layout(width='100%')).add_class('Sfresh-Out') # Create new output for each click, otherwise it will not show
        self._btn.icon = 'minus'
        self._btn.disabled = True
        try:
            with out:
                display(*self.outputs) 
            self._box.children = [self._btn, out]
        finally:
            self._btn.disabled = False
            self._btn.icon = 'plus'  
    
    def update_display(self):
        "Updates the display of the dynamic content."
        self._on_click(None)
    
    def fmt_html(self): 
        content = ''
        for out in self.outputs:
            content += _fmt_html(out)
        _class = ' '.join(self._box._dom_classes) # keep styling
        return f'<div class="{_class}">{content}</div>'
    
    @property
    def metadata(self): return {'DYNAMIC': self._idx} # Important
    
    @property
    def data(self): return getattr(self._box, '_repr_mimebundle_', lambda: {'application':'dproxy'})()
    
    @property
    def outputs(self):
        "Executes given function and returns its output as list of outputs."
        self._slide._app._in_dproxy = self
        self._columns = {} # Reset columns here just before executing function
        self._error_outputs = [] # Reset error output in start of next capture each time

        with self._slide._app._set_running(self._slide): # Set running slide to this slide
            try:
                with capture_content() as captured:
                    self._func()

                self._last_outputs = _expand_objs(captured.outputs,self) # Expand columns is necessary

            except:
                if self._raise_error:
                    wdgts = self.error_handler() # should capture outside
                    with capture_content() as err_captured:
                        display(*wdgts)

                    self._error_outputs = err_captured.outputs

            finally:
                self._slide._app._in_dproxy = None
            
        if self._error_outputs: 
            return self._last_outputs + self._error_outputs
        return self._last_outputs
    
    def error_handler(self):
        btn = Button(description = '✕ Clear Error and Keep Last Successful Output', layout = Layout(width='auto'))
        
        def remove_error_outputs(btn):
            self._raise_error = False 
            try:
                self._error_outputs = []
                self.update_display() 
            finally:
                self._raise_error = True
        
        ftb = FormattedTB(color_scheme='Neutral')  
        tb = ftb.structured_traceback(*sys.exc_info())  
        
        out = Output()
        with out:
            print(ftb.stb2text(tb)) 
        
        btn.on_click(remove_error_outputs)
        return btn, out
    
    
class Proxy:
    "Proxy object, should not be instantiated directly by user."
    def __init__(self, text, slide):
        if slide._app.in_dproxy:
            raise RuntimeError("Can't place proxy inside a refreshable function.")
        
        if slide._app.in_proxy:
            raise RuntimeError("Can't place proxy inside another proxy being captured.")
        
        self._slide = slide
        self._to_display = self
        self._text = text.strip() # Remove leading and trailing spaces
        self._outputs = []
        self._key = str(len(self._slide._proxies))
        self._slide._proxies[self._key] = self
        self._columns = {} 
        self._exportables = {}
        display(self._to_display, metadata= {'Proxy': self._key}) 
        
    def _exp4widget(self, widget, func):
        return Exp4Widget(widget, func, self)
    
    @property
    def text(self): return self._text # Useful if user wants to filter proxies
    
    @property
    def slide(self): return self._slide # Useful if user wants to test if proxy is in slide
    
    def __repr__(self):
        return f'Proxy(text = {self._text!r}, slide_number = {self._slide.number}, proxy_index = {self._key})'
    
    def _repr_html_(self): # This is called when displayed
        return alert(repr(self)).value
    
    @property
    def outputs(self):
        "Returns the outputs of the proxy, if it has been replaced."
        if self._outputs:
            return self._outputs 
        with capture_content() as captured:
            display(self._to_display, metadata= {'Proxy': self._key}) # This will update the slide refrence on each display to provide useful info
        return captured.outputs
    
    def fmt_html(self): 
        content = ''
        for out in self.outputs:
            content += _fmt_html(out)
        return content
    
    @contextmanager
    def capture(self):
        "Context manager to capture output to current prpxy. Use it like this: with proxy.capture(): ... after a slide is already created."
        if self._slide._app.this:
            raise RuntimeError("Can't use Proxy.capture() contextmanager inside a slide constructor.")
        
        self._columns = {} # Reset columns
        self._exportables = {} # Reset exportables
        self._slide._app._in_proxy = self # Used to get print statements to work in order and coulm aware
        try:
            with capture_content() as captured:
                yield

            if captured.stderr:
                raise RuntimeError(captured.stderr)

            self._outputs = _expand_objs(captured.outputs, self) # Expand columns
            self._slide.update_display() # Update display to show new output
        finally:
            self._slide._app._in_proxy = None
            
class Exp4Widget:
    def __init__(self, widget, func, context):
        if not isinstance(context, (Slide, Proxy)):
            raise TypeError("context should be a Slide or Proxy object.")
        
        self._widget = widget
        self._func = func 
        self._context = context # Should be slide or proxy
        self._key = str(len(self._context._exportables))
        self._context._exportables[self._key] = self # Add to exportables
    
    def _ipython_display_(self):
        display(self._widget, metadata= self.metadata)
    
    @property
    def metadata(self): return {'Exp4Widget': self._key} # Important
    
    @property
    def data(self): return getattr(self._widget, '_repr_mimebundle_', lambda: {'application':'Exp4Widget'})()
    
    def fmt_html(self):
        "Returns alternative html representation of the widget."
        return self._func(self._widget)
    

class Slide:
    "Slide object, should not be instantiated directly by user."
    _animations = {'main':'slide_h','frame':'appear'}
    _overall_css = html('style','')
    def __init__(self, app, number):
        self._widget = Output(layout = Layout(margin='auto',padding='1em', visibility='hidden')).add_class("SlideArea")
        self._app = app
            
        self._css = html('style','')
        self._bg_image = ''
        self._number = number
        self._index = number if number == 0 else None # First slide should have index ready
        
        self._contents = []
        self._notes = '' # Should be update by Notes and Slides calss
        self._animation = None
        self._source = {'text': '', 'language': ''} # Should be update by Slides
        self._has_widgets = False # Update in _build_slide function
        self._citations = {} # Added from Slides
        self._cframe = 0 # current frame
        self._section = None # Added from Slides
        self._sec_id = f"s-{id(self)}" # should there alway wether a section or not
        self._proxies = {} # Placeholders added to this slide
        self._dproxies = {} # Dynamic placeholders added to this slide
        self._exportables = {} # Exportable widgets added to this slide
        self._columns = {} # Columns added to this slide
        self._split_frames = True
        self._has_top_frame = True
        self._set_refs = True

        if not self._contents: # show slide number hint there
            self.set_css({
                f' > .jp-OutputArea:empty:after': {
                    'content': f'"{self!r}"',
                    'color': 'var(--accent-color)',
                    'font-size': '2em',
                }
            })
        
    def _exp4widget(self, widget, func):
        return Exp4Widget(widget, func, self)
  
    def set_source(self, text, language):
        "Set source code for this slide."
        self._source = {'text': text, 'language': language}
    
    def reset_source(self):
        "Reset old source but leave markdown source for observing chnages"
        if not self._markdown:
            self.set_source("","")
    
    def _dynamic_private(self, func, tag = None, hide_refresher = False):  
        "Add dynamic content to this slide which updates on refresh/update_display etc. func takes no arguments." 
        dr = DynamicRefresh(func, self) 
        if hide_refresher:
            dr._btn.add_class('Hidden')
        if isinstance(tag, str): # To keep track what kind of dynamic content it is
            setattr(self, tag, True)
            if tag == '_toced':
                setattr(self, '_slide_tocbox',dr._box) # need in refresh
        return display(dr) # This will be handleded by _ipython_display_ method
            
    def _proxy_private(self, text):
        return Proxy(text, self) # get auto displayed
        
    def _on_load_private(self, func):
        with self._app._hold_running(): # slides will not be running during switch, so make it safe
            with capture_content() as cap: # check if code is correct
                func(self)
            
            if cap.outputs or cap.stdout:
                raise Exception('func in on_load(func) should not print or display anything!')
            elif cap.stderr:
                raise RuntimeError(f'func in on_load(func) raised an error. See above traceback!')
        
        # This should be outside the try/except block even after finally, if successful, only then assign it.
        self._on_load = func # This will be called in main app
    
    def run_on_load(self):
        "Called when a slide is loaded into view. Use it to register notifications etc."
        self._widget.layout.height = '100%' # Trigger a height change to reset scroll position
        start = time.time()
        self._app.widgets.htmls.glass.value = self._bg_image or getattr(self._app.settings,'_bg_image','') # slide first

        try: # Try is to handle errors in on_load, not for attribute errors, and also finally to reset height
            if hasattr(self,'_on_load') and callable(self._on_load):
                self._on_load(self) # Now no need to raise Error as it is already done in _on_load_private, and no one can handle it either
        finally:
            if (t := time.time() - start) < 0.05: # Could not have enought time to resend another event
                time.sleep(0.05 - t) # Wait at least 50ms, (it does not effect anything else) for the height to change from previous trigger
            self._widget.layout.height = '' # Reset height to auto
        
    def __repr__(self):
        return f'Slide(number = {self.number}, index = {self.index})'
    
    @contextmanager
    def _capture(self):
        "Capture output to this slide."
        self._app._next_number = self.number + 1
        self._cframe = 0 
        self._app._slides_per_cell.append(self) # will be flushed at end of cell by post_run_cell event
        self._widget.add_class(f"n{self.number}").remove_class("Frames") # will be added by fsep
        self._split_frames = True # Defult
        self._has_top_frame = True # Default
        self._set_refs = True
    
        if hasattr(self,'_on_load'):
            del self._on_load # Remove on_load function
        if hasattr(self,'_target_id'):
            del self._target_id # Remove target_id

        with suppress(Exception): # register only in slides building, not other cells
            self._app._register_postrun_cell()
        
        with self._app._set_running(self):
            self.clear() # rest of cleanup here to avoid blinks in buidling slides
            with capture_content() as captured:
                yield captured
            
            if (self.number == 0) and self._fidxs:
                self._frame_idxs = () # to be clear on next run
                raise ValueError(f"Title slide does not support frames!")

            if captured.stderr:
                if 'warning' in captured.stderr.lower():
                    print(captured.stderr) # Don't throw error on soft warnings
                else:
                    raise RuntimeError(f'Error in building {self}: {captured.stderr}')

            self._contents = _expand_objs(captured.outputs, self) # Expand columns  
            self.set_css_classes(remove = 'Out-Sync') # Now synced
            self.update_display(go_there=True)    

            if self._app.widgets.checks.focus.value: # User preference
                self._app._box.focus()


    def clear(self):
        """Use with caution. This will required running cell again. 
        All content will be wiped out excpet css, animation, background image etc.
        You may want to use self.clear_display instead."""
        self._notes = '' # Reset notes
        self._citations = {} # Reset citations
        self._section = None # Reset sec_key
        self._proxies = {} # Reset placeholders
        self._dproxies = {} # Reset dynamic placeholders
        self._columns = {} # Reset columns
        self._exportables = {} # Reset exportables
        self._contents = [] # reset content to not be exportable
        wait = True if self._app.this is self else False # avoid blinking in building slides, otherwise no
        self.clear_display(wait = wait) 
        
    def update_display(self, go_there = True):
        "Update display of this slide."
        if go_there:
            self.clear_display(wait = True) # Clear and go there, wait to avoid blinking
        else:
            self._widget.clear_output(wait = True) # Clear, but don't go there
    
        with self._widget:
            display(*self.contents)
            for dp in self._dproxies.values(): 
                dp.update_display() # Update display to show new output as well
            
            for c in self._columns.values():
                c.update_display()

            self._handle_refs()

        
        # Update corresponding CSS but avoid animation here for faster and clean update
        self._app._update_tmp_output(self.css)
        self.set_css_classes('SlideArea', 'SlideArea') # Hard refresh, removes first and add later
        self._reset_frames() # after others to take everything into account
    
    def _reset_frames(self):
        nc_frames, contents = [], self.contents  # get once
        for i, c in enumerate(contents):
            if "FSEP" in c.metadata:
                if i > 0: # ignore first separator without content before
                    if "COLUMNS" in contents[i-1].metadata: # last before frame separator, keep poistive index
                        nc_frames.append((i, len(contents[i-1]._cols)))
                    else: 
                        nc_frames.append(i+1)
                elif self._split_frames: # User may not want to add content on each frame
                    nc_frames.append(0) # avoids creating a frame with no content
                    self._has_top_frame = False # reset by each run
            
        else: # Handle content after last frame
            if nc_frames: # Do not add if no frames already
                if "COLUMNS" in contents[-1].metadata:
                    nc_frames.append((len(contents), len(contents[-1]._cols)))
                
                if isinstance(nc_frames[-1],int): # safely add full
                    nc_frames[-1] = len(contents)
        
        new_frames = []
        for f in nc_frames:
            if isinstance(f,tuple):
                for k in range(f[1]): 
                    new_frames.append((f[0], k+1)) #upto again
            elif not f in new_frames: # avoid duplicates at end
                new_frames.append(f)
        
        if self._split_frames:
            new_frames = [0, *[f[0] + 1 if isinstance(f, tuple) else f for f in new_frames]] # column was at index, get upto for range
            new_frames = [range(i,j) for i,j in zip(new_frames[:-1], new_frames[1:]) if range(i,j)] # as range, non-empty only
       
        self._frame_idxs = tuple(new_frames)

        if self._frame_idxs:
            self.first_frame() # Bring up first frame to activate CSS
        else:
            if hasattr(self, '_frame_idxs'): # from previous run may be
                del self._frame_idxs
    
    @property
    def _fidxs(self): return getattr(self, '_frame_idxs', ())
    
    @property
    def nf(self):
        "Number of total frames."
        return len(self._fidxs) or 1 # each slide is single frame
    
    def _update_view(self, which):
        # avoids animation by updating CSS without first animation object and Prev class in all case
        self._app._update_tmp_output(*getattr(self._app, '_renew_objs',[])[1:]) 
        self._app.widgets.slidebox.remove_class('Prev') 

        if self._split_frames: # only if not incremental
            if which == 'prev':
                self._app.widgets.slidebox.add_class('Prev')
            self._app._update_tmp_output(*getattr(self._app, '_renew_objs',[]))

        self._app.widgets.update_progressbar(self, self._cframe)
        if self.index == self._app.wprogress.max: # This is last slide
            if self._cframe + 1 == self.nf:
                self._app._box.add_class("InView-Last")
            else:
                self._app._box.remove_class("InView-Last")
        
        if hasattr(self,'_on_load') and callable(self._on_load):
            if any(
                [ # first and last frames are speacial cases, handled by navigation if swicthing from other slide
                    self._cframe == 0 and which == 'prev',
                    self._cframe + 1 == self.nf and which == 'next',
                    0 < self._cframe < (self.nf - 1)
                ]
            ): self._on_load(self)
                
    
    def _show_frame(self, which):
        if self._fidxs:
            if (which == 'next') and ((self._cframe + 1) < self.nf):
                self._cframe += 1
            elif (which == 'prev') and ((self._cframe - 1) >= 0):
                self._cframe -= 1
            else:
                return False
            
            start, nrows, ncols, first = 1, self._fidxs[self._cframe], 0, 0
            if isinstance(nrows, tuple):
                nrows, ncols = nrows
            elif isinstance(nrows, range): # not joined
                start, nrows = nrows.start, nrows.stop
                if self._has_top_frame:
                    first = self._fidxs[0].stop

            self._fsep.value = _format_css({
                f'^.n{self.number} > .jp-OutputArea > .jp-OutputArea-child': {
                    f'^:not(:nth-child(n + {start}):nth-child(-n + {nrows}))': { # start through nrows
                        'height': '0 !important',
                    },
                    f'^.jp-OutputArea-child.jp-OutputArea-child:nth-child(-n + {first})': { # initial objs on each, increase spacificity 
                        'height': 'unset !important',
                    },
                    f'^.jp-OutputArea-child.jp-OutputArea-child:nth-child({len(self.contents) + 1})': { # for references, shown after contents
                        'height': 'unset !important'
                    },
                    **({f'^:nth-child({nrows}) .columns.writer:first-of-type > div:nth-child(n + {ncols+1})': { # avoid nested columms
                        'visibility': 'hidden !important', # enforce this instead of jumps in height
                    }} if isinstance(self._fidxs[self._cframe], tuple) else {}), 
                },
            }).value

            self._update_view(which)
            return True # indicators required
        else:
            if hasattr(self, '_fsep'):
                del self._fsep
            return False
    
    def next_frame(self):
        "Jump to next frame and return True. If no next frame, returns False"
        return self._show_frame('next')
        
    def prev_frame(self):
        "Jump to previous frame and return True. If no previous frame, returns False"
        return self._show_frame('prev')
    
    def first_frame(self):
        "Jump to first frame."
        self._cframe = -1
        return self.next_frame()
    
    def last_frame(self):
        "Jump to last frame"
        self._cframe = self.nf # go right and swicth back
        return self.prev_frame()
    
    def _get_pv(self, fidx):
        unit = 100/(self._app._iterable[-1].index or 1) # avoid zero division error or None
        value = round(unit * (self.index or 0), 4)
        if not self._fidxs:
            return value
        
        fidx = self._fidxs.index(self._fidxs[fidx]) # handles negative index automatically
        return round(value - unit*(self.nf - fidx - 1)/self.nf, 4)


    def _handle_refs(self):
        if hasattr(self, '_refs'): # from some previous settings and change
            delattr(self, '_refs') # added later  only if need
        
        if all([self._citations, self._set_refs, self._app.cite_mode == 'footnote']): # don't do in inline mode
            self._refs = html('div', # need to store attribute for export
                sorted(self._citations.values(), key=lambda x: x._id), 
                css_class='Citations', style = '')
            self._refs.display()

    
    def clear_display(self, wait = False):
        "Clear display of this slide."
        self._app.navigate_to(self.index) # Go there to see effects
        self._widget.clear_output(wait = wait)
    
    def show(self):
        "Show this slide in cell."
        out = Output().add_class('SlideArea')
        with out:
            display(*self.contents)
        return display(out)
    
    def get_footer(self, update_widget = False): # Used here and export_html
        "Return footer of this slide. Optionally update footer widget."
        return self._app.settings._get_footer(self, update_widget = update_widget)
    
    @property
    def proxies(self):
        "Return placeholder proxies in this slide."
        return tuple(self._proxies.values())
        
    def yoffset(self, value):
        "Set yoffset (in perect) for frames to have equal height in incremental content."
        self._app.verify_running("yoffset can only be used inside slide constructor!")
        if (not isinstance(value, int)) or (value not in range(101)): 
            raise ValueError("yoffset value should be integer in units of percent betweem [0,100]!")
        
        self._app.html('style', 
            f'''.SlideArea.n{self.number} > .jp-OutputArea {{
                top: {value}% !important;
                margin-top: 0 !important;
            }}''' # each frames get own yoffset, margin-top 0 is important to force top to take effect
        ).display()
        

        
    @property
    def notes(self): return self._notes
    
    @property
    def number(self): return self._number
    
    @property
    def css(self):
        return XTML(f'{self._overall_css}\n{self._css}') # Add overall CSS but self._css should override it
    
    @property
    def index(self): return self._index

    @property
    def indexf(self):
        "Returns index of current displayed frame."
        return max(self._cframe, 0) # _cframe is negative in start on purpose
    
    @property
    def _markdown(self): # No need to reset after v4.3.1 by user
        return self._source['text'] if self._source['language'] == 'markdown' else '' # Not All Slides have markdown
    
    @property
    def animation(self):
        return self._animation or html('style', 
            (self._animations['frame'] if self._fidxs else self._animations['main'])
            )
    
    @property
    def contents(self):
        outputs = []
        for out in self._contents:
            if "COLUMNS" in out.metadata:
                outputs.append(self._columns[out.metadata['COLUMNS']])
            elif 'Exp4Widget' in out.metadata:
                outputs.append(self._exportables[out.metadata['Exp4Widget']]) # This will get displayed as a widget
            elif 'DYNAMIC' in out.metadata:
                outputs.append(self._dproxies[out.metadata['DYNAMIC']]) # This will get displayed as a widget
            elif 'Proxy' in out.metadata:
                outputs.extend(self._proxies[out.metadata['Proxy']].outputs) # replace Proxy with its outputs/or new updated slide information
            else:
                outputs.append(out)
                
        return tuple(outputs) 
    
    def get_source(self, name = None):
        "Return source code of this slide, markdwon or python or None if no source exists."
        if self._source['text']:
            return self._app.code.from_string(**self._source, name = name)
        else:
            return self._app.code.cast('No source found!\n',language = 'markdown')
    
    def _set_overall_css(self, props: dict):
        self.__class__._overall_css = html('style','') # Reset overall CSS
        old_slide_css = self._css # Save old slide CSS without overall CSS
        self.set_css(props) # Set this slide's CSS
        self.__class__._overall_css = self.css # Set overall CSS from this slide's CSS, self.css takes both
        self._css = old_slide_css # Restore old slide CSS
    
    @_sub_doc(css_docstring = _css_docstring)
    def set_css(self,props : dict):
        """Attributes at the root level of the dictionary will be applied to the slide. You can add CSS classes by `Slide.set_css_classes`.
        use `ipyslides.Slides.settings.set_css` to set CSS for all slides at once.
        {css_docstring}"""
        self._css = _format_css(props, allow_root_attrs = True)
        
        # See effect of changes
        if not self._app.this: # Otherwise it has side effects
            if self._app._current is self:
                self._app._update_tmp_output(self.animation, self._css) # force refresh CSS
            else:
                self._app.navigate_to(self.index) # Go there to see effects automatically

    def set_css_classes(self, add=None, remove=None):
        "Sett CSS classes on this slide separated by space. classes are remove first and add after it."
        if remove is not None: # remove first to enable toggle
            if not isinstance(remove, str):
                raise TypeError("CSS classes should be a string with each class separated by space")
            for c in remove.split():
                self._widget.remove_class(c)
        
        if add is not None:
            if not isinstance(add, str):
                raise TypeError("CSS classes should be a string with each class separated by space")
            for c in add.split():
                self._widget.add_class(c)

    @property
    def css_class(self):
        "Readonly dom classes on this slide sepaarated by space."
        return ' '.join(self._widget._dom_classes) # don't let things modify on orginal
    
    def set_bg_image(self, src, opacity=0.25, filter='blur(2px)', contain=False):
        """Adds glassmorphic effect to the background with image. `src` can be a url or a local image path.
        
        ::: note-tip
            - This function alongwith `self.clear` enables you to add a slide purely with an image, possibly with `opacity=1` and `contain = True`.
            - This will be exported to HTML file.
        """
        overall = getattr(self._app.settings, '_bg_image','')
        self._app.settings.set_bg_image(src, opacity=opacity, filter=filter, contain=contain)
        self._bg_image = self._app.widgets.htmls.glass.value # Update for this slide
        self._app.settings._bg_image = overall # Reset that back for other slides 
        self._app.navigate_to(self.index) # Go there to see effects while changing on_load
    
    def _instance_animation(self,name):
        "Create unique animation for this slide instance on fly"
        return styles.animations[name].replace('.SlideBox',f'.{self._app.uid} .SlideBox')
        
    def _set_overall_animation(self, main = 'slide_h',frame = 'appear'):
        "Set animation for all slides."
        if main is None:
            self.__class__._animations['main'] = ''
        elif main in styles.animations:
            self.__class__._animations['main'] = self._instance_animation(main)
        else:
            raise KeyError(f'Animation {main!r} not found. Use None to remove animation or one of {tuple(styles.animations.keys())}')
            
        if frame is None:
            self.__class__._animations['frame'] = ''
        elif frame in styles.animations:
            self.__class__._animations['frame'] = self._instance_animation(frame)
        else:
            raise KeyError(f'Animation {frame!r} not found. Use None to remove animation or one of {tuple(styles.animations.keys())}')
        
        self._app._update_tmp_output(self.animation, self.css) # See effect
            
    def set_animation(self, name):
        "Set animation of this slide. Provide None if need to stop animation."
        if name is None:
            self._animation = html('style', '')
        elif isinstance(name,str) and name in styles.animations:
            self._animation = html('style',self._instance_animation(name))
            # See effect of changes
            if not self._app.this: # Otherwise it has side effects
                if self._app._current is self:
                    self._app._update_tmp_output(self._animation, self.css) # force refresh
                else:
                    self._app.navigate_to(self.index) # Go there to see effects
        else:
            self._animation = None # It should be None, not '' or don't throw error here

@contextmanager
def _build_slide(app, slide_number):
    "Use as contextmanager in Slides class to create slide."
    if not isinstance(slide_number, int):
        raise ValueError(f"slide_number should be int >= 0, got {slide_number}")

    if slide_number < 0:  # zero for title slide
        raise ValueError(f"slide_number should be int >= 0, got {slide_number}")
     
    if slide_number in app._slides_dict:
        this = app._slides_dict[slide_number] # Use existing slide is better as display is already there
        this.reset_source() # Reset old source but keep markdown for observing edits
    else:
        this = Slide(app, slide_number)
        app._slides_dict[slide_number] = this
        app.refresh() # rebuild slides to have index ready
            
    with this._capture(): 
        yield this
    
    def get_keys(data):
        keys = [k for k in data.keys()] if isinstance(data, dict) else [] # Most _reprs_
        if isinstance(data, tuple): # _repr_mimebublde_ of widgets
            for d in data:
                keys.extend(d.keys())
        return keys
    
    for k in [p for ps in this.contents for p in get_keys(ps.data)]:
        if k.startswith('application'): # Widgets in this slide
            this._has_widgets = True
            break # No need to check other widgets if one exists

        

    
        
    
    