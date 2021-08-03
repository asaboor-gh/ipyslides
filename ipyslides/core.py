import numpy as np
from IPython.display import display, Markdown, HTML
import ipywidgets as ipw
from ipywidgets import Layout,Label,Button,Box,HBox,VBox


def _intslider_html(slider, fill_color = '#61afef', empty_color = 'whitesmoke'):
    """Creates an html for a slider to make it like progressbar. You need ipywidgets.Box([slider,html]) for customization to take effect.
    - **Parameters**
        - slider: IntSlider widget
        - fill_color: Color of the bar displaying the slider value.
        - empty_color: Background color of the bar.
    """
    uid = 'custom-'+''.join(np.random.randint(9, size=(20)).astype(str))
    slider.add_class(uid) #Add unique slider
    _html_str = '''
    <style>
    .widget-hslider.{uid} .ui-slider .ui-slider-handle {{ 
        border: none;
        background: {fcolor}; 
        height: 0px;}}
    .widget-hslider.{uid} .ui-slider .ui-slider-handle:focus {{ 
        background: {fcolor};
        height: 16px; }}
    .widget-hslider.{uid} .ui-slider {{
        border: none;
        background: linear-gradient(to right, {fcolor} 0%, {fcolor} {value}%, {ecolor} {value}%, {ecolor} 100%) !important;
        }}
    .widget-inline-hbox .widget-readout  {{min-width:auto !important;}}
    </style>'''
    init_value = int(slider.value/slider.max*100)
    html = ipw.HTML(_html_str.format(value=init_value,fcolor=fill_color,ecolor=empty_color,uid=uid)) 
    def update_color(change):
        if change:
            value = int(slider.value/slider.max*100)
            html.value = _html_str.format(value=value,fcolor=fill_color,ecolor=empty_color, uid=uid)  
    
    slider.observe(update_color, names=['value'])
    return html

