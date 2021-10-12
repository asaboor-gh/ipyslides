from ipyslides.objs_formatter import bokeh2html, plt2html
import numpy as np, matplotlib.pyplot as plt # plt for imshow here
import itertools
from time import sleep
from PIL import ImageGrab
from IPython.display import display, Javascript, HTML, Image
import ipywidgets as ipw
from ipywidgets import Layout,Button,Box,HBox,VBox
from . import data_variables as dv
import datetime, re, os #re for updating font-size and slide number
from IPython.utils.capture import capture_output
from contextlib import contextmanager
from .utils import _cell_code, write, textbox
from . import utils
_under_slides = {k:getattr(utils,k,None) for k in utils.__all__}

def custom_progressbar(intslider):
    "This has a box as children[0] where you can put navigation buttons."
    html = ipw.HTML('''<style>
     .NavWrapper .nav-box .menu {font-size:24px !important; overflow:hidden;opacity:0.4;z-index:55;}
     .NavWrapper .nav-box .menu:hover {opacity:1;}

    .NavWrapper .nav-box {z-index:50;overflow: hidden;}
    .NavWrapper .widget-hprogress {height:4px; !impportant;}
    .NavWrapper, .NavWrapper>div {padding:0px;margin:0px;overflow:hidden;max-width:100%;}
    .NavWrapper .progress, .NavWrapper .progress .progress-bar {
        border-radius:0px; margin:0px;padding:0px;height:4px !important;overflow:hidden;left:0px;bottom:0px;}
    .NavWrapper .progress {width:100% !important;transform:translate(-2px,1px) !important;}
    </style>''')
    intprogress = ipw.IntProgress(min=intslider.min, max=intslider.max, layout=Layout(width='100%'))
    for prop in ('min','max','value'):
        ipw.link((intprogress, prop), (intslider, prop)) # These links enable auto refresh from outside
    return VBox([HBox(layout=Layout(height='0px')).add_class('nav-box'),
                            VBox([ html,intprogress]) ]).add_class('NavWrapper') #class is must
