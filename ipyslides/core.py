import sys, os, json, re, textwrap, math
from contextlib import contextmanager, suppress
from collections.abc import Iterable
from itertools import zip_longest

from IPython import get_ipython
from IPython.display import display, clear_output

from .xmd import fmt, parse, xtr, extender as _extender
from .source import Code
from .writer import GotoButton, write
from .formatters import XTML, HtmlWidget, bokeh2html, plt2html, highlight, htmlize, serializer
from . import utils

_under_slides = {k: getattr(utils, k, None) for k in utils.__all__}

from ._base.widgets import ipw # patched one
from ._base.base import BaseSlides
from ._base.intro import how_to_slide, get_logo
from ._base.slide import Proxy, Slide, _build_slide
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
                <a href="#{self._key}-back"> 
                    <span style="color:var(--accent-color);">{self._id}. </span>
                </a>{_value}</div>"""
        else:
            return f'<div class = "warning">Set value for cited key {self._key!r} and run again to clear warning!</div>'

    @property
    def inline_value(self):
        if _value := self._slide._app._citations.get(self._key, None):
            return utils.textbox(_value.partition("<p>")[-1].rpartition("</p>")[0],
                left="initial",
                top="initial",
            ).value
        else:
            return self.value


class Slides(BaseSlides):
    # This will be overwritten after creating a single object below!

    def __init__(self):
        super().__init__()  # start Base class in start
        self.shell = SHELL

        for k, v in _under_slides.items():  # Make All methods available in slides
            setattr(self, k, v)

        self.get_child_dir('.ipyslides-assets', create = True) # It should be present/created to load resources
        
        self.extender   = _extender
        self.plt2html   = plt2html
        self.bokeh2html = bokeh2html
        self.highlight  = highlight
        self.get_logo   = get_logo
        self.code       = Code  # Code source
        self.icon       = _Icon  # Icon is useful to add many places
        self.write      = write
        self.parse      = parse  # Parse extended markdown
        self.fmt        = fmt # So important for flexibility
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

        with self.set_dir(self._assets_dir):  # Set assets directory
            self._set_citations_from_file(
                "citations.json"
            )  # Load citations from file if exists

        self.wprogress = self.widgets.sliders.progress
        self.wprogress.observe(self._update_content, names=["value"])
        self.widgets.buttons.refresh.on_click(self._update_widgets)
        self.widgets.buttons.source.on_click(self._jump_to_source_cell)

        # All Box of Slides
        self._box = self.widgets.mainbox.add_class(self.uid)
        self._setup()  # Load some initial data and fixing

        
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

    def run_cell(self, cell, **kwargs):
        """Run cell and return result. Use this instead of IPython's run_cell for extra controls."""
        self._unregister_postrun_cell() # important to avoid putting contnet on slides
        output = self.shell.run_cell(cell, **kwargs)
        if self.this: # there was post_run_cell under building slides
            self._register_postrun_cell() # should be back
        return output
    
    def _post_run_cell(self, result):
        self._unregister_postrun_cell() # it will be initialized from next building slides
        if result.error_before_exec or result.error_in_exec:
            return  # Do not display if there is an error

        scroll_btn = ipw.Button(description= 'Go to Slides', icon= 'scroll', layout={'height':'0px'}).add_class('Scroll-Btn') # height later handled by hover
        
        if self._slides_per_cell:
            self.navigate_to(self._slides_per_cell[0].index) # more logical to go in start slide rather end

        for slide in self._slides_per_cell:
            slide._scroll_btn = scroll_btn
        
        self._slides_per_cell.clear() # empty it
        scroll_btn.on_click(lambda btn: self._box.focus()) # only need to go there, no slide switching 
        display(scroll_btn)
    
    def _unregister_postrun_cell(self):
        self._slides_per_cell.clear() # Must to let user jump on first slide run to be in correct place
        with suppress(Exception): 
            self.shell.events.unregister("post_run_cell", self._post_run_cell)
    
    def _register_postrun_cell(self):
        with suppress(Exception): 
            self.shell.events.register("post_run_cell", self._post_run_cell)
        
    def _jump_to_source_cell(self, btn):
        if hasattr(self._current, '_scroll_btn'):
            self._current._scroll_btn.focus()
        else:
            self.notify('No source cell found!')

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

    def __getitem__(self, key):
        "Get slide by index or slice of computed index. Use [number,] or [[n1,n2,..]] to access slides by number they were created with."
        if isinstance(key, int):
            return self._iterable[key]
        elif isinstance(key, slice):
            return self._iterable[key.start : key.stop : key.step]
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
            
            return tuple(items)

        raise KeyError(
            f"A slide could be accessed by index or slice, got {type(key)},\n"
            "Use `Slides[number,] -> Slide` or `Slides[[n1, n2,..]] -> tuple[Slide]` to access slides by number they were created with."
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
    def in_output(self):
        "Check if Output widgets is capturing output."
        return getattr(self, "_in_output", False)

    @property
    def draw_button(self):
        "Get a button to reveal drawing board easily from slide. Like it lets you remeber to draw now."
        return self.widgets.toggles.draw

    def verify_running(self, error_msg=""):
        "Verify if slide is being built, otherwise raise error."
        if self.this is None:
            raise RuntimeError(
                error_msg or "This operation is only allowed under slide constructor."
            )

    def _add_clean_title(self):
        with _build_slide(self, 0):
            self.cols(
                self.styled("color[var(--accent-color)]`Replace this with creating a slide with number` alert`0`",
                    padding = "8em 8px",
                ), 
                '', # empty column for space 🤣
                how_to_slide,widths=[14,1, 85]).display()
        
        self._unregister_postrun_cell() # This also clears slides per cell

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
    
    def _set_ctns(self, d):
        # Here other formatting does not work for citations
        new_citations = {k: self.parse(v, returns = True) for k, v in d.items()}
        if self._citations != new_citations: # same call again should not change anythong
            self._citations = new_citations
            self._set_unsynced() # will go synced after rerun
    
    def _set_unsynced(self):
        for slide in self.cited_slides:
            slide.set_css_classes(add = 'Out-Sync') # will go synced after rerun

    def set_citations(self, data, mode='footnote'):
        """Set citations from dictionary or file that should be a JSON file with citations keys and values, key should be cited in markdown as cite\`key\`.
        `mode` for citations should be one of ['inline', 'footnote']. Number of columns in citations are determined by `Slides.settings.set_layout(..., ncol_refs=N)`.

        ::: note
            - You should set citations in start if using voila or python script. Setting in start in notebook is useful as well.
            - Citations are replaced with new ones, so latest use of this function reprsents avilable citations.
        """
        if isinstance(data, dict):
            self._set_ctns(data)
        elif isinstance(data, str):
            if not os.path.isfile(data): # raise error here, not in file to let it load by __init__ silently
                raise FileNotFoundError(f"File: {data!r} does not exists.")
            
            self._set_citations_from_file(data) 
        else:
            raise TypeError(f"data should be a dict or path to a json file for citations, got {type(data)}")
    
        # Update mode and display after setting citations
        if mode not in ["inline", "footnote"]:
            raise ValueError(f'citation mode must be one of "inline" or "footnote" but got {mode}')
        
        if self._cite_mode != mode:
            self._cite_mode = mode # Update first as they need in display update
            self._set_unsynced() # will go synced after rerun

        # Make some possible updates
        for slide in self.cited_slides:
            slide.update_display(go_there=False) # will reset slides refrences
            
        
        # Finally write resources to file in assets
        with self.set_dir(self._assets_dir):
            with open("citations.json", "w", encoding="utf-8") as f:
                json.dump(self._citations, f, indent=4)


    def _set_citations_from_file(self, filename):
        "Load resources from file if present silently"
        if os.path.isfile(filename):
            with open(filename, "r", encoding="utf-8") as f:
                self._set_ctns(json.load(f))
    
    @property
    def cited_slides(self):
        "Return slides which have citations."
        return tuple([s for s in self[:] if s._citations])

    def section(self, text):
        """Add section key to presentation that will appear in table of contents. In markdown, use section`content` syntax.
        Sections can be written as table of contents.
        """
        self.verify_running("Sections can be added only inside a slide constructor!")

        self.this._section = text  # assign before updating toc
        
        for s in self[:]:
            if s._toc_args and s != self.this: 
                s.update_display(go_there=False)
 
    def toc(self, title='## Contents {.align-left}', summary = None):
        "You can also use markdown syntax to add it like toc`title` or ```toc title\n summary\n```. `summary` is written in right column."
        self.verify_running("toc can only be added under slides constructor!")
        self.this._toc_args = (title, summary)
        display(self.this._reset_toc()) # Must to have metadata there

    def _goto_button(
        self, text, target_slide=None, **kwargs
    ):
        if target_slide and not isinstance(target_slide, Slide):
            raise TypeError(f"target_slide should be Slide, got {type(target_slide)}")

        kwargs["description"] = text  # override description with text
        kwargs["layout"] = kwargs.get("layout", {"width": "max-content"})
        button = ipw.Button(**kwargs).add_class("goto-button")
        setattr(button, "_TargetSlide", target_slide)  # Monkey patching target slide

        def on_click(btn):
            try:
                self.wprogress.value = (
                    btn._TargetSlide.index
                )  # let it throw error if slide does not exist 
                btn._TargetSlide.first_frame()
            except:
                self.notify(
                    f"Failed to jump to slide {btn._TargetSlide.index!r}, you may have not used GotoButton.set_target() anywhere!"
                )

        button.on_click(on_click)
        return GotoButton(button, app=self)

    def goto_button(self, text, **kwargs):
        """
        Initialize a button to jump to given target slide when clicked.
        `text` is the text to be displayed on button.
        `kwargs` are passed to `ipywidgets.Button` function.

        - Pass to write command or use `.display()` method to display button in a slide.
        - Use `.set_target()` method under target slide.

        ::: note-tip
            - `goto_button` is converted to a link in exported slides that can be clicked to jump to slide.
            - You can use `.set_target()` on a previous slides and `.display()` on a later slide to create a link that jumps backwards.
        """
        return self._goto_button(text, target_slide=None, **kwargs)

    def show(self):
        "Display Slides."
        return self._ipython_display_()

    def _ipython_display_(self):
        "Auto display when self is on last line of a cell"
        if not self.is_jupyter_session():
            raise Exception("Python/IPython REPL cannot show slides. Use IPython notebook instead.")

        clear_output(wait = True) # Avoids jump buttons and other things in same cell created by scripts producing slides
        self._unregister_postrun_cell() # no need to scroll button where showing itself
        self._update_toc()  # Update toc before displaying app to include all sections
        self._update_widgets()  # Update before displaying app
        self.settings._update_theme() # force it, sometimes Inherit theme don't update
        self.frozen(ipw.HBox([self.widgets.mainbox]).add_class("SlidesContainer"),{}).display()  # Display slides within another box
        

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
                s.index for s in self[: self._current.index] if s._section
            ]  # Get all section indexes before current slide
            return idxs[-1] if idxs else 0  # Get last section index

    def _switch_slide(self, old_index, new_index):  
        uclass = f".{self.uid} .TOC"
        slide = self._iterable[new_index]
        self._renew_objs = (
            slide.animation, # keep animation first, needs in _show_frames
            slide.css,
            self.html(
                "style",
                f"{uclass} .toc-item.s{self._sectionindex} {{font-weight:bold;}}",
            ))

        self._update_tmp_output(*self._renew_objs)
        
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
            self._current.run_on_load()  # Run on_load setup after switching slide, it updates footer as well

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
        self._update_widgets() # refresh causes loose widgets sometimes

        if not any(['ShowSlide' in c._dom_classes for c in self.widgets.slidebox.children]):
            self.widgets.slidebox.children[0].add_class('ShowSlide')

        self.widgets.iw.msg_tojs = 'SwitchView' # Trigger view

    def proxy(self, text):
        """Place a proxy placeholder in your slide and return it's `handle`. This is useful when you want to update the placeholder later.
        Use `Slides.capture_proxy(slide_number, proxy_index)` or `handle.capture` contextmanager to update the placeholder.
        Use this in markdown as well by proxy `text` syntax.
        """
        self.verify_running(
            "proxy placeholder can only be used in a slide constructor!"
        )
        return Proxy(text, self.this)
    
    def capture_proxy(self, slide_number, proxy_index):
        "This is a shortcut for `Slides[slide_number,].proxies[proxy_index]`."
        return self[slide_number,].proxies[proxy_index]
    
    def _fix_slide_number(self, number):
        "For this, slide_number in function is set to be position-only argement."
        if str(number) != '-1': # handle %%slide -1 togther with others
            return number
        
        code = self.shell.get_parent().get('content',{}).get('code','')
        p = "\s*?\(\s*?-\s*?1" # call pattern in any way with space between (, -, 1 and on next line, but minimal matches due to ?
        matches = re.findall(rf"(\%\%slide\s+-1)|(build{p})|(slide{p})|(from_markdown{p})|(sync_with_file{p})", code)
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
                Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        ::: note
            - If Markdown is separated by two dashes (--) on it's own line, multiple frames are created and shown incrementally.
            - In case of frames, you can add %++ (percent plus plus) in the content to add frames incrementally.
            - Frames separator (--) just after `multicol` creates incremental columns.
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
            if any(map(lambda v: '\n--' in v, # I gave up on single regex after so much attempt
                (re.findall(r'```multicol(.*?)\n```', cell, flags=re.DOTALL | re.MULTILINE) or [''])
                )):
                raise ValueError("frame separator -- cannot be used inside multicol!")
            
            frames = re.split(r"^--$|^--\s+$", cell, flags=re.DOTALL | re.MULTILINE)  # Split on -- or --\s+
            edit_idx = 0

            with _build_slide(self, slide_number) as s:
                prames = re.split(r"^--$|^--\s+$", s._markdown, flags=re.DOTALL | re.MULTILINE)
                s.set_source(cell, "markdown")  # Update source beofore parsing content to make it available to user inside markdown too

                for idx, (frm, prm) in enumerate(zip_longest(frames, prames, fillvalue='')):
                    if '%++' in frm: # remove %++ from here, but stays in source above for user reference
                        frm = frm.replace('%++','').strip() # remove that empty line too
                        self.fsep.join()

                    parse(xtr.copy_ns(cell, frm), returns = False) # user may have used fmt
                    
                    if len(frames) > 1:
                        self.fsep() # should not be before, needs at least one thing there
                    
                    if prm != frm: 
                        edit_idx = idx
                        if (not self.this._split_frames) and ('```multicol' in frm): # show all columns if edit is inside multicol
                            edit_idx += (len(re.findall('^\+\+\+$|^\+\+\+\s+$',frm, flags=re.DOTALL | re.MULTILINE)) + 1)
            
            s.first_frame() # be at start first
            for _ in range(edit_idx): 
                s.next_frame() # go at latest edit

        else:  # Run even if already exists as it is user choice in Notebook, unlike markdown which loads from file
            with _build_slide(self, slide_number) as s:
                s.set_source(cell, "python")  # Update cell source beofore running
                self.run_cell(cell)  #

    @contextmanager
    def slide(self, slide_number, /): # don't allow keyword to have -1 robust
        """Same as `Slides.build` used as contexmanager."""
        slide_number = self._fix_slide_number(slide_number)

        with _build_slide(self, slide_number) as s, self.code.context(
            returns = True, depth=4
        ) as c:  # depth = 4 to source under context manager
            s.set_source(c.raw, "python")  # Update cell source befor yielding
            yield s  # Useful to use later

    def __xmd(self, line, cell=None):
        """Turns to cell magics `%%xmd` and line magic `%xmd` to display extended markdown.
        Can use in place of `write` commnad for strings.
        When using `%xmd`, you can pass variables as `{var}` which will substitute HTML representation
        if no other formatting specified.
        Inline columns are supported with ||C1||C2|| syntax."""
        if cell is None:
            return parse(line, returns = False)
        else:
            return parse(cell, returns = False)

    @contextmanager
    def _loading_private(self, btn):
        btn.icon = "minus"
        btn.disabled = True  # Avoid multiple clicks
        self.widgets.htmls.loading.style.display = "block"
        self.widgets.htmls.loading.value = loading_svg
        try:
            yield
        finally:
            btn.icon = "plus"
            btn.disabled = False
            self.widgets.htmls.loading.value = ""
            self.widgets.htmls.loading.style.display = "none"

    def _update_widgets(self, btn=None):
        with self._loading_private(self.widgets.buttons.refresh):
            for slide in self[:]:
                if slide._has_widgets:
                    slide.update_display(go_there=False)
        
        if btn:
            self.notify('Widgets on slides updated!')
        self._current._set_progress() # update display can take it over to other sldies

    def _collect_slides(self):
        slides_iterable = tuple(sorted(self._slides_dict.values(), key= lambda s: s.number))
        
        if len(slides_iterable) <= 1:
            self._box.add_class("SingleSlide")
        else:
            self._box.remove_class("SingleSlide")

        return slides_iterable

    def _update_toc(self):
        tocs_dict = {s._section: s for s in self._iterable if s._section}
        children = [
            ipw.HBox([
                HtmlWidget('<b> Table of Contents</b>'), self.widgets.buttons.toc
            ],layout=dict(border_bottom='1px solid #8988', margin='0 0 8px 0',justify_content='space-between'))
        ]

        if not tocs_dict:
            children.append(self.format_html(
                "No sections found!, create sections with markdown syntax alert`section\`content\``"
            ).as_widget())
        else:
            for i, (sec, slide) in enumerate(tocs_dict.items(), start=1):
                text = (
                    htmlize(f"color[var(--accent-color)]`{i}.` {sec}")
                    + f"<p>{slide.index}</p>"
                )
                def jump_to_slide(change):
                    self.navigate_to(change.owner._index)
                    self.widgets.buttons.toc.click()

                p_btn = HtmlWidget(text, click_handler=jump_to_slide)
                p_btn._index = int(slide.index) # int to remove attribute access

                children.append(
                    p_btn.add_class("toc-item").add_class(f"s{slide._index}")
                )  # class for CSS

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
    
