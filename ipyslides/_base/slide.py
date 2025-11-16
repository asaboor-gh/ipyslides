"""Slide Object, should not be instantiated directly"""

import textwrap
from contextlib import contextmanager, suppress
from functools import wraps
from IPython.display import display
from IPython.utils.capture import RichOutput
from ipywidgets import HTML as ipwHTML

from . import styles
from ..utils import XTML, html, _styled_css, _build_css
from ..xmd import capture_content
from ..formatters import _Output, widget_from_data
from ._layout_css import background_css, get_unique_css_class
from .styles import collapse_node

class Vars:
    """Container for markdown slide variables, to see and update variables
    set on a slide or a group of slides.
    
    - `slides.s1.vars.update(name="New")` updates variable 'name' on slide 1 only
    - `slides.s2.vars.pop('age')` removes variable 'age' from slide 2 only, so it is picked from notebook scope
    - `slides.s3.vars.clear()` clears all variables set on slide 3 only, so they are picked from notebook scope
    - `slides[:].vars.update(theme='dark')` updates variable 'theme' on all slides
    - `slides[1:3].vars.pop('title')` removes variable 'title' from slide 1 and 2 only
    - `slides[0].vars.scope` see variables with scope set on slide 0
    
    ::: note-tip
        If variables are not set on slide, they are picked from notebook scope if `Auto Rebuild` is enabled in side panel.
    """
    def __init__(self, *slides):
        self._slides = slides
    
    def __repr__(self):
        scp = self.scope # could be tuple of dicts or single dict
        scps = (scp,) if isinstance(scp, dict) else scp
        head = "Scope       Vars\n=====       ====\n"
        return head + str.join(f"\n-----       ----\n", 
            ('\n'.join(f"{sc:<12}{value}" 
            for sc, value in scp.items()) for scp in scps)
        )
    
    @property
    def scope(self):
        "Returns variables info at different levels. 0: Slide, 1: Notebook scope, 2: Undefined."
        scopes = tuple({
            f'Slide{s.number}': tuple(s._md_vars), # only those set on slide
            'Notebook': tuple(v for v in s._req_vars if v in s._app._nb_vars), # only for this slide out of all
            'Undefined': tuple(v for v in s._req_vars if v not in s._app._nb_vars),
        } for s in self._slides if s._has_vars) # only markdown slides have variables, no need to make empty dict
        return scopes[0] if len(scopes) == 1 else scopes
    
    def update(self, **vars):
        """Update variables on a slide or group of slides. Unsed variables are ignored silently.
        
        - `slides.s1.vars.update(name="New Name", age=30)` updates variables 'name' and 'age' on slide 1 only.
        - `slides[:].vars.update(theme='dark')` updates variable 'theme' on all slides.
        - `slides[1:3].vars.update(title="New Title")` updates variable 'title' on slide 1 and 2 only.
        """
        for s in self._slides:
            s._md_vars.update({k:v for k,v in vars.items() if k in s._has_vars}) # only update required vars
            s._rebuild(True if len(self._slides) == 1 else False) # go there only if single slide
        
    __call__ = update # allow calling directly like slide.vars(...)
    
    def pop(self, *vars):
        "Remove variables from a slide or group of slides, so they are picked from higher scopes."
        for s in self._slides:
            for k in vars:
                s._md_vars.pop(k, None) # avoid key error if not present
            s._rebuild(True if len(self._slides) == 1 else False) # go there only if single slide
    
    def clear(self):
        "Clear all variables from a slide or group of slides, so they are picked from higher scopes."
        for s in self._slides:
            s._md_vars.clear()
            s._rebuild(True if len(self._slides) == 1 else False) # go there only if single slide