class NavBar:
    def __init__(self,N=10):
        "N is number of slides here."
        self.N = N
        self.images = {} #Store screenshots
        self.__print_settings = {'load_time':0.5,'quality':100,'bbox':None}
        self.uid = ''.join(np.random.randint(9, size=(20)).astype(str)) #To use in _custom_progressbar
        self.prog_slider = ipw.IntSlider(max = self.N,continuous_update=False,readout=True)
        self.btn_prev =  Button(icon='chevron-left',layout= Layout(width='auto',height='auto')).add_class('arrows')
        self.btn_next =  Button(icon='chevron-right',layout= Layout(width='auto',height='auto')).add_class('arrows')
        self.btn_setting =  Button(description= '\u2630',layout= Layout(width='auto',height='auto')).add_class('menu').add_class('float-cross-btn')
        self.btn_capture =  Button(description='\u2913',layout= Layout(width='auto',height='auto'),
                                   tooltip='Take Screen short in full screen. Order of multiple shots in a slide is preserved!',
                                   ).add_class('menu').add_class('screenshot-btn')
        for btn in [self.btn_next, self.btn_prev, self.btn_setting,self.btn_capture]:
                btn.style.button_color= 'transparent'
                btn.layout.min_width = 'max-content' #very important parameter
        
        self.dd_clear = ipw.Dropdown(description='Delete',options = ['None','Delete Current Slide Screenshots','Delete All Screenshots'])
        self.btn_pdf = Button(description='Save Slides Screenshots to PDF',layout= Layout(width='auto',height='auto'))
        self.btn_print = Button(description='Print PDF',layout= Layout(width='auto',height='auto'))
                
        self.info_html = ipw.HTML('<p>Put Your Info Here using `self.set_footer` function</p>')
        self.nav_footer =  HBox([self.btn_setting,self.btn_capture,
                              HBox([self.info_html],layout= Layout(overflow_x = 'auto',overflow_y='hidden')),
                              ])
        self.controls = HBox([self.btn_prev,ipw.Box([self.prog_slider]).add_class('prog_slider_box'),self.btn_next],
                            ).add_class('controls')
        self.build_navbar() # this is the main function to build the navbar
         
        self.btn_prev.on_click(self.__shift_left)
        self.btn_next.on_click(self.__shift_right)
        self.btn_capture.on_click(self.capture_screen)
        self.btn_pdf.on_click(self.__save_pdf)
        self.btn_print.on_click(self.__print_pdf)
        self.dd_clear.observe(self.__clear_images)
    
    def build_navbar(self):
        self.nav_bar = custom_progressbar(self.prog_slider)
        self.nav_bar.children[0].children = (self.nav_footer,)
        self.nav_bar.children[0].layout.height = '32px'
       
    def __shift_right(self,change):
        if change:
            self.prog_slider.value = (self.prog_slider.value + 1) % (self.N + 1)     
    
    def __shift_left(self,change):
        if change:
            self.prog_slider.value = (self.prog_slider.value - 1) % (self.N + 1)
    
    def show(self):
        return self.nav_bar
    __call__ = show
    
        
    @contextmanager
    def __print_context(self):
        hide_widgets = [self.controls,self.btn_setting,self.btn_capture]
        for w in hide_widgets:
            w.layout.visibility = 'hidden'
        try:    
            yield
        finally:
            for w in hide_widgets:
                w.layout.visibility = 'visible'  
                
    def screen_bbox(self):
        "Return screen's bounding box on windows, return None on other platforms which works as full screen too in screenshot."
        try:
            import ctypes
            user = ctypes.windll.user32
            user.SetProcessDPIAware()
            return (0, 0, user.GetSystemMetrics(0), user.GetSystemMetrics(1))
        except:
            return None

    def set_print_settings(self,load_time=0.5,quality=95,bbox = None):
        """Print settings. 
        - load_time: 0.5; time in seconds for each slide to load before print, only applied to Print PDF, not on manual screenshot. 
        - quality: 95; In term of current screen. Will not chnage too much above 95. 
        - bbox: None; None for full screen on any platform. Given screen position of slides in pixels as [left,top,right,bottom].
        > Note: Auto detection of bbox in frontends where javascript runs is under progress. """
        if bbox and len(bbox) != 4:
            return print("bbox expects [left,top,right,bottom] in integers")
        self.__print_settings = {'load_time':load_time,'quality':quality,'bbox':bbox if bbox else self.screen_bbox()} # better to get on windows
        # Display what user sets
        if bbox:
            img = ImageGrab.grab(bbox=bbox)
            _ = plt.figure(figsize=(4, 3), dpi=480) # For clear view
            return plt.imshow(img)     
    
    def get_print_settings(self):
        return self.__print_settings    
    
    def __set_resolution(self,image):
        "Returns resolution to make PDF printable on letter/A4 page."
        w, h = image.size
        if w > h:
            long, short, res = w, h, w/11  # letter page long size
        else:
            long, short, res = h, w, h/11
        
        if short/res > 8.25: # short side if out page, bring inside A4 size so work for both
            res = res*long/short  # increase resolution to shrink pages size to fit for print
        
        return res   
    
    def capture_screen(self,btn):
        "Saves screenshot of current slide into self.images dictionary when corresponding button clicked. Use in fullscreen mode"
        with self.__print_context():
            sleep(0.05) # Just for above clearance of widgets views
            img = ImageGrab.grab(bbox=self.__print_settings['bbox']) 
        for i in itertools.count():
            if not f'im-{self.prog_slider.value}-{i}' in self.images:
                self.images[f'im-{self.prog_slider.value}-{i}'] =  img 
                return # Exit loop
            
    def save_pdf(self,filename='IPySlides.pdf'):
        "Converts saved screenshots to PDF!"
        ims = [v for k,v in sorted(self.images.items(), key=lambda item: item[0])] # images sorted list
        if ims: # make sure not empty
            self.btn_pdf.description = 'Generatingting PDF...'
            ims[0].save(filename,'PDF',quality= self.__print_settings['quality'] ,save_all=True,append_images=ims[1:],
                        resolution=self.__set_resolution(ims[0]),subsampling=0)
            self.btn_pdf.description = 'Save Slides Screenshots to PDF'
        else:
            print('No images found to convert. Take screenshots of slides in full screen mode.')
    
    def __save_pdf(self,btn):
        self.save_pdf() # Runs on button
        
    def __print_pdf(self,btn):
        "Quick Print"
        self.btn_setting.click() # Close side panel
        imgs = []
        for i in range(self.prog_slider.max + 1):  
            with self.__print_context():
                self.prog_slider.value = i #keep inside context manger to avoid slide transitions
                sleep(self.__print_settings['load_time']) #keep waiting here until it almost loads 
                imgs.append(ImageGrab.grab(bbox=self.__print_settings['bbox']))
                  
        if imgs:
            imgs[0].save('IPySlides-Print.pdf','PDF',quality= self.__print_settings['quality'],save_all=True,append_images=imgs[1:],
                         resolution=self.__set_resolution(imgs[0]),subsampling=0)
        # Clear images at end
        for img in imgs:
            img.close()     
            
    
    def __clear_images(self,change):
        if 'Current' in self.dd_clear.value:
            self.images = {k:v for k,v in self.images.items() if f'-{self.prog_slider.value}-' not in k}
            for k,img in self.images.items():
                if f'-{self.prog_slider.value}-' in k:
                    img.close() # Close image to save mememory
        elif 'All' in self.dd_clear.value:
            for k,img in self.images.items():
                img.close() # Close image to save mememory
            self.images = {} # Cleaned up
        
        self.dd_clear.value = 'None' # important to get back after operation
    
        
