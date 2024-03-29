"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""
import sys
from dataclasses import dataclass
import ipywidgets as ipw
from ipywidgets import HTML, VBox, HBox, Box, GridBox, Layout, Button
from IPython import get_ipython
from tldraw import TldrawWidget
from . import styles, _layout_css
from ._widgets import InteractionWidget, HtmlWidget, NotesWidget
from .intro import get_logo
from ..utils import html


class Output(ipw.Output):
    __doc__ = ipw.Output.__doc__ # same docs

    _ipyshell = get_ipython()
    _hooks = (sys.displayhook, _ipyshell.display_pub if _ipyshell else None) # store once in start

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

    def __enter__(self):
        if self._ipyshell:
            self._chooks = (sys.displayhook, self._ipyshell.display_pub) # current hooks in top capture
            sys.displayhook, self._ipyshell.display_pub = self._hooks
        
        super().__enter__()

    def __exit__(self, etype, evalue, tb):
        if self._ipyshell:
            sys.displayhook, self._ipyshell.display_pub = self._chooks

        super().__exit__(etype, evalue, tb)

# patching for correct order of outputs, loaded with ipywidgets import when ipyslides is present
ipw.interaction.Output = Output
ipw.Output = Output
ipw.widget_output.Output = Output

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
    setting =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Open Settings [G]').add_class('Menu-Item').add_class('Settings-Btn')
    toc     =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Toggle Table of Contents').add_class('Menu-Item').add_class('Toc-Btn')
    refresh =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'),tooltip='Refresh Dynamic Content').add_class('Menu-Item').add_class('Refresh-Btn')
    home    =  Button(description= '⇤',layout= Layout(width='auto',height='auto'), tooltip='Go to Title Page').add_class('Menu-Item')
    end     =  Button(description= '⇥',layout= Layout(width='auto',height='auto'), tooltip='Go To End of Slides').add_class('Menu-Item')
    info    =  Button(description= 'ℹ️',layout= Layout(width='auto',height='auto'), tooltip='Information').add_class('Menu-Item')
    capture =  Button(icon='camera',layout= Layout(width='auto',height='auto'),
                tooltip='Take Screen short in full screen. Order of multiple shots in a slide is preserved! [S]',
                ).add_class('Screenshot-Btn').add_class('Menu-Item')
    pdf     = Button(description='Save PDF',layout= Layout(width='auto',height='auto'))
    png     = Button(description='Save PNG',layout= Layout(width='auto',height='auto'))
    cap_all = Button(description='Capture All',layout= Layout(width='auto',height='auto'))
    export  = Button(description="Export to HTML",layout= Layout(width='auto',height='auto'))
    _inview = Button(description='Click to Optimize Experience in JupyterLab',layout= Layout(width='auto',height='auto')).add_class('InView-Btn') # For testing if inside LinkedView
    
@dataclass(frozen=True)
class _Toggles:
    """
    Instantiate under `Widgets` class only.
    """
    window  = ipw.ToggleButton(icon='plus',value = False, tooltip ='Fill Viewport [V]').add_class('FullWindow-Btn').add_class('Menu-Item')
    fscreen = ipw.ToggleButton(icon='plus',value = False, tooltip ='Enter Fullscreen [F]').add_class('FullScreen-Btn').add_class('Menu-Item')
    zoom    = ipw.ToggleButton(icon='plus',value = False, tooltip ='Enable Zooming Items [Z]').add_class('Zoom-Btn')
    laser   = ipw.ToggleButton(icon='plus',value = False, tooltip ='Show Laser Pointer [L]').add_class('Laser-Btn') 
    draw    = ipw.ToggleButton(icon='plus',value = False, tooltip ='Open Drawing Panel').add_class('Draw-Btn') 
    menu    = ipw.ToggleButton(icon='plus',value = False, tooltip ='Toggle Quick Menu').add_class('Menu-Btn').add_class('Menu-Item')        

