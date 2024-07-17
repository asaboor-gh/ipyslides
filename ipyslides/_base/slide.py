"""Slide Object, should not be instantiated directly"""

import time, textwrap
from contextlib import contextmanager, suppress
from IPython.display import display
from IPython.utils.capture import RichOutput

from . import styles
from .widgets import Output # Fixed one
from ..utils import XTML, html, alert, _styled_css, _build_css
from ..xmd import capture_content
from ..formatters import _Output, serializer, widget_from_data
from ._layout_css import background_css
    

class Proxy(Output): # Not from _Output, need to avoid slide-only content here
    "Proxy object, should not be instantiated directly by user., use Slides.proxy or proxy`text` in Makdown."
    def __init__(self, text, slide):
        slide._app.verify_running("Can't place proxy inside a context other than slides!.")
        
        super().__init__(clear_output=True, wait=True)
        
        self._slide = slide
        self._text = text.strip() # Remove leading and trailing spaces
        self._outputs = []
        self._key = str(len(self._slide._proxies))
        self._slide._proxies[self._key] = self
        self.outputs = ({'output_type': 'display_data', 'data': {
            'text/plain': self._text, 'text/html': alert(repr(self)).value}
        },)
    
    def __repr__(self):
        return f'Proxy(text = {self._text!r}, slide_number = {self._slide.number}, proxy_index = {self._key})'
    
    def fmt_html(self):
        return serializer._alt_output(self) 
    
    def __enter__(self):
        if self._slide._app.this:
            raise RuntimeError("Can't use Proxy contextmanager inside a slide constructor.")
        
        self.outputs = () # Reset for new outputs, clear_output is looping indefinitely
        super().__enter__()
        
    def __exit__(self, etype, evalue, tb):
        super().__exit__(etype, evalue, tb)

    def display(self): display(self) # For completeness

    def update_display(self):
        super().update_display()
        for out in self.outputs: # One level write columns should be update hardly
            meta = out.get('metadata',{})
            if 'UPDATE' in meta and (col := widget_from_data(meta['UPDATE'])):
                col.update_display()

