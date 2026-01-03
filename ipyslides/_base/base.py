"Inherit Slides class from here. It adds useful attributes and methods."
import os, re, textwrap
import traceback
from pathlib import Path
from contextlib import ContextDecorator

from IPython.display import display

from . import _syntax
from .widgets import Widgets
from .navigation import Navigation
from .settings import Settings
from .notes import Notes
from .export_html import _HhtmlExporter
from .slide import _build_slide
from ..formatters import XTML, htmlize
from ..xmd import error, get_slides_instance, resolve_included_files, _matched_vars, _parse_pages, _stream_chunks
from ..utils import _css_docstring


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
        return _parse_pages(_syntax.css_animations)
   
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

    def on_load(self, func):
        """
        Decorator for running a `func(slide)` when slide is loaded into view.
        Use this to e.g. notify during running presentation. func accepts single arguemnet, slide.
        Return value could a cleanup function (which also accepts slide as single argument) executed when slide exits.
        
        See `Slides.docs()` for few examples.

        ::: note-warning
            - If you use this to change global state of slides, return a clean up function which accepts slide as argument.
            - This can be used only single time per slide, overwriting previous function.
        """
        self.verify_running('on_load decorator can only be used inside slide constructor!')
        self.this._on_load_private(func) # This to make sure if code is correct before adding it to slide

    def _update_tmp_output(self, *objs):
        "Used for CSS/animations etc. HTML widget does not work properly."
        if self.is_jupyter_session():
            self.widgets._tmp_out.clear_output(wait=True)
            with self.widgets._tmp_out:
                display(*objs)
        
    def _from_markdown(self, start, /, content, synced=False, _vars=None):
        "Sames as `Slides.build` used as a function."
        if self.this:
            raise RuntimeError('Creating new slides under an already running slide context is not allowed!')
        
        if not isinstance(content, str): #check path later or it will throw error
            raise TypeError(f"content expects a makrdown string, got {content!r}")
        
        content = re.split(r'^\s*EOF\s*$',content, flags = re.MULTILINE)[0]
        md_kws = _vars or {} # given from build function call

        if synced:
            content = self._process_citations(content)
        
        chunks = list(_stream_chunks(content, '---'))
        handles = self.create(range(start, start + len(chunks))) # create slides faster or return older
        mdvars  = [{k:v for k,v in md_kws.items() if k in _matched_vars(chunk)} for chunk in chunks] # vars used in each chunk

        for chunk, hdl, mvs in zip(chunks, handles, mdvars):
            # Must run under this function to create frames with two dashes (--) and update only if things/variables change
            if any(['Out-Sync' in hdl._css_class, chunk != hdl._markdown, mvs != hdl._md_vars]):
                with self._loading_splash('Building markdown slides...'):
                    hdl._md_vars = mvs # set corresponding vars to access while building slide
                    self._slide(f'{hdl.number} -m', chunk)
            else: # when slide is not built, scroll buttons still need an update to point to correct button
                self._slides_per_cell.append(hdl)
        
        # Return refrence to slides for quick update
        return handles
    
    def _process_citations(self, content):
        match1, *others = re.findall(r'^```citations.*?^```|^:::\s*citations.*?(?=^:::|\Z|^\S)', content, flags= re.DOTALL | re.MULTILINE)
        if others:
            raise ValueError(f"Only a single block of citations is parsed, found {len(others) + 1} blocks\n{(match1, *others)}")
        
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
        
        start = self._fix_slide_number(start_slide_number)
        
        # NOTE: Background threads and other methods do not work. Do NOT change this way
        # First call itself before declaring other things, so errors can be captured safely
        self._from_markdown(start, resolve_included_files(path.read_text(encoding="utf-8")), synced=True) 
        self.widgets._timer.clear() # remove previous updates
        self._mtime = os.stat(path).st_mtime
        included_files = set()

        def update():
            if path.is_file():
                # Track whichever file is last edited from included or itself
                mtime = max(os.stat(f).st_mtime for f in [path, *included_files] if f.is_file())
                out_sync = any(['Out-Sync' in s._css_class for s in self.cited_slides]) or False
                if out_sync or (mtime > self._mtime):  # set by interaction widget
                    self._mtime = mtime
                    try: 
                        content = path.read_text(encoding="utf-8")
                        # included files will be one step behind in sync, beacuse they are only detectable now
                        included_files.update(
                            map(Path, re.findall(r'include\`(.*?)\`',content, flags = re.DOTALL))
                        ) 
                        self._from_markdown(start, 
                            resolve_included_files(content), # add included file text to be detected for changes
                            synced=True # only one citation block allowed for consistency
                        ) 
                        self.notify('x') # need to remove any notification from previous error
                        self._unregister_postrun_cell() # No cells buttons from inside file code run
                    except:
                        e, text = traceback.format_exc(limit=0).split(':',1) # only get last error for notification
                        self.notify(f"{error('SyncError','something went wrong')}<br/>{error(e,text)}",20)
            else:
                self.notify(error("SyncError", f"file {path!r} no longer exists!").value, 20)
        
        self.widgets._timer.run(interval, update, loop = True)
        print(f"Syncing content from file {path!r}\nYou can use `Slides.unsync()` to stop syncing.")
        

    def unsync(self):
        "Stop syncing markdown file synced with `Slides.sync_with_file` function."
        if self.widgets._timer._callback[0]:
            self.widgets._timer.clear()
        else:
            print("There was no markdown file linked to sync!")
    
    def build_(self, content = None, /, **vars):
        "Same as `build` but no slide number required inside Python file!"
        if self.inside_jupyter_notebook(self.build_):
            raise Exception("Notebook-only function executed in another context. Use build without _ in Notebook!")
        return self.build(self._next_number, content, **vars)

    class build(ContextDecorator):
        r"""Build slides with a single unified command in three ways:
        
        1. code`slides.build(number, callable)` to create a slide from a `callable(slide)` immediately, e.g. code`lambda s: slides.write(1,2,3)` or as a decorator.
            - Docstring of callable (if any) is parsed as markdown before calling function.
        2. code`with slides.build(number):` creates single slide. Equivalent to code`%%slide number` magic.
            - Use code`PAGE()` from top import or code`Slides.PAGE()` to split content into pages/sub slides.
            - Use code`for item in PAGE.iter(iterable):` block to automatically add page separator.
            - Use code`PAGE()` / code`PAGE.iter(...)` to display content on each page incrementally in parts.
            - Contents displayed by `write` function can be split into parts if `write` is called after `PART()` adjacently.
        3. code`slides.build(number, str, **vars)` creates many slides with markdown content. Equivalent to code`%%slide number -m` magic in case of one slide.
            - Page separator is double dashes `--` and slides separator is triple dashes `---`. Same applies to code`Slides.sync_with_file` too.
            - Use `++` to separted content into parts for incremental display on ites own line with optionally adding content after one space.
            - Markdown `columns` can be displayed incrementally if `++` is used (alone on line) before these blocks as a trigger.
            - See `slides.xmd.syntax` for extended markdown usage.
            - To debug markdown content, use EOF on its own line to keep editing and clearing errors. Same applies to `Slides.sync_with_file` too.
            - Variables such as \%{var} can be provided in `**vars` (or left during build) and later updated in notebook using `rebuild` method on slide handle or overall slides.
            - If an f-string is provided, variables in f-string are resolved eagerly and never get updated on rebuild including lazy ones provided by `Slides.esc`.
        
        
        ::: note-tip
            - In all cases, `number` could be used as `-1`.
            - Use yoffet`integer in percent` in markdown or code`Slides.this.yoffset(integer)` to make all frames align vertically to avoid jumps in increments.
            - You can use code`build_(...)` (with underscore at end) in python file instead of code`build(-1,...)`.
            - `**vars` are ignored silently if `build` is used as contextmanager or decorator.
        """
        @property
        def _app(self):
            kls = type(self)
            if getattr(kls, '_slides', None) is None:
                kls._slides = get_slides_instance()
            return kls._slides
        
        def __new__(cls, slide_number, content = None, /, **vars):
            self = super().__new__(cls) # instance
            self._snumber = self._app._fix_slide_number(slide_number)
            
            with self._app.code.context(returns = True, depth=3, start = True) as code:
                if (content is not None) and any([code.startswith(c) for c in ('@', 'with')]):
                    raise ValueError("content should be None while using as decorator or contextmanager!")
                
                # using fmt is tempting to delegate vars automatically but it raises error if var not found, 
                # which is against whole philosophy of lazy evaluation and rebuild.
                # Also, using vars in decorator mode for function docstring is a bad idea as it
                # will be evaluated only once and never updated on rebuild, also it is not supported by python syntax.
                if isinstance(content, str) and not code.startswith('with'): 
                    return self._app._from_markdown(self._snumber, content, _vars = vars)

                if callable(content) and not code.startswith('with'):
                    with _build_slide(self._app, self._snumber) as s: 
                        s._set_source(self._app.code.from_source(content).raw,'python') 
                        if (doc := getattr(content, '__doc__', None)):
                            self._app.xmd(doc, returns=False)
                        content(s) # call directly, set code before to make avaiable in function
                
                    return s
            
            if content is not None:
                raise ValueError(f"content should be None, str, or callable. got {type(content)}")

            return self # context manager

        def __enter__(self):
            "Use as contextmanager to create a slide."
            code = self._app.code.context(returns=True, depth = 3).__enter__()
            self._context = _build_slide(self._app, self._snumber)
            slide = self._context.__enter__()
            slide._set_source(code.raw, "python")
            return slide

        def __exit__(self, *args):
            return self._context.__exit__(*args)
        
        def __repr__(self):
            return f"<ContextDecorator build at {hex(id(self))}>"
        
        def __call__(self, func):
            "Use @build decorator. func accepts slide as argument."
            type(self)(self._snumber, func)
            

    def demo(self):
        "Demo slides with a variety of content."
        from .._demo import demo_slides
        return demo_slides(self)
        
        
    def docs(self):
        "Create presentation from docs of IPySlides."
        self.close_view() # Close any previous view to speed up building (minor effect but visually better)
        self.clear() # Clear previous content
        self.create(range(21)) # Create slides faster
        
        from ..core import Slides

        self.set_citations({'A': 'Citation A', 'B': 'Citation B'})
        self.settings.footer(text=self.get_logo("1em") + "IPySlides Documentation", date=None)

        with self.build(0): # Title page
            self.this.set_bg_image(self.get_logo(),0.25, filter='blur(10px)', contain=True)
            self.write(f'## IPySlides {self.version} Documentation\n### Creating slides with IPySlides')
            self.center(self.fmt('''
                alert`Abdul Saboor` ^`1`
                                 
                today``
                {.text-small}
                                 
                %{logo}
                                 
                ::: text-box
                    ^`1`My University is somewhere in the middle of nowhere
                
                ::: info
                    Right click (or click on footer) to open context menu for accessing settings, table of contents etc.  
                ''', logo = self.get_logo("4em"))).display()
        
        self.build(-1, '''
            ```md-after
                section`Introduction` 
                ```columns .block-green
                toc[True]`## Table of contents`
                +++
                ### This is summary of current section
                Oh we can use inline columns stack`Column A || Column B` here and what not!
                %{btn}
                ```
            ```''', btn = self.draw_button)
            
        with self.build(-1):
            self.PAGE()
            self.write('# Main App')
            self.doc(Slides).display()
            
            self.PAGE()
            self.write('# Jump between slides')
            self.doc(self.link, 'Slides').display()
            with self.code.context(returns=True) as c:
                skipper = self.link('Skip to dynamic content', 'Back to link info', icon='arrow', back_icon='arrowl')
                skipper.origin.display() # skipper.target is set later somewhere, can do backward jump too
            c.display()
        
            self.PAGE()
            self.write('## Adding Slides section`Adding Slides and Content`')
            self.write('Besides function below, you can add slides with `%%slide number [-m]` magic as well.\n{.note .info}')
            self.write([self.doc(self.build,'Slides'), self.doc(self.sync_with_file,'Slides')])
        
            self.PAGE()
            self.write('''
                ## Important Methods on Slide
                ::: note-warning
                    - Use slide handle or `Slides[number,]` to apply these methods becuase index can change on new builds.
                    - Use `Slides[start:stop:step]` to apply operations on many slides at once such as code`Slides[2:5].vars.update(...)`.
            ''')
            self.doc(self[0], members='yoffset vars set_animation set_bg_image update_display get_source show set_css'.split(), itself = False).display()
            self.css_syntax.display()
        
        with self.build(-1): 
            self.xmd.syntax.display()
            
        with self.build(-1):
            self.PAGE()
            self.write('## Adding Content')
            self.write('Besides functions below, you can add content to slides with `%%xmd`,`%xmd` as well.\n{.note .info}')
            self.write(self.doc(self.write,'Slides'), [self.doc(self.xmd,'Slides'),self.doc(self.as_html,'Slides'),self.doc(self.as_html_widget,'Slides'),self.doc(self.html,'Slides')])
        
            self.PAGE()
            self.write('## Adding Speaker Notes')
            self.write([rf'styled["note success"]`You can use alert`notes\`notes content\`` in markdown.`',
                       'This is experimental feature, and may not work as expected.\n{.note-error .error}'])
            self.doc(self.notes,'Slides.notes', members = True, itself = False).display()
                   
            self.PAGE()
            self.write('## Displaying Source Code')
            self.write('In markdown, the block `md-[before,after,var_name]` parses and displays source as well.')
            self.doc(self.code,'Slides', members = True, itself = True).display()
        
        self.build(-1, r'section`//Layout and color["yellow","black"]`Theme` Settings//` toc`### Contents`')
        
        with self.build(-1) as s:
            s.set_css({
                '.highlight': {'background':'#8984'}
            }, bg1 = 'linear-gradient(45deg, var(--bg3-color), var(--bg2-color), var(--bg3-color))')
            self.styled('## Layout and Theme Settings', 'info', border='1px solid red').display()
            self.doc(self.settings,'Slides', members=True,itself = True).display()
                
        with self.build(-1):
            self.write('## Useful Functions for Rich Content section`//Useful Functions for alert`Rich Content`//`')
            self.doc(self.alt,'Slides').display()
            
            members = sorted((
                'AnimationSlider alert bokeh2html bullets esc styled fmt code color details doc '
                'today error focus html iframe image frozen notify plt2html '
                'raw set_dir sig stack table textbox suppress_output suppress_stdout svg vspace'
            ).split())
            self.doc(self, 'Slides', members = members, itself = False).display()

        with self.build(-1):
            self.write(r'''
                ## Citations and Sections
                Use syntax alert`cite\`key\`` / alert`\@key` to add citations which should be already set by code`Slides.set_citations(data)` method.
                Any key that ends with `!` is displayed inplace. Number of columns in displayed citations are determined by 
                code`Slides.settings.layout(..., ncol_refs = int)` or locally by code`Slides.refs(ncol)`. @A
                       
                Add sections in slides to separate content by alert`section\`text\``. Corresponding table of contents
                can be added with alert`toc\`title\``.
            ''')
            self.doc(self, 'Slides', members = ['set_citations'], itself = False).display()
            
        with self.build(-1):
            skipper.target.display() # Set target for skip button
            self.write('## Dynamic Content')
            
            with self.capture_content() as cap, self.code.context():
                import time

                @self.dl.interact(post_init = lambda self: self.set_css(dict({'.out-main': dict(height='2em')},background='var(--bg2-color)')), date = False, btn = self.dl.button())  # self is Slides here
                def update_time(date, btn): 
                    local_time = time.localtime()
                    objs = ['Time: {3}:{4}:{5}'.format(*local_time)] # Print time in HH:MM:SS format
                    if date:
                        objs.append('Date: {0}/{1}/{2}'.format(*local_time))
                    self.stack(objs).display()

            with self.code.context(returns=True) as c:
                import datetime
                
                @self.on_load  # self is Slides here
                def push_toast(slide):
                    t = datetime.datetime.now()
                    time = t.strftime('%H:%M:%S')
                    self.notify(f'Notification at {time} form slide {slide.index} and frame {slide.indexf}', timeout=5)
                    return lambda s: self.notify('x') # clear notification immediately on exit by sending 'x'
            
            self.write(
                [self.doc(self.dl.interact,'ipyslides.dashlab')], 
                [*cap.outputs, c, self.doc(self.on_load,'Slides')],
            )
    
        self.build(-1, """
        ```md-src.collapsed
        stack[(3,7)]`//
        ## Content Styling
        You can **style**{.error} or **color["teal"]`colorize`** your *content*{: style="color:hotpink;"} and *color["hotpink","yellow"]`text`*.
        Provide **CSS**{.info} for that using code`Slides.html("style",...)` or use some of the available styles. 
        See these **styles**{.success} with `Slides.css_styles` property as shown on right.
        || %{self.css_styles}
        //`     
        ```
        <md-src/>
        """, self=self)
        
        with self.build(-1):
            self.css_animations.display()
        
        self.build(-1, '''
        ## Highlighting Code
        [pygments](https://pygments.org/) is used for syntax highlighting cite`A`.
        You can **highlight**{.error} code using `Slides.code` cite`B` or within markdown using named code blocks:
        ```python
        import ipyslides as isd
        ```
        ```javascript
        import React, { Component } from "react";
        ```
        Source code of slide can be embeded via variable too: %{self.this.source}
        ''', self=self)

        
        with self.build(-1):
            self.write('## Loading from File/Exporting to HTML section`Loading from File/Exporting to HTML`')
            self.write('You can parse and view a markdown file. The output you can save by exporting notebook in other formats.\n{.note .info}')
            self.write([self.doc(attr,'Slides') for attr in (self.sync_with_file,self.demo,self.docs,self.export_html)])
        
        self.build(-1, 'section`Advanced Functionality` toc`### Contents`')

        with self.build_() as s:
            self.write("## Adding content on frames incrementally")
            self.frozen(widget := (code := s.get_source()).as_widget()).display()
            # frozen in above line get oldest metadata for export
            def highlight_code(slide): widget.value = code.focus(range(slide.indexf + 1)).value
            self.on_load(highlight_code)
        
            for ws, cols in self.PART.iter(zip([None, (2,3),None], [(0,1),(2,3),(4,5,6,7)])):
                cols = [self.html('h1', f"{c}",style="background:var(--bg3-color);margin-block:0.05em !important;") for c in cols]
                self.write(*cols, widths=ws, css_class='anim-group anim-wipe-right')
                    
        with self.build(-1) as s:
            self.write('## Adding User defined Objects/Markdown Extensions')
            self.write(
                self.hold(display, self.html('h3','I will be on main slides',css_class='warning'),
                    metadata = {'text/html': '<h3 class="warning">I will be on exported slides</h3>'}
                ), # Can also do 'Slides.serilaizer.get_metadata(obj)' if registered
                s.get_source(), widths = [1,3]
            )
            self.write(r'If you need to serialize your own or third party objects not serialized by this module, you can use `\@Slides.serializer.register` to serialize them to html.\n{.note .info}')
            self.doc(self.serializer,'Slides.serializer', members = True, itself = False).display()
            self.write('**You can also extend markdown syntax** using `markdown extensions`, ([See here](https://python-markdown.github.io/extensions/) and others to install, then use as below):')
            self.doc(self.xmd.extensions,'Slides.xmd.extensions', members = True, itself = False).display()
        
        with self.build(-1):
            self.write(r'''
            ## Focus on what matters
            - Most of supported elements can be focused by default like images, matplotlib, bokeh, PIL image, altair plotly, dataframe, etc.
            - You can also enable focus on an object/widget by wrapping it inside \`Slide.focus\` function conveniently.
            - You can also enable focus by manully adding `focus-self`, `focus-child` classes to an element. To prevent focus under as `focus-child` class, use `no-focus` class.
            
            ::: focus-self block-red
                ### Focus on Me 😎
                Double click to focus on this block. Click at top right button or double click to exit.
            ''')

        with self.build(-1):
            with self.capture_content() as c:
                with self.code.context():
                    import ipywidgets as ipw
                    btn = ipw.Button(description='Chevron-Down Icon',icon='chevrond')    
                    self.write(btn)

            group = zip(self.icon.available[::2], self.icon.available[1::2]) # make 4 columns table
            self.write(['''
                ## SVG Icons
                Icons that apprear on buttons inslides (and their rotations) available to use in your slides as well
                besides standard ipywidgets icons.
                ''', *c.outputs, 'line`200`**Source code of this slide**',self.this.get_source()], 
                self.table([(f'`{j}`', self.icon(j,color='crimson').svg,f'`{k}`', self.icon(k,color='crimson').svg) for j, k in group],headers=['Name','Icon','Name','Icon']),
            widths=[3,2])
                
            
        with self.build_():
            self.write("""
                # Auto Slide Numbering
                Use alert`-1` as placeholder to update slide number automatically. 
                       
                - In Jupyter notebook, this will be updated to current slide number. 
                - In python file, it stays same.
                - You need to run cell twice if creating slides inside a for loop while using `-1`.
                - Additionally, in python file, you can use ` Slides.build_ ` instead of using `-1`.
                       
                ::: note-warning
                    Some kernels may not support auto slide numbering inside notebook.
            """)
        
        self.build(-1, lambda s: self.write(['## Presentation Code section`Presentation Code`',self.docs]))
        self.navigate_to(0) # Go to title
        return self