class LiveSlides:
    def __init__(self,func=lambda x: display(Markdown(x)), iterable=['# First Slide','# Second Slide'],
                 title_page_md='# <center style="color:red"> Title',accent_color='#2196F3'):
        """Interactive Slides in IPython Notebook. Use `display(Markdown('text'))` instead of `print` in slides.
        - **Parameters**
            - func : An outside defined function which act on elements of `iterable`  and handle required situations. 
                    Return value is not guranteed for output rendering except for IPython.display.display object. Use display
                    inside the function for rich formats rending as many time as you want.
            - iterable: Anything from list/tuple/dict etc whose each element is given as argument to `func`.
            - title_page_md: Title page as Markdown plain text.
            - accent_color: Valid CSS color. Applies to buttons, progressbar etc.
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
        self.title_page_md = title_page_md
        self.out = ipw.Output(layout= Layout(width='auto',height='auto',margin='auto',overflow='auto'))
        
        _max = len(self.iterable) if self.iterable else 1
        self.N = _max
        self.progressbar =  ipw.IntSlider(min=0, max=_max,value=0,continuous_update=False, readout=True,
                                          layout =  Layout(width='100%'))
        self.btn_prev =  Button(description='◀',layout= Layout(width='auto',height='auto')).add_class('menu')
        self.btn_next =  Button(description='▶',layout= Layout(width='auto',height='auto')).add_class('menu')
        self.btn_setting =  Button(description='≡',layout= Layout(width='auto',height='auto')).add_class('menu')
        self.btn_setting.add_class('voila-sidecar-hidden') #This is for full scale display, no settings required
        for btn in [self.btn_next, self.btn_prev, self.btn_setting]:
            btn.style.button_color= 'transparent'
            btn.layout.min_width = 'max-content' #very important parameter
        
        self.slider_html = _intslider_html(self.progressbar,fill_color=accent_color,empty_color='whitesmoke')
        self.count_label = ipw.HTML(f'/ {self.N}', layout= Layout(min_width='30px',width='max-content'))
        self.nav_bar_children = (self.progressbar, self.slider_html, self.count_label,self.btn_prev, self.btn_next)
        self.nav_bar =  HBox(self.nav_bar_children ,layout= Layout(width='100%',min_height='40px',display='flex',justify_content='flex-end'))
        self.style_html = ipw.HTML('''<style>
                                        .menu {{ color:{accent_color} ; font-size:180%}}
                                        .textfonts {{ font-size:120%; align-items: center;}}
                                        .centerslide {{ align-items: center;}}
                                        a.jp-InternalAnchorLink {{ display: none !important;}}
                                        .widget-inline-hbox .widget-readout  {{ min-width:auto !important;}}
                                        .menu:hover {{ animation-name: example; animation-duration: 4s;}}
                                        @keyframes example {{
                                          from {{ font-size: 250%;}}
                                          to {{font-size: 180%;}}
                                        }}
                                        .jupyterlab-sidecar .SlidesWrapper {{width: 100% !important; height: 100% !important;}}
                                        .SlidesWrapper pre, code{{ background:inherit !important; color: inherit !important;
                                                        height: auto !important; overflow:hidden;}}
                                        .jupyterlab-sidecar .SlidesWrapper .voila-sidecar-hidden {{display: none;}}
                                        #rendered_cells .SlidesWrapper .voila-sidecar-hidden {{display: none;}}
                                        #rendered_cells .SlidesWrapper {{
                                            position: absolute;
                                            width:100% !important;
                                            height: 100% !important;
                                            bottom: 0px !important;
                                            top: 0px !important;
                                            tight: 0px !important;
                                            left: 0px !important;
                                        }}
                                        .SlidesWrapper {{z-index: 10 !important;}}
                                        <style>'''.format(accent_color=accent_color))
        self.height_slider = ipw.IntSlider(min=200,max=1000, value = 480,continuous_update=False,description='Height (px)')
        self.width_slider = ipw.IntSlider(min=40,max=100, value = 60,continuous_update=False,description='Width (vw)')
        
        self.btn_prev.on_click(self.__shift_left)
        self.btn_next.on_click(self.__shift_right)
        self.progressbar.observe(self.__update_content,names=['value'])
        self.__update_content(True)
        self.btn_setting.on_click(self.__settings)
        
        self.box =  VBox([self.style_html,
                                        Box([self.out.add_class('textfonts').add_class('centerslide')
                                                        ],layout= Layout(width='100%',height='100%',margin='auto')),
                                        self.nav_bar
                           ],layout= Layout(width=f'{self.width_slider.value}vw', height=f'{self.height_slider.value}px',margin='auto'))
        self.box.add_class('SlidesWrapper') #Very Important
     
    def show(self):
        try:   #JupyterLab Case, Interesting in SideCar
            from sidecar import Sidecar 
            sc = Sidecar(title='Live Presentation')
            with sc:
                display(self.box)
        except:
            return self.box
    
    def __shift_right(self,change):
        if self.iterable and change:
            self.progressbar.value = (self.progressbar.value + 1) % (self.N + 1)     
    
    def __shift_left(self,change):
        if self.iterable and change:
            self.progressbar.value = (self.progressbar.value - 1) % (self.N + 1)
            
    def __settings(self,change):
        if self.btn_setting.description == '≡':
            self.btn_setting.description = '×'
            
            def _observe(change):
                self.box.layout.height = '{}px'.format(self.height_slider.value)
                self.box.layout.width = '{}vw'.format(self.width_slider.value)
                
            self.height_slider.observe(_observe,names=['value'])
            self.width_slider.observe(_observe,names=['value'])
            self.out.clear_output(wait=True)
            with self.out:
                display(VBox([ipw.HTML('<h2>Settings</h2>'), self.height_slider, self.width_slider,self.btn_setting],
                             layout=Layout(border='1px solid gray')).add_class('centerslide'))
    
        else:
            self.btn_setting.description = '≡'
            self.__update_content(True)
            
    def __update_content(self,change):
        if self.iterable and change:
            self.count_label.value = self.count_label.value + '↺'
            self.out.clear_output(wait=True)
            with self.out:
                if self.progressbar.value == 0:
                    self.btn_setting.description = '≡'
                    self.nav_bar.children = (self.btn_setting,self.btn_next,)
                    display(Markdown(self.title_page_md))
                else:
                    self.nav_bar.children = self.nav_bar_children
                    self.func(self.iterable[self.progressbar.value-1])
            self.count_label.value = self.count_label.value.replace('↺','')            
    
def collect_slides():
    """Collect cells with variables `__slide_[N]` and `__next_to_[N]` in user's namespace."""
    ns = get_ipython().user_ns
    if not '__slides_mode' in ns.keys() or not ns['__slides_mode']:
        return print('Set "__slides_mode = True" in top cell and run again.')
    
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
