import numpy as np
from IPython.display import display, Javascript
import ipywidgets as ipw
from ipywidgets import Layout,Button,Box,HBox,VBox
from . import data_variables as dv
import datetime, re, os #re for updating font-size and slide number
from IPython.utils.capture import capture_output
from contextlib import contextmanager
from .utils import write, _cell_code, set_dir, textbox

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
        
        self.uid = ''.join(np.random.randint(9, size=(20)).astype(str)) #To use in _custom_progressbar
        self.prog_slider = ipw.IntSlider(max = self.N,continuous_update=False,readout=True)
        self.btn_prev =  Button(icon='chevron-left',layout= Layout(width='auto',height='auto')).add_class('arrows')
        self.btn_next =  Button(icon='chevron-right',layout= Layout(width='auto',height='auto')).add_class('arrows')
        self.btn_setting =  Button(description= '\u2630',layout= Layout(width='auto',height='auto')).add_class('menu')
        for btn in [self.btn_next, self.btn_prev, self.btn_setting]:
                btn.style.button_color= 'transparent'
                btn.layout.min_width = 'max-content' #very important parameter
                
        self.info_html = ipw.HTML('<p>Put Your Info Here using `self.set_footer` function</p>')
        self.nav_footer =  HBox([self.btn_setting,
                              HBox([self.info_html],layout= Layout(overflow_x = 'auto',overflow_y='hidden')),
                              ])
        self.controls = HBox([self.btn_prev,ipw.Box([self.prog_slider]).add_class('prog_slider_box'),self.btn_next],
                            ).add_class('controls')
        self.build_navbar() # this is the main function to build the navbar
         
        self.btn_prev.on_click(self.__shift_left)
        self.btn_next.on_click(self.__shift_right)
    
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
        self.shell = get_ipython()
        self.shell.register_magic_function(self.__slide, magic_kind='cell',magic_name=f'slide{magic_suffix}')
        self.shell.register_magic_function(self.__title, magic_kind='cell',magic_name=f'title{magic_suffix}')
        self.user_ns = self.shell.user_ns #important for set_dir
        self.animation_css = animation_css
        self.__citations = {} # Initialize citations
        self.__slides_mode = False
        self.__slides_title_page = '''## Create title page using `%%title` magic or `self.title()` context manager.\n> Author: Abdul Saboor\n<div>
        <h4 style="color:green;">Create Slides using <pre>%%slide</pre> or with <pre>self.slide(<slide number>)</pre> context manager.</h4>
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
        self.theme_html = ipw.HTML(dv.style_html(dv.inherit_root.replace('__text_size__','16px')))
        self.main_style_html = ipw.HTML(dv.main_layout_css)
        self.loading_html = ipw.HTML() #SVG Animation in it
        self.prog_slider.observe(self.__update_content,names=['value'])
        
        self.setting = Customize(self)
        self.panel_box = self.setting.box
        self.slide_box = ipw.Box([self.out],layout= Layout(min_width='100%',overflow='auto')).add_class('SlideBox')
        
        self.box =  VBox([self.loading_html, self.main_style_html,
                          self.theme_html,
                          HBox([self.panel_box,
                                self.slide_box,
                          ],layout= Layout(width='100%',max_width='100%',height='100%',overflow='hidden')), #should be hidden for animation purpose
                          self.controls,
                          self.nav_bar
                          ],layout= Layout(width=f'{self.setting.width_slider.value}vw', height=f'{self.setting.height_slider.value}px',margin='auto'))
        self.box.add_class('SlidesWrapper') #Very Important 
        self.__update_content(True) # First attmpt
    
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
            
        try:   #JupyterLab Case, Interesting in SideCar
            from sidecar import Sidecar 
            sc = Sidecar(title='Live Presentation')
            with sc:
                display(self.box)
        except:
            return self.box
    __call__ = show
    
    def _ipython_display_(self):
        'Auto display when self is on last line of a cell'
        return display(self.box)
    
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
        if 'func' in item.keys():
            if item['func'] == None:
                return item['slide'].show() # Pre-Calculated Slides
            return item['func'](item['slide']) #Show dynamic slides
        else:
            return item['slide'].show() #show ipython capture/slide context or if item has a show method with display. 
           
    def __update_content(self,change):
        if self.__slides_title_page or (self.iterable and change):
            self.info_html.value = re.sub('>\d+\s+/\s+\d+<',f'>{self.prog_slider.value} / {self.N}<',self.info_html.value) #Slide Number
            self.loading_html.value = dv.loading_svg
            self.out.clear_output(wait=True)
            with self.out:
                write(self.animation_css) # Per Slide makes it uniform
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
        
    def __per_slide_css(self,**css_props):
        props_str = ''.join([f"{k.replace('_','-')}:{v};" for k,v in css_props.items()])
        return write("<style>\n.SlidesWrapper {" + props_str + "}\n</style>") # return a write object for actual write
    
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
            self.__per_slide_css(**css_props)
            yield
        # Now Handle What is captured
        if not self.__slides_mode:
            cap.show()
        else:
            self.__slides_dict[f'{slide_number}'] = cap 
            self.refresh()
    
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
            self.__per_slide_css(**css_props)
            yield
        # Now Handle What is captured
        if not self.__slides_mode:
            cap.show()
        else:
            self.__slides_title_page = cap 
            self.refresh()
    
    def slides(self, after_slide_number, *objs, calculate_now=True,**css_props):
        """Decorator for inserting slides dynamically, define a function with one argument acting on each obj in objs.
        No return of function required, if any, only should be display/show etc.\
        `calculate_now = True` build slides in advance and `False` calculate when slide appears.
        `css_props` are applied to all slides from *objs. `-` -> `_` as `font-size` -> `font_size` in python."""
        def _slides(func):
            if not isinstance(after_slide_number,int):
                return print(f'after_slide_number expects integer, got {after_slide_number!r}')

            if not self.__slides_mode:
                print(f'Showing raw form of given objects, will be displayed in slides using function {func} dynamically')
                return objs
            else:
                if calculate_now:
                    _slides = []
                    for obj in objs:
                        with capture_output() as cap:
                            self.__per_slide_css(**css_props)
                            func(obj)
                        _slides.append(cap)
                    
                    self.__dynamicslides_dict[f'd{after_slide_number}'] = {'objs': _slides,'func':None}
                else:
                    def new_func(item):
                        self.__per_slide_css(**css_props)
                        return func(item)
                    self.__dynamicslides_dict[f'd{after_slide_number}'] = {'objs': objs,'func':new_func}
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
                slides_iterable.append({'slide':self.__slides_dict[f'{i}']}) 
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
        
        self.height_slider = ipw.IntSlider(**describe('Height (px)'),min=200,max=1000, value = 500,continuous_update=False)
        self.width_slider = ipw.IntSlider(**describe('Width (vw)'),min=40,max=100, value = 65,continuous_update=False)
        self.scale_slider = ipw.FloatSlider(**describe('Font Scale'),min=0.5,max=3,step=0.0625, value = 1.0,readout_format='5.3f',continuous_update=False)
        self.theme_dd = ipw.Dropdown(**describe('Theme'),options=['Inherit','Light','Dark','Custom'])
        self.__instructions = ipw.Output(clear_output=False, layout=Layout(width='100%',height='100%',overflow='auto',padding='4px')).add_class('panel-text')
        self.btn_fs = ipw.ToggleButton(description='Window',icon='expand',value = False).add_class('sidecar-only')
        self.btn_mpl = ipw.ToggleButton(description='Matplotlib SVG Zoom',icon='toggle-off',value = False).add_class('sidecar-only').add_class('mpl-zoom')
        self.box = VBox([Box([self.__instructions],layout=Layout(width='100%',height='auto',overflow='hidden')),
                        VBox([
                            self.height_slider.add_class('voila-sidecar-hidden'), 
                            self.width_slider.add_class('voila-sidecar-hidden'),
                            self.scale_slider,
                            self.theme_dd,
                            HBox([self.btn_fs,self.btn_mpl],layout=Layout(justify_content='space-around',padding='8px',height='max-content',min_height='30px')),
                            Box([self.master.btn_setting],layout=Layout(width='auto',margin='auto'))
                            ],layout=Layout(width='100%',height='max-content',min_height='200px'))
                        ],layout=Layout(width='70%',min_width='50%',height='100%',padding='4px',overflow='auto',display='none')
                        ).add_class('panel')
        with self.__instructions:
            write(dv.settings_instructions)
            
        self.theme_dd.observe(self.update_theme)
        self.scale_slider.observe(self.__set_font_scale)
        self.height_slider.observe(self.__update_size,names=['value'])
        self.width_slider.observe(self.__update_size,names=['value'])
        self.master.btn_setting.on_click(self.__toggle_panel)
        self.btn_fs.observe(self.update_theme)
        self.btn_mpl.observe(self.update_theme)
        self.update_theme() #Trigger
        
    def __update_size(self,change):
            self.master.box.layout.height = '{}px'.format(self.height_slider.value)
            self.master.box.layout.width = '{}vw'.format(self.width_slider.value)
            
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
        text_size = '{}px'.format(int(self.master.font_scale*16))
        if self.theme_dd.value == 'Inherit':
            theme_css = dv.style_html(self.master.theme_root)
        elif self.theme_dd.value == 'Light':
            theme_css = dv.style_html(dv.light_root)
        elif self.theme_dd.value == 'Dark':
            theme_css = dv.style_html(dv.dark_root)
        elif self.theme_dd.value == 'Custom': # In case of Custom CSS
            with set_dir(self.master.user_ns['_dh'][0]):
                if not os.path.isfile('custom.css'):
                    with open('custom.css','w') as f:
                        _str = dv.style_html(dv.light_root).replace('<style>','').replace('</style>','')
                        f.writelines(['/* Author: Abdul Saboor */'])
                        f.write(_str)
                # Read CSS from file
                with open('custom.css','r') as f:
                    theme_css = '<style>' + ''.join(f.readlines()) + '</style>'
        # Replace font-size
        theme_css = theme_css.replace('__text_size__',text_size)   
        # Catch Fullscreen too.
        if self.btn_fs.value:
            theme_css = theme_css.replace('</style>','\n') + dv.fullscreen_css.replace('<style>','')
            self.btn_fs.icon = 'compress'
            try:self.master.box.add_class('FullScreen')
            except:pass
        else:
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
            
        # Add Javscript only in full screen mode
        with self.__instructions:
            self.__instructions.clear_output()
            write(dv.settings_instructions)
            # Must unregister events in edit mode to avoid slides switch while editing, leave touch as it is
            nav_js = dv.navigation_js if self.btn_fs.value else dv.navigation_js + "\ndocument.onkeydown = null"
            display(Javascript(nav_js))
        # Now Set Theme
        self.master.theme_html.value = theme_css



