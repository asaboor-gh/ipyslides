import sys, os, json, re, math, uuid, textwrap
from contextlib import contextmanager, suppress
from collections import namedtuple
from collections.abc import Iterable
from itertools import zip_longest
from typing import Union, overload
from functools import wraps
from pathlib import Path

from IPython import get_ipython
from IPython.display import display, clear_output

from .xmd import xmd, esc, fmt, get_main_ns, _matched_vars
from .writer import hold, write
from .formatters import bokeh2html, plt2html, serializer
from . import utils
from . import dashlab

_under_slides = {k: getattr(utils, k, None) for k in utils.__all__}

from ._base.widgets import TOCWidget, ipw # patched one
from ._base.base import BaseSlides
from ._base.intro import how_to_slide, get_logo
from ._base.slide import Slide, SlideGroup, _build_slide
from ._base.icons import Icon as _Icon
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
        self._id = math.nan
        self._slide._citations[key] = self  # Add to slide's citations

    def __repr__(self):
        return f"Citation(key = {self._key!r}, id = {self._id}, slide_number = {self._slide.number})"

    def __format__(self, spec):
        return f"{self.value:{spec}}"

    def _repr_html_(self):
        "HTML of this citation"
        return self.value

    @property
    def value(self):
        if _value := self._slide._app._citations.get(self._key, None):
            return f"""<div class = "citation" id="{self._key}">
                <a href="#{self._key}-back" class="citelink"> 
                    <span style="color:var(--accent-color);">{self._id}. </span>
                </a>{_value}</div>"""
        else:
            return self.inline_value # Just error message

    @property
    def inline_value(self):
        return self._slide._app._nocite(self._key)
        
class Singleton(type):
    # Before Slides calss was made singleton by creating a global instance. 
    # Got idea from PyCon2025 talk on Metaclasses Demystified by Jason C. McDonalad.
    # Now module can be imported in terminal as well, before it had to throw error
    _instance = None

    def __call__(cls, extensions=[], **settings): # I don't know what's magic is here!
        if cls._instance is None:
            cls._instance = super().__call__(extensions=extensions, **settings)
            cls._instance.fsep = fsep # frame separator is needed to be attached
        else: # reset these settings on previous instance on every call
            xmd.extensions.extend(extensions) 
            cls._instance.settings(**settings)
        return cls._instance


