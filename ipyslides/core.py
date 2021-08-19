from ssl import ALERT_DESCRIPTION_NO_RENEGOTIATION
from IPython.core.display import HTML
import numpy as np
from IPython.display import display, Markdown
import ipywidgets as ipw
from ipywidgets import Layout,Button,Box,HBox,VBox
from . import data_variables as dv
import datetime, re, os #re for updating font-size and slide number
from .utils import write

def custom_progressbar(intslider):
    "This has a box as children[0] where you can put navigation buttons."
    html = ipw.HTML('''<style>
     .NavWrapper .nav-box .menu, .NavWrapper .nav-box .menu.big-menu  {font-size:24px !important; overflow:hidden;}
     .NavWrapper .nav-box .menu.big-menu {font-size:55px !important;}
     .NavWrapper .nav-box .menu:hover {
            overflow: hidden;
            animation-name: example; animation-duration: 2s;
            animation-timing-function: ease-in-out;
    }
    @keyframes example {
            from { opacity: 0.2;}
            to {opacity: 1;}
    }
    .NavWrapper .nav-box {z-index:50;overflow: hidden;}
    .NavWrapper .widget-hprogress {height:4px; !impportant;}
    .NavWrapper, .NavWrapper>div {padding:0px;margin:0px;overflow:hidden;max-width:100%;}
    .NavWrapper .progress, .NavWrapper .progress .progress-bar {
        border-radius:0px; margin:0px;padding:0px;height:4px !important;overflow:hidden;left:0px;bottom:0px;}
    .NavWrapper .progress {width:100% !important;transform:translate(-2px,1px) !important;}
    </style>''')
    intprogress = ipw.IntProgress(min=intslider.min, max=intslider.max, layout=Layout(width='100%'))
    ipw.link((intprogress, 'value'), (intslider, 'value'))
    return VBox([HBox(layout=Layout(height='0px',justify_content='space-between',align_items='center')).add_class('nav-box'),
                            VBox([ html,intprogress]) ]).add_class('NavWrapper') #class is must
class NavBar:
    def __init__(self,N=10):
        "N is number of slides here."
        self.N = N
        
        self.uid = ''.join(np.random.randint(9, size=(20)).astype(str)) #To use in _custom_progressbar
        self.prog_slider = ipw.IntSlider(max = self.N,continuous_update=False,readout=True)
        self.btn_prev =  Button(icon='angle-left',layout= Layout(width='auto',height='auto')).add_class('menu').add_class('big-menu')
        self.btn_next =  Button(icon='angle-right',layout= Layout(width='auto',height='auto')).add_class('menu').add_class('big-menu')
        self.btn_setting =  Button(icon='bars',layout= Layout(width='auto',height='auto')).add_class('menu')
        for btn in [self.btn_next, self.btn_prev, self.btn_setting]:
                btn.style.button_color= 'transparent'
                btn.layout.min_width = 'max-content' #very important parameter
                
        self.info_html = ipw.HTML('Put Your Info Here using `self.info_html.value`')
        self.group_1 =  HBox([self.btn_setting,ipw.Box([self.info_html],layout= Layout(overflow_x = 'auto',overflow_y='hidden'))],
                             layout=Layout(justify_content='flex-start',align_items='center'))
        self.group_2 = HBox([self.btn_prev,ipw.Box([self.prog_slider]).add_class('prog_slider_box'),self.btn_next],
                            layout=Layout(justify_content='flex-end',align_items='center',min_width='max-content'))
        self.build_navbar() # this is the main function to build the navbar
         
        self.btn_prev.on_click(self.__shift_left)
        self.btn_next.on_click(self.__shift_right)
    
    def build_navbar(self):
        self.nav_bar = custom_progressbar(self.prog_slider)
        self.nav_bar.children[0].children = (self.group_1, self.group_2)
        self.nav_bar.children[0].layout.height = '50px'
       
    def __shift_right(self,change):
        if change:
            self.prog_slider.value = (self.prog_slider.value + 1) % (self.N + 1)     
    
    def __shift_left(self,change):
        if change:
            self.prog_slider.value = (self.prog_slider.value - 1) % (self.N + 1)
    
    def show(self):
        return self.nav_bar
    __call__ = show
    
    def player(self,interval=1000):
        play = ipw.Play(min=self.prog_slider.min,max=self.prog_slider.max,interval=interval)
        ipw.dlink((play, 'value'), (self.prog_slider, 'value'))
        return play
        
         
