"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""
from dataclasses import dataclass
import ipywidgets as ipw
from ipywidgets import HTML, IntProgress, VBox, HBox, Box, Layout, Button

from .. import data_variables as dv

auto_layout =  Layout(width='auto')
btns_layout = Layout(justify_content='space-around',padding='8px',height='max-content',min_height='30px',overflow='auto')
def describe(value): 
    return {'description': value, 'description_width': 'initial','layout':Layout(width='auto')}

@dataclass(frozen=True)
class _Buttons:
    """
    Instantiate under `Widgets` class only.
    """
    prev =  Button(icon='chevron-left',layout= Layout(width='auto',height='auto')).add_class('arrows')
    next =  Button(icon='chevron-right',layout= Layout(width='auto',height='auto')).add_class('arrows')
    setting =  Button(description= '\u2630',layout= Layout(width='auto',height='auto')).add_class('menu').add_class('float-cross-btn')
    capture =  Button(icon='camera',layout= Layout(width='auto',height='auto'),
                    tooltip='Take Screen short in full screen. Order of multiple shots in a slide is preserved!',
            ).add_class('screenshot-btn') # .add_class('menu')
    pdf = Button(description='Save PDF',layout= Layout(width='auto',height='auto'))
    png = Button(description='Save PNG',layout= Layout(width='auto',height='auto'))
    print = Button(description='Print PDF',layout= Layout(width='auto',height='auto'))
    

@dataclass(frozen=True)
class _Toggles:
    """
    Instantiate under `Widgets` class only.
    """
    display =  ipw.ToggleButtons(description='Display Mode',options=[('Inline',0),('Sidebar',1)],value = 1).add_class('DisplaySwitch')
    fscrn = ipw.ToggleButton(description='Window',icon='expand',value = False).add_class('sidecar-only').add_class('window-fs')
    zoom = ipw.ToggleButton(description='Zoom Items',icon='toggle-off',value = False).add_class('sidecar-only').add_class('mpl-zoom')
    timer = ipw.ToggleButton(description='Timer',icon='play',value = False).add_class('sidecar-only').add_class('presenter-btn')             
        


@dataclass(frozen=True)
class _Htmls:
    """
    Instantiate under `Widgets` class only.
    """
    info    = HTML('<p>Put Your Info Here using `self.set_footer` function</p>')
    theme   = HTML(dv.style_html(dv.theme_roots['Fancy'].replace(
        '__text_size__','16px')).replace(
        '__breakpoint_width__','650px').replace(
        '__textfont__','sans-serif').replace(
        '__codefont__','var(--jp-code-font-family)'))
    main    = HTML(dv.main_layout_css)
    sidebar = HTML(dv.sidebar_layout_css()) # Should be separate CSS
    loading = HTML() #SVG Animation in it
    logo    =  HTML()
    toast   = HTML() # For notifications
    cursor  = HTML().add_class('LaserPointer') # For beautiful cursor
    notes   = ipw.HTML('Notes Area').add_class('Inline-Notes') # For below slides area

@dataclass(frozen=True)
class _Inputs:
    """
    Instantiate under `Widgets` class only.
    """
    bbox = ipw.Text(description='L,T,R,B (px)',layout=auto_layout,value='Type left,top,right,bottom pixel values and press ↲')

@dataclass(frozen=True)
class _Checks:
    """
    Instantiate under `Widgets` class only.
    """
    reflow = ipw.Checkbox(value=False,description='Reflow Code',layout=auto_layout)
    notes  = ipw.Checkbox(value=False,description='Display Notes',layout=auto_layout) # do not observe, just keep track when slides work
    toast  = ipw.Checkbox(value = False, description='Hide Notifications')
        
    

@dataclass(frozen=True)
class _Sliders:
    """
    Instantiate under `Widgets` class only.
    """
    progress   = ipw.IntSlider(options= [(f'{i}',i) for i in range(1)],continuous_update=False,readout=True)
    visible    = ipw.IntSlider(description='View (%)',min=0,value=100,max=100,orientation='vertical').add_class('float-control')
    height     = ipw.IntSlider(**describe('Height (px)'),min=200,max=2160, value = 400,continuous_update=False).add_class('height-slider') #2160 for 4K screens
    width      = ipw.IntSlider(**describe('Width (vw)'),min=20,max=100, value = 50,continuous_update=False).add_class('width-slider')
    scale      = ipw.FloatSlider(**describe('Font Scale'),min=0.5,max=3,step=0.0625, value = 1.0,readout_format='5.3f',continuous_update=False)
        

@dataclass(frozen=True)
class _Dropdowns:
    """
    Instantiate under `Widgets` class only.
    """
    theme = ipw.Dropdown(**describe('Theme'),options=[*dv.theme_roots.keys(),'Custom'],value='Inherit')
    clear = ipw.Dropdown(description='Delete',options = ['None','Delete Current Slide Screenshots','Delete All Screenshots'])
        
    
@dataclass(frozen=True)
class _Outputs:
    """
    Instantiate under `Widgets` class only.
    """
    slide  = ipw.Output(layout= Layout(width='auto',height='auto',margin='auto',overflow='auto',padding='2px 36px')
                              ).add_class('SlideArea')
    intro  = ipw.Output(clear_output=False, layout=Layout(width='100%',height='100%',overflow='auto',padding='4px')).add_class('panel-text')
    js_fix = ipw.Output(layout=Layout(width='auto',height='0px'))
    js_var = ipw.Output(layout=Layout(width='auto',height='0px'))


