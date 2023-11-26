"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""
import os
from dataclasses import dataclass
import ipywidgets as ipw
from IPython.display import display, Javascript
from ipywidgets import HTML, FloatProgress, VBox, HBox, Box, GridBox, Layout, Button
from . import styles, _layout_css
from ._widgets import InteractionWidget, HtmlWidget, NotesWidget
from ..utils import html


auto_layout =  Layout(width='auto')
def describe(value): 
    return {'description': value, 'description_width': 'initial','layout':Layout(width='auto')}
@dataclass(frozen=True)
class _Buttons:
    """
    Instantiate under `Widgets` class only.
    """
    prev    =  Button(icon='chevron-left',layout= Layout(width='auto',height='auto'),tooltip='Previous Slide [<, Shift + Space]').add_class('Arrows').add_class('Prev-Btn')
    next    =  Button(icon='chevron-right',layout= Layout(width='auto',height='auto'),tooltip='Next Slide [>, Space]').add_class('Arrows').add_class('Next-Btn')
    setting =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Toggle Settings [G]').add_class('Menu-Item').add_class('Settings-Btn')
    toc     =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Toggle Table of Contents').add_class('Menu-Item').add_class('Toc-Btn')
    refresh =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'),tooltip='Refresh dynmaic content across all slides').add_class('Menu-Item').add_class('Refresh-Btn')
    home    =  Button(description= 'Home',layout= Layout(width='auto',height='auto', tooltip='Go to Title Page')).add_class('Menu-Item')
    end     =  Button(description= 'End',layout= Layout(width='auto',height='auto', tooltip='Go To End of Slides')).add_class('Menu-Item')
    capture =  Button(icon='camera',layout= Layout(width='auto',height='auto'),
                tooltip='Take Screen short in full screen. Order of multiple shots in a slide is preserved! [S]',
                ).add_class('Screenshot-Btn').add_class('Menu-Item')
    pdf     = Button(description='Save PDF',layout= Layout(width='auto',height='auto'))
    png     = Button(description='Save PNG',layout= Layout(width='auto',height='auto'))
    cap_all = Button(description='Capture All',layout= Layout(width='auto',height='auto'))
    _inview = Button(description='Click to Optimize Experience in JupyterLab',layout= Layout(width='auto',height='auto')).add_class('InView-Btn') # For testing if inside LinkedView
    
@dataclass(frozen=True)
class _Toggles:
    """
    Instantiate under `Widgets` class only.
    """
    window  = ipw.ToggleButton(icon='plus',value = False, tooltip='Fit/Restore Viewport [W]').add_class('FullWindow-Btn').add_class('Menu-Item')
    fscreen = ipw.ToggleButton(icon='plus',value = False, tooltip='Toggle Fullscreen [F]').add_class('FullScreen-Btn').add_class('Menu-Item')
    zoom    = ipw.ToggleButton(icon='plus',value = False, tooltip='Toggle Zooming Items [Z]').add_class('Zoom-Btn')
    laser   = ipw.ToggleButton(icon='plus',value = False, tooltip='Toggle Laser Pointer [L]').add_class('Laser-Btn') 
    overlay = ipw.ToggleButton(icon='plus',value = False, tooltip='Toggle Overlay Panel').add_class('Overlay-Btn')          
        

@dataclass(frozen=True)
class _Htmls:
    """
    Instantiate under `Widgets` class only.
    """
    footer  = HTML('<p>Put Your Info Here using `slides.settings.set_footer` function</p>',layout=Layout(margin='0')).add_class('Footer') # Zero margin is important
    theme   = HTML(html('style',styles.style_css(styles.theme_colors['Inherit'])).value)
    main    = HTML(html('style',_layout_css.layout_css('650px', styles.theme_colors['Inherit']['accent_color'])).value) # Will be update in theme as well
    window  = HTML(html('style','').value) # Should be separate CSS, need class to handle disconnect options
    loading = HTML(layout=Layout(display='none')).add_class('Loading') #SVG Animation in it
    logo    = HTML()
    tochead = HTML('<h4>Table of Contents</h4><hr/>')
    toast   = HTML().add_class('Toast') # For notifications
    cursor  = HtmlWidget('').add_class('LaserPointer') # For beautiful cursor
    hilite  = HTML() # Updated in settings on creation. For code blocks.
    zoom    = HTML() # zoom CSS, do not add here!
    capture = HTML('<span class="info">Edit above box and hit Enter to see screenshot here. ' 
                   'If nothing shown, your system does not support taking screenshots with PIL</span>').add_class('CaptureHtml') # Screenshot image here
    intro   = HTML().add_class('SidePanel-Text') # Intro HTML
    glass   = HTML().add_class('BackLayer') # For glass effect
    overlay = HTML().add_class('OverlayHtml') # For adding iframe of things
    