class LiveSlides(NavBar):
    def __init__(self,
                 func=lambda x: display(Markdown(x)), 
                 iterable=['# First Slide','# Second Slide'],
                 animation_css = dv.animation_css):
        """Interactive Slides in IPython Notebook. Use `display(Markdown('text'))` instead of `print` in slides.
        - **Parameters**
            - func : An outside defined function which act on elements of `iterable`  and handle required situations. 
                    Return value is not guranteed for output rendering except for IPython.display.display object. Use display
                    inside the function for rich formats rending as many time as you want.
            - iterable: Anything from list/tuple/dict etc whose each element is given as argument to `func`.
            - animation_css: CSS for animation. Set to '' if not animating. You can define yourself by editing `ipysildes.data_variables.animation_css`.
        - **Example**
            ```python
            from IPython.display import display, Markdown
            def fn(x):
                if isinstance(x,int):
                    display(Markdown(f'{x**2}'))
                if isinstance(x, str):
                    display(Markdown(x*10))
            slides = LiveSlides(fn, [0,2,5,'Python '],height=200)
            slides.show()
            #See result as ![Slides](https://github.com/massgh/pivotpy/tree/master/slides.gif)
            ```
        """
        self.func = func
        self.iterable = iterable
        self.user_ns = get_ipython().user_ns 
        self.out = ipw.Output(layout= Layout(width='auto',height='auto',margin='auto',overflow='auto',padding='2px 16px'))
        
        _max = len(self.iterable) if self.iterable else 1
        super().__init__(N=_max)
        self.theme_root = dv.inherit_root
        self.font_scale = 1 #Scale 1 corresponds to 16px
        self.theme_html = ipw.HTML(dv.style_html(dv.inherit_root.replace('__text_size__','16px')))
        self.main_style_html = ipw.HTML('''<style>
            .SlidesWrapper .textfonts { align-items: center;}
            a.jp-InternalAnchorLink { display: none !important;}
            .widget-inline-hbox .widget-readout  { min-width:auto !important;}
            .jupyterlab-sidecar .SlidesWrapper {width: 100% !important; height: 100% !important;}
            .SlidesWrapper pre, code { background:inherit !important; color: inherit !important;
                            height: auto !important; overflow:hidden;}
            .jupyterlab-sidecar .SlidesWrapper .voila-sidecar-hidden {display: none;}
            .sidecar-only {display: none;} /* No display when ouside sidecar,do not put below next line */
            .jupyterlab-sidecar .sidecar-only {display: block;}
            #rendered_cells .SlidesWrapper .voila-sidecar-hidden {display: none;}
            #rendered_cells .SlidesWrapper {
                position: absolute;
                width:100% !important;
                height: 100% !important;
                bottom: 0px !important;
                top: 0px !important;
                tight: 0px !important;
                left: 0px !important;
            }
            .SlidesWrapper {z-index: 10 !important;}
            <style>''')
        
        self.prog_slider.observe(self.__update_content,names=['value'])
        self.__update_content(True)
        
        self.setting = Customize(self)
        self.box_setting = self.setting.box
        
        self.box =  VBox([self.main_style_html, ipw.HTML(animation_css),
                          self.theme_html,
                          HBox([self.box_setting,ipw.Box([self.out.add_class('textfonts')],layout= Layout(width='auto',overflow='auto')),
                          ],layout= Layout(width='auto',max_width='100%',height='100%',margin='auto')),
                          self.nav_bar
                          ],layout= Layout(width=f'{self.setting.width_slider.value}vw', height=f'{self.setting.height_slider.value}px',margin='auto'))
        self.box.add_class('SlidesWrapper') #Very Important   
    
     
    def show(self):
        try:   #JupyterLab Case, Interesting in SideCar
            from sidecar import Sidecar 
            sc = Sidecar(title='Live Presentation')
            with sc:
                display(self.box)
        except:
            return self.box
    __call__ = show
    
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
           
    def __update_content(self,change):
        if self.iterable and change:
            self.info_html.value = re.sub('>\d+\s+/',f'>{self.prog_slider.value} /',self.info_html.value) #Slide Number
            self.info_html.value = self.info_html.value.replace('</p>', '| Loading...</p>')
            self.out.clear_output(wait=True)
            with self.out:
                if self.prog_slider.value == 0:
                    title = self.user_ns.get('__slides_title_page','#### No Title page found. Create one using `write_title` in a cell.')
                    if isinstance(title,str):
                        write(title) #Markdown String
                    else:
                        write(*title['args'],**title['kwargs']) #Ipython Captured Output
                else:
                    item = self.iterable[self.prog_slider.value-1]
                    try: item.show() #show ipython capture/MultiCols or if item has a show method with display.
                    except: self.func(item)
                    
            self.info_html.value = self.info_html.value.replace('| Loading...','')
            
    def set_footer(self, text = 'Abdul Saboor | <a style="color:blue;" href="www.google.com">google@google.com</a>', show_slide_number=True, show_date=True):
        if show_date:
            text += f' | <text style="color:var(--accent-color);">' + datetime.datetime.now().strftime('%b-%d-%Y')+ '</text>'
        if show_slide_number: #Slide number should be  exactlly like '>Int /' for regex substitutioon.  
            text += f' | <b style="color:var(--accent-color);">{self.prog_slider.value} / {self.N}<b>'
        self.info_html.value = f'<p style="white-space:nowrap;"> {text} </p>'