def _custom_progressbar(intslider):
    "Retruns a progress bar with custom style html linked to the slider"
    # This html should not be exposed to user
    html = HTML('''
    <style>
    .NavWrapper .nav-box .menu {
        font-size:24px !important; 
        overflow:hidden;
        opacity:0.4;
        z-index:55;
    }
    .NavWrapper .nav-box .menu:hover {
        opacity:1;
    }
    .NavWrapper .nav-box {
        z-index:50;
        overflow: hidden;
    }
    .NavWrapper .widget-hprogress {
        height:4px; !impportant;
    }
    .NavWrapper, .NavWrapper>div {
        padding:0px;
        margin:0px;
        overflow:hidden;
        max-width:100%;
    }
    .NavWrapper .progress, .NavWrapper .progress .progress-bar {
        border-radius:0px; 
        margin:0px;
        padding:0px;
        height:4px !important;
        overflow:hidden;
        left:0px;
        bottom:0px;
    }
    .NavWrapper .progress {
        width:100% !important;
        transform:translate(-2px,1px) !important;
    }
    </style>''')
    intprogress = IntProgress(min=intslider.min, max=intslider.max, layout=Layout(width='100%'))
    for prop in ('min','max','value'):
        ipw.link((intprogress, prop), (intslider, prop)) # These links enable auto refresh from outside
    
    return intprogress, html
    
    
class Widgets:
    """
    Instantiate under `LiveSLides` class only and provide to other classes after built-up.
    """
    def __init__(self,uid):
        "uid is the unique id of the slide provided from LiveSlides class"
        self.uid = uid # must be passed to other classes
        self.buttons = _Buttons()
        self.toggles = _Toggles()
        self.sliders = _Sliders()
        self.inputs  = _Inputs()
        self.checks  = _Checks()
        self.htmls   = _Htmls()
        self.ddowns  = _Dropdowns()
        self.outputs = _Outputs()
        
        # Make the progress bar and link to slides
        self.progressbar, self.__proghtml = _custom_progressbar(self.sliders.progress)
        
        # Layouts build on these widgets
        self.controls = HBox([
            self.buttons.prev,
            ipw.Box([
                self.sliders.progress.add_class(self.uid)
            ]).add_class('ProgBox').add_class(self.uid),
            self.buttons.next
        ]).add_class('controls').add_class(self.uid)
        
        self.navbox = VBox([
            HBox([self.buttons.setting,
                HBox([self.htmls.info],layout= Layout(overflow_x = 'auto',overflow_y='hidden')),
                self.buttons.capture
            ],layout=Layout(height='32px')
            ).add_class('nav-box'),
            VBox([
                self.__proghtml,
                self.progressbar
                ])
        ]).add_class('NavWrapper').add_class(self.uid) #class is must
        
        
        
        self.panelbox = VBox([
            Box([
                self.outputs.intro,
                self.buttons.setting,
            ],layout=Layout(width='100%',height='auto',overflow='hidden')),
            self.outputs.js_fix, 
            self.outputs.js_var, # Must be in middle so that others dont get disturbed.
            VBox([
                self.sliders.height.add_class('voila-sidecar-hidden'), 
                self.sliders.width.add_class('voila-sidecar-hidden'),
                self.sliders.scale,
                self.ddowns.theme,
                HTML('<hr/>'),
                self.inputs.bbox,
                ipw.HBox([
                    self.checks.notes, 
                    self.checks.toast, 
                    self.checks.reflow
                ],layout=btns_layout),
                self.ddowns.clear,
                HBox([
                    self.buttons.png, 
                    self.buttons.pdf, 
                    self.buttons.print
                ], layout=btns_layout),
                HTML('<hr/>'),
                HBox([
                    self.toggles.fscrn,
                    self.toggles.zoom, 
                    self.toggles.timer
                ], layout=btns_layout),
            ],layout = Layout(width='100%',height='max-content',min_height='400px',overflow='auto'))
        ],layout = Layout(width='70%',min_width='50%',height='100%',padding='4px',overflow='auto',display='none')
        ).add_class('panel').add_class(self.uid)
        
        self.slidebox = Box([
            self.outputs.slide.add_class(self.uid)
        ],layout= Layout(min_width='100%',overflow='auto')).add_class('SlideBox').add_class(self.uid)
        
        self.mainbox = VBox([
            self.htmls.loading, 
            self.htmls.toast,
            self.htmls.main,
            self.htmls.theme,
            self.htmls.logo, 
            self.htmls.sidebar,
            self.panelbox, 
            self.htmls.cursor.add_class(self.uid),
            HBox([ #Slide_box must be in a box to have animations work
                self.slidebox.add_class(self.uid), 
            ],layout= Layout(width='100%',max_width='100%',height='100%',overflow='hidden')), #should be hidden for animation purpose
            self.controls, # Importnat for unique display
            self.sliders.visible,
            self.navbox
            ],layout= Layout(width=f'{self.sliders.width.value}vw', height=f'{self.sliders.height.value}px',margin='auto')
        ).add_class('SlidesWrapper').add_class(self.uid) #Very Important to add this class

        for btn in [self.buttons.next, self.buttons.prev, self.buttons.setting,self.buttons.capture]:
            btn.style.button_color= 'transparent'
            btn.layout.min_width = 'max-content' #very important parameter
            btn.add_class(self.uid)
    
    def _push_toast(self,content,title='IPySlides Notification',timeout=5):
        "Send inside notifications for user to know whats happened on some button click. Set `title = None` if need only content. Remain invisible in screenshot."
        if content and isinstance(content,str):
            self.htmls.toast.value = '' # Set first to '', otherwise may not trigger for same value again.
            self.htmls.toast.value = dv.notification(content=content,title=title,timeout=timeout)