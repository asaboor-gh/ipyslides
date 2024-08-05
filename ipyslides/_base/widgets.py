"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""
import ipywidgets as ipw
from dataclasses import dataclass
from ipywidgets import HTML, VBox, HBox, Box, Layout, Button
from tldraw import TldrawWidget

from . import styles, _layout_css
from ._widgets import InteractionWidget, HtmlWidget, NotesWidget
from .intro import get_logo, how_to_print
from ..utils import html
from .. import formatters as fmtrs

class Output(fmtrs._Output):
    __doc__ = ipw.Output.__doc__ # same docs as main

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
    
    def __repr__(self):
        return f'<{self.__module__}.Output at {hex(id(self))}>'

    def __enter__(self):
        if (slides := fmtrs.get_slides_instance()):
            self._slides = slides
            self._other = self._slides._hold_running()
            self._slides._in_output = True
            self._other.__enter__()
        super().__enter__()
    
    def __exit__(self, etype, evalue, tb):
        if getattr(self, '_slides', None):
            self._slides._in_output = False
            self._other.__exit__(etype, evalue, tb)
            del self._slides, self._other
        super().__exit__(etype, evalue, tb)

# patching for correct order of outputs, loaded with ipywidgets import when ipyslides is present
ipw.interaction.Output = Output
ipw.Output = Output
ipw.widget_output.Output = Output

auto_layout =  Layout(width='auto')
def describe(value,**kwargs): 
    return {'description': value, 'description_width': 'initial','layout':Layout(**{'width':'auto',**kwargs})} # let change width too


@dataclass(frozen=True)
class _Buttons:
    """
    Instantiate under `Widgets` class only.
    """
    prev    =  Button(icon='chevron-left',layout= Layout(width='auto',height='auto'),tooltip='Previous Slide [<, Shift + Space]').add_class('Arrows').add_class('Prev-Btn')
    next    =  Button(icon='chevron-right',layout= Layout(width='auto',height='auto'),tooltip='Next Slide [>, Space]').add_class('Arrows').add_class('Next-Btn')
    setting =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Open Settings [S]').add_class('Menu-Item').add_class('Settings-Btn')
    toc     =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Toggle Table of Contents').add_class('Menu-Item').add_class('Toc-Btn')
    refresh =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Update Widgets Display').add_class('Menu-Item').add_class('Refresh-Btn')
    source  =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Edit Source Cell [E]').add_class('Menu-Item').add_class('Source-Btn')
    home    =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Go to Title Page').add_class('Menu-Item').add_class('Home-Btn')
    end     =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Go To End of Slides').add_class('Menu-Item').add_class('End-Btn')
    info    =  Button(icon= 'plus',layout= Layout(width='auto',height='auto'), tooltip='Read Information').add_class('Menu-Item').add_class('Info-Btn')
    export  =  Button(description="Export to HTML File",layout= Layout(width='auto',height='auto'))
    syncjlc =  Button(description="Sync Jupyterlab Colors",layout= Layout(width='auto',height='auto'), tooltip='You need this for Notes and exported HTML')
    
@dataclass(frozen=True)
class _Toggles:
    """
    Instantiate under `Widgets` class only.
    """
    fscreen = ipw.ToggleButton(icon='plus',value = False, tooltip ='Enter Fullscreen [F]').add_class('FullScreen-Btn').add_class('Menu-Item')
    zoom    = ipw.ToggleButton(icon='plus',value = False, tooltip ='Enable Zooming Items [Z]').add_class('Zoom-Btn')
    laser   = ipw.ToggleButton(icon='plus',value = False, tooltip ='Show Laser Pointer [L]').add_class('Laser-Btn') 
    draw    = ipw.ToggleButton(icon='plus',value = False, tooltip ='Open Drawing Panel').add_class('Draw-Btn').add_class('Menu-Item')  
    menu    = ipw.ToggleButton(icon='plus',value = False, tooltip ='Toggle Quick Menu').add_class('Menu-Btn').add_class('Menu-Item')   

    setattr(draw, 'fmt_html', lambda: html('a', '', href=f'https://www.tldraw.com', target="_blank", rel="noopener noreferrer", 
        style='color:var(--accent-color);text-decoration:none;', css_class='fa fa-edit goto-button').value) # send to website on exported slides 