class Customize:
    def __init__(self,instance_LiveSlides):
        "Provide instance of LivSlides to work."
        self.master = instance_LiveSlides
        describe = lambda value: {'description': value, 'description_width': 'initial','layout':Layout(width='auto')}
        
        self.height_slider = ipw.IntSlider(**describe('Height (px)'),min=200,max=1000, value = 500,continuous_update=False)
        self.width_slider = ipw.IntSlider(**describe('Width (vw)'),min=40,max=100, value = 65,continuous_update=False)
        self.scale_slider = ipw.FloatSlider(**describe('Font Scale'),min=0.5,max=3,step=0.0625, value = 1.0,readout_format='5.3f',continuous_update=False)
        self.theme_dd = ipw.Dropdown(**describe('Theme'),options=['Inherit','Light','Dark','Custom'])
        self.__instructions = ipw.Output(clear_output=False, layout=Layout(width='100%',height='100%',overflow='auto')).add_class('panel-text')
        self.btn_fs = ipw.ToggleButton(icon='expand',value = False,layout=Layout(width='auto',height='auto',margin='auto',overflow='hidden')).add_class('sidecar-only')
        self.btn_fs.style.button_color = 'transparent'
        # layout = Layout(width='100%',height='70px',margin='auto',overflow_y='hidden',align_items='center',justify_content='space-between')
        self.box = VBox([ipw.HBox([ipw.HTML('<h2>Settings</h2>'),self.btn_fs],layout=Layout(justify_content='space-between',align_items='center',min_width='max-content',min_height='50px',overflow='hidden')),
                        self.height_slider.add_class('voila-sidecar-hidden'), 
                        self.width_slider.add_class('voila-sidecar-hidden'),
                        self.scale_slider,
                        self.theme_dd,
                        ipw.Box([self.__instructions],layout=Layout(width='100%',height='auto',overflow='hidden')),
                        ipw.HBox([self.btn_fs,self.master.player(),self.master.prog_slider],layout=Layout(width='95%',min_height='50px',justify_content='flex-start',align_items='center',margin='auto'))
                        ],layout=Layout(width='0px',height='100%',padding='0px',overflow='auto')
                        ).add_class('panel')
        with self.__instructions:
            write(dv.settings_instructions)
            
        self.theme_dd.observe(self.update_theme)
        self.scale_slider.observe(self.__set_font_scale)
        self.height_slider.observe(self.__update_size,names=['value'])
        self.width_slider.observe(self.__update_size,names=['value'])
        self.master.btn_setting.on_click(self.__toggle_panel)
        self.btn_fs.observe(self.update_theme)
        self.update_theme() #Trigger
        
    def __update_size(self,change):
            self.master.box.layout.height = '{}px'.format(self.height_slider.value)
            self.master.box.layout.width = '{}vw'.format(self.width_slider.value)
            
    def __toggle_panel(self,change):
        if self.master.btn_setting.icon == 'bars':
            self.master.btn_setting.icon = 'close'
            self.box.layout.width = '70%' #Use both width & min_width to make sure it works.
            self.box.layout.min_width = '50%'
            self.box.layout.padding = '10px'
        else:
            self.master.btn_setting.icon = 'bars'
            self.box.layout.width = '0px'
            self.box.layout.min_width = '0px'
            self.box.layout.padding = '0px' 
                     
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
            fs_css = self.__jupyter_sidecar_fullscreen_css().replace('<style>','')
            self.master.theme_html.value = theme_css.replace('</style>','\n') + fs_css
            self.btn_fs.icon = 'compress'
        else:
            self.master.theme_html.value = theme_css #Push CSS without Fullscreen
            self.btn_fs.icon = 'expand' 
        
    def __jupyter_sidecar_fullscreen_css(self):
        return '''<style>
        .jupyterlab-sidecar > .jp-OutputArea-child, .SlidesWrapper {
            flex: 1;
            position: fixed;
            bottom: 0px;
            left: 0px;
            width: 100vw;
            height: 100vh;
            z-index: 100;
            margin: 0px;
            padding: 0;
        }    
        .jp-SideBar.lm-TabBar, .f17wptjy, #jp-bottom-panel { display:none !important;}
        #jp-top-panel, #jp-menu-panel {display:none !important;} /* in case of simple mode */
        </style>'''

