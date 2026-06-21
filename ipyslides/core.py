import os, shutil, inspect
import sys, json, re, math, uuid, textwrap, warnings
from contextlib import contextmanager, suppress
from collections import namedtuple
from collections.abc import Iterable
from itertools import zip_longest
from typing import Union, overload
from pathlib import Path
from pkg_resources import resource_filename

from IPython import get_ipython
from IPython.display import display, clear_output

from .xmd import xmd, esc, fmt, get_main_ns, _matched_vars, _stream_chunks
from .writer import hold, write, group
from .formatters import bokeh2html, plt2html, plt2image, serializer, _delim, slidebound
from . import formatters
from . import utils
from . import dashlab

_under_slides = {k: getattr(utils, k, None) for k in utils.__all__}

from ._base.widgets import TOCWidget, ipw # patched one
from ._base.base import BaseSlides
from ._base.intro import how_to_slide, get_logo
from ._base.slide import Slide, SlideGroup, _build_slide
from .__version__ import __version__


try:  # Handle python IDLE etc.
    SHELL = get_ipython()
except:
    print("Slides only work in IPython Notebook!")
    sys.exit()
    
def demo():
    "Setup and display the demo notebook for IPySlides. Click on the resulting link to open the demo notebook in a new tab."
    os.makedirs('ipyslides-demo', exist_ok=True)
    shutil.copy(Path(resource_filename('ipyslides', 'pkg_nbs/ips-demo.ipynb')), 'ipyslides-demo/demo.ipynb')
    utils.html('a','Open Demo Notebook:ipyslides-demo/demo.ipynb', href='ipyslides-demo/demo.ipynb', target='_blank').display()
    
