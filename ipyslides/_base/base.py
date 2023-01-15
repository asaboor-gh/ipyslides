"Inherit Slides class from here. It adds useful attributes and methods."
import os, re, textwrap
from .widgets import Widgets
from .screenshot import ScreenShot
from .navigation import Navigation
from .settings import LayoutSettings
from .notes import Notes
from .export_html import _HhtmlExporter
from .intro import key_combs
from ..formatters import _HTML
from ..xmd import _special_funcs

class BaseSlides:
    def __init__(self):
        self.__widgets = Widgets()
        self.__screenshot = ScreenShot(self.__widgets)
        self.clipboard_image = self.__screenshot.clipboard_image # For easy access
        self.__navigation = Navigation(self.__widgets) # Not accessed later, just for actions
        self.__settings = LayoutSettings(self, self.__widgets)
        self.__export = _HhtmlExporter(self)
        self.__notes = Notes(self, self.__widgets) # Needs main class for access to notes
        
        self.toast_html = self.widgets.htmls.toast
        
        self.widgets.checks.toast.observe(self.__toggle_notify,names=['value'])
    
    @property
    def notes(self):
        return self.__notes
    
    @property
    def widgets(self):
        return self.__widgets
    
    @property
    def export(self):
        return self.__export
    
    @property
    def screenshot(self):
        return self.__screenshot
    
    @property
    def settings(self):
        return self.__settings
    
    def notify(self,content,title='IPySlides Notification',timeout=5):
        "Send inside notifications for user to know whats happened on some button click. Set `title = None` if need only content. Remain invisible in screenshot."
        return self.widgets._push_toast(content,title=title,timeout=timeout)
    
    def __toggle_notify(self,change):
        "Blocks notifications if check is not enabled."
        if self.widgets.checks.toast.value:
            self.toast_html.layout.visibility = 'visible' 
            self.notify('Notifications are enabled now!')
        else:
            self.toast_html.layout.visibility = 'hidden'
    
    @property
    def css_styles(self):
        """CSS styles for markdown or `classed` command."""
        # self.html will be added from Chid class
        return self.raw('''
        Use any or combinations of these styles in className argument of writing functions:
        ------------------------------------------------------------------------------------
         className          | Formatting Style                                              
        ====================================================================================
         'align-center'     | ------Text------
         'align-left'       | Text------------
         'align-right'      | ------------Text
         'rtl'              | ------ اردو عربی 
         'info'             | Blue text. Icon ℹ️  for note-info class.
         'tip'              | Blue Text. Icon💡 for note-tip class.
         'warning'          | Orange Text. Icon ⚠️ for note-warning class.
         'success'          | Green text. Icon ✅ for note-success class.
         'error'            | Red Text. Icon⚡ for note-error class.
         'note'             | 📝 Text with note icon.
         'slides-only'      | Text will not appear in exported html report.
         'report-only'      | Text will not appear on slides. Use to fill content in report.
         'export-only'      | Hidden on main slides, but will appear in exported slides/report.
         'page-break'       | Report will break page in print after object with this class.
         'block'            | Block of text/objects
         'block-[color]'    | Block of text/objects with specific background color from red,
                            | green, blue, yellow, cyan, magenta and gray.
         'raw-text'         | Text will not be formatted and will be shown as it is.
         'zoom-self'        | Zooms object on hover, when Zoom is enabled.
         'zoom-child'       | Zooms child object on hover, when Zoom is enabled.
         'no-zoom'          | Disables zoom on object when it is child of 'zoom-child'.
        ------------------------------------------------------------------------------------
        ''')

    @property
    def xmd_syntax(self):
        "Special syntax for markdown."
        return _HTML(self.parse(textwrap.dedent('''
        ## Extended Markdown
        Extended syntax for markdown is constructed to support almost full presentation from Markdown.
        
        **Following syntax works only under currently building slide:**
        
        - alert`notes\`This is slide notes\``  to add notes to current slide
        - alert`cite\`key\`` to add citation to current slide
        - alert`citations\`citations title\``  to add citations at end if `citation_mode = 'global'`.
        - alert`section\`key\`` to add a section that will appear in the table of contents.
        - alert`toc\`Table of content header text\`` to add a table of contents. Run at last again to collect all.
        - alert`proxy\`placeholder text\`` to add a proxy that can be updated later with `Slides.proxies[index].capture` contextmanager. Useful to keep placeholders for plots in markdwon.
        - Triple dashes `---` is used to split markdown text in slides inside `from_markdown(start, file_or_str)` function.
        - Double dashes `--` is used to split markdown text in frames.
        
        **Other syntax can be used everywhere in markdown:**
        
        - A syntax alert`func\`&#63;Markdown&#63;\`` will be converted to alert`func\`Parsed HTML\`` in markdown. Useful to nest special syntax.
        - You can escape backtick with backslash: alert`\\\` → \``.
        - alert`include\`markdown_file.md\`` to include a file in markdown format.
        - Variables can be replaced with their HTML value (if possible) using \{\{variable\}\} syntax.
        - Two side by side columns can be added inline using alert`|&#124; Column A |&#124; Column B |&#124;` sytnax.
        - Block multicolumns are made using follwong syntax, column separtor is tiple plus `+++`: 
        
        ```markdown     
         ```multicol widthA widthB
         Column A
         +++
         Column B
         ```
        ```
        
        - Python code blocks can be exectude by syntax 
        ```markdown
         ```python run source {.CSS_className}
         slides = get_slides_instance() 
         slides.write('Hello, I was written from python code block using slides instance.')
         ```
        ```
        and source then can be emded with \{\{source\}\} syntax.
        
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
                `__format__` method in your class enables to use \{\{object\}\} syntax and `_repr_html_` method enables it to use inside `write` function.
        
        - Other options (that can also take extra args as alert`func[arg1,x=2,y=A]\`arg0\``) include:
        
        color[blue]`color[blue]\`text\``, color[yellow,skyblue]`color[yellow,skyblue]\`text\``, ''') + '\n' + ', '.join(f'alert`{k}\`{v}\``' for k,v in _special_funcs.items()),
        display_inline = False
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
        self.verify_running('Dynamic content can only be created under a slide constructor!')
        self.running._on_load_private(func) # This to make sure if code is correct before adding it to slide
    
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
        """
        return self._dynamic_private(func, tag = '_has_widgets', hide_refresher = False)
    
    def _dynamic_private(self, func, tag = None, hide_refresher = False):
        "Not for user use, internal function for other dynamic content decorators with their own tags."
        self.verify_running('Dynamic content can only be created under a slide constructor!')
        return self.running._dynamic_private(func, tag = tag, hide_refresher = hide_refresher)
        
    def from_markdown(self, start, file_or_str, trusted = False):
        """You can create slides from a markdown file or tex block as well. It creates slides `start + (0,1,2,3...)` in order.
        You should add more slides by higher number than the number of slides in the file/text, or it will overwrite.
        Slides separator should be --- (three dashes) in start of line.
        Frames separator should be -- (two dashes) in start of line. All markdown before first `--` will be written on all frames.
        
        **Markdown Content**
        ```markdown
        # Talk Title
        ---
        # Slide 1 
        || Inline - Column A || Inline - Column B ||
        {{some_var}} that will be replaced by it's html value.
         ```python run source
         myslides = get_slides_instance() # Access slides instance under python code block in markdown
         # code here will be executed and it's output will be shown in slide.
         ```
         {{source}} from above code block will be replaced by it's html value.
        ---
        # Slide 2
        --
        ## First Frame
         ```multicol 40 60
        # Block column 1
        +++
        # Block column 2
        || Mini - Column A || Mini - Column B ||
         ```
        --
        ## Second Frame
        ```
        This will create two slides along with title page if start = 0. Second slide will have two frames.
        
        Markdown content of each slide is stored as .markdown attribute to slide. You can append content to it later like this:
        ```python
        with slides.slide(2):
            slides.parse(slides[2].markdown) # Instead of write, parse take cares of code blocks
            plot_something()
        ```
        
        ::: note-tip
            Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        
        **Returns**: A tuple of handles to slides created. These handles can be used to access slides and set properties on them.
        """
        if self.shell is None or self.shell.__class__.__name__ == 'TerminalInteractiveShell':
            raise Exception('Python/IPython REPL cannot show slides. Use IPython notebook instead.')
        
        if not isinstance(file_or_str, str): #check path later or it will throw error
            raise ValueError(f"file_or_str expects a makrdown file path(str) or text block, got {file_or_str!r}")
        
        if not trusted:
            try: # Try becuase long string will through error for path
                os.path.isfile(file_or_str) # check if file exists then check code blocks
                with open(file_or_str, 'r') as f:
                    lines = f.readlines()
            except:
                lines = file_or_str.splitlines()
                    
            untrusted_lines = []
            for i, line in enumerate(lines, start = 1):
                if re.match(r'```python\s+run', line):
                    untrusted_lines.append(i)
            
            if untrusted_lines:
                raise Exception(f'Given file/text may contain unsafe code to be executed at lines: {untrusted_lines}'
                    ' Verify code is safe and try again with argument `trusted = True`.'
                    ' Never run files that you did not create yourself or not verified by you.')
        
        try:
            if os.path.isfile(file_or_str):
                with open(file_or_str, 'r') as f:
                    chunks = _parse_markdown_text(f.read())
            elif file_or_str.endswith('.md'): # File but does not exits
                raise FileNotFoundError(f'File {file_or_str} does not exist.')
            else:
                chunks = _parse_markdown_text(file_or_str)
        except:
            chunks = _parse_markdown_text(file_or_str)
            
        handles = self.create(*range(start, start + len(chunks))) # create slides faster
        
        with self.skip_post_run_cell():
            for i,chunk in enumerate(chunks, start = start):
                # Must run under this function to create frames with two dashes (--)
                self._slide(f'{i} -m', chunk)
        
        # Display slides if called form Notebook Cell only
        last_hist = list(self.shell.history_manager.get_range())[-1][-1]
        if re.findall(r'from_markdown\(|from_markdown\s+\(', last_hist):
            self.shell.events.register('post_run_cell', self._post_run_cell)
        
        # Return refrence to slides for quick update, frames should be accessed by slide.frames
        return handles
    
    def demo(self):
        "Demo slides with a variety of content."
        self.close_view() # Close any previous view to speed up loading 10x faster on average
        self.clear() # Clear previous content
        
        with self.set_dir(os.path.split(__file__)[0]):
            file = '../_demo.py'
            raw_source = self.source.from_file(file).raw
            N = raw_source.count('auto.') # Count number of slides
            self.create(*range(N)) # Create slides first, this is faster
            self.shell.run_line_magic('run', file) # Run demo in same namespace
            
        return self #_demo.demo(self) # Run demo
        
        
    def docs(self):
        "Create presentation from docs of IPySlides."
        self.close_view() # Close any previous view to speed up loading 10x faster on average
        self.clear() # Clear previous content
        self.create(*range(13)) # Create slides faster
        
        from ..core import Slides
        self.settings.set_footer('IPySlides Documentation')
        
        auto = self.AutoSlides() # Does not work inside notebook (should not as well)
        
        with auto.title(): # Title
            self.write(f'## IPySlides {self.version} Documentation\n### Creating slides with IPySlides')
            self.center('''
                alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`
                center`today```
                
                ::: text-box
                    sup`1`My University is somewhere in the middle of nowhere
                    sup`2`Their University is somewhere in the middle of nowhere
                ''').display()
        
        auto.from_markdown('section`Introduction` toc`### Contents`')
            
        with auto.slide():
            self.write(['# Main App',self.doc(Slides)])
        
        with auto.slide():
            self.write('## Adding Slides section`Adding Slides and Content`')
            self.write('Besides functions below, you can add slides with `%%title`/`%%slide` magics as well.\n{.note .info}')
            self.write([self.doc(self.title,'Slides'),self.doc(auto.slide,'Slides'),self.doc(self.frames,'Slides'),self.doc(self.from_markdown,'Slides')])
        
        with auto.slide():
            self.xmd_syntax.display() # This will display information about Markdown extended syntax
            
        with auto.slide():
            self.write('## Adding Content')
            self.write('Besides functions below, you can add content to slides with `%%xmd`,`%xmd`, `display(obj)` as well.\n{.note .info}')
            self.write([self.classed(self.doc(self.write,'Slides'),'block-green'), self.doc(self.parse,'Slides'),self.doc(self.cite,'Slides'),self.doc(self.clipboard_image,'Slides')])
        
        with auto.slide():
            self.write('## Adding Speaker Notes')
            self.write([f'You can use alert`notes\`notes content\`` in markdown.\n{{.note .success}}\n',
                       'This is experimental feature, and may not work as expected.\n{.note-error .error}'])
            self.doc(self.notes,'Slides.notes', members = True, itself = False).display()
            self.goto_button(10,'Jump to Slide 10', 'This is kind a alert`alt text` because button will alert`NOT` show in screenshot of slides')
                   
        with auto.slide():
            self.write('## Displaying Source Code')
            self.doc(self.source,'Slides.source', members = True, itself = False).display()
        
        auto.from_markdown('section`?Layout and color[yellow,black]`Theme` Settings?` toc`### Contents`')
        
        with auto.slide(): 
            self.write('## Layout and Theme Settings')
            self.doc(self.settings,'Slides.settings', members=True,itself = False).display()
                
        with auto.slide():
            self.write('## Useful Functions for Rich Content section`?Useful Functions for alert`Rich Content`?`')
            members = ['alert','block', 'bokeh2html', 'bullets','cite','classed',
                       'color', 'cols', 'details', 'doc','sub','sup', 'today', 'enable_zoom', 'format_css', 'format_html', 'highlight',
                       'html', 'iframe', 'image', 'keep_format', 'notify', 'plt2html', 'raw', 'rows',
                        'section', 'set_citations', 'set_dir', 'sig', 'textbox', 'suppress_output','suppress_stdout','svg', 'vspace']
            self.doc(self.clipboard_image,'Slides').display()
            self.doc(self, 'Slides', members = members, itself = False).display()
            
        with auto.slide() as s:
            self.write('## Dynamic Content')
            self.run_doc(self.on_refresh,'Slides')
            self.run_doc(self.on_load,'Slides')
            s.get_source().display()
            
    
        with auto.slide():
            self.write('## Content Styling')
            with self.source.context(auto_display = False) as c:
                self.write(('You can **style**{.error} or **color[teal]`colorize`** your *content*{: style="color:hotpink;"} and *color[hotpink,yellow]`text`*. ' 
                       'Provide **CSS**{.info} for that using `.format_css` or use some of the available styles. '
                       'See these **styles**{.success} with `.css_styles` property as below:'))
                self.css_styles.display()
                c.display()
        
        s8, = auto.from_markdown('''
        ## Highlighting Code
        [pygments](https://pygments.org/) is used for syntax highlighting.
        You can **highlight**{.error} code using `highlight` function or within markdown like this:
        ```python
        import ipyslides as isd
        ```
        ```javascript
        import React, { Component } from "react";
        ```
        proxy`source code of slide will be updated here later using slide_handle.proxies[0].capture contextmanager`
        ''', trusted= True)
        
        # Update proxy with source code
        with s8.proxies[0].capture(): # Capture to proxy
            s8.get_source().display()
        
        with auto.slide():
            self.write('## Loading from File/Exporting to HTML section`Loading from File/Exporting to HTML`')
            self.write('You can parse and view a markdown file. The output you can save by exporting notebook in other formats.\n{.note .info}')
            self.write([self.doc(self.from_markdown,'Slides'),
                        self.doc(self.demo,'Slides'), 
                        self.doc(self.docs,'Slides'),
                        self.doc(self.export.slides,'Slides.export'),
                        self.doc(self.export.report,'Slides.export')])
        
        auto.from_markdown('section`Advanced Functionality` toc`### Contents`')
        
        with auto.slide():
            self.write('## Adding User defined Objects/Markdown Extensions')
            self.write('If you need to serialize your own or third party objects not serialized by this module, you can use `@Slides.serializer.register` to serialize them to html.\n{.note .info}')
            self.doc(self.serializer,'Slides.serializer', members = True, itself = False).display()
            self.write('**You can also extend markdown syntax** using `markdown extensions`, ([See here](https://python-markdown.github.io/extensions/) and others to install, then use as below):')
            self.doc(self.extender,'Slides.extender', members = True, itself = False).display()
        
        with auto.slide():
            self.write('## Keys and Shortcuts\n'
                '- You can use `Slides.current` to access a slide currently in view.\n'
                '- You can use `Slides.running` to access the slide currently being built,'
                ' so you can set CSS, aminations etc.', key_combs)
        
        with auto.slide():
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
        with auto.slide():
            self.write('''
                ## SVG Icons
                Icons that apprear on buttons inslides (and their rotations) available to use in your slides as well.
                ''')
            self.write(' '.join([f'`{k}`: ' + self.icon(k,color='crimson').svg for k in self.icon.available]))
            
            with self.source.context():
                import ipywidgets as ipw
                btn = ipw.Button(description='Chevron-Down',icon='plus').add_class('MyIcon') # Any free font awesome icon, but class is important to overwrite icon     
                self.write(btn)
                self.format_css({'.MyIcon .fa.fa-plus': self.icon('chevron',color='crimson', size='1.5em',rotation=90).css}).display() # Overwrite icon with your own

            
        with auto.slide():
            self.write(['# Auto Slide Numbering in Python Scripts', self.doc(self.AutoSlides,'Slides')])
        
        with auto.slide():
            self.write(['## Presentation Code section`Presentation Code`',self.docs])
        
        self.navigate_to(0) # Go to title
        return self

def _parse_markdown_text(text_block):
    "Parses a Markdown text block and returns text for title and each slide."
    lines = textwrap.dedent(text_block).splitlines() # Remove overall indentation
    breaks = [-1] # start, will add +1 next
    for i,line in enumerate(lines):
        if line and line.strip() =='---':
            breaks.append(i)
    breaks.append(len(lines)) # Last one
    
    ranges = [range(j+1,k) for j,k in zip(breaks[:-1],breaks[1:])]
    return ['\n'.join(lines[x.start:x.stop]) for x in ranges]
        