class Slide:
    "Slide object, should not be instantiated directly by user."
    _animations = {'main':'slide_h','frame':'appear'}
    _overall_css = ''
    def __init__(self, app, number):
        self._widget = _Output(layout = dict(margin='auto',padding='16px', visibility='hidden')).add_class("SlideArea")
        self._app = app
            
        self._css = ''
        self._bg_image = ''
        self._number = number
        self._index = number if number == 0 else None # First slide should have index ready
        self._animation = None
        self._sec_id = f"s-{id(self)}" # should there alway wether a section or not
        self._set_defaults()

        if not self._contents: # show slide number hint there
            self.set_css({
                f' > .jp-OutputArea:empty:after': {
                    'content': f'"{self!r}"',
                    'color': 'var(--accent-color)',
                    'font-size': '2em',
                }
            })
    
    def __setattr__(self, name: str, value):
        if not name.startswith('_') and hasattr(self, name):
            raise AttributeError(f"Can't reset attribute {name!r} on {self!r}")
        self.__dict__[name] = value
    
    def _set_defaults(self):
        if hasattr(self,'_on_load'):
            del self._on_load # Remove on_load function
        if hasattr(self,'_target_id'):
            del self._target_id # Remove target_id
        self._notes = '' # Reset notes
        self._citations = {} # Reset citations
        self._section = None # Reset sec_key
        self._proxies = {} # Reset placeholders
        self._indexf = 0 # current frame index
        self._contents = [] # reset content to not be exportable 
        self._has_widgets = False # Update in _build_slide function
        self._source = {'text': '', 'language': ''} # Should be update by Slides
        self._split_frames = True
        self._has_top_frame = True
        self._set_refs = True
        self._toc_args = () # empty by default
        self._widget.add_class(f"n{self.number}").remove_class("Frames") # will be added by fsep
  
    def set_source(self, text, language):
        "Set source code for this slide."
        self._source = {'text': text, 'language': language}
    
    def reset_source(self):
        "Reset old source but leave markdown source for observing chnages"
        if not self._markdown:
            self.set_source("","")
        
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
        self._app.widgets.htmls.bglayer.value = self._bg_image

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
        self._app._slides_per_cell.append(self) # will be flushed at end of cell by post_run_cell event
        self._set_defaults() 

        with suppress(Exception): # register only in slides building, not other cells
            self._app._register_postrun_cell()
        
        with self._app._set_running(self):
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

            self._contents = captured.outputs # Expand columns  
            self.set_css_classes(remove = 'Out-Sync') # Now synced
            self.update_display(go_there=True)    

            if self._app.widgets.checks.focus.value: # User preference
                self._app._box.focus()
        
    def update_display(self, go_there = True):
        "Update display of this slide."
        if go_there:
            self.clear_display(wait = True) # Clear and go there, wait to avoid blinking
            self._app._update_tmp_output(self.css) # Update corresponding CSS but avoid animation here
            self.set_css_classes('SlideArea', 'SlideArea') # Hard refresh, removes first and add later
        else:
            self._widget.clear_output(wait = True) # Clear, but don't go there
    
        with self._widget:
            for obj in self.contents:
                display(obj)
                if hasattr(obj, 'update_display'):
                    obj.update_display()
            else: # On successful for loop, handle refs at end
                self._handle_refs()
            
            for p in self._proxies.values():
                p.update_display()
        # after others to take everything into account
        self._reset_frames()
        self._app._update_toc()

    def _reset_toc(self):
        items = []
        for s in self._app[:self.index]:
            if s._section:
                items.append({"c":"prev", "s":s})

        if self._section:
            items.append({"c":"this", "s":self})
        elif items:
            items[-1].update({"c":"this"})

        for s in self._app[self.index + 1:]:
            if s._section:
                items.append({"c":"next", "s":s})
        
        first_toc = True
        for s in self._app[:]:
            if s._toc_args and first_toc:
                s._widget.add_class('FirstTOC')
                first_toc = False
            else:
                s._widget.remove_class('FirstTOC')

        items = [XTML(textwrap.dedent('''
            <li class="toc-item {c}">
                <a href="#{s._sec_id}" class="export-only citelink">{s._section}</a>
                <span class="jupyter-only">{s._section}</span>
            </li>''').format(**sec))
            for sec in items]
        
        title, highlight = getattr(self, '_toc_args', ['## Contents {.align-left}', False])
        css_class = 'toc-list toc-extra' if highlight else 'toc-list'
        ol = self._app.html('ol', items, style='', css_class=css_class)
        
        return RichOutput(
            data = {'text/plain': title,'text/html': self._app.cols([title, ol]).value},
            metadata = {"DataTOC": self.number}) # to access later
    
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
            
            if len(new_frames) > 1:
                self._frame_idxs = tuple(new_frames[1:]) # first join on all
                self._frame_top = new_frames[0].stop
            else:
                self._frame_idxs = ()
        else:
            self._frame_idxs = tuple(new_frames[1:]) # join first content here as well to make same number of fames

        if self._frame_idxs:
            self.first_frame() # Bring up first frame to activate CSS
        else:
            if hasattr(self, '_frame_idxs'): # from previous run may be
                del self._frame_idxs
            if hasattr(self, '_frame_add'):
                del self._frame_top
    
    @property
    def _fidxs(self): return getattr(self, '_frame_idxs', ())
    
    @property
    def nf(self):
        "Number of total frames."
        return len(self._fidxs) or 1 # each slide is single frame
    
    def _update_view(self, which):
        self._set_progress()
        if self._split_frames: # In case of incremental frames, only edge slides are animated automatically
            if which == 'prev':
                self._app.widgets.slidebox.add_class('Prev')
            else:
                self._app.widgets.slidebox.remove_class('Prev')
            self._app._update_tmp_output(*getattr(self._app, '_renew_objs',[]))
        elif not self.indexf in (self.nf-1, 0):
             self._app._update_tmp_output(*getattr(self._app, '_renew_objs',[])[1:]) # avoid animations

        if self.index == self._app.wprogress.max: # This is last slide
            if self.indexf + 1 == self.nf:
                self._app._box.add_class("InView-Last")
            else:
                self._app._box.remove_class("InView-Last")
        
        if any([ # first and last frames are speacial cases, handled by navigation if swicthing from other slide
            self.indexf == 0 and which == 'prev',
            self.indexf + 1 == self.nf and which == 'next',
            0 < self.indexf < (self.nf - 1)
        ]) and hasattr(self,'_on_load') and callable(self._on_load):
            self._on_load(self)
                
    
    def _show_frame(self, which):
        if self._fidxs:
            if (which == 'next') and ((self.indexf + 1) < self.nf):
                self._indexf += 1
            elif (which == 'prev') and ((self.indexf - 1) >= 0):
                self._indexf -= 1
            else:
                return False
            
            start, nrows, ncols, first = 1, self._fidxs[self.indexf], 0, getattr(self, '_frame_top',0)
            if isinstance(nrows, tuple):
                nrows, ncols = nrows
            elif isinstance(nrows, range): # not joined
                start, nrows = nrows.start, nrows.stop

            self._fsep.value = _styled_css({
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
                    }} if isinstance(self._fidxs[self.indexf], tuple) else {}), 
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
    

    def _reset_indexf(self, new_index, func): 
        old = int(self.indexf) # avoid pointing to property
        self._indexf = new_index

        try:
            condition = func()
        finally:
            if not condition:
                self._indexf = old
            return condition
    
    def first_frame(self):
        "Jump to first frame."
        return self._reset_indexf(-1, self.next_frame)  # go left and switch forward

    
    def last_frame(self):
        "Jump to last frame"
        return self._reset_indexf(self.nf, self.prev_frame) # go right and swicth back
    
    def _set_progress(self):
        unit = 100/(self._app._iterable[-1].index or 1) # avoid zero division error or None
        value = round(unit * ((self.index or 0) - (self.nf - self.indexf - 1)/self.nf), 4)
        self._app.widgets._progbar.children[0].layout.width = f"{value}%"
        self._app.widgets._snum.description = f"{self._app.wprogress.value or ''}" # empty for zero

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
        out = _Output().add_class('SlideArea')
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
        return self._indexf if self._fidxs else 0
    
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
            if "UPDATE" in out.metadata: # need this for export
                outputs.append(widget_from_data(out.metadata["UPDATE"]))
            elif 'DataTOC' in out.metadata:
                outputs.append(self._reset_toc())
            else:
                outputs.append(out)
                
        return tuple(outputs) 
    
    def get_source(self, name = None):
        "Return source code of this slide, markdwon or python or None if no source exists."
        if self._source['text']:
            return self._app.code.from_string(**self._source, name = name)
        else:
            return self._app.code.cast('No source found!\n',language = 'markdown')
    
    def _fix_css(self,props, this_slide=False):
        if not isinstance(props,dict):
            raise TypeError(f"expects dict, got {type(props)}")
        
        if not props:
            return ''
        
        props = {k:v for k,v in props.items() if k.lstrip(' ^<')} # Don't let user access top level to modify layout
        
        back_props = {}
        for k,v in props.copy().items():
            if not isinstance(v, dict):
                value = props.pop(k) # Remove all top level
                if 'background' in k:
                    back_props[k] = value # All background related things should go to Top
                else:
                    print(f"Ignored property {k!r}. At top level, only background properties are applied!")
                    if 'backdrop-filter' in k:
                        print("'backdrop-filter' is only useful in context of background image. Use `Slide.set_bg_image(src, filter)`.")
        
        _css = ''
        if back_props:
            _css += _build_css((f".{self._app.uid}.SlidesWrapper",), back_props)
        
        klass = f".{self._app.uid} .SlideArea"
        if this_slide:
            klass += f"^.n{self.number}"
        
        _css += ('\n' + _build_css((klass,), props))
        return self._app.html('style', _css)
    
    def set_css(self, this: dict=None, overall:dict=None):
        """
        Attributes at the root level of the dictionary are only picked if they are related to background. 
        You can add CSS classes by `Slide.set_css_classes`. Each call will reset previous call if props given explicitly, otherwise not.

        ::: note-tip
            See `Slides.css_syntax` for information on how to write CSS dictionary.
        """
        if this is not None:
            self._css = self._fix_css(this, this_slide=True)
        if overall is not None: # Avoid accidental re-write of overall CSS
            self.__class__._overall_css = self._fix_css(overall, this_slide=False)
        
        # See effect of changes
        if not self._app.this: # Otherwise it has side effects
            if self._app._current is self:
                self._app._update_tmp_output(self.animation, self.css) # force refresh CSS
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
    
    def set_bg_image(self, src=None, opacity=1, filter=None, contain=False):
        """Adds background image to this slide. `src` can be a url or a local image path or an svg str.
        filter is a CSS filter like blur(5px), grayscale() etc.
        
        ::: note-tip
            This function enables you to add a slide purely with an image, possibly with `opacity=1` and `contain = True`.
        """
        if not src: 
            self._app.widgets.htmls.bglayer.value = ""  # clear
            self._bg_image = ""
            return
        
        if (image := self._app.settings._resolve_img(src, '100%')):
            self._bg_image = f"""
            <style>
                {background_css(opacity= opacity, filter=filter, contain=contain)}
            </style>
            {image}"""
            self._app.widgets.htmls.bglayer.value = self._bg_image
            if not self._contents:
                self.set_css({}) # Remove empty CSS
            self._app.navigate_to(self.index) # Go there to see effects
    
    def _instance_animation(self,name):
        if not (name in styles.animations):
            KeyError(f'animation {name!r} not found. Use None to remove animation or one of {tuple(styles.animations.keys())}')
        return styles.animations[name].replace('.SlideBox',f'.{self._app.uid} .SlideBox')
            
    def set_animation(self, this=None, main = None,frame = None):
        "Set animation of this slide. Provide None if need to stop animation. Use main_all and frame to set animation to all slides."
        self.__class__._animations['main'] = '' if main is None else self._instance_animation(main)
        self.__class__._animations['frame'] = '' if frame is None else self._instance_animation(frame)
        self._animation = XTML('') if this is None else html('style',self._instance_animation(this))
        # See effect of changes
        if not self._app.this: # Otherwise it has side effects
            if self._app._current is self:
                self._app._update_tmp_output(self.animation, self.css) # force refresh
            else:
                self._app.navigate_to(self.index) # Go there to see effects

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

    for content in this._contents:
        if content.data.get('application/vnd.jupyter.widget-view+json',{}):
            this._has_widgets = True
            break # No need to check other widgets if one exists
        

    
        
    
    