class MultiCols:
    def __init__(self,width_percents=[50,50]):
        """Creat multicolumns with width spcified for each. Defuslt is two columns with equal width.
        This object is not displayed properly under %%slide, so you need to set it in `__dynamicslides_dict`.
        - **Example**
            > mc = Multicols()
            > with mc.header:
            >   write('## H2')
            > with mc.footer:
            >   write('## Footer')
            > with mc.c1: #and with c2,c3 etc
            >   print('Something')
            > mc.show() or mc.slide #displays it"""
        self.slide = VBox([],layout=Layout(width='auto',overflow_x='auto'))
        self.header = ipw.Output(layout=Layout(margin='auto',padding='2px 8px'))
        self.footer = ipw.Output(layout=self.header.layout)
        for i,wp in enumerate(width_percents):
            setattr(self,f'c{i+1}',ipw.Output(layout=Layout(margin='2px 8px',width='100%')))
        self.columns = HBox([Box([getattr(self,f'c{i+1}')],layout=Layout(width=f'{wp}%',overflow='auto'))
                                                for i,wp in enumerate(width_percents)],
                        layout=Layout(margin='0px',justify_content = 'center',column_border='2px solid red')
                        ).add_class('columns') # No need to set width. Its alright
        
        self.slide.children = [self.header,self.columns,self.footer]
        
    def show(self):
        return display(self.slide)   
    __call__ = show  
    
def collect_slides():
    """Collect cells with variables `__slide_[N]` and `__next_to_[N]` in user's namespace."""
    ns = get_ipython().user_ns
    if not '__slides_mode' in ns.keys() or not ns['__slides_mode']:
        return print('Set "convert2slides(True)" in top cell and run again.')
    
    dynamic_slides = [k.replace('d','') for k in ns['__dynamicslides_dict'].keys()]
    # If slide number is mistaken, still include that. 
    all_slides = [int(k) for k in [*ns['__slides_dict'].keys(), *dynamic_slides]]
    
    try: #handle dynamic slides if empty
        _min, _max = min(all_slides), max(all_slides) + 1
    except:
        _min, _max = 0, 0
    slides_iterable = []
    for i in range(_min,_max):
        if f'{i}' in ns['__slides_dict'].keys():
            slides_iterable.append(ns['__slides_dict'][f'{i}']) 
        if f'd{i}' in ns['__dynamicslides_dict'].keys():
            slides_iterable = [*slides_iterable,*ns['__dynamicslides_dict'][f'd{i}']]
            
    return tuple(slides_iterable)

def get_cell_code(this_line=True,magics=False,comments=False,lines=None):
    "Return current cell's code in slides for educational purpose. `lines` should be list/tuple of line numbers to include if filtered."
    current_cell_code = get_ipython().get_parent()['content']['code'].splitlines()
    if isinstance(lines,(list,tuple,range)):
        current_cell_code = [line for i, line in enumerate(current_cell_code) if i+1 in lines]
    if not this_line:
        current_cell_code = [line for line in current_cell_code if '_cell_code' not in line]
    if not magics:
        current_cell_code = [line for line in current_cell_code if not line.lstrip().startswith('%')]
    if not comments:
        current_cell_code = [line for line in current_cell_code if not line.lstrip().startswith('#')]
    return "```python\n{}\n```".format('\n'.join(current_cell_code))

def display_cell_code(this_line=False,magics=False,comments=False,lines=None):
    "Display cell data. `lines` should be list/tuple of line numbers to include if filtered."
    code = get_cell_code(this_line=this_line,magics=magics,comments=comments,lines=lines)
    return write(code)