class LiveSlides(NavBar):
    def __init__(self,magic_suffix='',animation_css = dv.animations['slide']):
        """Interactive Slides in IPython Notebook. Use `display(Markdown('text'))` instead of `print` in slides.
        - **Parameters**
            - magic_suffix: str, append a string to %%slide and %%title in case you have many instances of this class, they do not overwrite each other's magics.
                    So for LiveSlides('A'), use %%slideA, %%titleA, for LiveSlides('B'), use %%slideB, %%titleB and so on.
            - animation_css: CSS for animation. Set to '' if not animating. You can define yourself by editing `ipysildes.data_variables.animations`.
        - **Example**
            ```python 
            import ipyslides as isd 
            isd.initilize() #This will generate code in same cell including this class, which is self explainatory 
            ```
        """
        for k,v in _under_slides.items(): # Make All methods available in slides
            setattr(self,k,v)
        self.plt2html = plt2html
        self.bokeh2html = bokeh2html
        self.shell = get_ipython()
        self.shell.register_magic_function(self.__slide, magic_kind='cell',magic_name=f'slide{magic_suffix}')
        self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name=f'title{magic_suffix}')
        self.user_ns = self.shell.user_ns #important for set_dir
        self.animation_css = animation_css
        self.__citations = {} # Initialize citations
        self.__slides_mode = False
        self.__slides_title_page = '''## Create title page using `%%title` magic or `self.title()` context manager.\n> Author: Abdul Saboor\n<div>
        <h4 style="color:green;">Create Slides using <pre>%%slide</pre> or with <pre>self.slide(slide_number)</pre> context manager.</h4>
        <h4 style="color:olive;">Read instructions by clicking on left-bottom button</h4></div>
        '''
        self.__slides_dict = {} # Initialize slide dictionary
        self.__dynamicslides_dict = {} # initialize dynamic slides dictionary
        
        self.iterable = self.__collect_slides() # Collect internally
        self.out = ipw.Output(layout= Layout(width='auto',height='auto',margin='auto',overflow='auto',padding='2px 16px')
                              ).add_class('SlideArea')
        
        _max = len(self.iterable) if self.iterable else 0
        super().__init__(N=_max)
        self.theme_root = dv.inherit_root
        self.font_scale = 1 #Scale 1 corresponds to 16px
        self.theme_html = ipw.HTML(dv.style_html(dv.inherit_root.replace(
                                '__text_size__','16px').replace(
                                '__breakpoint_width__','650px')) + dv.editing_layout_css())
        self.main_style_html = ipw.HTML(dv.main_layout_css)
        self.loading_html = ipw.HTML() #SVG Animation in it
        self.prog_slider.observe(self.__update_content,names=['value'])
        
        self.setting = Customize(self)
        self.panel_box = self.setting.box
        self.slide_box = Box([self.out],layout= Layout(min_width='100%',overflow='auto')).add_class('SlideBox')
        self.logo_html = ipw.HTML()
        self.box =  VBox([self.loading_html, self.main_style_html,
                          self.theme_html,self.logo_html,
                          HBox([self.panel_box,
                                self.slide_box,
                          ],layout= Layout(width='100%',max_width='100%',height='100%',overflow='hidden')), #should be hidden for animation purpose
                          self.controls,
                          self.nav_bar
                          ],layout= Layout(width=f'{self.setting.width_slider.value}vw', height=f'{self.setting.height_slider.value}px',margin='auto'))
        self.box.add_class('SlidesWrapper') #Very Important 
        self.__update_content(True) # First attmpt
    
        
    def set_logo(self,src,width=80,top=0,right=16):
        "`src` should be PNG/JPEG file name or SVG string. width,top,right are pixels, should be integer."
        if '<svg' in src and '</svg>' in src:
            image = src
        else:
            img = Image(src,width=width)._repr_mimebundle_() # Picks PNG/JPEG
            _src,=[f'data:{k};base64, {v}' for k,v in img[0].items()]
            image = f"<img src='{_src}' width='{width}px'/>"
            
        self.logo_html.value = f"""<div style='position:absolute;right:{right}px;top:{top}px;width:{width}px;height:auto;'>
                                    {image}</div>"""
    
    def __add__(self,other):
        "Add two slides instance, title page of other is taken as a slide."
        slides = LiveSlides()
        slides.convert2slides(True)
        slides.set_footer() #starting text
        with slides.title():
            if isinstance(self.__slides_title_page, str):
                write(self.__slides_title_page) #Markdown String 
            else:
                self.__slides_title_page.show() #Ipython Captured Output 
        # Make slide from other slides' title page
        _slide = {'slide': other.__slides_title_page, 'func':write if isinstance(other.__slides_title_page, str) else None}
            
        for i, s in enumerate([*self.iterable, _slide, *other.iterable]):
            with slides.slide(i+1):
                if s['func'] == None:
                    s['slide'].show() # Pre-Calculated Slides
                else:
                    s['func'](s['slide']) #Show dynamic slides 
        return slides
    
    def cite(self,key, citation,here=False):
        "Add citation in presentation, both key and citation are text/markdown/HTML."
        if here:
            return textbox(citation,left='initial',top='initial') # Just write here
        self.__citations[key] = citation
        _id = list(self.__citations.keys()).index(key)
        return f'<sup style="color:var(--accent-color);">{_id + 1}</sup>'
    
    def write_citations(self,title='### References'):     
        collection = [f'<span><sup style="color:var(--accent-color);">{i+1}</sup>{v}</span>' for i,(k,v) in enumerate(self.__citations.items())]
        return write(title + '\n' +'\n'.join(collection))      
    
    def show(self,fix_buttons=False): 
        "Display Slides, If icons do not show, try with `fix_buttons=True`."
        if not self.__slides_mode:
            return print('Set "self.convert2slides(True)", then it will work.')
        if fix_buttons:
            self.btn_next.description = '▶'
            self.btn_prev.description = '◀'
            self.btn_prev.icon = ''
            self.btn_next.icon = ''
        else: # Important as showing again with False will not update buttons. 
            self.btn_next.description = ''
            self.btn_prev.description = ''
            self.btn_prev.icon = 'chevron-left'
            self.btn_next.icon = 'chevron-right'
        self.__jlab_in_cell_display()
        return self.box
    __call__ = show
    
    def _ipython_display_(self):
        'Auto display when self is on last line of a cell'
        self.__jlab_in_cell_display()
        return display(self.box)
    
    def __jlab_in_cell_display(self): 
        return display(ipw.HTML("""<h2 style='color:var(--accent-color);'>IPySlides ⇲</h2>"""))
    
    def align8center(self,b=True):
        "Central aligment of slide by default. If False, left-top aligned."
        if b:
            self.out.layout.margin = 'auto'
            self.out.layout.width = 'auto'
            self.out.layout.max_width = '100%'
        else:
            self.out.layout.margin = '2px 8px 2px 8px'
            self.out.layout.width = '100%'
        
    def set_font_scale(self,font_scale=1):
        self.font_scale= font_scale
        self.setting.update_theme()   
    
    def __display_slide(self):
        item = self.iterable[self.prog_slider.value-1]
        if item['func'] == None:
            return item['slide'].show() # Pre-Calculated Slides
        return item['func'](item['slide']) #Show dynamic slides 
           
    def __update_content(self,change):
        if self.__slides_title_page or (self.iterable and change):
            self.info_html.value = re.sub('>\d+\s+/\s+\d+<',f'>{self.prog_slider.value} / {self.N}<',self.info_html.value) #Slide Number
            self.loading_html.value = dv.loading_svg
            self.out.clear_output(wait=True)
            with self.out:
                if not self.controls.layout.visibility == 'hidden': #could be None too, so not hidden is better
                    write(self.animation_css) # Per Slide makes it uniform only when not printing
                    
                if self.prog_slider.value == 0:
                    if isinstance(self.__slides_title_page, str):
                        write(self.__slides_title_page) #Markdown String 
                    else:
                        self.__slides_title_page.show() #Ipython Captured Output
                else:
                    self.__display_slide()

            self.loading_html.value = ''       
            
    def set_footer(self, text = 'Abdul Saboor | <a style="color:blue;" href="www.google.com">google@google.com</a>', show_slide_number=True, show_date=True):
        if show_date:
            text += f' | <text style="color:var(--accent-color);">' + datetime.datetime.now().strftime('%b-%d-%Y')+ '</text>'
        if show_slide_number: #Slide number should be  exactlly like '>Int / Int<' for regex substitutioon.  
            text += f' | <b style="color:var(--accent-color);">{self.prog_slider.value} / {self.N}<b>'
        self.info_html.value = f'<p style="white-space:nowrap;"> {text} </p>'
        
    def refresh(self):
        "Auto Refresh whenever you create new slide or you can force refresh it"
        self.iterable = self.__collect_slides()
        self.N = len(self.iterable) if self.iterable else 0 #N an max both need to be updated
        self.prog_slider.max = self.N
        self.__update_content(True) # Force Refresh
        
    def write_slide_css(self,**css_props):
        "Prove CSS values with - replaced by _ e.g. font-size to font_size."
        _css_props = {k.replace('_','-'):f"{v}" for k,v in css_props.items()} #Convert to CSS string if int or float
        _css_props = {k:v.replace('!important','').replace(';','') + '!important;' for k,v in _css_props.items()}
        props_str = ''.join([f"{k}:{v}" for k,v in _css_props.items()])
        out_str = "<style>\n.SlidesWrapper {" + props_str + "}\n"
        if 'color' in _css_props:
            out_str += f".SlidesWrapper p, .SlidesWrapper>:not(div){{ color: {_css_props['color']}}}"
        return write(out_str + "\n</style>") # return a write object for actual write
    
    # defining magics and context managers
    
    def __slide(self,line,cell):
        "Turns to cell magic `slide` to capture slide. Moves to this slide when executed."
        line = line.strip() #VSCode bug to inclue \r in line
        if line and not line.isnumeric():
            return print(f'You should use %%slide integer, not %%slide {line}')
        if self.__slides_mode:
            self.shell.run_cell_magic('capture',line,cell)
            if line: #Only keep slides with line number
                self.__slides_dict[line] = self.shell.user_ns[line]
                del self.shell.user_ns[line] # delete the line from shell
                self.refresh()
                self.prog_slider.value = int(line) # Move there
        else:
            self.shell.run_cell(cell)
    
    @contextmanager
    def slide(self,slide_number,**css_props):
        """Use this context manager to generate any number of slides from a cell
        `css_props` are applied to current slide. `-` -> `_` as `font-size` -> `font_size` in python."""
        if not isinstance(slide_number,int):
            return print(f'slide_number expects integer, got {slide_number!r}')
        with capture_output() as cap:
            self.write_slide_css(**css_props)
            yield
        # Now Handle What is captured
        if not self.__slides_mode:
            cap.show()
        else:
            self.__slides_dict[f'{slide_number}'] = cap 
            self.refresh()
    
    def enum_slides(self,start,stop,step=1,**css_props):
        """Enumeration shortcurt for adding slides through a loop. start, stop, step are passed to `range`.
        It can overwrite slides created with `with slide`  and `%%slide`. css_props are applied to each slide.
        - **Example**
            for i,s in enum_slides(50,55):
            with s:
                print(f'Slide {i}')
        """
        return ((i , self.slide(i,**css_props)) for i in range(start,stop,step))
    
    def code_line_numbering(self,b=True):
        if b:
            return display(HTML('<style> code:before{ display:inline-block !important; } </style>'))
        return display(HTML('<style> code:before{ display:none !important; } </style>'))
    
    def __title(self,line,cell):
        "Turns to cell magic `title` to capture title"
        if self.__slides_mode:
            self.shell.run_cell_magic('capture','title_output',cell)
            self.__slides_title_page = self.shell.user_ns['title_output']
            del self.shell.user_ns['title_output'] # delete from shell
            self.refresh()
        else:
            self.shell.run_cell(cell)
            
    @contextmanager
    def title(self,**css_props):
        """Use this context manager to write title.
        `css_props` are applied to current slide. `-` -> `_` as `font-size` -> `font_size` in python."""
        with capture_output() as cap:
            self.write_slide_css(**css_props)
            yield
        # Now Handle What is captured
        if not self.__slides_mode:
            cap.show()
        else:
            self.__slides_title_page = cap 
            self.refresh()
    
    def slides(self, after_slide_number, *objs, **css_props):
        """Decorator for inserting slides dynamically, define a function with one argument acting on each obj in objs.
        No return of function required, if any, only should be display/show etc.\
        `css_props` are applied to all slides from *objs. `-` -> `_` as `font-size` -> `font_size` in python."""
        def _slides(func):
            if not isinstance(after_slide_number,int):
                return print(f'after_slide_number expects integer, got {after_slide_number!r}')

            if not self.__slides_mode:
                print(f'Showing raw form of given objects, will be displayed in slides using function {func} dynamically')
                return objs
            else:
                _slides = []
                for obj in objs:
                    with capture_output() as cap:
                        self.write_slide_css(**css_props)
                        func(obj)
                    _slides.append(cap)
                
                self.__dynamicslides_dict[f'd{after_slide_number}'] = {'objs': _slides,'func':None}
                    
                self.refresh() # Content chnage refreshes it.
        return _slides
        
    def convert2slides(self,b=False):
        "Turn ON/OFF slides vs editing mode. Should be in same cell as `LiveSLides`"
        self.__slides_mode = b
        
    def __collect_slides(self):
        """Collect cells for an instance of LiveSlides."""
        if not self.__slides_mode:
            return [] # return empty in any case

        dynamic_slides = [k.replace('d','') for k in self.__dynamicslides_dict.keys()]
        # If slide number is mistaken, still include that. 
        all_slides = [int(k) for k in [*self.__slides_dict.keys(), *dynamic_slides]]

        try: #handle dynamic slides if empty
            _min, _max = min(all_slides), max(all_slides) + 1
        except:
            _min, _max = 0, 0
        slides_iterable = []
        for i in range(_min,_max):
            if f'{i}' in self.__slides_dict.keys():
                slides_iterable.append({'slide':self.__slides_dict[f'{i}'],'func':None}) 
            if f'd{i}' in self.__dynamicslides_dict.keys():
                __dynamic = self.__dynamicslides_dict[f'd{i}']
                slides = [{'slide':obj,'func':__dynamic['func']} for obj in __dynamic['objs']]
                slides_iterable = [*slides_iterable,*slides]        
        return tuple(slides_iterable)
    
    def get_cell_code(self,this_line=True,magics=False,comments=False,lines=None):
        "Get current cell's code. `lines` should be list/tuple of line numbers to include if filtered."
        return _cell_code(shell=self.shell,this_line=this_line,magics=magics,comments=comments,lines=lines)