@dataclass(frozen=True)
class _Inputs:
    """
    Instantiate under `Widgets` class only.
    """
    bbox = ipw.Text(description='L,T,R,B (px)',layout=auto_layout,value='Type left,top,right,bottom pixel values and press ↲').add_class('Bbox-Input')

@dataclass(frozen=True)
class _Checks:
    """
    Instantiate under `Widgets` class only.
    """
    reflow  = ipw.Checkbox(indent = False, value=False,description='Reflow Content',layout=auto_layout)
    notes   = ipw.Checkbox(indent = False, value=False,description='Notes',layout=auto_layout) # do not observe, just keep track when slides work
    toast   = ipw.Checkbox(indent = False, value = True, description='Notifications',layout=auto_layout)
    postrun = ipw.Checkbox(indent = False, value = True, description='Display Per Cell',layout=auto_layout)
    proxy   = ipw.Checkbox(indent = False, value = True, description='Proxy Buttons',layout=auto_layout)
    navgui  = ipw.Checkbox(indent = False, value = False, description='Hide Nav. GUI',layout=auto_layout)

@dataclass(frozen=True)
class _Sliders:
    """
    Instantiate under `Widgets` class only.
    """
    progress = ipw.SelectionSlider(options=[('0',0)], value=0, continuous_update=False,readout=True)
    visible  = ipw.IntSlider(description='View (%)',min=0,value=100,max=100,orientation='vertical').add_class('FloatControl')
    width    = ipw.IntSlider(**describe('Width (vw)'),min=20,max=100, value = 70,continuous_update=False).add_class('Width-Slider') 
    scale    = ipw.FloatSlider(**describe('Font Scale'),min=0.5,max=3,step=0.0625, value = 1.0,readout_format='5.3f',continuous_update=False)
        
@dataclass(frozen=True)
class _Dropdowns:
    """
    Instantiate under `Widgets` class only.
    """
    aspect = ipw.Dropdown(**describe('Aspect Ratio'),options=[('2:1',0.50),('16:9',0.56),('16:10',0.63),('3:2',0.67), ('7:5',0.71),('4:3',0.75),('5:4',0.80)], value = 0.56,continuous_update=False).add_class('Height-Dd') #16:9 is better for in cell display
    theme  = ipw.Dropdown(**describe('Theme'),options=[*styles.theme_colors.keys(),'Custom'],value='Inherit')
    clear  = ipw.Dropdown(**describe('Delete'),options = ['None','Delete Current Slide Screenshots','Delete All Screenshots'])
    export = ipw.Dropdown(**describe('Export As'),options=['Slides','Report','Select'], value = 'Select')
    

def _custom_progressbar(intslider):
    "Retruns a progress bar linked to the slider"
    intprogress = FloatProgress(min=0, max=100,value=0, layout=Layout(width='100%'))
    ipw.link((intslider, 'value'), (intprogress, 'value')) # This link enable auto refresh from outside
    return intprogress

def _notification(content,title='IPySlides Notification',timeout=5):
    _title = f'<b>🔔 {title}</b><br/>' if title else '' # better for inslides notification
    return f'''<style>
        .NotePop {{
            display:flex;
            flex-direction:row;
            border-radius: 4px;
            padding:8px;
            width:auto;
            max-width:400px;
            height:max-content;
            backdrop-filter: blur(20px);
            box-shadow: 0 0 5px 0 rgba(255,255,255,0.2), 0 0 10px 0 rgba(0,0,0,0.2);
            animation: popup 0s ease-in {timeout}s;
            animation-fill-mode: forwards;
        }}
        .NotePop > div > b {{color: var(--accent-color); font-size:18px !important;}}
        .NotePop.NotePop.NotePop.NotePop > div > p {{ border-left: 2px solid var(--accent-color);padding-left:4px;font-size:16px !important;}}
        @keyframes popup {{
            to {{
                visibility:hidden;
                width:0;
                height:0;
            }}
        }}
        </style>
        <div style="position:absolute;left:50%;top:4px;z-index:1000;transform:translateX(-50%);" class="NotePop">
        <div>{_title}<p>{content}</p></div></div>'''