@dataclass(frozen=True)
class _Htmls:
    """
    Instantiate under `Widgets` class only.
    """
    footer  = HTML(layout=Layout(margin='0')).add_class('Footer') # Zero margin is important
    theme   = HTML(html('style',styles.style_css(styles.theme_colors['Inherit'])).value)
    main    = HTML(html('style',_layout_css.layout_css(styles.theme_colors['Inherit']['accent'], 16/9)).value) # Will be update in theme as well
    loading = HTML(layout=Layout(display='none')).add_class('Loading') #SVG Animation in it
    logo    = HTML().add_class('LogoHtml') # somehow my defined class is not behaving well in this case
    toast   = HtmlWidget().add_class('Toast') # For notifications
    cursor  = HtmlWidget().add_class('LaserPointer') # For beautiful cursor
    hilite  = HTML() # Updated in settings on creation. For code blocks.
    zoom    = HTML() # zoom CSS, do not add here!
    bglayer = HTML().add_class('BackLayer') # For glass effect

@dataclass(frozen=True)
class _Checks:
    """
    Instantiate under `Widgets` class only.
    """
    reflow  = ipw.Checkbox(value = False,description='Reflow Content',layout=auto_layout)
    notes   = ipw.Checkbox(value = False,description='Notes',layout=auto_layout) # do not observe, just keep track when slides work
    toast   = ipw.Checkbox(value = True, description='Notifications',layout=auto_layout)
    focus   = ipw.Checkbox(value = True, description='Auto Focus',layout=auto_layout)
    navgui  = ipw.Checkbox(value = True, description='Show Nav. GUI',layout=auto_layout)
    paste   = ipw.Checkbox(value = True, description='Show Image Paste GUI',layout=auto_layout)
    confirm = ipw.Checkbox(value = False, description='Overwrite Existing File',layout=auto_layout)

@dataclass(frozen=True)
class _Sliders:
    """
    Instantiate under `Widgets` class only.
    """
    progress = ipw.IntSlider(min=0, max=0, continuous_update=False,readout=True)
    width    = ipw.IntSlider(**describe('Width (vw)'),min=20,max=100, value = 60,continuous_update=False).add_class('Width-Slider') 
    fontsize = ipw.IntSlider(**describe('Font Size'),min=8,max=64,step=1, value = 20,continuous_update=False, tooltip="If you need more larger/smaller font size, use `Slides.settings.fonts.size`")