class Customize:
    def __init__(self,instance_LiveSlides):
        "Provide instance of LivSlides to work."
        self.master = instance_LiveSlides
        def describe(value): return {'description': value, 'description_width': 'initial','layout':Layout(width='auto')}
        
        self.height_slider = ipw.IntSlider(**describe('Height (px)'),min=200,max=2160, value = 500,continuous_update=False).add_class('height-slider') #2160 for 4K screens
        self.width_slider = ipw.IntSlider(**describe('Width (vw)'),min=20,max=100, value = 50,continuous_update=False).add_class('width-slider')
        self.scale_slider = ipw.FloatSlider(**describe('Font Scale'),min=0.5,max=3,step=0.0625, value = 1.0,readout_format='5.3f',continuous_update=False)
        self.theme_dd = ipw.Dropdown(**describe('Theme'),options=['Inherit','Light','Dark','Custom'])
        self.master.dd_clear.layout = self.theme_dd.layout # Fix same
        self.__instructions = ipw.Output(clear_output=False, layout=Layout(width='100%',height='100%',overflow='auto',padding='4px')).add_class('panel-text')
        self.out_js_css = ipw.Output(layout=Layout(width='auto',height='0px'))
        self.btn_fs = ipw.ToggleButton(description='Window',icon='expand',value = False).add_class('sidecar-only').add_class('window-fs')
        self.btn_mpl = ipw.ToggleButton(description='Matplotlib Zoom',icon='toggle-off',value = False).add_class('sidecar-only').add_class('mpl-zoom')
        btns_layout = Layout(justify_content='space-around',padding='8px',height='max-content',min_height='30px',overflow='auto')
        self.box = VBox([Box([self.__instructions],layout=Layout(width='100%',height='auto',overflow='hidden')),
                        self.master.btn_setting, # Must be in middle so that others dont get disturbed. 
                        self.out_js_css, # Must be in middle so that others dont get disturbed.
                        VBox([
                            self.height_slider.add_class('voila-sidecar-hidden'), 
                            self.width_slider.add_class('voila-sidecar-hidden'),
                            self.scale_slider,
                            self.theme_dd,
                            ipw.HTML('<hr/><span>Take screenshot in FULLSCREEN mode only or set `bbox` using `set_print_settings` method!</span>'),
                            self.master.dd_clear,
                            HBox([self.master.btn_pdf, self.master.btn_print], layout=btns_layout),
                            ipw.HTML('<hr/>'),
                            HBox([self.btn_fs,self.btn_mpl], layout=btns_layout),
                            ],layout=Layout(width='100%',height='max-content',min_height='400px'))
                        ],layout=Layout(width='70%',min_width='50%',height='100%',padding='4px',overflow='auto',display='none')
                        ).add_class('panel')
        with self.__instructions:
            write(dv.settings_instructions)
        
        self.__add_js() # Add js in start to load LabShell in required size    
        
        self.theme_dd.observe(self.update_theme)
        self.scale_slider.observe(self.__set_font_scale)
        self.height_slider.observe(self.__update_size,names=['value'])
        self.width_slider.observe(self.__update_size,names=['value'])
        self.master.btn_setting.on_click(self.__toggle_panel)
        self.btn_fs.observe(self.update_theme,names=['value'])
        self.btn_mpl.observe(self.update_theme,names=['value'])
        self.update_theme() #Trigger
    
    def __add_js(self):
        with self.out_js_css: 
            self.out_js_css.clear_output(wait=True)
            display(Javascript(dv.navigation_js))
            # For LabShell Resizing on width change, very important
            display(Javascript("window.dispatchEvent(new Event('resize'))"))
        
    def __update_size(self,change):
        self.master.box.layout.height = '{}px'.format(self.height_slider.value)
        self.master.box.layout.width = '{}vw'.format(self.width_slider.value)
        self.update_theme(change=None) # For updating size and breakpoints
        self.__add_js() # For LabShell Resize, very important
            
    def __toggle_panel(self,change):
        if self.master.btn_setting.description == '\u2630':
            self.master.btn_setting.description  = '⨉'
            self.box.layout.display = 'flex'
        else:
            self.master.btn_setting.description = '\u2630'
            self.box.layout.display = 'none'
                     
    def __set_font_scale(self,change):
        # Below line should not be in update_theme to avoid loop call.
        self.master.set_font_scale(self.scale_slider.value)
        
    def update_theme(self,change=None):  
        self.__add_js()
        text_size = '{}px'.format(int(self.master.font_scale*16))
        if self.theme_dd.value == 'Inherit':
            theme_css = dv.style_html(self.master.theme_root)
        elif self.theme_dd.value == 'Light':
            theme_css = dv.style_html(dv.light_root)
        elif self.theme_dd.value == 'Dark':
            theme_css = dv.style_html(dv.dark_root)
        elif self.theme_dd.value == 'Custom': # In case of Custom CSS
            with self.master.set_dir(self.master.user_ns['_dh'][0]):
                if not os.path.isfile('custom.css'):
                    with open('custom.css','w') as f:
                        _str = dv.style_html(dv.light_root).replace('<style>','').replace('</style>','')
                        f.writelines(['/* Author: Abdul Saboor */'])
                        f.write(_str)
                # Read CSS from file
                with open('custom.css','r') as f:
                    theme_css = '<style>' + ''.join(f.readlines()) + '</style>'
        # Replace font-size and breakpoint size
        theme_css = theme_css.replace('__text_size__',text_size) 
        # Catch Fullscreen too.
        if self.btn_fs.value:
            theme_css = theme_css.replace('__breakpoint_width__','650px').replace('</style>','\n') + dv.fullscreen_css.replace('<style>','')
            self.btn_fs.icon = 'compress'
            try:self.master.box.add_class('FullScreen')
            except:pass
        else:
            theme_css = theme_css.replace('__breakpoint_width__',f'{int(100*650/self.width_slider.value)}px') #Will break when slides is 650px not just window
            edit_mode_css = dv.editing_layout_css(self.width_slider.value)
            theme_css = theme_css.replace('</style>','\n') + edit_mode_css.replace('<style>','')
            self.master.theme_html.value = theme_css #Push CSS without Fullscreen
            self.btn_fs.icon = 'expand'
            try:self.master.box.remove_class('FullScreen')
            except: pass
        # Matplotlib's SVG Zoom 
        if self.btn_mpl.value:
            self.btn_mpl.icon= 'toggle-on'
            theme_css = theme_css.replace('</style>','\n') + dv.mpl_fs_css.replace('<style>','')
        else:
            self.btn_mpl.icon= 'toggle-off'
        
        # Now Set Theme
        self.master.theme_html.value = theme_css