class Slide:
    "Slide object, should not be instantiated directly by user."
    _animations = {'main':'slide_h','page':'appear'}
    _overall_css = ''
    def __init__(self, app, number):
        self._widget = _Output(layout = dict(margin='auto',padding='16px', visibility='hidden')).add_class("SlideArea")
        self._app = app
            
        self._css = ''
        self._bg_ikws = {} # store background image keywords only to save memory
        self._number = number
        self._index = number if number == 0 else None # First slide should have index ready
        self._animation = None
        self._sec_id = f"s-{id(self)}" # should there alway wether a section or not
        self._md_vars = {} # store variables set by build/rebuild on this slide
        self._esc_vars = {} # store escaped variables for rebuilds form build content
        self._set_defaults()
        self.vars = Vars(self) # to access variables info and update them
        self._alt_print = ipwHTML(layout={'margin':'0'}).add_class('print-only') # alternate print content for this slide which is shown dynamically on slides

        if not self._contents: # show slide number hint there at first creation
            self.set_css({
                f' > .jp-OutputArea:empty:after': {
                    'content': f'"{self!r}"',
                    'color': 'var(--accent-color)',
                    'font-size': '2em',
                }
            }) # This will be removed when content is added or bg image is set

    
    def __setattr__(self, name: str, value):
        if not name.startswith('_') and hasattr(self, name):
            raise AttributeError(f"Can't reset attribute {name!r} on {self!r}")
        self.__dict__[name] = value
    
    def _set_defaults(self):
        for attr in ['_on_load', '_on_exit', '_fsep_legacy']:
            if hasattr(self, attr):
                delattr(self, attr) # reset these attributes if any
    
        self._notes = '' # Reset notes
        self._citations = {} # Reset citations
        self._section = None # Reset sec_key
        self._indexf = 0 # current frame index
        self._contents = [] # reset content to not be exportable 
        self._has_widgets = False # Update in _build_slide function
        self._has_vars = () # Update in _slide function for markdown slides only
        self._source = {'text': '', 'language': ''} # Should be update by Slides
        self._split_frames = True
        self._set_refs = True
        self._toc_args = () # empty by default
        self._widget.add_class(f"n{self.number}").add_class("base") # base is needed to distinguisg clones during printing where it is removed
        self._tcolors = {} # theme colors for this slide only
        self._fcss = ipwHTML(layout={"margin": "0","padding": "0","heigh": "0"}) # frame separator CSS
  
    def _set_source(self, text, language):
        "Set source code for this slide. If"
        self._source = {'text': text, 'language': language}
    
    def _reset_source(self):
        "Reset old source but leave markdown source for observing chnages"
        if not self._markdown:
            self._set_source("","")
        
    def _on_load_private(self, func):
        with self._app._hold_running(): # slides will not be running during switch, so make it safe
            with capture_content() as cap: # check if code is correct
                out = func(self)
                if callable(out):
                    out(self) # test call to raise error if any
            
            if cap.outputs or cap.stdout:
                raise Exception('func in on_load(func) should not print or display anything!')
            elif cap.stderr:
                raise RuntimeError(f'func in on_load(func) raised an error. See above traceback!')
        
        # This should be itemside the try/except block even after finally, if successful, only then assign it.
        self._on_load = func # This will be called in main app
    
    def _run_on_load(self):
        "Called when a slide is loaded into view. Use it to register notifications, auto toggle laser pointer etc."
        # To ensure previous _on_exit and the new _on_load are called properly, try finally
        try:
            if callable(getattr(self,'_on_exit', None)):
                self._on_exit(self) # call exit function of previous slide if any
        finally: 
            if callable(getattr(self,'_on_load', None)):
                self._on_exit = self._on_load(self) # will be called when this slide is exited
        
    def __repr__(self):
        return f'Slide(number = {self.number}, index = {self.index}, nf = {self.nf})'
    
    @contextmanager
    def _capture(self):
        "Capture output to this slide."
        self._app._next_number = self.number + 1
        self._app._slides_per_cell.append(self) # will be flushed at end of cell by post_run_cell event
        self._set_defaults() 

        with suppress(Exception): # register only in slides building, not other cells
            self._app._register_postrun_cell()

        self._app._auto_rebuild(None) # avoid while building slides to trigger other updates, but keep auto_rebuild state by None
        
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
            
            outputs = self._handle_fsep_legacy(captured.outputs) # handle old frame separators if any before skipping trails 
            # Skip trailing delimiters (PAGE or PART) from the end, or empty capture
            stop = len(outputs)
            for i in range(stop - 1, -1, -1):
                out = outputs[i]
                metadata = getattr(out, 'metadata', None)
                delim = metadata.get("DELIM", None) if metadata and isinstance(metadata, dict) else None
                if delim in ("PAGE", "PART") or set(out.data.keys()) == {'text/plain'}:  # Check if DELIM exists or empty content
                    stop -= 1
                    continue
                break # Found non-delimiter / non-empty content, stop here
            
            self._contents = captured.outputs[:stop]
            self._set_css_classes(remove = 'Out-Sync') # Now synced
            self.update_display(go_there=True)    

            if self._app.widgets.checks.focus.value: # User preference
                self._app._box.focus()
    
    def _handle_fsep_legacy(self, contents):
        if getattr(self, '_fsep_legacy', False):
            for c in contents:
                if isinstance(c.metadata, dict) and "DELIM" in c.metadata:
                    new_delim = "PAGE" if self._split_frames else "PART"
                    if c.metadata["DELIM"] != "ROW": # allow explict setting in fsep for backward compatibility, except rows
                        c.metadata["DELIM"] = new_delim
        return contents
        
    def update_display(self, go_there = True):
        "Update display of this slides including reloading citations, widgets etc."
        if go_there:
            self._app.navigate_to(self.index) # Go there to see effects
            self._widget.clear_output(wait = True) # Avoid flickering
            self._app._update_tmp_output(self.css) # Update corresponding CSS but avoid animation here
            self._set_css_classes('SlideArea', 'SlideArea') # Hard refresh, removes first and add later
        else:
            self._widget.clear_output(wait = True) # Clear, but don't go there
        
        # Need to know how many contents before user provide content
        with capture_content() as cap:
            # show speaker notes at top if any to grab immediate attention of speaker, will be shown only in PDF.
            self._speaker_notes(returns=False) # displays directly if any
            display(
                html('span', '', id = self._sec_id, css_class='Slide-UID'), # span to not occupy space, need to remove from frames later.
                self._alt_print, # alternate print content such as CSS and bg image
                self._fcss, # frame separator CSS
                metadata={'skip-export':'export html assign itself'}
            )  # to register section id in DOM
            
        self._offset = len(cap.outputs) # to offset frames later, store for export
                
        with self._widget:
            display(*cap.outputs) # speaker notes and metadata stuff as top
            for obj in self.contents:
                display(obj)
                if hasattr(obj, 'update_display'): 
                    obj.update_display() # UPDATE metadata objects like columns
                elif (w := widget_from_data(obj.data)): # Output on top or in children
                    [c.update_display() for c in getattr(w, 'children',[w]) if isinstance(c, _Output)]
            else: # On successful for loop, handle refs at end
                self._handle_refs()
            
        # after others to take everything into account
        self._reset_frames(offset = self._offset)
        self._app._update_toc()
    
    def _rebuild(self, go_there=False):
        if not self._markdown and go_there: # this avoid printing logs during bacth rebuilds
            return print("Exception: Can only rebuild slides created purely from markdown!")
        
        with self._app.navigate_back(self.index if go_there else None):
            self._app._slide(f'{self.number} -m', self._markdown)
            self._app._unregister_postrun_cell() # Avoid showing slides in this rebuild
            self._app._auto_rebuild('ondemand') # set back to previous state as capture removes it
    
    @property
    def _req_vars(self):
        return tuple([v for v in self._has_vars if not v in self._md_vars]) # only those not set on slide

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
                <a href="#{s._sec_id}" class="slide-link citelink">{s._section}</a>
            </li>''').format(**sec))
            for sec in items]
        
        title, highlight = self._toc_args or ('## Contents {.align-left}', False)
        css_class = 'toc-list toc-extra' if highlight else 'toc-list'
        ol = self._app.html('ol', items, style='', css_class=css_class)
        
        return RichOutput(
            data = {'text/plain': title,'text/html': self._app.html('div', [title, ol]).value},
            metadata = {"DataTOC": self.number}) # to access later
    

    def _reset_frames(self, offset=0):
        frames, contents = [], self.contents  # get once
        pages = [
            i for i, c in enumerate(contents) 
            if isinstance(c.metadata, dict) and 
            c.metadata.get("DELIM","") == "PAGE"
        ]  # find page delimiters
        
        if pages:
            pages = [{"head": pages[0] - 1, "start": p, "end": (pages[i+1] if (i+1) < len(pages) else len(contents)) - 1} for i, p in enumerate(pages)]
        else:
            pages = [{"head": -1, "start": 0, "end": len(contents) - 1}] # One page by default
        
        for ip, page in enumerate(pages):
            # Parts inside head only take effect on first frame
            start = 0 if ip == 0 and page["head"] > -1 else page["start"]
            if parts := self._resolve_parts(page, contents, range(start, page["end"] + 1)):
                parts[0]["anim"] = "next" # add animation flag to first part while navigative forward
                parts[-1]["anim"] = "prev" # add animation flag to last part while navigative backward
                frames.extend(parts)
            else:
                frames.append({**page, "anim": "both"}) # no parts, single frame, animate both ways
        
        # Add offeset to all indices to keep metadata available across all frames
        for i, frame in enumerate(frames):
            for key in ("head", "start", "part", "end"):
                if key in frame and isinstance(frame[key], int):
                    frames[i][key] += offset
        
        self._frame_idxs = frames if len(frames) > 1 else ()
        if self._frame_idxs:
            self.first_frame() # Bring up first frame to activate CSS
        elif hasattr(self, '_frame_idxs'): # from previous run may be
            del self._frame_idxs
        return frames
    
    def _resolve_parts(self, page, contents, indxs):
        frames = []
        
        for index in indxs:
            meta = contents[index].metadata
            if isinstance(meta, dict) and meta.get("DELIM", "") == "PART":
                meta_prev = contents[index - 1].metadata if index - 1 in indxs else {}
                meta_next = contents[index + 1].metadata if index + 1 in indxs else {}
                if not isinstance(meta_prev, dict): meta_prev = {} # insure dict type
                if not isinstance(meta_next, dict): meta_next = {} # insure dict type
                
                # Single column flattened after PART with its ROW delimiters
                if ("FLATCOL" in meta_next):
                    for i in range(index, index + meta_next["FLATCOL"]):
                        meta_row = contents[i].metadata if i in indxs else {}
                        if isinstance(meta_row, dict) and meta_row.get("DELIM", "") == "ROW":
                            meta_row["DELIM"] = "PART"  # change ROW to PART for frame handling
                
                # Check if PART is before COLUMNS to trigger increments
                if "COLUMNS" in meta_next:
                    # PART before COLUMNS - trigger column incremental
                    for part in contents[index + 1]._parts:
                        frames.append({**page, "part": index + 1, **part})
                else:
                    if meta_prev.get("DELIM") == "PART" or "COLUMNS" in meta_prev: 
                        continue  # Skip PART adjacent to PART and COLUMNS, already handled
                    frames.append({**page, "part": index}) # add stand alone PART normally
        
        if frames and frames[-1].get("part") != index: # Last index in range
            frames.append({**page, "part": index})  # only up to last part if something is left over
        return frames       
    
    @property
    def _fidxs(self): return getattr(self, '_frame_idxs', ())
    
    @property
    def nf(self):
        "Number of total frames."
        return len(self._fidxs) or 1 # each slide is single frame
    
    def _update_view(self, which):
        self._set_progress()
        # Determine if we should animate based on frame position and type
        frame = self._fidxs[self.indexf] if self._fidxs else {}
        anim = frame.get('anim', None)  # 'next', 'prev', or 'both'

        # Only animate on appropriate edges
        should_animate = anim == 'both' or anim == which
    
        if should_animate:
            if which == 'prev':
                self._app.widgets.slidebox.add_class('Prev')
            else:
                self._app.widgets.slidebox.remove_class('Prev')
            self._app._update_tmp_output(self.animation, self.css)
        else:
             self._app._update_tmp_output(self.css) # avoid animations between frames

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
        
    def _frame_css(self, index):
        if not self._fidxs:
            return ''
        
        if index < 0 or index >= self.nf:
            raise IndexError(f"Frame index {index} out of range for slide {self.number} with {self.nf} frames!")
        
        # Helper to hide/show elements with proper collapse
        def hide(b): 
            return {'^, ^ *': {'visibility': ('hidden' if b else 'inherit') + '!important'}}
        
        def collapse(b):
            return {**collapse_node(b), '@media print': hide(b)} # somehow needs invisibility in print, otherwise shows up

        # Build CSS to show only current frame's content
        frame = self._fidxs[index]
        css_rules = {}

        # head content visible everywhere
        head_end = frame.get("head", -1) + 1 # CSS nth-child is 1-indexed
        if head_end > 0:
            css_rules[f'^:nth-child(-n + {head_end})'] = hide(False)
        
        # Collapse nodes between head and start
        start = frame["start"] + 1
        if head_end > 0 and start > head_end + 1:
            css_rules[f'^:nth-child(n + {head_end + 1}):nth-child(-n + {start - 1})'] = collapse(True)
        
        # Collapse nodes after end
        end = frame["end"] + 1
        css_rules[f'^:nth-child(n + {end + 1})'] = collapse(True)

        # Handle PART incremental frames
        if "part" in frame:
            part_end = frame["part"] + 1
            css_rules[f'^:nth-child(n + {start}):nth-child(-n + {part_end})'] = hide(False)
            # Hide content after part
            if part_end < end:
                css_rules[f'^:nth-child(n + {part_end + 1}):nth-child(-n + {end})'] = hide(True)

            # Handle column incremental display
            if "col" in frame:
                col_idx = frame["col"]
                # Within the PART output (which contains COLUMNS), hide columns after current one
                col_sel = f'^:nth-child({part_end}) .columns.writer:first-of-type > div'
                css_rules[f'{col_sel}:nth-child(n + {col_idx + 2})'] = hide(True)

                if "row" in frame:
                    # Hide rows after current one in the current column
                    rows_hide = frame["row"] + 2 # +2 to start hiding after this row
                    css_rules[f'{col_sel}:nth-child({col_idx + 1}) > .jp-OutputArea > .jp-OutputArea-child:nth-child(n + {rows_hide})'] = hide(True)

        # Build final CSS with proper selector
        base_selector = f'^.n{self.number}.base > .jp-OutputArea > .jp-OutputArea-child'
        final_css = {base_selector: css_rules}
    
        return _styled_css(final_css).value
    
    def _show_frame(self, which):
        if self._fidxs:
            if (which == 'next') and ((self.indexf + 1) < self.nf):
                self._indexf += 1
            elif (which == 'prev') and ((self.indexf - 1) >= 0):
                self._indexf -= 1
            else:
                return False
            
            self._fcss.value = self._frame_css(self.indexf)
            self._update_view(which)
            return True # indicators required
        else:
            self._fcss.value = '' # clear frame css if any
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
    
    def _set_print_css(self, merge_frames = False):
        if merge_frames:
            self._fcss.value = '' # Just let free print go
        else: 
            self._fcss.value = self._frame_css(0) # set first frame for print mode without other actions
    
    def _set_progress(self):
        unit = 100/(self._app._iterable[-1].index or 1) # avoid zero division error or None
        value = round(unit * ((self.index or 0) - (self.nf - self.indexf - 1)/self.nf), 4)
        self._app.widgets._progbar.children[0].layout.width = f"{value}%"
        self._app.widgets._snum.description = f"{self._app.wprogress.value or ''}" # empty for zero
        self._app.widgets._snum.tooltip = f"{self._app._current}" # hint for current slide number

    def _handle_refs(self):
        if hasattr(self, '_refs'): # from some previous settings and change
            delattr(self, '_refs') # added later  only if need
        
        if all([self._citations, self._set_refs, self._app.cite_mode == 'footnote']): # don't do in inline mode
            if self.nf > 1:
                return self._app.notify(f"Slide {self.number} has frames, so refs should be set explicitly!", 5)
        
            self._refs = html('div', # need to store attribute for export
                sorted(self._citations.values(), key=lambda x: x._id), 
                css_class='Citations', style = '')
            self._refs.display()
    
    def _speaker_notes(self, returns=False):
        if self._notes:
            out = html('div', self._notes, 
                css_class='speaker-notes print-only'
            ) # hidden in slides always, shown in print/export if enabled
            return out.value if returns else display(out)
        return ''
    
    def show(self):
        "Show this slide in cell."
        out = _Output().add_class('SlideArea')
        with out:
            display(*self.contents)
        return display(out)
        
    def yoffset(self, value):
        "Set yoffset (in percent) for frames to have equal height in incremental content. Set global yoffset in layout settings."
        self._app.verify_running("yoffset can only be used inside slide constructor!")
        if (not isinstance(value, int)) or (value not in range(101)): 
            raise ValueError("yoffset value should be integer in units of percent betweem [0,100]!")
        
        self._app.html('style', 
            f'''.SlideArea.n{self.number}.n{self.number} > .jp-OutputArea {{
                top: {value}% !important;
                height: {100 - value}% !important; 
                margin-top: 0 !important;
            }}''' # each frames get own yoffset, margin-top 0 is important to force top to take effect
        ).display() # height is important to avoid spilling padding of SlideArea
        
    @property
    def notes(self): return self._notes
    
    @property
    def number(self): return self._number
    
    @property
    def css(self):
        "Returns CSS for this slide including overall CSS. Used while navigating to this slide."
        back = self._app.html('style',_build_css((f".{self._app.uid}.SlidesWrapper",), self._tcolors), css_class='jupyter-only') # don't mess export here
        return XTML(f'{back}{self._overall_css}\n{self._css}') # Add overall CSS but self._css should override it
    
    @property
    def index(self): return self._index

    @property
    def indexf(self):
        "Returns index of current displayed frame."
        return self._indexf if self._fidxs else 0
    
    @property
    def _markdown(self): 
        return self._source['text'] if self._source['language'] == 'markdown' else '' # Not All Slides have markdown
    
    @property
    def source(self):
        "Use get_source if you want to have a different name in top of block."
        return self.get_source(None)
    
    @property
    def animation(self):
        key = 'page' if self._fidxs else 'main'
        return html('style', self._animation or self._animations[key])
    
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
    
    def get_source(self, name = None, height='400px', **kwargs):
        "Return source code of this slide, markdwon or python or None if no source exists. kwargs are passed to `Slides.code.from_string`."
        if self._source['text']:
            return self._app.code.from_string(**self._source, name = name, height=height, **kwargs)
        else:
            return self._app.code.cast('No source found!\n',language = 'markdown')
    
    def _fix_css(self,props, colors, this_slide=False):
        if props is None:
            props = {} # may be colors only
        
        if not isinstance(props,dict):
            raise TypeError(f"expects dict, got {type(props)}")
        
        for k,v in props.items():
            if not isinstance(v, dict): # Don't let user modify layout with top level props
                raise TypeError("CSS properties are not allowed at slide level. "
                    f"If {k!r} meant to be a CSS selector, its value must be a dict, got {type(v)}")
            sels = k.split(',') # can be multiple selectors
            for s in sels:
                if not s.strip():
                    raise KeyError(f"Empty CSS selector found in {k!r}, perhaps due to extra comma?")
                if any([c in s for c in ['^', '<']]): # avoid layout modifications by user
                    raise KeyError(f"Tryign to access silde node with selector {s!r} in {k!r} is restricted!")
        
        _allowed = ['fg1', 'fg2', 'fg3', 'bg1', 'bg2', 'bg3', 'accent', 'pointer']
        
        for key, value in colors.items():
            if key not in _allowed:
                raise KeyError(f"Theme color key {key!r} not recognized. Allowed color keys are {_allowed}")
            if not isinstance(value, str):
                raise TypeError(f"Theme color value for key {key!r} should be str, got {type(value)}")
        
        self._tcolors = {f'--{k}-color':v for k,v in colors.items()} # reset to new colors each time
        props = {**self._tcolors, **props} # allow theme colors to be used directly per slide
        
        if not props:
            return ''
        
        klass = f".{self._app.uid} .SlideArea"
        if this_slide:
            klass += f".n{self.number}"
        return self._app.html('style', _build_css((klass,), props))
    
    def _set_alt_print(self):
        alt = f'{self._css}' # XTML or str
        if self._bg_ikws.get('src',None):
            alt += self._get_bg_image(get_unique_css_class()) # get bg image for print and dispaly behind slides
        self._alt_print.value = alt
    
    def set_css(self, this: dict=None, overall:dict=None, **theme_colors):
        """
        Set CSS on `this` slide or `overall` or both cases. 
        Each call will reset previous call if props given explicitly, otherwise not.

        ::: note-tip
            - See code`Slides.css_syntax` for information on how to write CSS dictionary.
            - You can set theme colors per slide. Accepted color keys are `fg1`, `fg2`, `fg3`, `bg1`, `bg2`, `bg3`, `accent` and `pointer`.
              This does not affect overall theme colors, for that use `Slides.settings.theme.colors`.
        """
        if theme_colors or this is not None:
            self._css = self._fix_css(this, theme_colors, this_slide=True) # theme colors for this slide only
            self._set_alt_print() # update alternate print content, we still need to dynamicallly set css for animations etc to work
        if overall is not None: # Avoid accidental re-write of overall CSS
            self.__class__._overall_css = self._fix_css(overall, {}, this_slide=False) # no theme colors for overall CSS
        
        # See effect of changes
        if not self._app.this: # Otherwise it has side effects
            if self._app._current is self:
                self._app._update_tmp_output(self.animation, self.css) # force refresh CSS
            else:
                self._app.navigate_to(self.index) # Go there to see effects automatically

    def _set_css_classes(self, add=None, remove=None):
        "Set CSS classes on this slide separated by space. classes are remove first and add after it."
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
    def _css_class(self):
        "Readonly dom classes on this slide sepaarated by space."
        return ' '.join(self._widget._dom_classes) # don't let things modify on orginal
    
    def set_bg_image(self, src=None, opacity=1, filter=None, contain=False):
        """Adds background image to this slide. `src` can be a url or a local image path or an svg str.
        filter is a CSS filter like blur(5px), grayscale() etc.
        
        ::: note-tip
            - This function enables you to add a slide purely with an image, possibly with `opacity=1` and `contain = True`.
            
        ::: note-warning
            - Too many slides withlarge background images may slow down the presentation/print and increase memory usage.
            - Setting background image on a slide with frames multiplies memory usage as each frame needs to render the background.
        """
        # We only store keywords to save memory and send image on javascript side for quick loading of images and printing
        self._bg_ikws = {
            'src': src, 'opacity': opacity, 'filter': filter, 'contain': contain, 
            '_id': f"bgi-uid{self.number}", # for unique filters and styles
        } # store for export etc
        
        if src is not None:
            self._set_alt_print() # update alternate print-only content
            if not self._contents:
                self.set_css({}) # Remove empty CSS
            self._app.widgets.iw.msg_tojs = 'SetIMG' # if it not happens to be there yet, will be done on swicthing slides
            self._app.navigate_to(self.index) # Go there to see effects
    
    def _get_bg_image(self, selector):
        if (image := self._app.settings._resolve_img(self._bg_ikws.get('src',None), '100%')):
            return f'''<div id="{self._bg_ikws['_id']}" class="BackLayer print-only">
            <style>
                {background_css(selector, **{k:v for k,v in self._bg_ikws.items() if k != 'src'})}
            </style>
            {image}
            </div>'''
        return ''
    
    def _instance_animation(self,name):
        if not (name in styles.animations):
            raise KeyError(f'animation {name!r} not found. Use None to remove animation or one of {tuple(styles.animations.keys())}')
        return styles.animations[name].replace('.SlideBox',f'.{self._app.uid} .SlideBox')
            
    def set_animation(self, this=None, main = None, page = None):
        "Set animation of this slide. Provide None if need to stop animation. Use `main` and `page` to set animation to all slides and pages."
        self.__class__._animations['main'] = '' if main is None else self._instance_animation(main)
        self.__class__._animations['page'] = '' if page is None else self._instance_animation(page)
        self._animation = '' if this is None else self._instance_animation(this)
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
        this._reset_source() # Reset old source but keep markdown for observing edits
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
        
class SlideGroup:
    """Proxy calls/attributes to multiple Slide instances.

    - Broadcasts Slide methods to all slides in group; returns None if all methods return None, else a tuple of results
    - Non-callable attributes return a tuple of values
    - Special attribute 'vars' returns a Vars proxy over the group
    - Behaves like a tuple for indexing/iteration; use .values to get underlying slides
    """
    def __init__(self, slides):
        self._slides = tuple(slides)

    def __repr__(self):
        ids = ','.join(str(s.number) for s in self._slides)
        return f"SlideGroup([{ids}])"

    def __len__(self): return len(self._slides)
    def __iter__(self): return iter(self._slides)
    def __contains__(self, item): return item in self._slides
    
    @property
    def values(self): 
        "Returns underlying Slide instances as a tuple."
        return self._slides

    def __getitem__(self, key):
        if isinstance(key, slice):
            return SlideGroup(self._slides[key])
        return self._slides[key]

    def __dir__(self):
        # expose public Slide attributes for completion
        slide_attrs = [n for n in dir(Slide) if not n.startswith('_')]
        return sorted(set(slide_attrs + ['vars', 'values'] + list(self.__dict__.keys())))

    def __getattr__(self, name: str):
        # Broadcast method or collect attribute across slides
        attr = getattr(Slide, name, None)
        if callable(attr):
            @wraps(attr)
            def _call(*args, **kwargs):
                results = tuple(getattr(s, name)(*args, **kwargs) for s in self._slides)
                return None if all(r is None for r in results) else results
            
            _call.__doc__ = f"Broadcast Slide.{name} to all slides in this group.\n" + (attr.__doc__ or '')
            return _call
        elif name == 'vars':
            return Vars(*self._slides)
        return tuple(getattr(s, name) for s in self._slides)
