"Inherit Slides class from here. It adds useful attributes and methods."
import os, re, textwrap, json
import traceback
from pathlib import Path
from contextlib import ContextDecorator

from IPython.display import display

from .widgets import Widgets
from .navigation import Navigation
from .settings import Settings
from .notes import Notes
from .export_html import _HhtmlExporter
from .slide import _build_slide
from ..formatters import XTML
from ..xmd import _special_funcs, _md_extensions, error, fmt, get_slides_instance, resolve_included_files
from ..utils import _css_docstring

class BaseSlides:
    def __init__(self):
        self._uid = f'{self.__class__.__name__}-{id(self)}' # Unique ID for this instance to have CSS, should be before settings
        self.widgets = Widgets()
        self._navigation = Navigation(self) # should be after widgets
        self.settings = Settings(self, self.widgets)
        self.export_html = _HhtmlExporter(self).export_html
        self.notes = Notes(self, self.widgets) # Needs main class for access to notes
        
        self.toast_html = self.widgets.htmls.toast
        
        self.widgets.checks.toast.observe(self._toggle_notify,names=['value'])
    
    def __setattr__(self, name: str, value):
        if not name.startswith('_') and hasattr(self, name):
            raise AttributeError(f"Can't reset attribute {name!r} on {self!r}")
        self.__dict__[name] = value
    
    def notify(self,content,timeout=5):
        """Send inside notifications for user to know whats happened on some button click. 
        Send 'x' in content to clear previous notification immediately."""
        return self.widgets._push_toast(content,timeout=timeout)
    
    def _toggle_notify(self,change):
        "Blocks notifications if check is not enabled."
        if self.widgets.checks.toast.value:
            self.toast_html.layout.visibility = 'visible' 
            self.notify('Notifications are enabled now!')
        else:
            self.toast_html.layout.visibility = 'hidden'
    
    @property
    def uid(self):
        "Unique CCS class for slides."
        return self._uid
    
    @property
    def css_styles(self):
        """CSS styles for markdown or `styled` command."""
        return XTML(self.parse('''
        Use any or combinations of these styles in css_class argument of writing functions:
                               
        | css_class         | Formatting Style                                                                    
        |:------------------|:---------------------------------------------------------
         `text-[value]`     | [value] should be one of tiny, small, big, large, huge.
         `align-[value]`    | [value] should be one of center, left, right.
         `rtl`              | اردو،  فارسی، عربی،  ۔۔۔ {: .rtl}
         `info`             | Blue text. Icon ℹ️  for note-info class. {: .info}
         `tip`              | Blue Text. Icon💡 for note-tip class. {: .tip}
         `warning`          | Orange Text. Icon ⚠️ for note-warning class. {: .warning}
         `success`          | Green text. Icon ✅ for note-success class. {: .success}
         `error`            | Red Text. Icon⚡ for note-error class. {: .error}
         `note`             | Text with note icon, can combine other classes as shown above. {: .note}
         `export-only`      | Hidden on main slides, but will appear in exported slides.
         `jupyter-only`     | Hidden on exported slides, but will appear on main slides.
         `block`            | Block of text/objects {: .block}
         `block-[color]`    | Block of text/objects with specific background color from <br> red, green, blue, yellow, cyan, magenta and gray.
         `raw-text`         | Text will be shown as printed style. {: .raw-text}
         `zoom-self`        | Zooms object on hover, when Zoom is enabled. {: .zoom-self}
         `zoom-child`       | Zooms child object on hover, when Zoom is enabled.
         `no-zoom`          | Disables zoom on object when it is child of 'zoom-child'.
        
        Besides these CSS classes, you always have `Slide.set_css`, `Slides.html('style',...) functions at your disposal.
        ''',returns = True))

    @property
    def xmd_syntax(self):
        "Special syntax for markdown."
        return XTML(self.parse(textwrap.dedent(rf'''
        **Extended Markdown**{{.text-large}}
                                               
        Extended syntax for markdown is constructed to support almost full presentation from Markdown.
        
        **Slides-specific syntax**{{.text-big}}
        
        Notes
        : alert`notes\`This is slide notes\``  to add notes to current slide
        
        Slides & Frames Separators
        : Triple dashes `---` is used to split text in slides inside markdown content of `Slides.build` function or markdown file.
        Double dashes `--` is used to split text in frames. Alongwith this `%++` can be used to increment text on framed slide.
        
        Citations
        : - alert`cite\`key1,key2\``/alert`\@key1,\@key2` to add citation to current slide. citations are automatically added in suitable place and should be set once using `Slides.set_citations` function (or see below).
        - With citations mode set as 'footnote', you can add alert`refs\`ncol_refs\`` to add citations anywhere on slide. If `ncol_refs` is not given, it will be picked from layout settings.
        - Force a citation to be shown inline by appending a ! even in footnote mode, such as alert`\@key!`.
        - In the synced markdown file (also its included files) through `Slides.sync_with_file`, you can add citations with block sytnax:                             
        <code>\\`\\`\\`citations [inline or footnote]
        @key1: Saboor et. al., 2025
        @key2: A citations can span multiple lines, but key should start on new line
        \\`\\`\\`</code>
        
        Sections & TOC
        : alert`section\`content\`` to add a section that will appear in the table of contents.
        alert`toc\`Table of content header text\`` to add a table of contents. See `Slides.docs()` for creating a `TOC` accompanied by section summary.
        
        **General syntax**{{.text-big}}
        
        - Use alert`fa\`icon_name\`` to add FontAwesome icons, e.g. fa\\`arrow-right\\` → fa`arrow-right`, fa\\`check\\` → fa`check`, fa\\`info-circle\\` → fa`info-circle` etc.
        - Use syntax \`<link:[unique id here]:origin label>\` and \`<link:[unique id here same as origin]:target [back_label,optional]>\` to jump between slides. See `Slides.link` for more details.
        - Variables can be shown as widgets or replaced with their HTML value (if no other formatting given) using alert`\%{{variable}}` (or legacy alert`\`{{variable}}\``) 
            (should be single curly braces pair wrapped by backticks after other formattings done) syntax. If a format_spec/conversion is provided like
            alert`\%{{variable:format_spec}}` or alert`\%{{variable!conversion}}`, that will take preference.
        - A special formatting alert`\%{{variable:nb}}` is added (`version >= 4.5`) to display objects inside markdown as they are displayed in a Notebook cell.
            Custom objects serialized with `Slides.serializer` or serialized by `ipyslides` should be displayed without `:nb` whenever possible to appear in correct place in all contexts. e.g.
            a matplotlib's figure `fig` as shown in `\%{{fig:nb}}` will only capture text representation inplace and actual figure will be shown at end, while `\%{{fig}}` will be shown exactly in place.
        
        ::: note-tip
            - Variables are automatically updated in markdown when changed in Notebook for slides built purely from markdown.
                - You can also use hl`Slide[number,].rebuild(**kwargs)` to force update variables if some error happens. This is useful for setting unique values of a variable on each slide.
                - Markdown enclosed in hl`fmt(content, **vars)` will not expose encapsulated `vars` for updates later, like static stuff but useful inside python scripts to pick local scope variable.
                - In summary, variables are resolved by scope in the prefrence `rebuild > __main__`. Outer scope variables are overwritter by inner scope variables.
            - Use unique variable names on each slide to avoid accidental overwriting during update.
            - Varibales used as attributes like `\%{{var.attr}}` and indexing like `\%{{var[0]}}`/`\%{{var["key"]}}` will be update only if `var` itself is changed.

        ::: note-warning
            alert`\%{{variable:nb}}` breaks the DOM flow, e.g. if you use it inside heading, you will see two headings above and below it with splitted text. Its fine to use at end or start or inside paragraph.                                    
        
        ::: note-info
            - Widgets behave same with or without `:nb` format spec. 
            - Formatting is done using `str.format` method, so f-string like literal expressions are not supported, but you don't need to supply variables, just enclose text in `Slides.fmt`.
            - Variables are substituted from top level scope (Notebook's hl`locals()`/hl`globals()`). To use variables from a nested scope, use `Slides.fmt`.
        
        - Cells in markdown table can be spanned to multiple rows/columns by attributes | cell text \{{: rowspan="2" colspan="1"}}| inside a cell, should be a space bewteen text and attributes.
        - Escape a backtick with \\, i.e. alert`\\\` → \``. In Python >=3.12, you need to make escape strings raw, including the use of $ \LaTeX $ and re module.
        - alert`include\`markdown_file.md\`` to include a file in markdown format. These files are watched for eidts if included in synced markdown file via `Slides.sync_with_file`.
        - Inline columns/rows can be added by using alert`stack\`Column A | Column B\`` sytnax. You can escape pipe `|` with `\|` to use it as text inside stack. See at end how to nest such stacking.
        - Block multicolumns are made using follwong syntax, column separator is triple plus `+++`:
        
        ```markdown     
         ```multicol widthA widthB .class1.class2
         Column A
         +++
         Column B
         ```
        ```
        
        - Definition list syntax:
        ```multicol 30 10 30 30 .block-red
            Item 1 Header
            : Item 1 details
        
            Item 1 Header
            : Item 1 details
        +++
        vspace`4`👉
        +++
        Item 1 Header
        : Item 1 details

        Item 1 Header
        : Item 1 details
        ```
        
        - Code blocks syntax highlighting. (there is an inline highlight syntax as well alert`hl\`code\``)
        
        ```python
        print('Hello, I was highlighted from a code block!')
        ```     
                                                                              
        - A whole block of markdown can be CSS-classed using syntax
        ```multicol 30 10 30 30 .block-blue
            ::: block-yellow
                Some **bold text**
        +++
        vspace`2`👉
        +++
        ::: block-yellow
            Some **bold text**
        ```
            
        ::: note 
            Above block syntax is enabled using [customblocks](https://github.com/vokimon/markdown-customblocks) 
            which is added by default and can be used to build nested html blocks.
            
        ::: block-red 
            - You can use `Slides.extender` to extend additional syntax using Markdown extensions such as 
                [markdown extensions](https://python-markdown.github.io/extensions/) and 
                [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
            - These markdown extensions are inluded by default hl`{_md_extensions}`.
            - You can serialize custom python objects to HTML using `Slides.serializer` function. Having a 
                `__format__` method in your class enables to use {{obj}} syntax in python formatting and \%{{obj}} in extended Markdown.
        
        - Upto 4 level nesting is parsed using as many `%` within backticks in functions given below. 
            Try alert`stack\`%%% A | stack\`%% B | stack\`% C | stack\` D | E \` %\` %%\` %%%\``. 
            This always parse markdown in `returns=True` mode internally. Use markdown customblocks for general cases.
            Legacy single nesting alert`func\`?content?\`` is also supported for backward compatibility.
        - Other options (that can also take extra args [python code as strings] as alert`func[arg1,x=2,y=A]\`arg0\``) include:
        ''') + '\n' + ',\n'.join(rf'    - alert`{k}`\\`{v}\\`' for k,v in _special_funcs.items()),
        returns = True
        ))
    
    @property
    def css_syntax(self):
        "CSS syntax for use in Slide.set_css, Slides.html('style', ...) etc."
        return XTML(_css_docstring)
   
    def get_source(self, title = 'Source Code', **kwargs):
        "Return source code of all slides except created as frames with python code. kwargs are passed to `Slides.highlight`."
        sources = []
        for slide in self.all_slides:
            if slide._source['text']:
                kwargs['name'] = f'{slide._source["language"].title()}: Slide {slide.index}' #override name
                sources.append(slide.get_source(**kwargs))
            
        if sources:
            return self.frozen(f'<h2>{title}</h2>' + '\n'.join(s.value for s in sources),{})
        else:
            self.html('p', 'No source code found.', css_class='info')

    def on_load(self, func):
        """
        Decorator for running a function when slide is loaded into view. No return value is required.
        Use this to e.g. notify during running presentation. func accepts single arguemnet, slide.
        
        See `Slides.docs()` for few examples.

        ::: note-warning
            - Do not use this to change global state of slides, because that will affect all slides.
            - This can be used single time per slide, overwriting previous function.
        """
        self.verify_running('on_load decorator can only be used inside slide constructor!')
        self.this._on_load_private(func) # This to make sure if code is correct before adding it to slide

    def _update_tmp_output(self, *objs):
        "Used for CSS/animations etc. HTML widget does not work properly."
        if self.is_jupyter_session():
            self.widgets._tmp_out.clear_output(wait=True)
            with self.widgets._tmp_out:
                display(*objs)
        
    def _from_markdown(self, start, /, content, synced=False):
        "Sames as `Slides.build` used as a function."
        if self.this:
            raise RuntimeError('Creating new slides under an already running slide context is not allowed!')
        
        if not isinstance(content, (str,fmt)): #check path later or it will throw error
            raise TypeError(f"content expects a makrdown text block or fmt, got {content!r}")
        
        content, fmt_kws = fmt._astuple(content) # fmt used on top level, or string means no keywords
        content = re.split(r'^\s*EOF\s*$',content, flags = re.MULTILINE)[0]

        if synced:
            content = self._process_citations(content)

        if any(map(lambda v: '\n---' in v, # I gave up on single regex after so much attempt
            (re.findall(r'```multicol(.*?)\n```', content, flags=re.DOTALL | re.MULTILINE) or [''])
            )):
            raise ValueError("slides separator --- cannot be used inside multicol!")
        
        chunks = _parse_markdown_text(content)
        handles = self.create(range(start, start + len(chunks))) # create slides faster or return older

        for i,chunk in enumerate(chunks):
            # Must run under this function to create frames with two dashes (--) and update only if things/variables change
            if any(['Out-Sync' in handles[i]._css_class, chunk != handles[i]._markdown]):
                with self._loading_splash(self.widgets.buttons.refresh): # Hold and disable other refresh button while doing it
                    self._slide(f'{i + start} -m', chunk, fmt_kws=fmt_kws, synced=synced)
            else: # when slide is not built, scroll buttons still need an update to point to correct button
                self._slides_per_cell.append(handles[i])
        
        # Return refrence to slides for quick update
        return handles
    
    def _process_citations(self, content):
        match1, *others = re.findall(r'```citations(.*?)\n```', content, flags= re.DOTALL | re.MULTILINE)
        if others:
            raise ValueError(f"Only a single block of citations is parsed, found {len(others) + 1} blocks")
            
        content = content.replace(f'```citations{match1}\n```','') # clean up
        if getattr(self,'_bib_md','') != match1:
            self._bib_md = match1 # set for next test

            mode, refs = [line.strip() for line in match1.split('\n',1)] # should be ```citations mode and then below
            if not mode:
                mode = self._cite_mode # keep same
            self.set_citations(refs, mode=mode)
        return content
    
    def sync_with_file(self, start_slide_number, /, path, interval=500):
        r"""Auto update slides when content of markdown file changes. You can stop syncing using `Slides.unsync` function.
        interval is in milliseconds, 500 ms default. Read `Slides.build` docs about content of file.
        
        The variables inserted in file content are used from top scope.

        You can add files inside linked file using include\\`file_path.md\\` syntax, which are also watched for changes.
        This helps modularity of content, and even you can link a citation file in markdown format as shown below. Read more in `Slides.xmd_syntax` about it.

        ```markdown
         ```citations footnote
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
    
    def build_(self, content = None):
        "Same as `build` but no slide number required inside Python file!"
        if self.inside_jupyter_notebook(self.build_):
            raise Exception("Notebook-only function executed in another context. Use build without _ in Notebook!")
        return self.build(self._next_number, content=content)

    class build(ContextDecorator):
        r"""Build slides with a single unified command in three ways:
        
        1. hl`slides.build(number, callable)` to create a slide from a `callable(slide)` immediately, e.g. hl`lambda s: slides.write(1,2,3)` or as a decorator.
            - Docstring of callable (if any) is parsed as markdown before calling function.
        2. hl`with slides.build(number):` creates single slide. Equivalent to hl`%%slide number` magic.
            - Use hl`fsep()` from top import or hl`Slides.fsep()` to split content into frames.
            - Use hl`for item in fsep.iter(iterable):` block to automatically add frame separator.
            - Use hl`fsep(True)`/hl`fsep.iter(...,stack=True)` to join content of frames incrementally.
        3. hl`slides.build(number, str | fmt)` creates many slides with markdown content. Equivalent to hl`%%slide number -m` magic in case of one slide.
            - Frames separator is double dashes `--` and slides separator is triple dashes `---`. Same applies to hl`Slides.sync_with_file` too.
            - Use `%++` to join content of frames incrementally.
            - Markdown `multicol` before `--` creates incremental columns if `%++` is provided.
            - See `slides.xmd_syntax` for extended markdown usage.
            - To debug markdown content, use EOF on its own line to keep editing and clearing errors. Same applies to `Slides.sync_with_file` too.
            - In case of str input, varaiables such as \%{var} can be updated by creating/updating `var` in notebook.
            - In case of `fmt(str, **kwargs)`, varaiables are picked from `kwargs` or local scope and can't be changed later. Useful in python scripts.
        

        ::: note-tip
            - In all cases, `number` could be used as `-1`.
            - Use yoffet`integer in px` in markdown or hl`Slides.this.yoffset(integer)` to make all frames align vertically to avoid jumps in increments.
            - You can use hl`build_(...)` (with underscore at end) in python file instead of hl`build(-1,...)`.
        """
        @property
        def _app(self):
            kls = type(self)
            if getattr(kls, '_slides', None) is None:
                kls._slides = get_slides_instance()
            return kls._slides
        
        def __new__(cls, slide_number, /, content = None):
            self = super().__new__(cls) # instance
            self._snumber = self._app._fix_slide_number(slide_number)
            
            with self._app.code.context(returns = True, depth=3, start = True) as code:
                if (content is not None) and any([code.startswith(c) for c in ('@', 'with')]):
                    raise ValueError("content should be None while using as decorator or contextmanager!")
                
                if isinstance(content, (str,fmt)) and not code.startswith('with'): 
                    return self._app._from_markdown(self._snumber, content)

                if callable(content) and not code.startswith('with'):
                    with _build_slide(self._app, self._snumber) as s: 
                        s._set_source(self._app.code.from_source(content).raw,'python') 
                        if (doc := getattr(content, '__doc__', None)):
                            self._app.parse(doc, returns=False)
                        content(s) # call directly, set code before to make avaiable in function
                
                    return s
            
            if content is not None:
                raise ValueError(f"content should be None, str,fmt, or callable. got {type(content)}")

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
            "Use @build decorator. func accepts slide as arguemnt."
            type(self)(self._snumber, func)
            

    def demo(self):
        "Demo slides with a variety of content."
        from .._demo import demo_slides
        return demo_slides(self)
        
        
    def docs(self):
        "Create presentation from docs of IPySlides."
        self.close_view() # Close any previous view to speed up loading 10x faster on average
        self.clear() # Clear previous content
        self.create(range(25)) # Create slides faster
        
        from ..core import Slides

        self.set_citations({'A': 'Citation A', 'B': 'Citation B'}, mode = 'footnote')
        self.settings.footer(text=self.get_logo("1em") + "IPySlides Documentation", date=None)

        with self.build(0): # Title page
            self.this.set_bg_image(self.get_logo(),0.25, filter='blur(10px)', contain=True)
            self.write(f'## IPySlides {self.version} Documentation\n### Creating slides with IPySlides')
            self.center(self.fmt('''
                alert`Abdul Saboor`sup`1`
                                 
                today``
                {.text-small}
                                 
                %{logo}
                                 
                ::: text-box
                    sup`1`My University is somewhere in the middle of nowhere
                ''', logo = self.get_logo("4em"))).display()
        
        self.build(-1, self.fmt('''
            section`Introduction` 
            ```multicol .block-green
            toc[True]`## Table of contents`
            +++
            ### This is summary of current section
            Oh we can use inline columns stack`Column A | Column B` here and what not!
            %{btn}
            ```
            ```markdown
             ```multicol .block-green
             toc[True]`## Table of contents`
             +++
             Extra content for current section which is on right
             ```
            ```''', btn = self.draw_button))
            
        with self.build(-1):
            self.write('# Main App')
            self.doc(Slides).display()
        
        with self.build(-1):
            self.write('# Jump between slides')
            self.doc(self.link, 'Slides').display()
            with self.code.context(returns=True) as c:
                skipper = self.link('Skip to dynamic content', 'Back to link info', icon='arrow', back_icon='arrowl')
                skipper.origin.display() # skipper.target is set later somewhere, can do backward jump too
            c.display()
        
        with self.build(-1):
            self.write('## Adding Slides section`Adding Slides and Content`')
            self.write('Besides function below, you can add slides with `%%slide number [-m]` magic as well.\n{.note .info}')
            self.write([self.doc(self.build,'Slides'), self.doc(self.sync_with_file,'Slides')])
        
        with self.build_():
            self.write('''
                ## Important Methods on Slide
                ::: note-warning
                    Use slide handle or `Slides[number,]` to apply these methods becuase index can change on new builds.
            ''')
            self.doc(self[0], members='yoffset set_animation set_bg_image update_display get_source show set_css'.split(), itself = False).display()
            self.css_syntax.display()
        
        with self.build(-1), self.code.context():
            # self is in scope, auto picked, also fmt can be parsed on display
            display(self.fmt('%{self.version!r} %{self.xmd_syntax}'))
            
        with self.build(-1):
            self.write('## Adding Content')
            self.write('Besides functions below, you can add content to slides with `%%xmd`,`%xmd` as well.\n{.note .info}')
            self.write([self.styled(self.doc(self.write,'Slides'),'block-green'), self.doc(self.parse,'Slides')])
        
        with self.build(-1):
            self.write('## Adding Speaker Notes')
            self.write([rf'You can use alert`notes\`notes content\`` in markdown.\n{{.note .success}}\n',
                       'This is experimental feature, and may not work as expected.\n{.note-error .error}'])
            self.doc(self.notes,'Slides.notes', members = True, itself = False).display()
                   
        with self.build(-1):
            self.write('## Displaying Source Code')
            self.doc(self.code,'Slides.code', members = True, itself = False).display()
        
        self.build(-1, r'section`%Layout and color["yellow","black"]`Theme` Settings%` toc`### Contents`')
        
        with self.build(-1) as s:
            s.set_css({
                '--bg1-color': 'linear-gradient(45deg, var(--bg3-color), var(--bg2-color), var(--bg3-color))',
                '.highlight': {'background':'#8984'}
            }) 
            self.styled('## Layout and Theme Settings', 'info', border='1px solid red').display()
            self.doc(self.settings,'Slides', members=True,itself = True).display()
                
        with self.build(-1):
            self.write('## Useful Functions for Rich Content section`%Useful Functions for alert`Rich Content`%`')
            self.doc(self.alt,'Slides').display()
            
            members = sorted((
                'AnimationSlider alert block bokeh2html bullets styled fmt color details doc '
                'today error zoomable highlight html iframe image frozen notify plt2html '
                'raw set_dir sig stack table textbox suppress_output suppress_stdout svg vspace'
            ).split())
            self.doc(self, 'Slides', members = members, itself = False).display()

        with self.build(-1):
            self.write(r'''
                ## Citations and Sections
                Use syntax alert`cite\`key\``/alert`\@key` to add citations which should be already set by hl`Slides.set_citations(data, mode)` method.
                Citations are written on suitable place according to given mode. Number of columns in citations are determined by 
                hl`Slides.settings.layout(..., ncol_refs = int)`. @A
                       
                Add sections in slides to separate content by alert`section\`text\``. Corresponding table of contents
                can be added with alert`toc\`title\``.
            ''')
            self.doc(self, 'Slides', members = ['set_citations'], itself = False).display()
            
        with self.build(-1):
            skipper.target.display() # Set target for skip button
            self.write('## Dynamic Content')
            
            with self.capture_content() as cap, self.code.context():
                import time

                @self.ei.interact(auto_update=False, grid_css = dict({'.out-main': dict(height='2em')},background='var(--bg2-color)'), date = False)  # self is Slides here
                def update_time(date): 
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
            
            self.write(self.doc(self.ei.interact,'Slides.ei'), [*cap.outputs, c, self.doc(self.on_load,'Slides')])
    
        with self.build(-1):
            self.write('## Content Styling')
            with self.code.context(returns = True) as c:
                self.write(('You can **style**{.error} or **color["teal"]`colorize`** your *content*{: style="color:hotpink;"} and *color["hotpink","yellow"]`text`*. ' 
                       'Provide **CSS**{.info} for that using hl`Slides.html("style",...)` or use some of the available styles. '
                       'See these **styles**{.success} with `Slides.css_styles` property as below:'))
                self.css_styles.display()
                c.display()
        
        s, *_ = self.build(-1, self.fmt('''
        ## Highlighting Code
        [pygments](https://pygments.org/) is used for syntax highlighting cite`A`.
        You can **highlight**{.error} code using `highlight` function cite`B` or within markdown using code blocks enclosed with three backticks:
        ```python
        import ipyslides as isd
        ```
        ```javascript
        import React, { Component } from "react";
        ```
        **s is assigned variable to this slide**: %{s.source}
        ''', self=self))

        
        with self.build(-1):
            self.write('## Loading from File/Exporting to HTML section`Loading from File/Exporting to HTML`')
            self.write('You can parse and view a markdown file. The output you can save by exporting notebook in other formats.\n{.note .info}')
            self.write([self.doc(attr,'Slides') for attr in (self.sync_with_file,self.demo,self.docs,self.export_html)])
        
        self.build(-1, 'section`Advanced Functionality` toc`### Contents`')

        with self.build_() as s:
            self.write("## Adding content on frames incrementally yoffset`0`")
            self.frozen(widget := (code := s.get_source()).as_widget()).display()
            self.fsep(stack=True) # frozen in above line get oldest metadata for export
            def highlight_code(slide): widget.value = code.focus_lines(range(slide.indexf + 1)).value
            self.on_load(highlight_code)
        
            for ws, cols in self.fsep.iter(zip([None, (2,3),None], [(0,1),(2,3),(4,5,6,7)])):
                cols = [self.html('h1', f"{c}",style="background:var(--bg3-color);margin-block:0.05em !important;") for c in cols]
                self.write(*cols, widths=ws)
                    
        with self.build(-1) as s:
            self.write('## Adding User defined Objects/Markdown Extensions')
            self.write(
                self.hold(display, self.html('h3','I will be on main slides',css_class='warning'),
                    metadata = {'text/html': '<h3 class="warning">I will be on exported slides</h3>'}
                ), # Can also do 'Slides.serilaizer.get_metadata(obj)' if registered
                s.get_source(), widths = [1,3]
            )
            self.write('If you need to serialize your own or third party objects not serialized by this module, you can use `\@Slides.serializer.register` to serialize them to html.\n{.note .info}')
            self.doc(self.serializer,'Slides.serializer', members = True, itself = False).display()
            self.write('**You can also extend markdown syntax** using `markdown extensions`, ([See here](https://python-markdown.github.io/extensions/) and others to install, then use as below):')
            self.doc(self.extender,'Slides.extender', members = True, itself = False).display()
        
        with self.build(-1):
            self.write(r'''
            ## Focus on what matters
            - There is a zoom button on top bar which enables zooming of certain elements. This can be toggled by `Z` key.
            - Most of supported elements are zoomable by default like images, matplotlib, bokeh, PIL image, altair plotly, dataframe, etc.
            - You can also enable zooming for an object/widget by wrapping it inside \`Slide.zoomable\` function conveniently.
            - You can also enable by manully adding `zoom-self`, `zoom-child` classes to an element. To prevent zooming under as `zoom-child` class, use `no-zoom` class.
            
            ::: zoom-self block-red
                ### Focus on Me 😎
                - If zoom button is enabled, you can hover here to zoom in this part!
                - You can also zoom in this part by pressing `Z` key while mouse is over this part.
            ''')

        with self.build(-1):
            with self.capture_content() as c:
                with self.code.context():
                    import ipywidgets as ipw
                    btn = ipw.Button(description='Chevron-Down Icon',icon='chevrond')    
                    self.write(btn)

            self.write(['''
                ## SVG Icons
                Icons that apprear on buttons inslides (and their rotations) available to use in your slides as well
                besides standard ipywidgets icons.
                ''', *c.outputs, 'line`200`**Source code of this slide**',self.this.get_source()], 
                self.table([(f'`{k}`', self.icon(k,color='crimson').svg) for k in self.icon.available],headers=['Name','Icon']),
            widths=[2,1])
                
            
        with self.build_():
            self.write("""
                # Auto Slide Numbering
                Use alert`-1` as placeholder to update slide number automatically. 
                       
                - In Jupyter notebook, this will be updated to current slide number. 
                - In python file, it stays same.
                - You need to run cell twice if creating slides inside a for loop while using `-1`.
                - Additionally, in python file, you can use `Slides.build_` instead of using `-1`.
                       
                ::: note-warning
                    Some kernels may not support auto slide numbering inside notebook.
            """)
        
        self.build(-1, lambda s: self.write(['## Presentation Code section`Presentation Code`',self.docs]))
        self.navigate_to(0) # Go to title
        return self
    
def _parse_markdown_text(text_block):
    "Parses a Markdown text block and returns text for title and each slide."
    # user may used fmt
    lines = textwrap.dedent(text_block).splitlines() # Remove overall indentation
    breaks = [-1] # start, will add +1 next
    for i,line in enumerate(lines):
        if line and re.search(r'^---$|^---\s+$', line): # for hr, can add space in start
            breaks.append(i)

    breaks.append(len(lines)) # Last one
    
    ranges = [range(j+1,k) for j,k in zip(breaks[:-1],breaks[1:])]
    return ['\n'.join(lines[x.start:x.stop]) for x in ranges]