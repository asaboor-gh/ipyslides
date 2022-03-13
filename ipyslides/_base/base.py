"Inherit LiveSlides class from here. It adds useful attributes and methods."
import os, io
from IPython import get_ipython
from contextlib import suppress
from .widgets import Widgets
from .print_pdf import PdfPrint
from .navigation import Navigation
from .settings import LayoutSettings
from .notes import Notes

class BaseLiveSlides:
    def __init__(self):
        "Both instnaces should be inside `LiveSlide` class."
        self.__widgets = Widgets()
        self.__print = PdfPrint(self.__widgets)
        self.__navigation = Navigation(self.__widgets) # Not accessed later, just for actions
        self.__settings = LayoutSettings(self.__widgets)
        self.notes = Notes(self, self.__widgets) # Needs main class for access to notes
        
        self._md_content = 'Slides not loaded from markdown.'
        
        self._toasts = {} #Store notifications
        self.toast_html = self.widgets.htmls.toast
        
        self.widgets.checks.toast.observe(self.__toggle_notify,names=['value'])
    
    @property
    def widgets(self):
        return self.__widgets
    
    @property
    def print(self):
        return self.__print
    
    @property
    def settings(self):
        return self.__settings
    
    def notify(self,content,title='IPySlides Notification',timeout=5):
        "Send inside notifications for user to know whats happened on some button click. Set `title = None` if need only content. Remain invisible in screenshot."
        return self.widgets._push_toast(content,title=title,timeout=timeout)
    
    def __toggle_notify(self,change):
        "Blocks notifications."
        if self.widgets.checks.toast.value:
            self.toast_html.layout.visibility = 'hidden' 
        else:
            self.toast_html.layout.visibility = 'visible'

    
    def notify_later(self, title='IPySlides Notification', timeout=5):
        """Decorator to push notification at slide under which it is run. 
        It should return a string that will be content of notifictaion.
        The content is dynamically generated by underlying function, 
        so you can set timer as well. Remains invisible in screenshot through app itself.
        
        @notify_at(title='Notification Title', timeout=5)
        def push_notification():
            time = datetime.now()
            return f'Notification at {time}'
        """
        def _notify(func): 
            self._toasts[f'{self._current_slide}'] = dict(func = func, kwargs = dict(title=title, timeout=timeout))
        return _notify
    
    def clear_notifications(self):
        "Remove all redundent notifications that show up."
        self._toasts = {} # Free up
    
    @property
    def notifications(self):
        "See all stored notifications."
        return self._toasts
    
    def display_toast(self):
        toast = self._toasts.get(self.access_key,None) #access_key is current slide's number from LiveSlides
        if toast:
            # clear previous content of notification as new one is about to be shown, this will ensure not to see on wrong slide
            self.widgets.htmls.toast.value = ''
            self.notify(content = toast['func'](), **toast['kwargs'])
    
    @property
    def md_content(self):
        "Get markdown content from loaded file."
        return self._md_content
        
    
    def from_markdown(self, path, footer_text = 'Author Name'):
        """You can create slides from a markdown file or StringIO object as well. It creates slides 1,2,3... in order.
        You should add more slides by higher number than the number of slides in the file, or it will overwrite.
        Slides separator should be --- (three dashes) in start of line.
        _________ Markdown File Content __________
        # Talk Title
        ---
        # Slide 1 
        ---
        # Slide 2
        ___________________________________________
        This will create two slides along with title page.
        
        Content of each slide from imported file is stored as list in `slides.md_content`. You can append content to it like this:
        ```python
        with slides.slide(2):
            write(slides.md_content[2])
            plot_something()
            write_something()
        ```
        
        > Note: With this method you can add more slides besides created ones.
        """
        if not (isinstance(path, io.StringIO) or os.path.isfile(path)): #check path later or it will throw error
            raise ValueError(f"File {path!r} does not exist or not a io.StringIO object.")
        
        self.convert2slides(True)
        self.clear()
        self.settings.set_footer(footer_text)
        
        if isinstance(path, io.StringIO):
            chunks = _parse_md_file(path)
        else:
            with open(path, 'r') as fp:
                chunks = _parse_md_file(fp)

        with self.title():
            self.write(chunks[0])
        for i,chunk in enumerate(chunks[1:],start=1):
            with self.slide(i):
                self.write(chunk)
            
        self._md_content = chunks # Store for later use
        
        return self
    
    def demo(self):
        """Demo slides with a variety of content."""
        get_ipython().user_ns['_s_l_i_d_e_s_'] = self
        from .. import _demo
        slides = _demo.slides # or it is self
        with slides.slide(100):
            slides.write('## This is all code to generate slides')
            slides.write(_demo)
            slides.write(self.demo)
        with slides.slide(101,background='#9ACD32'):
            with slides.source.context() as s:
                slides.write_citations()
            slides.write(s)
        
        slides.progress_slider.index = 0 # back to title
        return slides
        
        

def _parse_md_file(fp):
    "Parse a Markdown file or StringIO to put in slides and returns text for title and each slide."
    lines = fp.readlines()
    breaks = [-1] # start, will add +1 next
    for i,line in enumerate(lines):
        if line and line.strip() =='---':
            breaks.append(i)
    breaks.append(len(lines)) # Last one
    
    ranges = [range(j+1,k) for j,k in zip(breaks[:-1],breaks[1:])]
    return [''.join(lines[x.start:x.stop]) for x in ranges]
        