class Slides(BaseSlides,metaclass=Singleton):
    """Interactive Slides in IPython Notebook. Only one instance can exist. `settings` 
    are passed to code`Slides.settings()` if you like to set during initialization. You
    can also edit file .ipyslides-assets/settings.json to make settings persistent across sessions
    and load/sync them via GUI in sidepanel.
    
    To suppress unwanted print from other libraries/functions, use:
    ```python
    with slides.suppress_stdout():
        some_function_that_prints() # This will not be printed
        print('This will not be printed either')
        display('Something') # This will be printed
    ```
    ::: note-info
        The traitlets callables under settings returns settings back to enable chaining 
        without extra typing, like code`Slides.settings.logo().layout()...` .
    
    ::: note-tip
        - Use code`Slides.instance()` class method to keep older settings. code`Slides()` apply default settings every time.
        - Run code`slides.demo()` to see a demo of some features.
        - Run code`slides.docs()` to see documentation.
        - Instructions in left settings panel are always on your fingertips.
        - Creating slides in a batch using `Slides.create` is much faster than adding them one by one.
        - In JupyterLab, right click on the slides and select `Create New View for Output` for optimized display.
        - To jump to source cell and back to slides by clicking buttons, set `Windowing mode` in Notebook settings to `defer` or `none`.
        - See code`Slides.xmd.syntax` for extended markdown syntax, especially variables formatting.
        - Inside python scripts or for encapsulation, use `Slides.fmt` to pick variables from local scope.
    
    ::: note-info
        - `Slides` can be indexed same way as list for sorted final indices. 
        - For indexing slides with given number, use comma as code`Slides[number,] → Slide` 
        - Access many via list as code`Slides[[n1,n2,..]] → SlideGroup` or slice as code`Slides[start:stop:step] → SlideGroup`.
        - `SlideGroup` can be used to apply batch operations on many slides at once, e.g. code`Slides[[1,3,5]].vars.update(name='Alice')` or code`Slides[2:5].set_css(...)`.
        - Use indexing with given number to apply persistent effects such as CSS or acess via attributes such as 
          code`Slides.s0`, code`Slides.s1` etc. for existing slides, so `Slides.s10 == Slides[10,]` if slide with number 10 exists.
    """

    @classmethod
    def instance(cls):
        "Access current instnace without changing the settings."
        return cls._instance

    def __init__(self, extensions=[],**settings):
        super().__init__()  # start Base class in start
        self.shell = SHELL

        for k, v in _under_slides.items():  # Make All methods available in slides
            setattr(self, k, v)

        self.get_child_dir('.ipyslides-assets', create = True) # It should be present/created to load resources     
        self.settings(**settings)
        xmd.extensions.extend(extensions) # globally once
 
        self.plt2html   = plt2html
        self.bokeh2html = bokeh2html
        self.get_logo   = get_logo
        self.icon       = _Icon  # Icon is useful to add many places
        self.dl         = dashlab # whole dashlab module
        self.write      = write
        self.hold       = hold  # Hold display of a function until it is captured in a column of `Slides.write`
        self.xmd        = xmd  # Extended markdown parser
        self.fmt        = fmt # So important for flexibility
        self.esc        = esc # lazy escape for variables in markdown
        self.serializer = serializer  # Serialize IPython objects to HTML

        with suppress(Exception):  # Avoid error when using setuptools to install
            self.shell.register_magic_function(self._slide, magic_kind="cell", magic_name="slide")
            self.shell.register_magic_function(self.__xmd, magic_kind="line_cell", magic_name="xmd")

        self._cite_mode = 'footnote'

        self._slides_dict =  {} # Initialize slide dictionary, updated by user or by _setup.
        self._iterable = []  # self._collect_slides() # Collect internally
        self._running_slide = (
            None  # For Notes, citations etc in markdown, controlled in Slide class
        )
        self._next_number = 0  # Auto numbering of slides should be only in python scripts
        self._citations = {}  # Initialize citations dictionary
        self._slides_per_cell = [] # all buidling slides in a cell will be added while capture, and removed with post run cell
        self._last_vars = {} # will be handled by a post run cell

        self._set_saved_citations() # from previous session
        self.wprogress = self.widgets.sliders.progress
        self.wprogress.observe(self._update_content, names=["value"])
        self.widgets.buttons.refresh.on_click(self._force_update)
        self.widgets.buttons.source.on_click(self._jump_to_source_cell)
        self.widgets.checks.rebuild.observe(self._auto_rebuild, names=['value'])

        # All Box of Slides
        self._box = self.widgets.mainbox.add_class(self.uid)
        self._setup()  # Load some initial data and fixing
        
        # setup toc widget after all attributes are set
        self._toc_widget = TOCWidget(self)
    
    def __setattr__(self, name: str, value): # Don't raise error
        if not name.startswith('_') and hasattr(self, name):
            raise AttributeError(f"Can't reset attribute {name!r} on {self!r}")
        self.__dict__[name] = value
    
    def __getattr__(self, name: str) -> Slide:
        if name.startswith('s') and name[1:].isdigit(): # s0, s1, s2...
            number = int(name[1:])
            if number in self._slides_dict:
                return self._slides_dict[number]
            raise KeyError(f"Slide with number {number} was never created or may be deleted!")
        return super().__getattribute__(name)
    
    def __dir__(self):
        # To show s0, s1, s2... for existing slides in auto-completion
        slide_attrs = [f's{k}' for k in self._slides_dict]
        return sorted(super().__dir__() + slide_attrs)
        
    @contextmanager
    def _set_running(self, slide):
        "Context manager to set running slide and turns back to previous."
        if slide and not isinstance(
            slide, Slide
        ):  # None is acceptable to hold running slide in other function
            raise TypeError(f"slide must be None or Slide, got {type(slide)}")

        old = self.this
        self._running_slide = slide
        try:
            yield
        finally:
            self._running_slide = old

    @contextmanager
    def _hold_running(self):
        "Context manager to pause running slide and restore it after"
        with self._set_running(None):
            yield

    def _run_cell(self, cell, **kwargs):
        """Run cell and return result. Use this instead of IPython's run_cell for extra controls."""
        spc = list(self._slides_per_cell) # make copy
        self._unregister_postrun_cell() # important to avoid putting contnet on slides
        self.shell.run_cell(cell, **kwargs)
        
        if self.this: # there was post_run_cell under building slides
            self._slides_per_cell.extend(spc) # was cleared above in unregister
            self._register_postrun_cell() # should be back
    
    @property
    def _nb_vars(self): # variables from notebook scope, not set by build/rebuild
        # Keep this as property, as any pop out from rebuild will be picked at latest
        keys = [k for s in self.markdown_slides for k in s._req_vars] # All markdown slides vars names
        user_ns = get_main_ns() # works both in top running module and notebook
        return {k: user_ns[k] for k in keys if k in user_ns} # avoid undefined variables
    
    def _auto_rebuild(self, change):
        # Enable/Disable automatic rebuilding of markdown slides after each cell execution to update variables.
        with suppress(Exception): # Remove previous on each if exits
            self.shell.events.unregister("post_run_cell", self._md_post_run_cell)
            self.notify('x') # to remove previous toast if any
            
        # None is used to keep previous state but remove handler in slide capture
        if change is not None and self.widgets.checks.rebuild.value: # don't employ change, we need to call it independently
            self.shell.events.register("post_run_cell", self._md_post_run_cell)
            if change != 'ondemand': # only when user checked toggle
                self.notify("Auto rebuild of markdown slides is enabled for notebook-level variables update!", 10)
    
    def _md_post_run_cell(self, result):
        if result.error_before_exec or result.error_in_exec:
            return  # Do not proceed for side effects
        
        new_vars = self._nb_vars # latest
        diff = {key:value for key, value in new_vars.items() if not (key in self._last_vars)} # diff operator ^ can only work for hashable types
        diff.update({key:value for key, value in new_vars.items() if value != self._last_vars.get(key,None)}) 
        if diff:
            self._last_vars.update(new_vars) # update to compare next time
            with self.navigate_back():
                for slide in self.markdown_slides: 
                    if diff.keys() & slide._req_vars: # Intersection of keys
                        slide._rebuild(True)
    
    def _post_run_cell(self, result):
        self._auto_rebuild('ondemand') # keep auto_rebuild state, but register if needed
        with suppress(Exception):
            self.shell.events.unregister("post_run_cell", self._post_run_cell) # it will be initialized from next building slides
        if result.error_before_exec or result.error_in_exec:
            return  # Do not display if there is an error

        if self._slides_per_cell:
            self.navigate_to(self._slides_per_cell[0].index) # more logical to go in start slide rather end

            scroll_btn = ipw.Button(description= 'Go to Slides', icon= 'scroll', layout={'height':'0px'}).add_class('Scroll-Btn') # height later handled by hover
            scroll_btn.on_click(lambda btn: self._box.focus()) # only need to go there, no slide switching 
            
            for slide in self._slides_per_cell:
                slide._scroll_btn = scroll_btn
        
            self._slides_per_cell.clear() # empty it
            return display(scroll_btn)
    
    def _unregister_postrun_cell(self):
        self._slides_per_cell.clear() # Must to let user jump on first slide run to be in correct place
        with suppress(Exception): 
            self.shell.events.unregister("post_run_cell", self._post_run_cell)
    
    def _register_postrun_cell(self):
        with suppress(Exception): 
            self.shell.events.register("post_run_cell", self._post_run_cell)
        
    def _jump_to_source_cell(self, btn):
        if hasattr(self._current, '_scroll_btn'):
            toast = ""
            self._current._scroll_btn.focus()
        else:
            toast = 'No source cell found!'
        
        vars_info = utils.code(repr(self._current.vars)).inline.value if self._current._has_vars else ""
        self.notify(toast + (vars_info or ""), 10 if vars_info else 2) #  seconds to show message

    def _setup(self):
        if not self._slides_dict:  # prevent overwrite
            self._add_clean_title()

    def __repr__(self):
        repr_all = ",\n    ".join(repr(s) for s in self._iterable)
        return f"Slides(\n    {repr_all}\n)"

    def __iter__(self):  # This is must have for exporting
        return iter(self._iterable)

    def __len__(self):
        return len(self._iterable)
    
    def __contains__(self, key): 
        return key in self._slides_dict
    
    # Auto-completion after indexing like Slides[2].<Tab> exposes attributes of Slide
    @overload
    def __getitem__(self, key: int) -> Slide: ...
    @overload
    def __getitem__(self, key: tuple[int]) -> Slide: ...
    @overload
    def __getitem__(self, key: list[int]) -> SlideGroup: ...
    @overload
    def __getitem__(self, key: slice) -> SlideGroup: ...
    
    def __getitem__(self, key) -> Union[Slide, SlideGroup]:
        "Get slide by index or slice of computed index. Use [number,] or [[n1,n2,..]] to access slides by number they were created with."
        if isinstance(key, int):
            return self._iterable[key]
        elif isinstance(key, slice):
            return SlideGroup(self._iterable[key.start : key.stop : key.step])
        elif isinstance(key, tuple): # as [1,] or [(1,)]
            if len(key) != 1:
                raise ValueError(f"Wrong indexing {key} found, use [number,] to access single slide by given number, or [[n1,n2,...]] for many slides!")
            return self._slides_dict[key[0]]
        elif isinstance(key, list):
            if not all([isinstance(k,int) for k in key]):
                raise TypeError(f"All indexers in {key} should be integers!")
            
            items = []
            for k in key:
                if k in self._slides_dict:
                    items.append(self._slides_dict[k])
                else:
                    raise KeyError(f"Slide with number {k} was never created or may be deleted!")
            
            return SlideGroup(items)

        raise KeyError(
            f"A slide could be accessed by index or slice, got {type(key)},\n"
            "Use `Slides[number,] → Slide` or `Slides[[n1, n2,..]] → tuple[Slide]` to access slides by number they were created with."
        )
    
    def __del__(self):
        for k, v in globals():
            if isinstance(v, Slides):
                del globals()[k]

        for k, v in locals():
            if isinstance(v, Slides):
                del locals()[k]

    def navigate_to(self, index):
        "Programatically Navigate to slide by index, if possible."
        if isinstance(index, int):
            self.wprogress.value = index

    @contextmanager
    def navigate_back(self, index=None):
        "Bring slides position back to where it was (or optionally at index) after performing operations."
        old_index = index or int(self.wprogress.value)
        try:
            yield
        finally:
            self.navigate_to(old_index)

    @property
    def version(self):
        "Get Slides version."
        return __version__

    @version.setter
    def version(self, value):
        raise AttributeError("Cannot set version.")
    
    @property
    def _assets_dir(self):
        "Get assets directoty."
        return utils.get_child_dir('.ipyslides-assets', create = True)
    
    @property
    def clips_dir(self):
        "Get path to directory where clips are saved. If not exists, created!"
        return utils.get_clips_dir()
    
    @property
    def cite_mode(self):
        return self._cite_mode

    @property
    def _current(self):
        if not self._iterable: # not collected yet
            return self._slides_dict.get(0, None)
        return self._iterable[self.wprogress.value]

    @property
    def this(self):
        "Access slide currently being built. Useful for operations like set_css etc."
        return self._running_slide

    @property
    def draw_button(self):
        "Get a button to reveal drawing board easily from slide. Like it lets you remeber to draw now."
        return self.widgets.toggles.draw
    
    @property
    def toc_widget(self):
        "Get table of contents widget. It can be exported to HTML as well. Normally use Slides.toc()."
        return self._toc_widget

    def verify_running(self, error_msg=""):
        "Verify if slide is being built, otherwise raise error."
        if self.this is None:
            raise RuntimeError(
                error_msg or "This operation is only allowed under slide constructor."
            )

    def _add_clean_title(self):
        with _build_slide(self, 0):
            self.stack([
                self.styled("color['var(--accent-color)']`Replace this with creating a slide with number` alert`0`",
                    padding = "8em 8px",
                ), 
                '', # empty column for space 🤣
                how_to_slide],sizes=[14,1, 85]).display()
        
        self._unregister_postrun_cell() # This also clears slides per cell
        self.settings.footer.text = self.get_logo('14px') + ' IPySlides'

    def clear(self):
        "Clear all slides."
        self._slides_dict = {}  # Clear slides
        self._next_number = 0  # Reset slide number to 0, because user will overwrite title page.
        self._add_clean_title()  # Add clean title page without messing with resources.

    def _cite(self, keys):
        self.verify_running("Citations can be added only inside a slide constructor!")
        citeds = [self._cite_key(key.strip()) for key in keys.split(',')] # avoid whitespaces around key

        if self.cite_mode == "inline":
            return '<br/>'.join(citeds)
        
        return '<sup>,</sup>'.join(citeds) 

    def _cite_key(self, key):
        """Use markdown syntax cite`key` to add citations since output has to be inline. 
        Citations corresponding to keys used can be added by ` Slides.set_citations ` method.
        """
        cited = _Citation(slide=self.this, key=key)

        if self.cite_mode == "inline":
            return cited.inline_value  # Just write here
        else: # Set _id for citation in footnote mode
            cited._id = list(self.this._citations.keys()).index(key) + 1 # Get index of key from unsorted ones

        # Return string otherwise will be on different place, avoid newline here
        return f'<a href="#{key}" class="citelink"><sup id ="{key}-back" style="color:var(--accent-color) !important;">{cited._id}</sup></a>'
    
    def _nocite(self, key): # @key! without adding to citations
        if key in self._citations:
            return utils.textbox(self._citations[key].partition("<p>")[-1].rpartition("</p>")[0],
            left="initial",top="initial").value
        return utils.error("KeyError",f"Set value for cited key {key!r} and build slide again!").value

    
    def _set_ctns(self, d):
        # Here other formatting does not work for citations
        new_citations = {k: self.xmd(v, returns = True) for k, v in d.items()}
        added = set(new_citations) - set(self._citations)
        removed = set(self._citations) - set(new_citations)
        changed = {k for k in (set(new_citations) & set(self._citations)) if self._citations[k] != new_citations[k]}
        if changed := (added | removed | changed):
            self._citations = new_citations
            self._set_unsynced(changed) # will go synced after rerun
    
    def _set_unsynced(self, changed):
        if changed is True:
            req_update = self.cited_slides
        elif isinstance(changed,set):
            req_update = [s for s in self.cited_slides if changed & set(s._citations)]
        else:
            raise TypeError(f"changed should be True or set of keys, got {type(changed)}")
        
        for slide in req_update:
            if slide._markdown:
                slide._rebuild(go_there=False)
            else:
                slide._set_css_classes(add = 'Out-Sync') # will go synced after rerun

    def set_citations(self, data, mode='footnote'):
        r"""Set citations from dictionary or string with content like `\@key: citation value` on their own lines, 
        key should be cited in markdown as cite\`key\` / \@key, optionally comma separated keys.
        `mode` for citations should be one of ['inline', 'footnote']. Number of columns in citations are determined by code`Slides.settings.layout(..., ncol_refs=N)`.

        ```python
        set_citations({"key1":"value1","key2":"value2"})
        
        set_citations('''
        @key1: citation for key1
        @key2: citation for key2
        ''')

        with open("citations_file.md","r") as f:
            set_citations(f.read()) # same content as string above

        with open("citations_file.json","r") as f:
            set_citations(json.load(f))   
        ```

        ::: note
            - You should set citations in start if using voila or python script. Setting in start in notebook is useful as well.
            - Citations are replaced with new ones, so latest use of this function reprsents available citations.
            - Makrdown equivalent of this function is a citation block only supported in `Slides.sync_with_file`'s context.
        """
        if isinstance(data, dict):
            self._set_ctns(data)
        elif isinstance(data, str):
            self._set_ctns({
                k.strip() : v.strip() 
                for k,v in re.findall(r'^@(.+?):\s*(.*?)(?=^@|\Z)', textwrap.dedent(data), flags=re.MULTILINE | re.DOTALL)
            })
        else:
            raise TypeError(f"data should be a dict or string content (including read from file), got {type(data)}")
    
        # Update mode and display after setting citations
        if mode not in ["inline", "footnote"]:
            raise ValueError(f'citation mode must be one of "inline" or "footnote" but got {mode}')
        
        if self._cite_mode != mode:
            self._cite_mode = mode # Update first as they need in display update
            self._set_unsynced(True) # will go synced after rerun 
        
        # Finally write resources to file in assets
        with self.set_dir(self._assets_dir):
            with open(".citations.json", "w", encoding="utf-8") as f:
                json.dump(self._citations, f, indent=4)


    def _set_saved_citations(self):
        "Load resources from file if present silently"
        with self.set_dir(self._assets_dir):  # Set assets directory
            if os.path.isfile("citations.json"): # legacy filename, want to somehow depict it private with .
                os.rename("citations.json",".citations.json")
        
            if (path := Path(".citations.json")).exists():
                self._set_ctns(json.loads(path.read_text()))
            
    @property
    def cited_slides(self) -> SlideGroup:
        "SlideGroup of all slides which have citations. See also `markdown_slides`."
        return SlideGroup([s for s in self._iterable if s._citations])
    
    @property
    def markdown_slides(self) -> SlideGroup:
        "SlideGroup of all slides built from markdown. See also `cited_slides`."
        return SlideGroup([s for s in self._iterable if s._markdown])

    def section(self, text):
        """Add section key to presentation that will appear in table of contents. In markdown, use section`content` syntax.
        Sections can be written as table of contents.
        """
        self.verify_running("Sections can be added only inside a slide constructor!")

        self.this._section = text  # assign before updating toc
        
        for s in self[:]:
            if s._toc_args and s != self.this: 
                s.update_display(go_there=False)
 
    def toc(self, title='## Contents {.align-left}', highlight = False):
        "You can also use markdown syntax to add it like toc`title` or toc[highlight=True]`title` or toc[True]`title`, and `Slides.toc_widget as well."
        self.verify_running("toc can only be added under slides constructor!")
        self.this._toc_args = (title, highlight)
        display(self.this._reset_toc()) # Must to have metadata there
    
    def refs(self, ncol=2, *keys):
        r"""Displays references when in footnote mode (explicit use on slides with frames required). 
        References are set in `Slides.set_citations`. In markdown, use refs\`ncol\` syntax.
        You can optionally provide keys to show only specific citations at a place, which is useful on slides with frames.
        """
        self.verify_running("refs can only be added under slides constructor!")
        self.this._set_refs = False # already added here
        objs = self.this._citations.values() if not keys else [v for k,v in self.this._citations.items() if k in keys]
        if self._cite_mode == "footnote":
            _cits = ''.join(v.value for v in sorted(objs, key=lambda x: x._id))
            return self.html("div", _cits, css_class = 'Citations text-small', 
                style = f'column-count: {ncol} !important;')

    def link(self, label, back_label=None, icon=None, back_icon=None):
        r"""Create a link to jump to another slide. Use `label` for link text 
        and `back_label` for the  optional text on the target slide if need to jump back.

        - Use `link.origin` to create a link to jump to target slide where `link.target` is placed.
        - If back_label was provided, `link.target` will be able to jump back to the `link.origin`.
        - In makdown, you can use created link as variables like `\%{link.origin}` and `\%{link.target}` to display links.
        - Use similar links in markdown as `<link:[unique id here]:origin label>` and `<link:[unique id here same as origin]:target [back_label,optional]>`.
        - In markdown, icons can be passed in label as alert`"fa\`arrow\` label text"`.
        """
        anchor_id = uuid.uuid4().hex  # Generate unique anchor id
        
        origin = self.html('a',
            (f' <i class="fa fa-{icon}"></i>' if icon else '') + label,
            id=f"origin-{anchor_id}", 
            href = f"#target-{anchor_id}", 
            css_class="slide-link"
        )

        target = self.html('a',
            (f' <i class="fa fa-{back_icon}"></i>' if back_icon else '') + (back_label or ''), 
            id=f"target-{anchor_id}", 
            href = f"#origin-{anchor_id}", 
            css_class="slide-link"
        )
        return namedtuple("Link", ["origin", "target"])(origin, target)

    def show(self):
        "Display Slides."
        return self._ipython_display_()

    def _ipython_display_(self):
        "Auto display when self is on last line of a cell"
        if not self.is_jupyter_session():
            raise Exception("Python/IPython REPL cannot show slides. Use IPython notebook instead.")

        clear_output(wait = True) # Avoids jump buttons and other things in same cell created by scripts producing slides
        self._unregister_postrun_cell() # no need to scroll button where showing itself
        self._auto_rebuild('ondemand') # keep auto_rebuild state, but register if needed
        self._force_update()  # Update before displaying app, some contents get lost
        self.settings._update_theme() # force it, sometimes Inherit theme don't update
        with self._loading_splash(None, self.get_logo('48px', 'IPySlides')): # need this to avoid color flicker in start
            display(ipw.HBox([self.widgets.mainbox]).add_class("SlidesContainer"))  # Display slides within another box

    def close_view(self):
        "Close slides/cell view, but keep slides in memory than can be shown again."
        self.widgets.iw.msg_tojs = "CloseView"

    @property
    def _sectionindex(self):
        "Get current section index"
        if self._current._section:
            return self._current.index
        else:
            idxs = [
                s.index for s in self[:self._current.index] if s._section
            ]  # Get all section indexes before current slide
            return idxs[-1] if idxs else 0  # Get last section index

    def _switch_slide(self, old_index, new_index):
        self.notify(self._sectionindex)
        if inds := [opt.ti for opt in self._toc_widget.options if opt.si == self._sectionindex]:
            self._toc_widget.send({'active' : inds[0]}) # Update toc widget focus without changing index
        
        slide = self._iterable[new_index]
        self._update_tmp_output(slide.animation, slide.css)
        
        # Do this here, not in navigation module, as slider can jump to any value
        if not slide._fidxs:
            slide._set_progress()
        else:
            slide.first_frame() if new_index > old_index else slide.last_frame()

        if (old_index + 1) > len(self.widgets.slidebox.children):
            old_index = new_index  # Just safe

        self.widgets.slidebox.children[old_index].layout.visibility = 'hidden'
        self.widgets.slidebox.children[new_index].layout.visibility = 'visible'
        # Above code can be enforced if does not work in multiwindows
        self.widgets.slidebox.children[old_index].remove_class("ShowSlide").add_class("HideSlide")
        self.widgets.slidebox.children[new_index].add_class("ShowSlide").remove_class("HideSlide")
        self.widgets.iw.msg_tojs = 'SwitchView'

    def _update_content(self, change):
        if self.wprogress.value == 0:  # First slide
            self._box.add_class("InView-Title").remove_class("InView-Last")
        elif self.wprogress.value == self.wprogress.max:  # Last slide
            self._box.add_class("InView-Last").remove_class("InView-Title")
        else:
            self._box.remove_class("InView-Title").remove_class("InView-Last")

        if self._iterable and change:
            self.notes.display()  # Display notes first
            self.notify('x') # clear notification
            self._switch_slide(old_index=change["old"], new_index=change["new"])
            self._current._run_on_load()  # Run on_load setup after switching slide, it updates footer as well

    def refresh(self):
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self._iterable = self._collect_slides()  # would be at least one title slide
        if not self._iterable:
            self.wprogress.max = 0
            self.widgets.slidebox.children = []  # Clear older slides
            return None
        
        old = self.wprogress.value
        self.wprogress.max = len(self._iterable) - 1  # Progressbar limit
        self.wprogress.value = min(old, self.wprogress.max) # avoid jumping back to title each time

        # Update Slides
        self.widgets.slidebox.children = [it._widget for it in self._iterable]
        for i, s in enumerate(self._iterable):
            s._index = i  # Update index

        self._update_toc()  # Update table of content if any
        self._force_update() # refresh causes lose widgets sometimes

        if not any(['ShowSlide' in c._dom_classes for c in self.widgets.slidebox.children]):
            self.widgets.slidebox.children[0].add_class('ShowSlide')

        self.widgets.iw.msg_tojs = 'SwitchView' # Trigger view
    
    def _fix_slide_number(self, number):
        "For this, slide_number in function is set to be position-only argement."
        if str(number) != '-1': # handle %%slide -1 togther with others
            return number
        
        with suppress(AttributeError): # some kernels may not implement changing cell code on fly
            code = self.shell.kernel.get_parent().get('content',{}).get('code','')
            p = r"\s*?\(\s*?-\s*?1" # call pattern in any way with space between (, -, 1 and on next line, but minimal matches due to ?
            matches = re.findall(rf"(\%\%slide\s+-1)|(build{p})|(sync_with_file{p})", code)
            number = int(self._next_number) # don't use same attribute, that will be updated too
            if matches:
                if len(matches) > 1:
                    number -= (len(matches) - 1) # same cell multislides create a jump in numbering, subtract that

                for ms in matches:
                    for m in ms:
                        if m:
                            code = code.replace(m, f"{m[:m.index('-')]}{number}",1) # replace before -, could be -<spaces>1
                            number += 1
                self.shell.set_next_input(code, True) # for notebook
    
        return self._next_number # for python file as well as first run of cell in notebook

    # defining magics and context managers
    def _slide(self, line, cell):
        """Capture content of a cell as `slide`.
            ---------------- Cell ----------------
            %%slide 1
            #python code here

        You can use extended markdown to create slides
            ---------------- Cell ----------------
            %%slide 2 -m
            Everything here and below is treated as markdown, not python code.
            ::: note-info
                Find special syntax to be used in markdown by `Slides.xmd.syntax`.
        ::: note
            - If Markdown is separated by two dashes (--) on it's own line, multiple frames are created and shown incrementally.
            - In case of frames, you can add %++ (percent plus plus) in the content to add frames incrementally.
            - Frames separator (--) just after `multicol` creates incremental columns.
            - Use `%%slide -1` to enable auto slide numbering. Other cell code is preserved.
            - 

        """
        line = line.strip().split()  # VSCode bug to inclue \r in line
        line[0] = str(self._fix_slide_number(line[0])) # fix inplace as string here

        if line and not line[0].isnumeric():
            raise TypeError(
                f"You should use %%slide integer >= 1 -m(optional), got {line}"
            )

        slide_number = int(line[0])  # First argument is slide number

        if "-m" in line[1:]:
            if any(map(lambda v: re.search(r"^\s*--\s*$",v, flags=re.DOTALL | re.MULTILINE), 
                (re.findall(r'```multicol(.*?)\n```', cell, flags=re.DOTALL | re.MULTILINE) or [''])
                )):
                raise ValueError("frame separator -- cannot be used inside multicol!")
            
            frames = re.split(r"^\s*--\s*$", cell, flags=re.DOTALL | re.MULTILINE)  # Split on -- or --\s+
            edit_idx = 0

            with _build_slide(self, slide_number) as s:
                prames = re.split(r"^\s*--\s*$", s._markdown, flags=re.DOTALL | re.MULTILINE)   
                # Update source beofore parsing content to make it available for variable testing
                s._set_source(cell, "markdown") # set source before running to have it available for user
                vars = _matched_vars(cell) # update has_vars before running to have ready for auto rebuild
                stored = {**esc._store, **s._esc_vars} # keep previous stored variables, first time come only from esc._store
                s._has_vars = tuple([v for v in vars if v not in stored]) # esc is encapsulated by design
                s._esc_vars = {v: stored[v] for v in vars if v in stored} # store for rebuilds internally
                
                for idx, (frm, prm) in enumerate(zip_longest(frames, prames, fillvalue='')):
                    if '%++' in frm: # remove %++ from here, but stays in source above for user reference
                        frm = frm.replace('%++','').strip() # remove that empty line too
                        s.stack_frames(True)
                    
                    self.xmd(frm, returns = False) # parse and display content
                    
                    if len(frames) > 1:
                        self.fsep() # should not be before, needs at least one thing there
                    
                    if prm != frm: 
                        edit_idx = idx
                        if self.this.stacked and ('```multicol' in frm): # show all columns if edit is inside multicol
                            edit_idx += (len(re.findall(r'^\+\+\+$|^\+\+\+\s+$',frm, flags=re.DOTALL | re.MULTILINE)) + 1)
            
            s.first_frame() # be at start first
            for _ in range(edit_idx): 
                s.next_frame() # go at latest edit

        else:  # Run even if already exists as it is user choice in Notebook, unlike markdown which loads from file
            with _build_slide(self, slide_number) as s:
                s._set_source(cell, "python")  # Update cell source beofore running
                self._run_cell(cell)  #

    def __xmd(self, line, cell=None):
        r"""Turns to cell magics `%%xmd` and line magic `%xmd` to display extended markdown.
        Can use in place of `write` commnad for strings.
        When using `%xmd`, you can pass variables as \%{var} (slash for escap here) which will substitute HTML representation
        if no other formatting specified.
        Inline columns are supported with stack`C1 || C2` syntax."""
        if cell is None:
            return xmd(line, returns = False)
        else:
            return xmd(cell, returns = False)

    @contextmanager
    def _loading_splash(self, btn, extra = None):
        if btn:
            if btn is self.widgets.buttons.refresh: btn.icon = "minus"
            btn.disabled = True  # Avoid multiple clicks
        self.widgets.htmls.loading.layout.display = "block"
        self.widgets.htmls.loading.value = (extra or '') + self.icon('loading', color='var(--accent-color, skyblue)',size='48px').value
        try:
            yield
        finally:
            if btn:
                if btn is self.widgets.buttons.refresh: btn.icon = "plus"
                btn.disabled = False
                self.widgets.htmls.loading.value = ""
                self.widgets.htmls.loading.layout.display = "none"
            # In case of None, when slides are displayed, it will be clear via javascript
            


    def _force_update(self, btn=None):
        with self._loading_splash(btn or self.widgets.buttons.refresh):
            for slide in self[:]:  # Update all slides
                if slide._has_widgets or (slide is self._current): # Update current even if not has_widgets, fixes plotlty etc
                    slide.update_display(go_there=False)
            
            if btn:
                self.notify('Widgets updated everywhere!')
            
            self.settings.footer._apply_change(None) # sometimes it is not updated due to message lost, so force it too
            self._current._set_progress() # update display can take it over to other sldies

    def _collect_slides(self):
        slides_iterable = tuple(sorted(self._slides_dict.values(), key= lambda s: s.number))
        
        if len(slides_iterable) <= 1:
            self._box.add_class("SingleSlide")
        else:
            self._box.remove_class("SingleSlide")

        return slides_iterable
    
    def _update_toc(self):
        tocs = [(s.index, s._section) for s in self._iterable if s._section]
        children = [
            ipw.HTML('<b> Table of Contents</b>',layout=dict(border_bottom='1px solid #8988', margin='0 0 8px 0'))
        ]

        if not tocs:
            children.append(self.html('',
                [r"No sections found!, create sections with markdown syntax alert`section\`content\``"]
            ).as_widget())
        else:
            self._toc_widget.set_toc_items(tocs) # instead of setting options here
            children.append(self._toc_widget)

        self.widgets.tocbox.children = children

    def create(self, slide_numbers):
        "Create empty slides with given slide numbers. If a slide already exists, it remains same. This is much faster than creating one slide each time."
        if not isinstance(slide_numbers, Iterable):
            raise TypeError("slide_numbers should be list-like!")
        
        for number in slide_numbers:
            if not isinstance(number, int):
                raise TypeError(f"items in slide_numbers should all be integeres! got {type(number)}")

        new_slides = False
        for slide_number in slide_numbers:
            if slide_number not in self._slides_dict:
                self._slides_dict[slide_number] = Slide(self, slide_number)
                new_slides = True

        if new_slides:
            self.refresh()  # Refresh all slides

        return tuple(filter(lambda s: s.number in slide_numbers, self._slides_dict.values())) 
    
