"Inherit LiveSlides class from here. It adds useful attributes and methods."
import json, re
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
        
        self.__toasts = {} #Store notifications
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
        if self.toast_check.value:
            self.toast_html.layout.visibility = 'hidden' 
        else:
            self.toast_html.layout.visibility = 'visible'
    
    def notify_at(self, slide, title='IPySlides Notification', timeout=5):
        """Decorartor to push notification at given slide. It should return as string. `slide` here is what you see on slides's footer like 3.1, not just int.
        The content is dynamically generated by underlying function, so you can set timer as well. Remains invisible in screenshot through app itself.
        
        @notify_at(slide=1)
        def push_to(slide): #you can refer slide number in noteification function. 
            ..."""
        def _notify(func): 
            self.__toasts[f'{slide}'] = dict(func = func,arg = slide,kwargs = dict(title=title, timeout=timeout))
        return _notify
    
    def clear_notifications(self):
        "Remove all redundent notifications that show up."
        self.__toasts = {} # Free up
    
    @property
    def notifications(self):
        "See all stored notifications."
        return self.__toasts
    
    def display_toast(self):
        # self.iterable is picked from LiveSlide class after instantiation
        slide_id = str(self.iterable[self.widgets.sliders.progress.value - 1]['n'])
        try:
            toast = self.__toasts[slide_id]
            self.notify(content=toast['func'](toast['arg']),**toast['kwargs'])
        except:pass 
        

    def load_ipynb(self, filename):
        """If you want to create slides in clean and linear execution way, use this method.
            
            - First cell of notebook should be imports and it will be executed.
                
                import ipyslides as isd
                slides = isd.LiveSlides()
                
            - Next cell will be used to create title page
                This should not have %%title or `with title`
            - Other cells will be slides
                Do not use `%%slide` or `with` slide if you use this function
                use other methods freely e.g.
                
                slides.cite...
                slides.notes.insert...
                slide.image...
            
            - Last cell should call `slides.load_ipynb(filename)`.
                This will not execute any other line of code in the cell.
                
            - A cell with tag #hide will not be executed.
        
        > Make sure notebook is saved before using this function. 
        """
        with open(filename, 'r') as f:
            try:
                nb = json.load(f, cls = DecodeCleanNotebook)
            except:
                raise ValueError(f'Notebook {filename!r}cannot be parsed')

        cells = [cell for cell in nb['cells'] if cell['source']]
        # check if previous slides
        for cell in cells:
            for check in ['^%%title','with*.title','^%%slide','@*.frames','with*.slide']: # Nod idea why . matches . and nothing too
                    if re.search(check, cell['source']):
                        return self.shell.run_cell_magic('markdown','',f'<span style="color:red">Cannot recreate a previously created slide</span>\n```python\n{cell["source"]}\n```')

        if len(cells) < 2:
            raise ValueError('Notebook should have at least 2 cells, first cell is just for imports and cell where `load_ipynb` is run is not included.')

        if cells[0]['cell_type'] == 'code':
            self.shell.run_cell(cells[0]) # run for any imports
            
        self.convert2slides(True) # call before adding slides
        
        with self.title():
            if cells[1]['cell_type'] == 'code':
                self.shell.run_cell(cells[1]['source'])
            else:
                self.write(cells[1]['source']) # Usually Markdown cell for title

        for i, cell in enumerate(cells[2:],start = 1):
            with self.slide(i):
                source = cell['source']
                if cell['cell_type'] == 'code':
                    self.shell.run_cell(source)
                else:
                    self.write(source) # Markdown

        return self
        

class DecodeCleanNotebook(json.JSONDecoder):
    """
    - Deserilizes Jupyter-Noteebook to dictionary with taking care of `#hide` in top of cell.
    - **Usage**
        - `json.load(fp,cls = DecodeCleanNotebook)`.
    """
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        ignored = ['metadata', 'execution_count', 'outputs']
        if 'cell_type' in obj:
            obj = {k:v for k,v in obj.items() if k not in ignored}
            obj['source'] = ''.join(obj['source']) #Make multiline string
            if '#hide' in obj['source']: #cells with #hide should not be executed
                obj['source'] = ''
            if 'load_ipynb' in obj['source']: # Don't repeat loading notebook
                obj['source'] = ''
        return obj