def docs():
    "Open the documentation notebook for IPySlides in a new tab."
    os.makedirs('ipyslides-docs', exist_ok=True)
    shutil.copy(Path(resource_filename('ipyslides', 'pkg_nbs/ips-docs.ipynb')), 'ipyslides-docs/docs.ipynb')
    utils.html('a','Open Documentation Notebook:ipyslides-docs/docs.ipynb', href='ipyslides-docs/docs.ipynb', target='_blank').display()

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
        else: # reset these settings on previous instance on every call
            xmd.extensions.extend(extensions) 
            cls._instance.settings(**settings)
        
        formatters._slides_singleton = cls._instance # internal use
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
        - In JupyterLab, right click on the cell containing slides (outside slides) and select `Create New View for Output` for optimized display.
        - To jump to source cell and back to slides by clicking buttons, set `Windowing mode` in Notebook settings to `defer` or `none`.
        - See code`Slides.xmd.syntax` for extended markdown syntax, especially variables formatting.
        - Inside python scripts or for encapsulation, use `Slides.fmt` to pick variables from local scope.
    
    ::: note-info
        - `Slides` can be indexed same way as list for sorted final indices. 
        - For indexing slides with given number, use comma as code`Slides[number,] → Slide` 
        - Access many via list as code`Slides[[n1,n2,..]] → SlideGroup` or slice as code`Slides[start:stop:step] → SlideGroup`.
        - `SlideGroup` can be used to apply batch operations on many slides at once, e.g. code`Slides[[1,3,5]].vars.update(name='Alice')`.
        - Use indexing with given number to apply persistent effects such as CSS or acess via attributes such as 
          code`Slides.s0`, code`Slides.s1` etc. for existing slides, so `Slides.s10 == Slides[10,]` if slide with number 10 exists.
        - Use code`section[True]\`Backup slides\`` to mark start of supplemental slides. Progress completes before this section and supplemental frames/slides are numbered as `S.1`, `S.2`, ... while remaining navigable.
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
        self.plt2image  = plt2image
        self.bokeh2html = bokeh2html
        self.get_logo   = get_logo
        self.dl         = dashlab # whole dashlab module
        self.write      = write
        self.group      = group
        self.hold       = hold  # Hold display of a function until it is captured in a column of `Slides.write`
        self.xmd        = xmd  # Extended markdown parser
        self.fmt        = fmt # So important for flexibility
        self.esc        = esc # lazy escape for variables in markdown
        self.serializer = serializer  # Serialize IPython objects to HTML

        with suppress(Exception):  # Avoid error when using setuptools to install
            self.shell.register_magic_function(self._slide, magic_kind="cell", magic_name="slide")
            self.shell.register_magic_function(self.__xmd, magic_kind="line_cell", magic_name="xmd")

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
        self.widgets._ctxmenu._callback('refresh',self._force_update) # only single callback is allowed
        self.widgets._ctxmenu._callback('source',self._jump_to_source_cell) 
        self.widgets.checks.rebuild.observe(self._auto_rebuild, names=['value'])
        self.widgets.buttons.build.on_click(self._click_build_if_pending)

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
    
    @property
    def _in_restricted_ctx(self):
        return (self.this is not None # building slide should not allow nesting
            or getattr(self, '_in_output', False) # inside output context manager
            or getattr(self, '_holding_this', False) # temporarily holding running slide is still a nesting context
        )
    
    @contextmanager
    def _set_running(self, slide):
        "Context manager to set running slide and turns back to previous."
        if self._in_restricted_ctx:
            raise RuntimeError("Nested slide building is not allowed!")
        
        if slide and not isinstance(
            slide, Slide
        ):  # None is acceptable to hold running slide in other function
            raise TypeError(f"slide must be None or Slide, got {type(slide)}")

        self._running_slide = slide
        try:
            yield
        finally:
            self._running_slide = None

    @contextmanager
    def _hold_running(self):
        "Context manager to pause running slide and restore it after"
        old = self.this # whether Slide or None
        self._running_slide = None
        self._holding_this = True if old else False # only if slide context was present
        try: 
            yield
        finally:
            self._running_slide = old
            self._holding_this = False

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
            slide = self._slides_per_cell[0]
            if not slide._pending(): # avoid auto naviagte to pending builds to wait unexpectedly for execution
                self.navigate_to(slide.index) 

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
        
    def _jump_to_source_cell(self, ctx=None, value=None):
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
            
        # may be slider can't go there due to single slide, enforce it
        if index == 0 and self._iterable:
            self._iterable[0]._set_css_classes('ShowSlide', 'HideSlide ShowSlide')
            for slide in self._iterable[1:]: slide._set_css_classes(add = 'HideSlide') # safegaurd
        
        self._current._set_progress()  # update progress bar and footer
        self._current._widget.layout.visibility = 'visible'  # ensure visibility, as JS may not be able to yet get it

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
        return self.html('span', 
            self.html('button', '<i class="fa fa-edit"></i>', 
                title = 'Open Drawing Board',
                css_class="req-click jupyter-only", # req-click for internal use only
                style = dict(border="none",background="transparent",cursor="pointer") # overwrite for avoiding double border
            ).value + '<a href="https://www.tldraw.com" target="_blank" rel="noopener noreferrer" class="fa fa-edit export-only"></a>',
            css_class = "link-button jupyter-button draw-button"
        )

    def _add_clean_title(self):
        with _build_slide(self, 0):
            self.stack([
                self.styled("""
                    color['var(--accent-color)']`Replace this with creating a slide with number` alert`0`
                    
                    ::: note-tip
                        Right click (or click on footer) to open context menu for accessing settings, table of contents etc.  
                    """,
                    padding = "8em 8px",
                ), 
                '', # empty column for space 🤣
                how_to_slide],sizes=[14,1, 85]).display()
        
        self._unregister_postrun_cell() # This also clears slides per cell
        self.settings.footer.text = self.get_logo('14px') + ' IPySlides'
        self.navigate_to(0)  # Go to title slide

    def clear(self, keep):
        """Clear all slides except first `keep` slides (default 1). Contents are removed to free memory.
        After clearing, auto slide numbering is reset to `Slides[-1].number + 1` for use in `Slides.slide(-1)`.
        """
        if not isinstance(keep, int) or keep < 1:
            raise ValueError("keep should be positive integer > 0 to keep that many slides from start, at least one!")
        
        for slide in self._slides_dict.values():
            if slide.index is not None and slide.index >= keep: # keep is number of slides to keep from start, so index >= keep should be removed
                slide._citations.clear() # Break circular references
                slide._widget.outputs = () # clear output to free visual clutter
                slide._contents = [] # clear contents to free memory
                if hasattr(slide, '_src_func'): del slide._src_func
                if hasattr(slide, '_scroll_btn'): del slide._scroll_btn
        
        self._slides_dict = {k: s for k, s in self._slides_dict.items() if s.index is not None and s.index < keep}
        self.refresh() # Reset internal structures
        self._next_number = self[-1].number + 1 if self._slides_dict else 0 # reset next number

    @slidebound("Citations")
    def _cite(self, keys):
        citeds = [self._cite_key(key.strip()) for key in keys.split(',')] # avoid whitespaces around key
        return '<sup>,</sup>'.join(citeds) 

    def _cite_key(self, key):
        """Use markdown syntax cite`key` to add citations since output has to be inline. 
        Citations corresponding to keys used can be added by ` Slides.set_citations ` method.
        """
        cited = _Citation(slide=self.this, key=key)
        cited._id = list(self.this._citations.keys()).index(key) + 1 # Get index of key from unsorted ones

        # Return string otherwise will be on different place, avoid newline here
        return f'<a href="#{key}" class="citelink"><sup id ="{key}-back" style="color:var(--accent-color) !important;">{cited._id}</sup></a>'
    
    def _nocite(self, key): # @key!, cite`key!` without adding to citations
        if key in self._citations:
            return self.html('span',self._citations[key].partition("<p>")[-1].rpartition("</p>")[0],
            style = dict(left="initial",top="initial"), css_class = "citetext text-box text-small").value
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

    def set_citations(self, data):
        r"""Set citations from dictionary or string with content like `\@key: citation value` on their own lines, 
        key should be cited in markdown as cite\`key\` / \@key, optionally comma separated keys.
        Number of columns in displayed citations are determined by code`Slides.settings.layout(..., ncol_refs=N)` or markdown refs\`N\`/`Slides.refs(N)`.

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
            - Citations are replaced with new ones, so latest use of this function represents available citations.
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
        
        # Finally write resources to file in assets
        with self.set_dir(self._assets_dir):
            with open(".citations.json", "w", encoding="utf-8") as f:
                json.dump(self._citations, f, indent=4)


    def _set_saved_citations(self):
        "Load resources from file if present silently"
        with self.set_dir(self._assets_dir):  # Set assets directory
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

    
    @slidebound("Section")
    def section(self, text, supplemental = False):
        """Add section key to presentation that will appear in table of contents. In markdown, use section`content` syntax.
        Sections can be written as table of contents. First call with supplemental=True will win and following all sections would be in supplemental part.
        """
        self.this._section = str(text).strip()  # assign before updating toc
        # Keep keyboard End/Home boundaries in sync even when rebuilding existing slides.
        if supplemental:
            self.this._is_supp = True # make on slide, not outside to make correct when slide get deleted
        
        self.widgets.iw._main_end = self._lms_idx # need for frontend
        
        for s in self[:]:
            self.settings.footer._set_on(s) # update all slides footer to reflect correct sections
            if s._toc_args and s != self.this: 
                s.update_display()
 
    @slidebound
    def toc(self, title='## Contents {.align-left}', highlight = False):
        """You can also use markdown syntax to add it like toc`title` or toc[highlight=True]`title` 
        or toc[True]`title`."""
        self.this._toc_args = (title, highlight)
        display(self.this._reset_toc()) # Must to have metadata there
    
    @slidebound
    def refs(self, ncol=None, *keys):
        r"""Return XTML or None for references with all keys or a subset of keys which were used without `!` at end.
        Unused keys from all calls to this function will be added at end of slide automatically. 
        References are set in `Slides.set_citations`. In markdown, use refs\`ncol\` syntax.
        """
        objs = self.this._citations.values() if not keys else [v for k,v in self.this._citations.items() if k in keys]
        for obj in objs:
            obj._used = True  # mark as used to track unused ones
        return self.this._build_refs(objs, ncol=ncol)

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
        self._clean_display()
        
    def _clean_display(self): # This helps reduce a jarring flash on display
        height = self._box.layout.height
        self._box.layout.height = '0'  # collapse during updates
        try:
            self._unregister_postrun_cell() # no need to scroll button where showing itself
            self._auto_rebuild('ondemand') # keep auto_rebuild state, but register if needed
            self.settings._update_theme() # force it, sometimes Inherit theme don't update
            self._force_update()  # Update to avoid some content like widgets may be lost
            clear_output(wait = True) # Avoids jump buttons and other things in same cell created by scripts producing slides
            display(ipw.HBox([self.widgets.mainbox]).add_class("SlidesContainer"))  # Display slides within another box
        finally: 
            self._box.layout.height = height  # restore height
            self.widgets.iw.msg_tojs = "RESCALE"  # force rescale after display

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

    @property
    def _lms_idx(self):
        "Get last index of main slides, excluding supplemental slides."
        for s in self[:]:
            if getattr(s, '_is_supp', False):
                return max(s.index - 1, 0) # return index -1 at first found supplemental section
        return max(len(self._iterable) - 1, 0)  # if no supplemental section, return index of last slide

    def _progress_value(self, slide, fidx=0):
        "Progress percentage for a slide/frame, or None for supplemental slides."
        if slide.index > self._lms_idx:
            return None

        unit = 100/(self._lms_idx or 1)
        value = round(unit * ((slide.index or 0) - (slide.nf - fidx - 1)/slide.nf), 4)
        return max(0, min(100, value))


    def _switch_slide(self, old_index, new_index):
        if inds := [opt.ti for opt in self._toc_widget.options if opt.si == self._sectionindex]:
            self._toc_widget.send({'active' : inds[0]}) # Update toc widget focus without changing index
        
        slide = self._iterable[new_index]
        slide._update_transition_objs()
        
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
        # do after ShowSlide available on naviagted slide
        self._send_nav_msg(new_index > old_index or new_index == 0) # There is no other way to animate title slide except on returning back to it
        self.settings.footer._update_footer() # keep running-section footer text in sync
    
    def _build_if_pending(self, slide):
        if not slide._pending(): return  # if slide is not pending, return immediately
        
        with _build_slide(self, slide.number): 
            slide._set_source(self.code.from_source(slide._src_func).raw,'python') # set source code to be accessible
            if (doc := getattr(slide._src_func, '__doc__', None)):
                self.xmd(doc, returns=False)
            slide._src_func(slide) # call to build slide now
            
            # clean up after building the slide
            slide._set_css_classes(remove = 'Stale') # lazy slides will be back here to be built
            del slide._src_func # remove build function for building once
        
    def _click_build_if_pending(self, btn):
        "Build first pending slide when user clicks build button."
        with dashlab.disabled(btn): # disable button during build
            if slide := self._next_pending:
                self.navigate_to(slide.index) # must go there before starting a build to see the slide
                self._build_if_pending(slide) # build first pending slide
            else:
                self.notify('No pending slides to build!') # programatic click by [B] even if button not visible
    
    @property
    def _next_pending(self):
        if self._current and self._current._pending(): 
            return self._current # check current first
        for slide in self._iterable:
            if slide._pending(): return slide # get and exit

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
    
    def _send_nav_msg(self, forward=True, parts=False, selector=None):
        "Send navigation message to front-end on slide or frame switching."
        msg = "NAV:RIGHT" if forward else "NAV:LEFT"
        if selector is not None:
            msg += f"/SELECTOR:{selector}"
        elif parts: 
            msg += f"/PARTS"
        self.widgets.iw.msg_tojs = msg
    
    def run_animation(self, selector=None):
        """Run animation of current slide from python side. 
        Optionally, you can provide CSS selector to restrict animation inside specific element.
        In dashlab's interactive components, animation is run automatically when a content with `anim-` class is created each time.
        """
        self._send_nav_msg(forward=True, selector=selector)
    
    def refresh(self):
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self._iterable = self._collect_slides()  # would be at least one title slide
        if not self._iterable:
            self.wprogress.max = 0
            self.widgets.iw._main_end = 0
            self.widgets.slidebox.children = []  # Clear older slides
            self.widgets.htmls.usercss.value = "" # clear user css as that is a side effect
            self.widgets._tmp_out.clear_output(wait=False) # clear left over transient objects if any
            self.widgets.htmls.footer.value = "" # clear footer as well to avoid confusion, but without changing its settings
            return None
        
        old = self.wprogress.value
        self.wprogress.max = len(self._iterable) - 1  # Progressbar limit
        self.wprogress.value = min(old, self.wprogress.max) # avoid jumping back to title each time

        # Update Slides
        self.widgets.slidebox.children = [it._widget for it in self._iterable]
        for i, s in enumerate(self._iterable):
            s._index = i  # Update index

        self.widgets.iw._main_end = self._lms_idx # set for frontend
        if not any(['ShowSlide' in c._dom_classes for c in self.widgets.slidebox.children]):
            self.widgets.slidebox.children[0].add_class('ShowSlide')
        
        # Update stuff on slides and side effects
        self._update_toc()  # Update table of content if any
        self._force_update() # refresh causes lose widgets sometimes
        self.settings.footer._update_footer() # keep footer in sync
        (self._current or self[0,])._mount_user_css() # reset CSS to cleanup unwanted leftover per slide CSS
        (self._current or self[0,])._update_transition_objs() # new update on current or first slide
        self.widgets.iw.msg_tojs = 'SwitchView' # Trigger view
    
    def _fix_slide_number(self, number):
        "For this, slide_number in function is set to be position-only argement."
        if str(number) != '-1': # handle %%slide -1 togther with others
            return number
        
        with suppress(AttributeError): # some kernels may not implement changing cell code on fly
            code = self.shell.kernel.get_parent().get('content',{}).get('code','')
            p = r"\s*?\(\s*?-\s*?1" # call pattern in any way with space between (, -, 1 and on next line, but minimal matches due to ?
            matches = re.findall(rf"(\%\%slide\s+-1)|(slide{p})|(build{p})|(sync_with_file{p})", code)
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
            - You can add ++ (plus plus) in the content staring on new line to add parts which reveal incrementally.
            - Parts separator (++) just before `columns` creates incremental columns and rows. `++[isolate]` triggers isolation of columns from previous content.
            - Use `%%slide -1` to enable auto slide numbering. Other cell code is preserved.

        """
        line = line.strip().split()  # VSCode bug to inclue \r in line
        line[0] = str(self._fix_slide_number(line[0])) # fix inplace as string here

        if line and not line[0].isnumeric():
            raise TypeError(
                f"You should use %%slide integer >= 1 -m(optional), got {line}"
            )

        slide_number = int(line[0])  # First argument is slide number
        
        if "-m" in line[1:]:            
            frames = list(_stream_chunks(cell, sep='--'))
            with _build_slide(self, slide_number) as s:
                prames = list(_stream_chunks(s._markdown, sep='--'))  
                # Update source beofore parsing content to make it available for variable testing
                s._set_source(cell, "markdown") # set source before running to have it available for user
                vars = _matched_vars(cell) # update has_vars before running to have ready for auto rebuild
                stored = {**esc._store, **s._esc_vars} # keep previous stored variables, first time come only from esc._store
                s._has_vars = tuple([v for v in vars if v not in stored]) # esc is encapsulated by design
                s._esc_vars = {v: stored[v] for v in vars if v in stored} # store for rebuilds internally
                
                for page, (frm, prm) in enumerate(zip_longest(frames, prames, fillvalue=''), start=1): # page starts from 1
                    self.xmd(frm, returns = False) # parse and display content
                    
                    if len(frames) > 1: self.PAGE() # add page separator if multiple frames
                    
                    if prm != frm: 
                        s._lre_page = page  # mark least recent edited page for jumping there

        else:  # Run even if already exists as it is user choice in Notebook, unlike markdown which loads from file
            with _build_slide(self, slide_number) as s:
                s._set_source(cell, "python")  # Update cell source beofore running
                self._run_cell(cell)  #
    
    @contextmanager
    def _slide_context(self, slide_number):
        with _build_slide(self, slide_number) as s:
            with self.code.context(returns=True, depth=4) as code:
                s._set_source(code.raw, "python")  # set source before running 
                yield s
    
    def slide(self, slide_number, content=None, /, **vars):
        """Create a slide using contextmanager or markdown content.
        
        1. If content is None, returns a context manager for the slide (equivalent to `%%slide`)
            - Contents displayed by `write` function can be split into incremental parts if `write` is called after `pause()` adjacently.
            - You can defer the content generation using the `@pending` decorator for faster notebook cell runs and heavy computations
              until user clicks on the Pending Slides button. Both contextmanager and `%%slide` can benefit from this mechanism.
        2. If content is a string, it is treated as markdown content for the slide (equivalent to `%%slide -m`)
            - Use `++` to separted content into parts for incremental display on ites own line with optionally adding content after one space.
            - Markdown `columns/group` blocks can be displayed incrementally if `++` is used (alone on line) before these blocks as a trigger.
            - See `slides.xmd.syntax` for extended markdown usage.
            - Variables such as \%{var} can be provided in `**vars` (or left during build) and later updated in notebook using `rebuild` method on slide handle or overall slides.
            - If an f-string is provided, variables in f-string are resolved eagerly and never get updated on rebuild including lazy ones provided by `Slides.esc`.
        
        - In both cases, `slide_number` could be used as `-1`.
        - Use yoffet`integer in percent` in markdown or code`Slides.yoffset(integer)` to make all frames align vertically to avoid jumps in increments.
        - `**vars` are ignored silently if `build` is used as contextmanager or decorator.
        """
        # Only contextmanager and direct markdown build is useful for adding content to slides.
        # Don't fall for a function decorator, since that restricts %%slide to be lazy,
        # Instead pending makes it possible to make %%slide and with slide both lazy
        with self.code.context(returns=True, start=True, depth=3) as caller: # string called code
            if caller.strip().startswith('@'):
                raise RuntimeError('slide function cannot be used as a decorator. Use it as a context manager or with markdown content.')
            if content is not None and caller.strip().startswith('with'):
                raise RuntimeError('slide function cannot be used as a context manager with content passed. Use either as a context manager or provide markdown content.')
        
        snumber = self._fix_slide_number(slide_number)
        
        if content is None:
            return self._slide_context(snumber)  # return the slide context manager if no content is provided
        elif not isinstance(content, str):
            raise TypeError(f"content should be a string for markdown slide or None for contextmanager, got {type(content)}")
        
        # Markdown slide: parse and display content, DO NOT FALL for multiple slides, need to be same as %%slide -m
        # using fmt is tempting to delegate vars automatically but it raises error if var not found, 
        # which is against whole philosophy of rebuild.
        slide, = self.create([snumber]) # create or access slide handle
        expected_vars = _matched_vars(content) # only filter required variables
        slide._md_vars = {k:v for k,v in vars.items() if k in expected_vars}
        self._slide(f'{snumber} -m', content) 
        return slide
    
    @slidebound
    def pending(self, func):
        """Decorator to mark a function as pending for a slide.
        
        The function will not be executed immediately but will be deferred until the user clicks the Pending Slides button.
        The function must accept a single argument, which is the slide handle.
        This is useful for deferring heavy computations until the user decides to build the slide.
        
        Must be used within a slide constructor (e.g., inside a `%%slide` cell or a slide contextmanager) 
        to mark function as pending for that specific slide.
        
        Only single function can be marked as pending, so last one marked will override any previously marked function for that slide.
        """
        # Do some static checks, so it at least valid function
        uw_func = inspect.unwrap(func) # unwrap to get original function
        if inspect.isgeneratorfunction(uw_func):
            raise TypeError("@pending decorator does not support generator functions. Use standard functions only.")
        
        if len(inspect.signature(uw_func).parameters) != 1:
            raise ValueError("@pending decorator function must accept single argument, slide.")
        
        self.this._src_func = func # store for later build
        self.this._set_css_classes(add = 'Stale') # mark as stale to build later
        self.html('center',f"<code>{self.this}</code> is pending!<br>"
            "Click <code>Pending Slides</code> button at right bottom to build it.",
            css_class='warning'
        ).display() # need hint be there
        

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

    def _force_update(self, ctx=None, value=None):
        if not self._current: return # no slides yet
        try:
            self._current._waiting_contents() # show loading sekeleton 
            for slide in self[:]:  # Update all slides
                if slide._has_widgets and (slide is not self._current): # Update current at end
                    slide.update_display()
        finally: self._current.update_display()  # Update current slide at end to remove waiting contents
        
        if ctx:
            self.notify('Widgets updated everywhere!')
        
        self.settings.footer._update_footer() # sometimes it is not updated due to message lost, so force it too
        self._current._set_progress() # update display can take it over to other sldies
        self.run_animation()  # to trigger any animation on current slide on refresh

    def _collect_slides(self):
        slides_iterable = tuple(sorted(self._slides_dict.values(), key= lambda s: s.number))
        
        if len(slides_iterable) <= 1:
            self._box.add_class("SingleSlide")
        else:
            self._box.remove_class("SingleSlide")

        return slides_iterable
    
    def _update_toc(self):
        tocs = [(s.index, s._section) for s in self._iterable if s._section]
        children = []

        if not tocs:
            children.append(self.html('',
                [r"No sections found!, create sections with markdown syntax alert`section\`content\``"]
            ).as_widget())
        else:
            self._toc_widget.set_toc_items(tocs) # instead of setting options here
            children.append(self._toc_widget)

        self.widgets.panelbox._tocsTab.children = children

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
    
    def demo(self):
        "Setup and display the demo notebook for IPySlides. Click on the resulting link to open the demo notebook in a new tab."
        print("Use top level ipyslides.demo() instead!")
        return demo()
    
    class pause:
        """Pause delimiter! Use `Slides.pause()` or import `pause` from top level to create a new revealable part in slide.
        In markdown slides, use two plus signs `++` on its own line, optionally add content right after `++ `.
        
        - Adjacent pause delimiters are ignored, so no empty parts are created in normal flow.
        - A call `pause()` before `write` command adds parts inside columns and rows. 
            - Use code`pause(isolate=True)` to isolate previous content from a following `write(...columns...)` reveal.
            - In markdown, use `++[isolate]` before `::: columns` (with `+++` separators) for the same behavior.
                    See `write` command for more details.
        - Use code`pause.iter(iterable)` to create multiple parts from iterable automatically.
        - Last empty pause delimiter is ignored.
        
        ::: note
            `Slides.PART` is deprecated and kept as an alias for backward compatibility.
        """
        # DO NOT FALL FOR GLOBAL PAGE STUFF, THAT WOULD BE A NIGHTMARE TO HANDLE 
        # AND CANNOT HAVE ITS OWN STATE METADATA, AS WE REMOVED IT EARLIER.
        _type = "PART"
        
        def __init__(self, isolate=False):
            delim = _delim(self._type)
            if isolate and isinstance(getattr(delim, 'metadata', None), dict):
                delim.metadata['ISOLATE'] = True
            display(delim)

        @classmethod
        def _optional_trail(self, trail):
            if trail is True: display(_delim(self._type))
            elif trail in ("PART", "PAGE"):
                display(_delim("PART" if trail == "PART" else trail))
            elif trail is not False: 
                raise ValueError(f"trail should be True, False, 'PART' or 'PAGE', got {trail!r}")

        @classmethod
        def iter(cls, iterable, isolate=False, trail=True):
            """Loop over given iterable by adding a separator before each item.
            If `trail` is True (default), a separator of this type is added at end as well.
            You can also set `trail` to 'PART' or 'PAGE' to add that type of separator at end instead 
            or set to False to avoid adding any separator at end, while is useful to avoid incremental 
            behavior in next write command in case of pause delimiter.
            Set `isolate=True` to mark only the first inserted delimiter as isolate.
            """
            if not isinstance(iterable, Iterable) or isinstance(iterable, (str, bytes, dict)):
                raise TypeError(f"iterable should be a list-like object, got {type(iterable)}")
            for i, item in enumerate(iterable):
                cls(isolate=bool(isolate) and i == 0) # isolate should affect only the first delimiter
                yield item
            # This will be only one separator at end if no items were yielded, its like itself called once
            cls._optional_trail(trail) # put one separator at end if needed, default True

    class PAGE(pause):
        """Legacy page delimiter kept for backward compatibility.

        Markdown `--` maps to this delimiter internally.
        """
        _type = "PAGE"
    
        def __init__(self, empty=False):
            display(_delim(self._type))
            if empty:
                utils.html('span','').display() # to preserve empty page, otherwise two adjacent PAGE delimiters are ignored
                display(_delim(self._type)) # add one more to create empty page

    class PART(pause):
        "Deprecated alias for `Slides.pause`."

        def __init__(self, *parts, trail=True):
            warnings.warn(
                "Slides.PART is deprecated and will be removed in a future release; use Slides.pause instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            super().__init__()
            write(parts)
            if parts:
                type(self)._optional_trail(trail)

        @classmethod
        def iter(cls, iterable, trail=True):
            warnings.warn(
                "Slides.PART.iter is deprecated and will be removed in a future release; use Slides.pause.iter instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return super().iter(iterable, trail=trail)