class Widgets:
    """
    Instantiate under `Sides` class only and provide to other classes after built-up.
    """
    def __setattr__(self, name , value):
        if name in self.__dict__:
            raise AttributeError(f'{name} is a read-only attribute')
        
        self.__dict__[name] = value
        
    def __init__(self):
        # print(f'Inside: {self.__class__.__name__}')
        self._tmp_out = Output(layout=dict(margin='0',width='0',height='0')) # For adding slide's CSS and animations
        self._progbar = ipw.Box([ipw.Box(layout={"width":"0"}).add_class("Progress")],layout=dict(width="100%",height="3px", visibility = "visible")).add_class("Progress-Box") # border not working everywhere
        self._snum   = Button(disabled=True, layout= Layout(width='auto',height='16px')).add_class("Slide-Number").add_class('Menu-Item')
        self.theme   = ipw.Dropdown(**describe('Theme'),options=[*styles.theme_colors.keys(),'Custom'],value='Inherit').add_class("ThemeSelect")
        self.buttons = _Buttons()
        self.toggles = _Toggles()
        self.sliders = _Sliders()
        self.checks  = _Checks()
        self.htmls   = _Htmls()
        self.iw      = InteractionWidget(self)
        self.notes   = NotesWidget(value = 'Notes Preview')
        self.drawer  = ipw.Box([TldrawWidget().add_class('Draw-Widget'), self.toggles.draw]).add_class('Draw-Wrapper')
        self.drawer.layout = dict(width='100%',height='0',overflow='hidden') # height will be chnaged by button
        self.buttons.syncjlc.on_click(self.sync_jupyter_colors)
        
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
                self.toggles.draw,
                self.buttons.toc, 
                self.buttons.source,
            ]).add_class('Menu-Box'),
            self.htmls.footer,
            #HBox([self.htmls.footer]), # should be in Box to avoid overflow
        ],layout=Layout(height='20px')).add_class('NavBox')
        
        self.navbox = VBox([
            self.footerbox,
        ]).add_class('NavWrapper')   #class is must

        _many_btns = [self.buttons.setting, self.toggles.fscreen, self.toggles.laser, self.toggles.zoom, self.buttons.refresh, self.toggles.draw]
        _html_layout = Layout(border_bottom='1px solid #8988', margin='8px 0 0 8px')
        
        self.panelbox = VBox([
            HBox(_many_btns).add_class('TopBar').add_class('Inside'),
            VBox([
                HTML('<b>Layout and Theme</b>',layout = _html_layout),
                self.sliders.fontsize,
                self.sliders.width,
                self.theme,
                self.buttons.syncjlc,
                HTML('<b>Additional Features</b>',layout = _html_layout),
                self.checks.focus, self.checks.notes,self.checks.toast,
                self.checks.navgui, self.checks.reflow,
                self.checks.paste,
                HTML(html('details',[html('summary','<b>HTML File Export</b>'), how_to_print]).value,layout = _html_layout),
                self.buttons.export,
                self.checks.confirm,
                self._tmp_out,
                self.notes, # Just to be there for acting on a popup window
            ],layout=Layout(width='auto',height='max-content',overflow_y='scroll',padding='12px',margin='0')),
        ],layout = Layout(height='0',overflow='hidden')).add_class('SidePanel') 
        
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
            self.htmls.bglayer, # should be before everything, otherwise it will cover the slide area
            self.htmls.loading, 
            self.htmls.toast,
            self.htmls.main,
            self.htmls.theme,
            self.htmls.logo,
            self.iw,
            self.quick_menu,
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

        for btn in [self.buttons.next, self.buttons.prev, self.buttons.setting]:
            btn.style.button_color= 'transparent'
            btn.layout.min_width = 'max-content' #very important parameter

        self._active_start(self.footerbox)
    
    def sync_jupyter_colors(self,btn=None):
        "Pick correct jupyter theme colors if Inherit theme selected, before exporting to HTML."
        if self.theme.value == "Inherit":
            self.iw.msg_tojs = "SetColors"
            self.buttons.syncjlc.layout.display = ''
            if btn:
                self._push_toast(f'Inherit theme colors synced successfully.')
        else:
            self.buttons.syncjlc.layout.display = 'none'
            
    def _deactivate(self):
        for w in getattr(self, '_aws',[]):
            w.remove_class("Active-Start")  
    
    def _active_start(self, *ws):
        self._aws = ws 
        for w in ws:
            w.add_class("Active-Start")
    
    def _push_toast(self,content,timeout=5):
        "Send inside notifications for user to know whats happened on some button click."
        if content and isinstance(content,str):
            to_send = {"content": "x"} if content == "x" else {'content': get_logo("2em","Notification") + "<br/>" + content}
            if isinstance(timeout,(int, float)):
                to_send['timeout'] = int(timeout*1000) # convert to ms
            elif timeout is not None:
                raise ValueError(f"timout should be int/float in seconds or None, got {timeout}")
            
            self.iw.send(to_send) # Send notification
        