# Make available as Singleton Slides
_private_instance = Slides()  # Singleton in use namespace
# This is overwritten below to just have a singleton

class fsep:
    """Frame separator! If it is just after `write` command, columns are incremented too.
    You can import it on top level or use as `Slides.fsep`.

    - Use `fsep()` to split code into frames. In markdown slides, use two dashes --.
    - Use `fsep.loop(iterable)`/`fsep.enum(iterable)` to split after each item in iterable automatically.
    - Use `fsep.join()` once under a slide to show frames incrementally. In markdown slides, use %++.
    - Content before first frame separator is added on all frames. This helps adding same title once.
    """
    _app = _private_instance
    
    def __init__(self):
        self._app.verify_running("Cant use fsep in a capture context other than slides!")
        self._app.this._widget.add_class("Frames")
        self._app.this._fsep = getattr(self._app.this, '_fsep',self._app.format_css({}).as_widget()) # create once
        self._app.frozen(self._app.this._fsep, {"FSEP": "","skip-export":"no need in export"}).display()

    @classmethod
    def loop(cls, iterable):
        "Loop over iterable. Frame separator is add before each item and at end of the loop."
        cls._app.verify_running()
        if not isinstance(iterable, Iterable) or isinstance(iterable, (str, bytes, dict)):
            raise TypeError(f"iterable should be a list-like object, got {type(iterable)}")
        
        for item in iterable:
            cls() # put separator before
            yield item
        else:
            cls() # put one last to separate this block
    
    @classmethod
    def enum(cls, iterable, start=0):
        "Enumerate iterable with automatically adding frame separators."
        return enumerate(cls.loop(iterable), start=start)
    
    @classmethod
    def join(cls):
        """Join frames incrementally. This enables `write` and `multicol` followed by a frame separator to increment as well.
        Use %++ in makdown in place of this.
        """
        cls._app.verify_running()
        cls._app.this._split_frames = False