def _ensure_slides_init(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if Slides.instance() is None:
            raise RuntimeWarning("Slides was never initialized!")
        return func(*args, **kwargs)
    return inner


class fsep:
    """Frame separator! If it is just after `write` command, columns are incremented too.
    You can import it on top level or use as `Slides.fsep`.

    - Use `fsep()` to split code into frames. In markdown slides, use two dashes --.
    - Use `fsep.iter(iterable)` to split after each item in iterable automatically.
    - Setting `stack=True` in `fsep` or `fsep.iter` once under a slide to show frames incrementally. 
        In markdown slides, use %++. The last called value of stack overrides any previous value.
    - Content before first frame separator is added on all frames. This helps adding same title once.
    """
    _app_ins = Slides.instance # need to be called as it would not be defined initially
    
    @_ensure_slides_init
    def __init__(self, stack=None):
        app = self._app_ins()
        app.verify_running("Cant use fsep in a capture context other than slides!")
        app.this._widget.add_class("base") # this is needed to distinguisg clones during printing
        
        sep = app.html('')
        if not hasattr(app.this, '_fsep'): 
            sep = sep.as_widget() # first separator must be a widget
            app.this._fsep = sep # this is used to change frames dynamically
        
        display(sep, metadata={"FSEP": "","skip-export":"no need in export"})
        
        if stack in (True, False):
            app.this.stack_frames(stack)
        elif stack is not None:
            raise ValueError(f"stack should be set True or False or left as None for default behavior, got {type(stack)}")

    @classmethod
    @_ensure_slides_init
    def iter(cls, iterable, stack=None):
        "Loop over iterable. Frame separator is add before each item and at end of the loop."
        cls._app_ins().verify_running()
        if not isinstance(iterable, Iterable) or isinstance(iterable, (str, bytes, dict)):
            raise TypeError(f"iterable should be a list-like object, got {type(iterable)}")
        
        for item in iterable:
            cls(stack) # put one separator before
            yield item
        cls(stack) # put after all done to keep block separated
