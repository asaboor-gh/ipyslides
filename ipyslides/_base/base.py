"Inherit Slides class from here. It adds useful attributes and methods."
import os, re, textwrap
import traceback
from pathlib import Path

from IPython.display import display

from .widgets import Widgets
from .screenshot import ScreenShot
from .navigation import Navigation
from .settings import LayoutSettings
from .notes import Notes
from .export_html import _HhtmlExporter
from .intro import key_combs
from ..formatters import XTML
from ..xmd import _special_funcs, error, xtr

class BaseSlides:
    def __init__(self):
        self._warnings = [] # Will be printed at end of building slides
        self._uid = f'{self.__class__.__name__}-{id(self)}' # Unique ID for this instance to have CSS, should be before settings
        self.__widgets = Widgets()
        self.__screenshot = ScreenShot(self.__widgets)
        self.clip_image = self.__screenshot.clip_image # For easy access
        self.__navigation = Navigation(self.__widgets) # Not accessed later, just for actions
        self.__settings = LayoutSettings(self, self.__widgets)
        self.export_html = _HhtmlExporter(self).export_html
        self.__notes = Notes(self, self.__widgets) # Needs main class for access to notes
        
        self.toast_html = self.widgets.htmls.toast
        
        self.widgets.checks.toast.observe(self._toggle_notify,names=['value'])
    
    @property
    def notes(self):
        return self.__notes
    
    @property
    def widgets(self):
        return self.__widgets
    
    @property
    def screenshot(self):
        return self.__screenshot
    
    @property
    def settings(self):
        return self.__settings
    
    def notify(self,content,timeout=5):
        """Send inside notifications for user to know whats happened on some button click. 
        Remain invisible in screenshot.
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
        """CSS styles for markdown or `classed` command."""
        # self.html will be added from Chid class
        return self.raw('''
        Use any or combinations of these styles in className argument of writing functions:
        ------------------------------------------------------------------------------------
         className          | Formatting Style                                              
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
        Besides these CSS classes, you always have `Slide.format_css` function at your disposal.
        ''')

    @property
    def xmd_syntax(self):
        "Special syntax for markdown."
        return XTML(self.parse(textwrap.dedent('''
        ## Extended Markdown
        Extended syntax for markdown is constructed to support almost full presentation from Markdown.
        
        **Following syntax works only under currently building slide:**
        
        - alert`notes\`This is slide notes\``  to add notes to current slide
        - alert`cite\`key\`` to add citation to current slide. citations are automatically added in suitable place and should be set once using `Slides.set_citations` function.
        - With citations mode set as 'footnote', you can add alert`refs\`ncol\`` to add citations anywhere on slide. If ncol is not given, it will be picked from layout settings.
        - alert`section\`content\`` to add a section that will appear in the table of contents.
        - alert`toc\`Table of content header text\`` to add a table of contents. For block type toc, see below.
        - alert`proxy\`placeholder text\`` to add a proxy that can be updated later with `Slides.get(slide_number).proxies[index].capture` contextmanager or a shortcut `Slides.capture_proxy(slides_number, proxy_index)`. Useful to keep placeholders for plots/widgets in markdwon.
        - Triple dashes `---` is used to split markdown text in slides inside `from_markdown(start, content)` function.
        - Double dashes `--` is used to split markdown text in frames.
        
        Block table of contents with extra content can be added as follows:
                                               
        ```markdown
         ```toc Table of contents
         Extra content for current section appears on right
         Can use small column notation here || A || B || but not `multicol`
         ```
        ```
        
        **Other syntax can be used everywhere in markdown:**
        
        - Variables can be replaced with their HTML value (if no other formatting given) using alert`\`{variable}\`` 
            (should be single curly braces pair wrapped by backticks after other formattings done) syntax. If a format_spec/conversion is provided like
            alert`\`{variable:format_spec}\`` or alert`\`{variable!conversion}\``, that will take preference.
        
            ::: note-info
                - Formatting is done using `str.format` method, so f-string like literal expressions are not supported, but you don't need to supply variables, just enclose text in `Slides.fmt`.
                - Variables are substituted from top level scope (Notebook's `locals()`/`globals()`). To use varirables from a nested scope, use `Slides.fmt` which you can import on top level as well to just make it fmt.
                                               
        - A syntax alert`func\`&#63;Markdown&#63;\`` will be converted to alert`func\`Parsed HTML\`` in markdown. Useful to nest special syntax.
        - You can escape backtick with backslash: alert`\\\` → \``.
        - alert`include\`markdown_file.md\`` to include a file in markdown format.
        - Two side by side columns can be added inline using alert`|&#124; Column A |&#124; Column B |&#124;` sytnax.
        - Block multicolumns are made using follwong syntax, column separator is tiple plus `+++`:
        
        ```markdown     
         ```multicol widthA widthB
         Column A
         +++
         Column B
         ```
        ```
        
        - `multicol` syntax supports frames separator `--` within itself.
        - Python code blocks can be exectude by syntax 
        ```markdown
         ```python run source {.CSS_className} 
         slides = get_slides_instance() 
         slides.write('Hello, I was written from python code block using slides instance.')
         ```
        ```
        and source then can be emded with \`{source}\` syntax.
        
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
                [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/)
            - You can serialize custom python objects to HTML using `Slides.serializer` function. Having a 
                `__format__` method in your class enables to use {obj} syntax in python formatting and \`{obj}\` in extended Markdown.
        
        - Other options (that can also take extra args as alert`func[arg1,x=2,y=A]\`arg0\``) include:
        
        color[blue]`color[blue]\`text\``, color[yellow,skyblue]`color[yellow,skyblue]\`text\``, ''') + '\n' + ', '.join(f'alert`{k}\`{v}\``' for k,v in _special_funcs.items()),
        returns = True
        ))
   
    def get_source(self, title = 'Source Code'):
        "Return source code of all slides created using `from_markdown` or `%%slide`."
        sources = []
        for slide in self[:]:
            if slide._source['text']:
                sources.append(slide.get_source(name=f'{slide._source["language"].title()}: Slide {slide.label}'))
            
        if sources:
            return self.keep_format(f'<h2>{title}</h2>' + '\n'.join(s.value for s in sources))
        else:
            self.html('p', 'No source code found.', className='info')

    def on_load(self, func):
        """
        Decorator for running a function when slide is loaded into view. No return value is required.
        Use this to e.g. notify during running presentation.
        
        ```python run source
        import datetime
        slides = get_slides_instance() # Get slides instance, this is to make doctring runnable
        source.display() # Display source code of the block
        @slides.on_load
        def push_toast():
            t = datetime.datetime.now()
            time = t.strftime('%H:%M:%S')
            slides.notify(f'Notification at {time}', timeout=5)
        ```
        ::: note-warning
            - Do not use this to change global state of slides, because that will affect all slides.
            - This can be used single time per slide, overwriting previous function.
        """
        for name in ['write','print','display','alt']:
            if name in func.__code__.co_names:
                self._warnings.append(f'UserWarning: Output of `{name}` function under `on_load` may be lost while presenting. I hope you know what you are doing!')
        
        if 'settings' in func.__code__.co_names:
            self._warnings.append(f'UserWarning: Changing settings under `on_load` may have side effects on all slides. I hope you know what you are doing!')
        
        self.verify_running('on_load decorator can only be used inside slide constructor!')
        self.this._on_load_private(func) # This to make sure if code is correct before adding it to slide
    
    def on_refresh(self,func):
        """
        Decorator for inserting dynamic content on slide, define a function with no arguments.
        Content updates when `slide.update_display` is called or when `Slides.refresh` is called.
        ::: note-tip
            You can use it to dynamically fetch a value from a database or API while presenting, without having to run the cell again.
        ::: note
            - No return value is required. If any, should be like `display('some value')`, otherwise it will be ignored.
            - A slide with dynamic content enables a refresh button in bottom bar.
            - All slides with dynamic content are updated when refresh button in top bar is clicked.
            
        ```python run source
        import time
        slides = get_slides_instance() # Get slides instance, this is to make doctring runnable
        source.display() # Display source code of the block
        @slides.on_refresh
        def update_time():
            print('Local Time: {3}:{4}:{5}'.format(*time.localtime())) # Print time in HH:MM:SS format
        # Updates on update_display or refresh button click
        ```
        ::: note-warning
            Do not use this to change global state of slides, because that will affect all slides.
        
        ::: note-info
            Use `ipywidgets.interact/interactive` if you need extra control widgets beyond just a refresh.
        """
        return self._dynamic_private(func, tag = '_has_widgets', hide_refresher = False)
    
    def _dynamic_private(self, func, tag = None, hide_refresher = False):
        "Not for user use, internal function for other dynamic content decorators with their own tags."
        self.verify_running('Dynamic content can only be used inside slide constructor!')
        return self.this._dynamic_private(func, tag = tag, hide_refresher = hide_refresher)
        
    def _update_tmp_output(self, *objs):
        "Used for CSS/animations etc. HTML widget does not work properly."
        if self.is_jupyter_session():
            self.widgets._tmp_out.clear_output(wait=True)
            with self.widgets._tmp_out:
                display(*objs)
        
    def from_markdown(self, start, content, trusted = False):
        """You can create slides from a markdown tex block as well. It creates slides `start + (0,1,2,3...)` in order.
        You should add more slides by higher number than the number of slides in the file/text, or it will overwrite.
        
        - Slides separator should be --- (three dashes) in start of line.
        - Frames separator should be -- (two dashes) in start of line. All markdown before first `--` will be written on all frames.
        - In case of frames, you can add %++ (percent plus plus) in the content to add frames incrementally.
        - You can use frames separator (--) inside `multicol` to make columns span multiple frames with %++.
        

        Markdown content of each slide is stored as `.markdown` attribute to slide. You can append content to it later like this:
        ```python
        with slides.slide(2):
            slides.parse(slides[2].markdown) # Instead of write, parse take cares of code blocks
            plot_something()
        ```
        
        ::: note-tip
            Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        
        ::: note-tip
            Use `Slides.sync_with_file` to auto update slides as markdown content changes.
        
        ::: note-info
            Use this function with 'next_' prefix to enable auto numbeing of slides inside python file.
        
        **Returns**: A tuple of handles to slides created. These handles can be used to access slides and set properties on them.
        """
        if self.this:
            raise RuntimeError('Creating new slides under an already running slide context is not allowed!')
        
        if not isinstance(content, str): #check path later or it will throw error
            raise TypeError(f"content expects a makrdown text block, got {content!r}")
        
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
            
        handles = self.create(*range(start, start + len(chunks))) # create slides faster or return older

        for i,chunk in enumerate(chunks):
            # Must run under this function to create frames with two dashes (--) and update only if things/variables change
            checks = (str(chunk) != getattr(handles[i],'_mdff',''), re.findall(r"\`\{(.*?)\}\`", chunk, flags=re.DOTALL), 'Out-Sync' in handles[i].dom_classes,)
            if any(checks):
                with self._loading_private(self.widgets.buttons.refresh): # Hold and disable other refresh button while doing it
                    self._slide(f'{i + start} -m', chunk)
            else: # when slide is not built, scroll buttons still need an update to point to correct button
                self._slides_per_cell.append(handles[i])
                for frame in handles[i].frames:
                    self._slides_per_cell.append(frame)

            handles[i]._mdff = str(chunk) # This is need for update while editing, chunk could be ns_str, avoid that
        
        # Return refrence to slides for quick update, frames should be accessed by slide.frames
        return handles
    
    def sync_with_file(self, start, path, trusted = False, interval=500):
        """Auto update slides when content of markdown file changes. You can stop syncing using `Slides.unsync` function.
        interval is in milliseconds, 500 ms default. Read `Slides.from_markdown` docs about content of file.
        
        The variables inserted in file content are used from top scope.
        """
        if not self.inside_jupyter_notebook(self.sync_with_file):
            raise Exception("Notebook-only function executed in another context!")
        
        path = Path(path) # keep as Path object
        
        if not path.is_file():
            raise FileNotFoundError(f"File {path!r} does not exists!")
        
        if not isinstance(interval, int) or interval < 100:
            raise ValueError("interval should be integer greater than 100 millieconds.")
        
        # NOTE: Background threads and other methods do not work. Do NOT change this way
        self.from_markdown(start, path.read_text(encoding="utf-8"), trusted) # First call itself before declaring other things, so errors can be captured safely
        
        if hasattr(self.widgets.iw,'_sync_args'): # remove previous updates
            self.unsync()

        self._mtime = os.stat(path).st_mtime

        def update(widget, content, buffer):
            if path.is_file():
                mtime = os.stat(path).st_mtime
                out_sync = any(['Out-Sync' in s.dom_classes for s in self.cited_slides]) or False
                if out_sync or (mtime > self._mtime):  # set by interaction widget
                    self._mtime = mtime
                    try: 
                        self.from_markdown(start, path.read_text(encoding="utf-8"), trusted)
                        self.notify('x') # need to remove any notification from previous error
                    except:
                        e, text = traceback.format_exc(limit=0).split(':',1) # onlly get last error for notification
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


    def demo(self):
        "Demo slides with a variety of content."
        from .._demo import demo_slides
        return demo_slides(self)
        
        
    def docs(self):
        "Create presentation from docs of IPySlides."
        self.close_view() # Close any previous view to speed up loading 10x faster on average
        self.clear() # Clear previous content
        self.create(*range(22)) # Create slides faster
        
        from ..core import Slides

        self.set_citations({'A': 'Citation A', 'B': 'Citation B'}, mode = 'footnote')
        self.settings.set_footer('IPySlides Documentation')

        with self.title(): # Title
            self.write(f'## IPySlides {self.version} Documentation\n### Creating slides with IPySlides')
            self.center('''
                alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`
                center`today```
                
                ::: text-box
                    sup`1`My University is somewhere in the middle of nowhere
                    sup`2`Their University is somewhere in the middle of nowhere
                ''').display()
        
        self.next_from_markdown(f'''
            section`Introduction` 
            ```toc ## Table of contents
            vspace`2`
            ### This is summary of current section
            Oh we can use inline columns || Column A || Column B || here and what not!
            ```
            ```markdown
             ```toc Table of contents
             Extra content for current section which is on right
             ```
            ```''')
            
        with self.next_slide():
            self.write(['# Main App',self.doc(Slides), '### Jump between slides'])
            self.doc(self.goto_button, 'Slides').display()
        
        with self.next_slide():
            self.write('## Adding Slides section`Adding Slides and Content`')
            self.write('Besides functions below, you can add slides with `%%title`/`%%slide` magics as well.\n{.note .info}')
            self.write([self.doc(self.title,'Slides'),self.doc(self.slide,'Slides'),self.doc(self.frames,'Slides'),self.doc(self.from_markdown,'Slides')])
        
        with self.next_slide(), self.code.context():
            self.write(self.fmt('`{self.version!r}` `{self.xmd_syntax}`'))
            
        with self.next_slide():
            self.write('## Adding Content')
            self.write('Besides functions below, you can add content to slides with `%%xmd`,`%xmd` as well.\n{.note .info}')
            self.write([self.classed(self.doc(self.write,'Slides'),'block-green'), self.doc(self.parse,'Slides'),self.doc(self.clip_image,'Slides')])
        
        with self.next_slide():
            self.write('## Adding Speaker Notes')
            (skipper := self.goto_button('Skip to Dynamic Content')).display()
            self.write([f'You can use alert`notes\`notes content\`` in markdown.\n{{.note .success}}\n',
                       'This is experimental feature, and may not work as expected.\n{.note-error .error}'])
            self.doc(self.notes,'Slides.notes', members = True, itself = False).display()
                   
        with self.next_slide():
            self.write('## Displaying Source Code')
            self.doc(self.code,'Slides.code', members = True, itself = False).display()
        
        self.next_from_markdown('section`?Layout and color[yellow,black]`Theme` Settings?` toc`### Contents`')
        
        with self.next_slide(): 
            self.write('## Layout and Theme Settings')
            self.doc(self.settings,'Slides.settings', members=True,itself = False).display()
                
        with self.next_slide():
            self.write('## Useful Functions for Rich Content section`?Useful Functions for alert`Rich Content`?`')
            self.doc(self.clip_image,'Slides').display()
            self.run_doc(self.alt,'Slides')
            
            members = sorted((
                'alert block bokeh2html bullets classed format_html fmt color cols details doc sub sup '
                'today error enable_zoom format_css highlight html iframe image keep_format notify plt2html '
                'raw rows set_dir sig textbox suppress_output suppress_stdout svg vspace'
            ).split())
            self.doc(self, 'Slides', members = members, itself = False).display()

        with self.next_slide():
            self.write('''
                ## Citations and Sections
                Use syntax alert`cite\`key\`` to add citations which should be already set by `Slides.set_citations(data, mode)` method.
                Citations are written on suitable place according to given mode. Number of columns in citations are determined by 
                `Slides.settings.set_layout(..., ncol_refs = int)`. cite`A`
                       
                Add sections in slides to separate content by alert`section\`text\``. Corresponding table of contents
                can be added with alert`toc\`title\``/alert`\`\`\`toc title\\n summary of current section \\n\`\`\``.
            ''')
            self.doc(self, 'Slides', members = ['set_citations'], itself = False).display()
            
        with self.next_slide():
            skipper.set_target() # Set target for skip button
            self.write('## Dynamic Content')
            self.run_doc(self.on_refresh,'Slides')
            self.run_doc(self.on_load,'Slides')
            self.this.get_source().display() # this refers to slide being built
    
        with self.next_slide():
            self.write('## Content Styling')
            with self.code.context(returns = True) as c:
                self.write(('You can **style**{.error} or **color[teal]`colorize`** your *content*{: style="color:hotpink;"} and *color[hotpink,yellow]`text`*. ' 
                       'Provide **CSS**{.info} for that using `.format_css` or use some of the available styles. '
                       'See these **styles**{.success} with `.css_styles` property as below:'))
                self.css_styles.display()
                c.display()
        
        s8, = self.next_from_markdown('''
        ## Highlighting Code
        [pygments](https://pygments.org/) is used for syntax highlighting cite`A`.
        You can **highlight**{.error} code using `highlight` function cite`B` or within markdown like this:
        ```python
        import ipyslides as isd
        ```
        ```javascript
        import React, { Component } from "react";
        ```
        proxy`source code of slide will be updated here later using slide_handle.proxies[0].capture contextmanager`
        ''', trusted= True)
        
        # Update proxy with source code
        with s8.proxies[0].capture(): # or with self.capture_proxy(s8.number, 0):
            s8.get_source().display()
        
        with self.next_slide():
            self.write('## Loading from File/Exporting to HTML section`Loading from File/Exporting to HTML`')
            self.write('You can parse and view a markdown file. The output you can save by exporting notebook in other formats.\n{.note .info}')
            self.write([self.doc(attr,'Slides') for attr in (self.sync_with_file,self.from_markdown,self.demo,self.docs,self.export_html)])
        
        self.next_from_markdown('section`Advanced Functionality` toc`### Contents`')
        
        with self.next_slide() as s:
            self.write('## Adding User defined Objects/Markdown Extensions')
            self.write(
                lambda: display(self.html('h3','I will be on main slides',className='warning'), 
                metadata = {'text/html': '<h3 class="warning">I will be on exported slides</h3>'}), # Can also do 'Slides.serilaizer.get_metadata(obj)' if registered
                s.get_source(), widths = [1,3]
            )
            self.write('If you need to serialize your own or third party objects not serialized by this module, you can use `@Slides.serializer.register` to serialize them to html.\n{.note .info}')
            self.doc(self.serializer,'Slides.serializer', members = True, itself = False).display()
            self.write('**You can also extend markdown syntax** using `markdown extensions`, ([See here](https://python-markdown.github.io/extensions/) and others to install, then use as below):')
            self.doc(self.extender,'Slides.extender', members = True, itself = False).display()
        
        with self.next_slide():
            self.write('''
            ## Focus on what matters
            - There is a zoom button on top bar which enables zooming of certain elements. This can be toggled by `Z` key.
            - Most of supported elements are zoomable by default like images, matplotlib, bokeh, PIL image, altair plotly, dataframe, etc.
            - You can also enable zooming for an object/widget by wrapping it inside `Slide.enable_zoom` function conveniently.
            - You can also enable by manully adding `zoom-self`, `zoom-child` classes to an element. To prevent zooming under as `zoom-child` class, use `no-zoom` class.
            
            ::: zoom-self block-red
                ### Focus on Me 😎
                - If zoom button is enabled, you can hover here to zoom in this part!
                - You can also zoom in this part by pressing `Z` key while mouse is over this part.
            ''')
        with self.next_slide():
            self.write('''
                ## SVG Icons
                Icons that apprear on buttons inslides (and their rotations) available to use in your slides as well.
                ''')
            self.write(' '.join([f'`{k}`: ' + self.icon(k,color='crimson').svg for k in self.icon.available]))
            
            with self.code.context():
                import ipywidgets as ipw
                btn = ipw.Button(description='Chevron-Down',icon='plus').add_class('MyIcon') # Any free font awesome icon, but class is important to overwrite icon     
                self.write(btn)
                self.format_css({'.MyIcon .fa.fa-plus': self.icon('chevron',color='crimson', size='1.5em',rotation=90).css}).display() # Overwrite icon with your own

            
        with self.next_slide():
            self.write([
                '# Auto Slide Numbering in Python Scripts', 
                *[self.doc(attr,'Slides') for attr in (self.next_slide, self.next_frames, self.next_from_markdown, self.next_number)]
            ])
        
        with self.next_slide():
            self.write(['## Presentation Code section`Presentation Code`',self.docs])
        
        self.navigate_to(0) # Go to title
        return self

def _parse_markdown_text(text_block):
    "Parses a Markdown text block and returns text for title and each slide."
    # user may used fmt
    lines = textwrap.dedent(text_block).splitlines() # Remove overall indentation
    breaks = [-1] # start, will add +1 next
    for i,line in enumerate(lines):
        if line and line.strip() =='---':
            breaks.append(i)
    breaks.append(len(lines)) # Last one
    
    ranges = [range(j+1,k) for j,k in zip(breaks[:-1],breaks[1:])]
    return [xtr.copy_ns(text_block, '\n'.join(lines[x.start:x.stop])) for x in ranges]
        