@dataclass(frozen=True)
class _Htmls:
    """
    Instantiate under `Widgets` class only.
    """
    footer  = HTML('<p>Put Your Info Here using `slides.settings.set_footer` function</p>',layout=Layout(margin='0')).add_class('Footer') # Zero margin is important
    theme   = HTML(html('style',styles.style_css(styles.theme_colors['Inherit'])).value)
    main    = HTML(html('style',_layout_css.layout_css(styles.theme_colors['Inherit']['accent_color'])).value) # Will be update in theme as well
    window  = HTML(html('style','').value) # Should be separate CSS, need class to handle disconnect options
    loading = HTML(layout=Layout(display='none')).add_class('Loading') #SVG Animation in it
    logo    = HtmlWidget('').add_class('LogoHtml')
    toast   = HtmlWidget('').add_class('Toast') # For notifications
    cursor  = HtmlWidget('').add_class('LaserPointer') # For beautiful cursor
    hilite  = HTML() # Updated in settings on creation. For code blocks.
    zoom    = HTML() # zoom CSS, do not add here!
    glass   = HTML().add_class('BackLayer') # For glass effect
    
@dataclass(frozen=True)
class _Inputs:
    """
    Instantiate under `Widgets` class only.
    """
    bbox = ipw.Text(description='L,T,R,B (px)',layout=auto_layout,value='Type left,top, right,bottom pixel values and press ↲').add_class('Bbox-Input')
    
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
    width    = ipw.IntSlider(**describe('Width (vw)'),min=20,max=100, value = 70,continuous_update=False).add_class('Width-Slider') 
    fontsize = ipw.IntSlider(**describe('Font Size'),min=8,max=64,step=1, value = 20,continuous_update=False, tooltip="If you need more larger/smaller font size, use `Slides.settings.set_font_size`")

@dataclass(frozen=True)
class _Dropdowns:
    """
    Instantiate under `Widgets` class only.
    """
    theme  = ipw.Dropdown(**describe('Theme'),options=[*styles.theme_colors.keys(),'Custom'],value='Inherit')
    clear  = ipw.Dropdown(**describe('Delete'),options = ['None','Delete Current Slide Screenshots','Delete All Screenshots'])    