class Widgets:
    """
    Instantiate under `Sides` class only and provide to other classes after built-up.
    """
    def __setattr__(self, name , value):
        if name in self.__dict__:
            if name == '_notebook_dir':
                self.__dict__[name] = value
            else:
                raise AttributeError(f'{name} is a read-only attribute')
        
        self.__dict__[name] = value
        
    @property
    def assets_dir(self):
        "Returns the assets directory, if not exist, create one"
        _dir = os.path.join(self._notebook_dir,'.ipyslides_assets')
        if not os.path.isdir(_dir):
            os.makedirs(_dir)
        return _dir
        
    def __init__(self):
        # print(f'Inside: {self.__class__.__name__}')
        self._notebook_dir = '.' # This will be updated later
        self.buttons = _Buttons()
        self.toggles = _Toggles()
        self.sliders = _Sliders()
        self.inputs  = _Inputs()
        self.checks  = _Checks()
        self.htmls   = _Htmls()
        self.ddowns  = _Dropdowns()
        self.iw      = InteractionWidget(self)
        self.notes   = NotesWidget(value = 'Notes Preview')
        self.tmp_output = ipw.Output(layout= Layout(height='0',width = '0',margin='0',opacity='0')) # for hodling slide CSS
        
        # Make the progress bar and link to slides
        self.progressbar = _custom_progressbar(self.sliders.progress)
        
        # Layouts build on these widgets
        self.controls = HBox([
            self.buttons.prev,
            ipw.Box([
                self.sliders.progress 
            ]).add_class('ProgBox') ,
            self.buttons.next
        ]).add_class('Controls') 
        
        self.footerbox = HBox([
            self.buttons.toc,
            HBox([self.htmls.footer]), # should be in Box to avoid overflow
            self.buttons.capture,
        ],layout=Layout(height='28px')).add_class('NavBox')
        
        self.navbox = VBox([
            self.buttons._inview,
            self.footerbox,
            VBox([
                self.progressbar
                ])
        ]).add_class('NavWrapper')   #class is must
        
        _many_btns = [self.buttons.setting, self.toggles.overlay, self.toggles.window, self.toggles.fscreen, self.toggles.laser, self.toggles.zoom, self.buttons.refresh]
        self.panelbox = VBox([
            self.htmls.glass,
            HBox(_many_btns).add_class('TopBar').add_class('Inside'),
            VBox([
                self.sliders.scale,
                self.ddowns.theme,
                HTML('<hr/>'),
                self.sliders.width,
                self.ddowns.aspect, 
                self.ddowns.export,
                Box([GridBox([
                    self.checks.notes,
                    self.checks.toast,
                    self.checks.reflow,
                    self.checks.proxy,
                    self.checks.navgui,
                    self.checks.postrun,
                    self.buttons.cap_all,
                    self.buttons.pdf,
                    self.buttons.png
                ],layout=Layout(width='auto',overflow_x='scroll',
                                grid_template_columns='1fr 1fr 1fr',grid_gap='4px',
                                padding='4px',margin='auto')
                )],layout=Layout(min_height='120px')),# This ensures no collapse and scrollable Grid
                self.ddowns.clear,
                self.inputs.bbox,
                self.htmls.capture,
                self.tmp_output,
                self.notes, # Just to be there for acting on a popup window
                self.htmls.intro  
            ],layout=Layout(width='auto',height='auto',overflow_y='scroll',padding='8px',margin='0')),
        ],layout = Layout(width='70%',min_width='50%',height='100%',overflow='hidden',display='none')).add_class('SidePanel') 
        
        self.tocbox = VBox([],layout = Layout(width='30%',min_width='400px',height='100%',overflow='auto',display='none')).add_class('TOC')
        
        self.slidebox = Box([
            # Slides are added here dynamically
        ],layout= Layout(min_width='100%',overflow='auto')).add_class('SlideBox') 
        
        self.mainbox = VBox([
            self.htmls.glass, # This is the glass pane, should be before everything, otherwise it will cover the slide area
            self.htmls.loading, 
            self.htmls.toast,
            self.htmls.main,
            self.htmls.theme,
            self.htmls.logo,
            self.iw,
            HBox(_many_btns).add_class('TopBar').add_class('Outside'),
            self.htmls.window,
            self.panelbox,
            self.htmls.cursor,
            self.htmls.hilite,
            self.htmls.zoom,
            HBox([ #Slide_box must be in a box to have animations work
                self.tocbox, # Should be on left of slides
                self.slidebox , 
            ],layout= Layout(width='100%',max_width='100%',height='100%',overflow='hidden')), #should be hidden for animation purpose
            self.controls, # Importnat for unique display
            self.sliders.visible,
            self.htmls.overlay, 
            self.navbox, # Navbox should come last
            ],layout= Layout(width=f'{self.sliders.width.value}vw', height=f'{int(self.sliders.width.value*self.ddowns.aspect.value)}vw',margin='auto')
        ).add_class('SlidesWrapper')  #Very Important to add this class

        for btn in [self.buttons.next, self.buttons.prev, self.buttons.setting,self.buttons.capture]:
            btn.style.button_color= 'transparent'
            btn.layout.min_width = 'max-content' #very important parameter
            btn 
    
    def _push_toast(self,content,title='IPySlides Notification',timeout=5):
        "Send inside notifications for user to know whats happened on some button click. Set `title = None` if need only content. Remain invisible in screenshot."
        if content and isinstance(content,str):
            self.htmls.toast.value = '' # Set first to '', otherwise may not trigger for same value again.
            self.htmls.toast.value = _notification(content=content,title=title,timeout=timeout)
        