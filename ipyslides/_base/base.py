"Inherit Slides class from here. It adds useful attributes and methods."
import re, textwrap
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
from ..formatters import XTML, htmlize, slidebound
from ..xmd import error, resolve_included_files, _parse_as_snapshots, _stream_chunks
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
        
    def _exec_synced_src(self, content):
        if not isinstance(content, str): #check path later or it will throw error
            raise TypeError(f"content expects a makrdown string, got {content!r}")
        
        # included files should be able to trigger updates even if main file not edited yet, so we track them as assets
        if hasattr(self, '_src_watcher'):
            self._src_watcher.assets = re.findall(r'include\`(.*?)\`',content, flags = re.DOTALL)
        
        # Now flatten incuded files, after detecting them as assets above
        content = resolve_included_files(content)
        content = self._process_citations(content) # after resolve, enable citations form included files
        
        chunks = list(_stream_chunks(content, '---'))
        handles = self.create(range(0, len(chunks))) # create slides faster or return older
        
        last_updated = None
        for chunk, hdl in zip(chunks, handles):
            if chunk != hdl._markdown:
                with self.slide(hdl.number) as last_updated:
                    self.src(chunk, **(hdl._md_vars if isinstance(hdl._md_vars, dict) else {})) # preserve variables if they were updated from python code
        
        self._next_number = len(handles) # update next number to avoid overwrites from python on these slides accidentally
        if last_updated: 
            self.navigate_to(last_updated.index) # go to last edited slide
    
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
    
    def sync_with_file(self, path, interval=500):
        r"""Auto update slides when content of markdown file changes. You can stop syncing using `Slides.unsync` function.
        interval is in milliseconds, 500 ms default. Read `Slides.slide` docs about content of file.
        
        The variables inserted in file content are used from notebook's global scope.

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
            Synced file includes all slides from title slide onwards, you can insert placeholder variables using `\%{variable_name}` 
            in the content that will receive values from the notebook's global scope as soon as that variable is defined.
        
        ::: note-tip
            To debug the linked file or included file, use EOF on its own line to keep editing and clearing errors.
        """
        if not self.inside_jupyter_notebook(self.sync_with_file):
            raise Exception("Notebook-only function executed in another context!")
        
        if self.this:
            raise RuntimeError('Sync file must be called outside of an active slide context!')
        
        path = Path(path) # keep as Path object
        
        if not path.is_file():
            raise FileNotFoundError(f"File {path!r} does not exists!")
        
        if not isinstance(interval, int) or interval < 100:
            raise ValueError("interval should be integer greater than 100 millieconds.")
        
        if hasattr(self, '_src_watcher'):
            self.unsync() # clear any existing file watcher before setting a new one
        
        self._src_watcher = FileWatcher(path, interval=interval)
        
        # First call after watcher set, so it can observe included files immediately, 
        # and errors must be caught before going forward
        self._exec_synced_src(path.read_text(encoding="utf-8")) 

        def update_target_slides(change):
            value = change["new"]
            if not value or not hasattr(value, 'path'): return # file deleted or None value
            
            try: 
                self._exec_synced_src(value.path.read_text(encoding="utf-8")) 
                self.notify('x') # need to remove any notification from previous error
                self._unregister_postrun_cell() # No cells buttons from inside file code run
            except:
                e, text = traceback.format_exc(limit=0).split(':',1) # only get last error for notification
                self.notify(f"{error('SyncError','something went wrong')}<br/>{error(e,text)}",20)
        
        self._src_watcher.observe(update_target_slides, "value") # start observing changes to the file
        display(self._src_watcher) # must be displayed to work
        self._unregister_postrun_cell() # avoid unnessary scroll button after postrun cell here

    def unsync(self):
        "Stop syncing markdown file synced with `Slides.sync_with_file` function."
        if getattr(self, '_src_watcher', None):
            self._src_watcher.stop()  # stop the file watcher
            self._src_watcher.close() # clear the displayed watcher at frontend
            del self._src_watcher  # remove reference to the watcher
        else:
            print("There was no markdown file linked to sync!")
            