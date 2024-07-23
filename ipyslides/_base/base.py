"Inherit Slides class from here. It adds useful attributes and methods."
import os, re, textwrap
import traceback
from pathlib import Path
from contextlib import ContextDecorator

from IPython.display import display

from ipywidgets import interact as ipyinteract

from .widgets import Widgets
from .navigation import Navigation
from .settings import Settings
from .notes import Notes
from .export_html import _HhtmlExporter
from .slide import _build_slide
from ..formatters import XTML
from ..xmd import _special_funcs, _md_extensions, error, xtr, get_slides_instance
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
        # self.html will be added from Chid class
        return self.raw('''
        Use any or combinations of these styles in css_class argument of writing functions:
        ------------------------------------------------------------------------------------
         css_class          | Formatting Style                                              
        ====================================================================================
         'text-[value]'     | [value] should be one of tiny, small, big, large, huge.
         'align-[value]'    | [value] should be one of center, left, right.
         'rtl'              | ------ اردو عربی 
         'info'             | Blue text. Icon ℹ️  for note-info class.
         'tip'              | Blue Text. Icon💡 for note-tip class.
         'warning'          | Orange Text. Icon ⚠️ for note-warning class.
         'success'          | Green text. Icon ✅ for note-success class.
         'error'            | Red Text. Icon⚡ for note-error class.
         'note'             | 📝 Text with note icon.
         'export-only'      | Hidden on main slides, but will appear in exported slides.
         'jupyter-only'     | Hidden on exported slides, but will appear on main slides.
         'block'            | Block of text/objects
         'block-[color]'    | Block of text/objects with specific background color from red,
                            | green, blue, yellow, cyan, magenta and gray.
         'raw-text'         | Text will not be formatted and will be shown as it is.
         'zoom-self'        | Zooms object on hover, when Zoom is enabled.
         'zoom-child'       | Zooms child object on hover, when Zoom is enabled.
         'no-zoom'          | Disables zoom on object when it is child of 'zoom-child'.
        ------------------------------------------------------------------------------------
        Besides these CSS classes, you always have `Slide.set_css`, `Slides.html('style',...) functions at your disposal.
        ''')

    @property
    def xmd_syntax(self):
        "Special syntax for markdown."
        return XTML(self.parse(textwrap.dedent(rf'''
        ## Extended Markdown
        Extended syntax for markdown is constructed to support almost full presentation from Markdown.
        
        **Following syntax works only under currently building slide:**
        
        - alert`notes\`This is slide notes\``  to add notes to current slide
        - alert`cite\`key\`` to add citation to current slide. citations are automatically added in suitable place and should be set once using `Slides.set_citations` function.
        - With citations mode set as 'footnote', you can add alert`refs\`ncol\`` to add citations anywhere on slide. If ncol is not given, it will be picked from layout settings.
        - alert`section\`content\`` to add a section that will appear in the table of contents.
        - alert`toc\`Table of content header text\`` to add a table of contents. For block type toc, see below.
        - alert`proxy\`placeholder text\`` to add a proxy that can be updated later using hl`with Slides[slide_number,].proxies[index]:` or a shortcut hl`with Slides.capture_proxy(slides_number, proxy_index):`. Useful to keep placeholders for plots/widgets in markdwon.
        - Triple dashes `---` is used to split text in slides inside markdown content of `Slides.build` function or markdown file.
        - Double dashes `--` is used to split text in frames. Alongwith this `%++` can be used to increment text on framed slide.
        
        Block table of contents with extra content as summary of current section can be added as follows:
                                               
        ```markdown
         ```multicol 
         toc[True]`Table of contents`
         +++
         Extra content for current section appears on right
         ```
        ```
        
        **Other syntax can be used everywhere in markdown:**
        
        - Variables can be shown as widgets or replaced with their HTML value (if no other formatting given) using alert`\`{{variable}}\`` 
            (should be single curly braces pair wrapped by backticks after other formattings done) syntax. If a format_spec/conversion is provided like
            alert`\`{{variable:format_spec}}\`` or alert`\`{{variable!conversion}}\``, that will take preference.
        - A special formatting alert`\`{{variable:nb}}\`` is added (`version >= 4.5`) to display objects inside markdown as they are displayed in a Notebook cell.
            Custom objects serialized with `Slides.serializer` or serialized by `ipyslides` should be displayed without `:nb` whenever possible to appear in correct place in all contexts. e.g.
            a matplotlib's figure `fig` as shown in \`{{fig:nb}}\` will only capture text representation inplace and actual figure will be shown at end, while \`{{fig}}\` will be shown exactly in place.
        - Variables are not automatically updated in markdown being a costly operation, press `U` or use `Update Variables & Widgets` button in quick menu after you update a variable in notebook used in markdown.
            This has additional benefit of having everything refreshed at end without rebuidling markdown slides. Note that this only updates variables used in markdown file and in `Slides.build` command.
            Also, each newly added slide and new display of slides enables variables sync across all slides automatically. 

        ::: note-warning
            alert`\`{{variable:nb}}\`` breaks the DOM flow, e.g. if you use it inside heading, you will see two headings above and below it with splitted text. Its fine to use at end or start or inside paragraph.                                    
        
        ::: note-info
            - Widgets behave same with or without `:nb` format spec. 
            - Formatting is done using `str.format` method, so f-string like literal expressions are not supported, but you don't need to supply variables, just enclose text in `Slides.fmt`.
            - Variables are substituted from top level scope (Notebook's hl`locals()`/hl`globals()`). To use varirables from a nested scope, use `Slides.fmt` which you can import on top level as well to just make it fmt.

        - A syntax alert`func\`?Markdown?\`` will be converted to alert`func\`Parsed HTML\`` in markdown. Useful to nest special syntax.
        - Escape a backtick with \\, i.e. alert`\\\` → \``. In Python >=3.12, you need to make escape strings raw, including the use of $ \LaTeX $ and re module.
        - alert`include\`markdown_file.md\`` to include a file in markdown format.
        - Two side by side columns can be added inline using alert`|&#124;[width optionally here in 1-99] Column A |&#124; Column B |&#124;` sytnax.
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
        
        - Python code blocks can be exectude by syntax 
        ```markdown
         ```python run source {{.CSS_className}} 
         slides = get_slides_instance() 
         slides.write('Hello, I was written from python code block using slides instance.')
         ```
        ```
        and source then can be emded with \`{{source}}\` syntax.
        
        - A whole block of markdown can be CSS-classed using syntax
        ```markdown
        ::: block-yellow
            ### This is Header 3
            <hr/>
            Some **bold text**
        ```
        gives 
        ::: block-yellow
            ### This is Header 3
            <hr/>
            Some **bold text**
            
        ::: note 
            You can also look at [customblocks](https://github.com/vokimon/markdown-customblocks) 
            extension to make nested blocks with classes. It is added as dependency and can be used to build nested html blocks.
            
        ::: block-red 
            - You can use `Slides.extender` to extend additional syntax using Markdown extensions such as 
                [markdown extensions](https://python-markdown.github.io/extensions/) and 
                [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
            - These markdown extensions are inluded by default hl`{_md_extensions}`.
            - You can serialize custom python objects to HTML using `Slides.serializer` function. Having a 
                `__format__` method in your class enables to use {{obj}} syntax in python formatting and \`{{obj}}\` in extended Markdown.
        
        - Other options (that can also take extra args as alert`func[arg1,x=2,y=A]\`arg0\``) include:
        ''') + '\n' + ',\n'.join(rf'    - alert`{k}`\`{v}\`' for k,v in _special_funcs.items()),
        returns = True
        ))
    
    @property
    def css_syntax(self):
        "CSS syntax for use in Slide.set_css, Slides.html('style', ...) etc."
        return XTML(_css_docstring)
   
    def get_source(self, title = 'Source Code'):
        "Return source code of all slides except created as frames with python code."
        sources = []
        for slide in self[:]:
            if slide._source['text']:
                sources.append(slide.get_source(name=f'{slide._source["language"].title()}: Slide {slide.index}'))
            
        if sources:
            return self.frozen(f'<h2>{title}</h2>' + '\n'.join(s.value for s in sources),{})
        else:
            self.html('p', 'No source code found.', css_class='info')

    def on_load(self, func):
        """
        Decorator for running a function when slide is loaded into view. No return value is required.
        Use this to e.g. notify during running presentation. func accepts single arguemnet, slide.
        
        ```python run source
        import datetime
        slides = get_slides_instance() # Get slides instance, this is to make doctring runnable
        source.display() # Display source code of the block
        @slides.on_load
        def push_toast(slide):
            t = datetime.datetime.now()
            time = t.strftime('%H:%M:%S')
            slides.notify(f'Notification at {time} form slide {slide.index} and frame {slide.indexf}', timeout=5)
        ```
        ::: note-warning
            - Do not use this to change global state of slides, because that will affect all slides.
            - This can be used single time per slide, overwriting previous function.
        """
        self.verify_running('on_load decorator can only be used inside slide constructor!')
        self.this._on_load_private(func) # This to make sure if code is correct before adding it to slide
    
    def interact(self, __func = None, __options={'manual': True, 'height':''}, **kwargs):
        """
        ipywidgets's interact functionality tailored for ipyslides's needs. It adds 'height' as additional
        parameter in options. Set height to avoid flickering output.

        ```python run source
        import time
        slides = get_slides_instance() # Get slides instance, this is to make docstring runnable
        source.display() # Display source code of the block
        @slides.interact({'height':'2em'}, date = False)
        def update_time(date): 
            local_time = time.localtime()
            objs = ['Time: {3}:{4}:{5}'.format(*local_time)] # Print time in HH:MM:SS format
            if date:
                objs.append('Date: {0}/{1}/{2}'.format(*local_time))
            slides.write(*objs)
        ```

        ::: note-tip
            You can use this inside columns using delayed display trick, like hl`write('First column', lambda: interact(f, x = 5))`.

        ::: note-warning
            Do not use this to change global state of slides, because that will affect all slides.
        """
        if not isinstance(__options, dict):
            raise TypeError('__options should be a dictionary with keys "manual" and "height"')

        def inner(func, options={}):
            def new_func(**kws):
                with self._hold_running():
                    if (btn := getattr(new_func, 'btn', None)):
                        btn.icon = 'minus'
                        try:
                            func(**kws)
                            btn.remove_class('Rerun')
                        finally:
                            btn.icon = 'plus'
                    else:
                        func(**kws)

            _interact = ipyinteract.options(manual = options.get('manual', True), manual_name='', auto_display=True)
            widget = _interact(new_func, **kwargs).widget.add_class('on-refresh')
            widget.out.layout.height = options.get('height','')

            if (btn := getattr(widget, 'manual_button', None)):
                new_func.btn = widget.manual_button
                for w in widget.kwargs_widgets:
                    w.observe(lambda change: btn.add_class('Rerun'))

                btn.add_class('Refresh-Btn').add_class('Menu-Item')
                btn.layout = {'width': 'auto', 'height':'28px'}
                btn.tooltip = 'Click to refresh output'
                btn.icon = 'plus'
                btn.click() # first run to ensure no dynamic inside
        
        if __func is None:
            return inner
        elif isinstance(__func, dict): # Only options passed 
            return lambda func: inner(func, __func)
        else:
            inner(__func, __options)
        
    def _update_tmp_output(self, *objs):
        "Used for CSS/animations etc. HTML widget does not work properly."
        if self.is_jupyter_session():
            self.widgets._tmp_out.clear_output(wait=True)
            with self.widgets._tmp_out:
                display(*objs)
        
    def from_markdown(self, start_slide_number, /, content, trusted = False):
        "Sames as `Slides.build` used as a function."
        if self.this:
            raise RuntimeError('Creating new slides under an already running slide context is not allowed!')
        
        if not isinstance(content, str): #check path later or it will throw error
            raise TypeError(f"content expects a makrdown text block, got {content!r}")
        
        content = xtr.copy_ns(content, re.split(r'^\s*EOF\s*$',content, flags = re.MULTILINE)[0])

        if any(map(lambda v: '\n---' in v, # I gave up on single regex after so much attempt
            (re.findall(r'```multicol(.*?)\n```', content, flags=re.DOTALL | re.MULTILINE) or [''])
            )):
            raise ValueError("slides separator --- cannot be used inside multicol!")
        
        start = self._fix_slide_number(start_slide_number) 
        
        if not trusted:
            lines = content.splitlines()
                    
            untrusted_lines = []
            for i, line in enumerate(lines, start = 1):
                if re.match(r'```python\s+run', line):
                    untrusted_lines.append(i)
            
            if untrusted_lines:
                raise Exception(f'Given text may contain unsafe code to be executed at lines: {untrusted_lines}'
                    ' Verify code is safe and try again with argument `trusted = True`.'
                    ' Never run files that you did not create yourself or not verified by you.')
        
        chunks = _parse_markdown_text(content)
            
        handles = self.create(range(start, start + len(chunks))) # create slides faster or return older

        for i,chunk in enumerate(chunks):
            # Must run under this function to create frames with two dashes (--) and update only if things/variables change
            if any(['Out-Sync' in handles[i]._css_class, chunk != getattr(handles[i],'_mdff','')]):
                with self._loading_private(self.widgets.buttons.refresh): # Hold and disable other refresh button while doing it
                    self._slide(f'{i + start} -m', chunk)
            else: # when slide is not built, scroll buttons still need an update to point to correct button
                self._slides_per_cell.append(handles[i])

            handles[i]._mdff = chunk # This is need for update while editing and refreshing variables
        
        # Return refrence to slides for quick update
        return handles
    
    def sync_with_file(self, start_slide_number, /, path, trusted = False, interval=500):
        """Auto update slides when content of markdown file changes. You can stop syncing using `Slides.unsync` function.
        interval is in milliseconds, 500 ms default. Read `Slides.build` docs about content of file.
        
        The variables inserted in file content are used from top scope.
        
        ::: note-tip
            To debug a linked file, use EOF on its own line to keep editing and clearing errors.
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
        self.from_markdown(start, path.read_text(encoding="utf-8"), trusted) # First call itself before declaring other things, so errors can be captured safely
        
        if hasattr(self.widgets.iw,'_sync_args'): # remove previous updates
            self.unsync()

        self._mtime = os.stat(path).st_mtime

        def update(widget, content, buffer):
            if path.is_file():
                mtime = os.stat(path).st_mtime
                out_sync = any(['Out-Sync' in s._css_class for s in self.cited_slides]) or False
                if out_sync or (mtime > self._mtime):  # set by interaction widget
                    self._mtime = mtime
                    try: 
                        self.from_markdown(start, path.read_text(encoding="utf-8"), trusted)
                        self.notify('x') # need to remove any notification from previous error
                        self._unregister_postrun_cell() # No cells buttons from inside file code run
                    except:
                        e, text = traceback.format_exc(limit=0).split(':',1) # only get last error for notification
                        self.notify(f"{error('SyncError','something went wrong')}<br/><br/>{error(e,text)}",20)
            else:
                self.notify(error("SyncError", f"file {path!r} no longer exists!").value, 20)

        self.widgets.iw.on_msg(update)
        self.widgets.iw.msg_tojs = f'SYNC:ON:{interval}'
        self.widgets.iw._sync_args = {"func": update, "interval": interval}
        print(f"Syncing content from file {path!r}\nYou can use `Slides.unsync()` to stop syncing.")
        

    def unsync(self):
        "Stop syncing markdown file synced with `Slides.sync_with_file` function."
        if hasattr(self.widgets.iw,'_sync_args'):
            self.widgets.iw.on_msg(self.widgets.iw._sync_args["func"],remove=True)
            self.widgets.iw.msg_tojs = 'SYNC:OFF'
            delattr(self.widgets.iw,'_sync_args')
        else:
            print("There was no markdown file linked to sync!")
    
    def build_(self, content = None, *, trusted = False, widths=None):
        "Same as `build` but no slide number required inside Python file!"
        if self.inside_jupyter_notebook(self.build_):
            raise Exception("Notebook-only function executed in another context. Use build without _ in Notebook!")
        return self.build(self._next_number, content=content, trusted=trusted, widths=widths)

    class build(ContextDecorator):
        """Build slides with a single unified command in three ways:
        
        1. hl`slides.build(number, str, trusted)` creates many slides with markdown content. Equivalent to hl`%%slide number -m` magic in case of one slide.
            - Frames separator is double dashes `--` and slides separator is triple dashes `---`. Same applies to hl`Slides.sync_with_file` too.
            - Use `%++` to join content of frames incrementally.
            - Markdown `multicol` before `--` creates incremental columns if `%++` is provided.
            - See `slides.xmd_syntax` for extended markdown usage.
            - Keyword argument `trusted` is used here if there are `python run` blocks in markdown.
            - To debug markdown content, use EOF on its own line to keep editing and clearing errors. Same applies to `Slides.sync_with_file` too.
        2. hl`slides.build(number, list/tuple, widths)` to create a slide from list-like contents immediately.
            - We use hl`write(*contents, widths)` to make slide. This is a shortcut way of step 3 if you want to create slides fast with few objects.
        3. hl`with slides.build(number):` creates single slide. Equivalent to hl`%%slide number` magic.
            - Use hl`fsep()` from top import or hl`Slides.fsep()` to split content into frames.
            - Use hl`for item in fsep.loop(iterable):` block to automatically add frame separator.
            - Use hl`fsep.join` to join content of frames incrementally.

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
        
        def __new__(cls, slide_number, /, content = None, *, trusted = False, widths=None):
            self = super().__new__(cls) # instance
            self._snumber = self._app._fix_slide_number(slide_number)
            
            with self._app.code.context(returns = True, depth=3, start = True) as code:
                if isinstance(content, str) and not code.startswith('with'): 
                    return self._app.from_markdown(self._snumber, content, trusted = trusted)
            
                if isinstance(content, (list, tuple)) and not code.startswith('with'):
                    with _build_slide(self._app, self._snumber) as s: 
                        self._app.write(*content, widths=widths)
                    
                    if code.count('(') != code.count(')'):
                        code = code.strip() + ' ...' 
                    s._set_source(code,'python') # Just hinted one-liner code
                    return s
            
            if content is not None:
                raise ValueError(f"content should be None, str, list or tuple. got {type(content)}")

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

    def demo(self):
        "Demo slides with a variety of content."
        from .._demo import demo_slides
        return demo_slides(self)
        
        
    def docs(self):
        "Create presentation from docs of IPySlides."
        self.close_view() # Close any previous view to speed up loading 10x faster on average
        self.clear() # Clear previous content
        self.create(range(24)) # Create slides faster
        
        from ..core import Slides

        self.set_citations({'A': 'Citation A', 'B': 'Citation B'}, mode = 'footnote')
        self.settings.footer(text='IPySlides Documentation', date=None)

        with self.build(0): # Title page
            self.this.set_bg_image(self.get_logo(),0.25, filter='blur(10px)', contain=True)
            self.write(f'## IPySlides {self.version} Documentation\n### Creating slides with IPySlides')
            self.center(self.fmt('''
                alert`Abdul Saboor`sup`1`
                                 
                today``
                {.text-small}
                                 
                `{logo}`
                                 
                ::: text-box
                    sup`1`My University is somewhere in the middle of nowhere
                ''', logo = self.get_logo("4em"))).display()
        
        self.build(-1, self.fmt('''
            section`Introduction` 
            ```multicol .block-green
            toc[True]`## Table of contents`
            +++
            ### This is summary of current section
            Oh we can use inline columns || Column A || Column B || here and what not!
            `{btn}`
            ```
            ```markdown
             ```multicol .block-green
             toc[True]`## Table of contents`
             +++
             Extra content for current section which is on right
             ```
            ```''', btn = self.draw_button))
            
        with self.build(-1):
            self.write(['# Main App',self.doc(Slides), '### Jump between slides'])
            self.doc(self.goto_button, 'Slides').display()
        
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
            self.write(self.fmt('`{self.version!r}` `{self.xmd_syntax}`', self=self))
            
        with self.build(-1):
            self.write('## Adding Content')
            self.write('Besides functions below, you can add content to slides with `%%xmd`,`%xmd` as well.\n{.note .info}')
            self.write([self.styled(self.doc(self.write,'Slides'),'block-green'), self.doc(self.parse,'Slides'),self.doc(self.image_clip,'Slides')])
        
        with self.build(-1):
            self.write('## Adding Speaker Notes')
            (skipper := self.goto_button('Skip to Dynamic Content', icon='arrowr')).display()
            self.write([rf'You can use alert`notes\`notes content\`` in markdown.\n{{.note .success}}\n',
                       'This is experimental feature, and may not work as expected.\n{.note-error .error}'])
            self.doc(self.notes,'Slides.notes', members = True, itself = False).display()
                   
        with self.build(-1):
            self.write('## Displaying Source Code')
            self.doc(self.code,'Slides.code', members = True, itself = False).display()
        
        self.build(-1, 'section`?Layout and color[yellow,black]`Theme` Settings?` toc`### Contents`')
        
        with self.build(-1) as s:
            s.set_css({
                '--bg1-color': 'linear-gradient(45deg, var(--bg3-color), var(--bg2-color), var(--bg3-color))',
                '.highlight': {'background':'#8984'}
            }) 
            self.styled('## Layout and Theme Settings', 'info', border='1px solid red').display()
            self.doc(self.settings,'Slides', members=True,itself = True).display()
                
        with self.build(-1):
            self.write('## Useful Functions for Rich Content section`?Useful Functions for alert`Rich Content`?`')
            self.write("clip[caption=clip\`test.png\`]`test.png`", self.doc(self.clip,'Slides'))
            self.run_doc(self.alt,'Slides')
            self.doc(self.alt_clip,'Slides').display()
            self.doc(self.image_clip,'Slides').display()
            
            members = sorted((
                'alert block bokeh2html bullets styled fmt color cols details doc sub sup '
                'today error zoomable highlight html iframe image frozen notify plt2html '
                'raw rows set_dir sig textbox suppress_output suppress_stdout svg vspace'
            ).split())
            self.doc(self, 'Slides', members = members, itself = False).display()

        with self.build(-1):
            self.write(r'''
                ## Citations and Sections
                Use syntax alert`cite\`key\`` to add citations which should be already set by hl`Slides.set_citations(data, mode)` method.
                Citations are written on suitable place according to given mode. Number of columns in citations are determined by 
                hl`Slides.settings.layout(..., ncol_refs = int)`. cite`A`
                       
                Add sections in slides to separate content by alert`section\`text\``. Corresponding table of contents
                can be added with alert`toc\`title\``/alert`\`\`\`toc title\\n summary of current section \\n\`\`\``.
            ''')
            self.doc(self, 'Slides', members = ['set_citations'], itself = False).display()
            
        with self.build(-1):
            skipper.set_target() # Set target for skip button
            self.write('## Dynamic Content')
            self.run_doc(self.interact,'Slides')
            self.run_doc(self.on_load,'Slides')
            self.this.get_source().display() # this refers to slide being built
    
        with self.build(-1):
            self.write('## Content Styling')
            with self.code.context(returns = True) as c:
                self.write(('You can **style**{.error} or **color[teal]`colorize`** your *content*{: style="color:hotpink;"} and *color[hotpink,yellow]`text`*. ' 
                       'Provide **CSS**{.info} for that using hl`Slides.html("style",...)` or use some of the available styles. '
                       'See these **styles**{.success} with `Slides.css_styles` property as below:'))
                self.css_styles.display()
                c.display()
        
        s8, = self.build(-1, '''
        ## Highlighting Code
        [pygments](https://pygments.org/) is used for syntax highlighting cite`A`.
        You can **highlight**{.error} code using `highlight` function cite`B` or within markdown like this:
        ```python
        import ipyslides as isd
        ```
        ```javascript
        import React, { Component } from "react";
        ```
        proxy`source code of slide will be updated here later using slide_handle.proxies[0] contextmanager`
        ''', trusted= True)
        
        # Update proxy with source code
        with s8.proxies[0]: # or with self.capture_proxy(s8.number, 0):
            display(self.draw_button)
            s8.get_source().display()
        
        with self.build(-1):
            self.write('## Loading from File/Exporting to HTML section`Loading from File/Exporting to HTML`')
            self.write('You can parse and view a markdown file. The output you can save by exporting notebook in other formats.\n{.note .info}')
            self.write([self.doc(attr,'Slides') for attr in (self.sync_with_file,self.demo,self.docs,self.export_html)])
        
        self.build(-1, 'section`Advanced Functionality` toc`### Contents`')

        with self.build_() as s:
            self.write("## Adding content on frames incrementally yoffset`0`")
            self.frozen(widget := (code := s.get_source()).as_widget()).display()
            self.fsep() # frozen in above line get oldest metadata for export
            def highlight_code(slide): widget.value = code.focus_lines(range(slide.indexf + 1)).value
            self.on_load(highlight_code)
        
            for ws, cols in self.fsep.loop(zip([None, (2,3),None], [(0,1),(2,3),(4,5,6,7)])):
                cols = [self.html('h1', f"{c}",style="background:var(--bg3-color);margin-block:0.05em !important;") for c in cols]
                self.fsep.join() # incremental
                self.write(*cols, widths=ws)
                    
        with self.build(-1) as s:
            self.write('## Adding User defined Objects/Markdown Extensions')
            self.write(
                lambda: display(self.html('h3','I will be on main slides',css_class='warning'), 
                metadata = {'text/html': '<h3 class="warning">I will be on exported slides</h3>'}), # Can also do 'Slides.serilaizer.get_metadata(obj)' if registered
                s.get_source(), widths = [1,3]
            )
            self.write('If you need to serialize your own or third party objects not serialized by this module, you can use `@Slides.serializer.register` to serialize them to html.\n{.note .info}')
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
            self.write('''
                ## SVG Icons
                Icons that apprear on buttons inslides (and their rotations) available to use in your slides as well
                besides standard ipywidgets icons.
            ''')
            self.write(' '.join([f'`{k}`: ' + self.icon(k,color='crimson').svg for k in self.icon.available]))
            
            with self.code.context():
                import ipywidgets as ipw
                btn = ipw.Button(description='Chevron-Down Icon',icon='chevrond')    
                self.write(btn)
                
            
        with self.build_():
            self.write("""
                # Auto Slide Numbering
                Use alert`-1` as placeholder to update slide number automatically. 
                       
                - In Jupyter notebook, this will be updated to current slide number. 
                - In python file, it stays same.
                - You need to run cell twice if creating slides inside a for loop while using `-1`.
                - Additionally, in python file, you can use `Slides.build_` instead of using `-1`.
            """)
        
        self.build(-1, [('## Presentation Code section`Presentation Code`',self.docs)])
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
    return [xtr.copy_ns(text_block, '\n'.join(lines[x.start:x.stop])) for x in ranges]
        