class Widgets:
    """
    Instantiate under `Sides` class only and provide to other classes after built-up.
    """
    def __setattr__(self, name , value):
        if name in self.__dict__:
            raise AttributeError(f'{name} is a read-only attribute')
        
        self.__dict__[name] = value
    
    def update_progressbar(self):
        self._progbar.children[0].layout.width = f"{self.sliders.progress.value}%"
        self._snum.description = self.sliders.progress.label
        
    def __init__(self):
        # print(f'Inside: {self.__class__.__name__}')
        self._tmp_out = Output(layout=dict(margin='0',width='0',height='0')) # For adding slide's CSS and animations
        self._progbar = ipw.Box([ipw.Box().add_class("Progress")],layout=dict(width="100%",height="3px", visibility = "visible")).add_class("Progress-Box") # border not working everywhere
        self._snum   = Button(description='',layout= Layout(width='auto',height='auto')).add_class("Slide-Number").add_class('Menu-Item')
        self.buttons = _Buttons()
        self.toggles = _Toggles()
        self.sliders = _Sliders()
        self.inputs  = _Inputs()
        self.checks  = _Checks()
        self.htmls   = _Htmls()
        self.ddowns  = _Dropdowns()
        self.iw      = InteractionWidget(self)
        self.notes   = NotesWidget(value = 'Notes Preview')
        self.drawer  = ipw.Box([TldrawWidget().add_class('Draw-Widget'), self.toggles.draw]).add_class('Draw-Wrapper')
        self.drawer.layout = dict(width='100%',height='0',overflow='hidden') # height will be chnaged by button
        
        # Layouts build on these widgets
        self.controls = HBox([
            self.buttons.prev,
            ipw.Box([
                self.sliders.progress 
            ]).add_class('ProgBox') ,
            self.buttons.next
        ]).add_class('Controls') 

        
        self.footerbox = HBox([
            HBox([
                self.toggles.menu,
                self.buttons.capture,
                self.buttons.toc,
            ]).add_class('Menu-Box'),
            HBox([self.htmls.footer]), # should be in Box to avoid overflow
        ],layout=Layout(height='28px')).add_class('NavBox')
        
        self.navbox = VBox([
            self.buttons._inview,
            self.footerbox,
        ]).add_class('NavWrapper')   #class is must

        _many_btns = [self.buttons.setting, self.toggles.window, self.toggles.fscreen, self.toggles.laser, self.toggles.zoom, self.buttons.refresh, self.toggles.draw]
        
        self.panelbox = VBox([
            self.htmls.glass,
            HBox(_many_btns).add_class('TopBar').add_class('Inside'),
            VBox([
                self.sliders.fontsize,
                self.sliders.width,
                self.ddowns.theme,
                HTML('<hr/>'),
                Box([GridBox([
                    self.buttons.export, self.buttons.info, HTML(), # one empty button place
                    self.checks.notes,self.checks.toast,self.checks.reflow,
                    self.checks.proxy,self.checks.navgui,self.checks.postrun,
                    self.buttons.cap_all,self.buttons.pdf,self.buttons.png,
                ],layout=Layout(width='auto',overflow_x='scroll',
                                grid_template_columns='1fr 1fr 1fr',grid_gap='4px',
                                padding='4px',margin='auto')
                )],layout=Layout(min_height='120px')),# This ensures no collapse and scrollable Grid
                self.ddowns.clear,
                HTML('<span style="font-size:14px;">Set screenshot bounding box (if slides not fullscreen)</span>'),
                self.inputs.bbox,
                self._tmp_out,
                self.notes, # Just to be there for acting on a popup window
            ],layout=Layout(width='auto',height='auto',overflow_y='scroll',padding='12px',margin='0')),
        ],layout = Layout(width='70%',min_width='50%',height='0',overflow='hidden')).add_class('SidePanel') 
        
        self.tocbox = VBox([],layout = Layout(width='30%',min_width='400px',height='0',overflow='auto')).add_class('TOC')
        
        self.slidebox = Box([
            # Slides are added here dynamically
        ],layout= Layout(min_width='100%',min_height='100%', overflow='hidden')).add_class('SlideBox') 
        
        self.quick_menu = VBox([HBox([self.buttons.home, self.buttons.end, self.buttons.info, self.toggles.menu]),*_many_btns[::-1]],layout= dict(width='auto', height='0')).add_class('TopBar').add_class('Outside')

        def close_quick_menu(change):
            self.toggles.menu.value = False

        for btn in self.quick_menu.children: # All buttons should close menu
            if hasattr(btn, 'on_click'):
                btn.on_click(close_quick_menu)
            else:
                btn.observe(close_quick_menu, names=["value"])

        self.mainbox = VBox([
            self.htmls.glass, # This is the glass pane, should be before everything, otherwise it will cover the slide area
            self.htmls.loading, 
            self.htmls.toast,
            self.htmls.main,
            self.htmls.theme,
            self.htmls.logo,
            self.iw,
            self.quick_menu,
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
            self.drawer, 
            self.navbox, 
            self._snum,
            self._progbar # progressbar should come last
            ],layout= Layout(width=f'{self.sliders.width.value}vw', height=f'{int(self.sliders.width.value*9/16)}vw',margin='auto') # 9/16 is default, will change by setting
        ).add_class('SlidesWrapper')  #Very Important to add this class

        for child in self.mainbox.children:
            if isinstance(child, (HTML, HtmlWidget)):
                child.layout.margin = "0" # Important to reclaim useless space

        for btn in [self.buttons.next, self.buttons.prev, self.buttons.setting,self.buttons.capture]:
            btn.style.button_color= 'transparent'
            btn.layout.min_width = 'max-content' #very important parameter

        self._active_start(self.footerbox)

    def _deactivate(self):
        for w in getattr(self, '_aws',[]):
            w.remove_class("Active-Start")  
    
    def _active_start(self, *ws):
        self._aws = ws 
        for w in ws:
            w.add_class("Active-Start")
    
    def _push_toast(self,content,timeout=5):
        "Send inside notifications for user to know whats happened on some button click. Remain invisible in screenshot."
        if content and isinstance(content,str):
            to_send = {"content": "x"} if content == "x" else {'content': get_logo("2em","Notification") + "<br/>" + content}
            if isinstance(timeout,(int, float)):
                to_send['timeout'] = int(timeout*1000) # convert to ms
            elif timeout is not None:
                raise ValueError(f"timout should be int/float in seconds or None, got {timeout}")
            
            self.iw.send(to_send) # Send notification
        