"Inherit Slides class from here. It adds useful attributes and methods."
import os, re, textwrap
import traceback
import inspect
from pathlib import Path

from IPython.display import display

from . import _syntax
from .widgets import Widgets
from .navigation import Navigation
from .settings import Settings
from .notes import Notes
from .export_html import _HhtmlExporter
from .slide import SlideGroup, _build_slide
from ..formatters import XTML, htmlize, slidebound
from ..xmd import error, get_slides_instance, resolve_included_files, _matched_vars, _parse_as_snapshots, _stream_chunks
from ..utils import _css_docstring
from ..dashlab import FileWatcher


class BaseSlides:
    def __init__(self):
        self._uid = f'{self.__class__.__name__}-{id(self)}' # Unique ID for this instance to have CSS, should be before settings
        self.widgets = Widgets()
        self._navigation = Navigation(self) # should be after widgets
        self.settings = Settings(self, self.widgets)
        self.export_html = _HhtmlExporter(self).export_html
        self.notes = Notes(self, self.widgets) # Needs main class for access to notes
        self.widgets.checks.toast.observe(self._toggle_notify,names=['value'])
    
    def __setattr__(self, name: str, value):
        if not name.startswith('_') and hasattr(self, name):
            raise AttributeError(f"Can't reset attribute {name!r} on {self!r}")
        self.__dict__[name] = value
    
    def notify(self,content,timeout=5):
        """Send inside notifications for user to know whats happened on some button click. 
        Send 'x' in content to clear previous notification immediately."""
        if self.widgets.checks.toast.value:
            return self.widgets._push_toast(content,timeout=timeout)
    
    def _toggle_notify(self,change):
        "Blocks notifications if check is not enabled."
        self.notify('Notifications are enabled now!') # will only show when on
        if not self.widgets.checks.toast.value:
            self.widgets._push_toast('x') # clean previous notifications by this signal
    
    @property
    def uid(self):
        "Unique CCS class for slides."
        return self._uid
    
    @property
    def css_styles(self):
        """CSS styles for markdown or `styled` command."""
        return XTML(htmlize(_syntax.css_styles))

    @property
    def css_syntax(self):
        "CSS syntax for use in Slide.set_css, Slides.html('style', ...) etc."
        return XTML(_css_docstring)
    
    @property
    def css_animations(self):
        "CSS animations for use in content blocks."
        return _parse_as_snapshots(_syntax.css_animations)
   
    def get_source(self, title = 'Source Code', **kwargs):
        "Return source code of all slides except created as frames with python code. kwargs are passed to `Slides.code`."
        sources = []
        for slide in self[:]:
            if slide._source['text']:
                kwargs['name'] = f'{slide._source["language"].title()}: Slide {slide.index}' #override name
                sources.append(slide.get_source(**kwargs))
            
        if sources:
            return self.frozen(f'<h2>{title}</h2>' + '\n'.join(s.value for s in sources),{})
        else:
            self.html('p', 'No source code found.', css_class='info')

    @slidebound("on_load decorator")
    def on_load(self, func):
        """
        Decorator for running a `func(slide)` when slide is loaded into view.
        Use this to e.g. notify during running presentation. func accepts single arguemnet, slide.
        Return value could a cleanup function (which also accepts slide as single argument) executed when slide exits.
        
        See `ipyslides.docs()` for few examples.

        ::: note-warning
            - If you use this to change global state of slides, return a clean up function which accepts slide as argument.
            - This can be used only single time per slide, overwriting previous function.
        """
        # inside BaseSlides.on_load, before self.this._on_load_private(func)
        uw_func = inspect.unwrap(func)

        if inspect.isgeneratorfunction(uw_func):
            raise TypeError("@on_load does not support generator functions.")

        if len(inspect.signature(uw_func).parameters) != 1:
            raise ValueError("@on_load callback must accept exactly one argument: slide.")
        
        self.this._on_load_private(func) # This to make sure if code is correct before adding it to slide
        
    def _from_markdown(self, start, /, content, synced=False, _vars=None):
        "Sames as `Slides.build` used as a function."
        if self.this:
            raise RuntimeError('Creating new slides under an already running slide context is not allowed!')
        
        if not isinstance(content, str): #check path later or it will throw error
            raise TypeError(f"content expects a makrdown string, got {content!r}")
        
        md_kws = _vars or {} # given from build function call

        if synced:
            content = self._process_citations(content)
        
        # included files should be able to trigger updates even if main file not edited yet, so we track them as assets
        if synced and hasattr(self, '_watcher'):
            self._watcher.assets = re.findall(r'include\`(.*?)\`',content, flags = re.DOTALL)
        
        # Now flatten incuded files, after detecting them as assets above
        content = resolve_included_files(content)
        
        chunks = list(_stream_chunks(content, '---'))
        handles = self.create(range(start, start + len(chunks))) # create slides faster or return older
        mdvars  = [{k:v for k,v in md_kws.items() if k in _matched_vars(chunk)} for chunk in chunks] # vars used in each chunk

        last_updated = None
        for chunk, hdl, mvs in zip(chunks, handles, mdvars):
            self._next_number = hdl.number + 1 # If markdown does not change, slide number still needs to be updated for next cell to avoid overwites
            # Must run under this function to create frames with two dashes (--) and update only if things/variables change
            if any([chunk != hdl._markdown, mvs != hdl._md_vars]):
                with self.slide(hdl.number) as last_updated:
                    self.src(chunk, **mvs) # builds full markdown slide
                    
            else: # when slide is not built, scroll buttons still need an update to point to correct button
                self._slides_per_cell.append(hdl)
                
        if synced and last_updated: self.navigate_to(last_updated.index) # only in sync mode
        # Return refrence to slides for quick update
        return SlideGroup(handles)
    
    def _process_citations(self, content):
        matches = re.findall(r'^```citations.*?^```|^:::\s*citations.*?(?=^:::|\Z|^\S)', content, flags= re.DOTALL | re.MULTILINE)
        if len(matches) > 1:
            raise ValueError(f"Only a single block of citations is parsed, found {len(matches)} blocks\n{matches}")
        
        match1 = matches[0] if matches else ''
        content = content.replace(match1, '') # clean up
        if getattr(self,'_bib_md','') != match1:
            self._bib_md = match1 # set for next test
            _, refs = match1.split('\n', 1) # split into mode and references
            refs = refs.rstrip('` ') # remove trailing ` or space, 
            self.set_citations(textwrap.dedent(refs))
        return content
    
    def sync_with_file(self, start_slide_number, /, path, interval=500):
        r"""Auto update slides when content of markdown file changes. You can stop syncing using `Slides.unsync` function.
        interval is in milliseconds, 500 ms default. Read `Slides.build` docs about content of file.
        
        The variables inserted in file content are used from top scope.

        You can add files inside linked file using include\\`file_path.md\\` syntax, which are also watched for changes.
        This helps modularity of content, and even you can link a citation file in markdown format as shown below. Read more in `Slides.xmd.syntax` about it.

        ```markdown
         ```citations
         @key1: Saboor et. al., 2025
         @key2: A citations can span multiple lines, but key should start on new line
         <!-- Or put this content in a file 'bib.md' and then inside citations block use include`bib.md` -->
         ```
        ```
        
        ::: note-tip
            To debug the linked file or included file, use EOF on its own line to keep editing and clearing errors.
        """
        if not self.inside_jupyter_notebook(self.sync_with_file):
            raise Exception("Notebook-only function executed in another context!")
        
        path = Path(path) # keep as Path object
        
        if not path.is_file():
            raise FileNotFoundError(f"File {path!r} does not exists!")
        
        if not isinstance(interval, int) or interval < 100:
            raise ValueError("interval should be integer greater than 100 millieconds.")
        
        if hasattr(self, '_watcher'):
            self.unsync() # clear any existing file watcher before setting a new one
        
        start = self._fix_slide_number(start_slide_number)
        self._watcher = FileWatcher(path, interval=interval)
        
        # First call after watcher set, so it can observe included files immediately, 
        # and errors must be caught before going forward
        self._from_markdown(start, path.read_text(encoding="utf-8"), synced=True) 

        def update_target_slides(change):
            value = change["new"]
            if not value or not hasattr(value, 'path'): return # file deleted or None value
            
            try: 
                self._from_markdown(start, value.path.read_text(encoding="utf-8"), synced=True) 
                self.notify('x') # need to remove any notification from previous error
                self._unregister_postrun_cell() # No cells buttons from inside file code run
            except:
                e, text = traceback.format_exc(limit=0).split(':',1) # only get last error for notification
                self.notify(f"{error('SyncError','something went wrong')}<br/>{error(e,text)}",20)
        
        self._watcher.observe(update_target_slides, "value") # start observing changes to the file
        display(self._watcher) # must be displayed to work
        self._unregister_postrun_cell() # avoid unnessary scroll button after postrun cell here

    def unsync(self):
        "Stop syncing markdown file synced with `Slides.sync_with_file` function."
        if getattr(self, '_watcher', None):
            self._watcher.stop()  # stop the file watcher
            self._watcher.close() # clear the displayed watcher at frontend
            del self._watcher  # remove reference to the watcher
        else:
            print("There was no markdown file linked to sync!")
            