class Slides:
    _version = (
        _private_instance.version
    )  # This is for initial use, and will be overwritten by property version
    __doc__ = textwrap.dedent(
        """
    Interactive Slides in IPython Notebook. Only one instance can exist.
    `auto_focus` can be reset from settings and enable jumping back to slides after a cell is executed. 
    `settings` are passed to `Slides.settings.apply` if you like to set during initialization.
    
    To suppress unwanted print from other libraries/functions, use:
    ```python
    with slides.suppress_stdout():
        some_function_that_prints() # This will not be printed
        print('This will not be printed either')
        display('Something') # This will be printed
    ```
    ::: note-info
        The methods under settings starting with `Slides.settings.set_` returns settings back to enable chaining 
        without extra typing, like `Slides.settings.set_animation().set_layout()...` .
    
    ::: note-tip
        - Use `Slides.instance()` class method to keep older settings. `Slides()` apply default settings every time.
        - Run `slides.demo()` to see a demo of some features.
        - Run `slides.docs()` to see documentation.
        - Instructions in left settings panel are always on your fingertips.
        - Creating slides in a batch using `Slides.create` is much faster than adding them one by one.
        - In JupyterLab, right click on the slides and select `Create New View for Output` for optimized display.
        - To jump to source cell and back to slides by clicking buttons, set `Windowing mode` in Notebook settings to `defer` or `none`.
        - See `Slides.xmd_syntax` for extended markdown syntax, especially variables formatting.
    
    ::: note-info
        `Slides` can be indexed same way as list for sorted final indices. For indexing slides with given number, use comma as `Slides[number,] -> Slide` 
        or access many via list as `Slides[[n1,n2,..]] -> tuple[Slide]`. Use indexing with given number to apply persistent effects such as CSS.
    """
    )
    @classmethod
    def instance(cls):
        "Access current instnace without changing the settings."
        return _private_instance

    def __new__(
        cls,
        extensions=[],
        auto_focus = True,
        **settings
        ):
        "Returns Same instance each time after applying given settings. Encapsulation."
        instance = cls.instance()
        instance.fsep = fsep # attach for use under slides
        instance.__doc__ = cls.__doc__  # copy docstring
        instance.extender.extend(extensions) # globally once
        instance.settings.apply(**settings)
        instance.widgets.checks.focus.value = auto_focus # useful
        return instance

    # No need to define __init__, __new__ is enough to show signature and docs
