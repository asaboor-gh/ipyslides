"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""
from dataclasses import dataclass
from collections import namedtuple

from traitlets import observe
import ipywidgets as ipw
from ipywidgets import HTML, VBox, HBox, Box, Layout, Button
from tldraw import TldrawWidget
from dashlab import ListWidget, JupyTimer, TabsWidget

from . import styles
from ._widgets import InteractionWidget, NotesWidget, LaserPointer
from .intro import get_logo, how_to_print, instructions, key_combs
from ..utils import html, htmlize
from .. import formatters as fmtrs
  

class TOCWidget(ListWidget):
    def __init__(self, app, *args, **kwargs):
        self._app = app
        super().__init__(transform=self._make_toc, *args, **kwargs)
        self.description = '' # no description for this widget
        self.layout.max_height = '' # unset here
    
    def fmt_html(self): # for export
        for slide in self._app[:1]: # just pick one slide to get the toc work
            return slide._reset_toc().data.get('text/html','')
        return ''
    
    def set_toc_items(self, items):
        "items be a list of tuple (target_slide_index, section_text)"
        tss = namedtuple("TocItem", ['ti', 'si', 'sec'])
        self.options = [tss(i, *item) for i, item in enumerate(items)]
    
    def _make_toc(self, obj):
        return htmlize(f"color['var(--accent-color)']`{obj.ti + 1}.` {obj.sec}") +  f"<p>{obj.si}</p>"
    
    @observe('value')
    def _jump_to_section(self, change):
        if change.new:
            self._app.navigate_to(change.new.si) # jump at slide index
            if self._app.widgets.panelbox.is_open():
                self._app.widgets.panelbox.toggle(False) # close panel

class CtxMenu(ListWidget):
    def __init__(self, ws, *args, **kwargs):
        self.ws = ws # store reference to widgets class
        kwargs['transform'] = self._transform # custom transform for icons
        super().__init__(*args, **kwargs)
        self._handlers = {}
        self._opts_map = {
            "fscreen": {
                "text":"{state} Fullscreen <kbd>F</kbd>","icon":"compress",
                "iconFalse":"expand", "state":("Enter", "Exit")
            },
            "laser": {
                "text":"{state} Laser Pointer <kbd>L</kbd>","icon":"circle",
                "iconFalse":"laser", "state":("Show", "Hide")
            },
            "panel": {
                "text":"{state} Side Panel <kbd>S</kbd>","icon":"close",
                "iconFalse":"panel", "state":("Open", "Close")
            },
            "draw": {"text":"Open Drawing Board","icon":"edit"},
            "ksc": {"text":"Keyboard Shortcuts <kbd>K</kbd>","icon":"keyboard" },
            "info": {"text":"Read Instructions","icon":"info" },
            "source": {"text":"Edit Source Cell <kbd>E</kbd>","icon":"code" },
            "refresh": {"text":"Refresh Widgets Display","icon":"refresh" },
            "toc": {"text":"Table of Contents","icon":"bars" },
        }
        self._state = {
            "draw": None,  "toc":None, "fscreen": False, "laser": False, "panel": False, 
            "source": None, "refresh": None, "ksc": None, "info": None
        } # state changes on selection
        self.add_class('CtxMenu')
        self.hide() # initially closed
        self._set_opts() # set all options initially
        
    def _transform(self, item):
        key, value = item
        obj = self._opts_map.get(key, {})
        icon = obj.get("iconFalse" if value is False else "icon", "")
        text = obj.get("text", key).format(state=obj.get("state", ("Enable","Disable"))[1 if value else 0])
        return f"<i class='fa fa-{icon}'></i> {text}" if icon else text

    def show(self, x, y, units='%'):
        "Open menu at given x,y coordinates in given units."
        if self.ws.panelbox.is_open():
            self._set_opts('panel')
        elif 'mode-inactive' in self.ws.mainbox._dom_classes: # prefer over fullscreen
            self._set_opts('fscreen','laser','draw')
        elif 'mode-fullscreen' in self.ws.mainbox._dom_classes:
            self._set_opts('fscreen','laser','draw','panel','toc','ksc')
        else:
            self._set_opts()
        self.layout.left = f'{x}{units.strip()}' 
        self.layout.top = f'{y}{units.strip()}'
        self.layout.visibility = 'visible'
    
    def hide(self):
        "Close menu."
        self.layout.top = '101%' # below view, keep left as is
        self.layout.visibility = 'hidden'
        
    def _callback(self, key, handler):
        "Register single handler for selection of given key in options. handler should accept two argument (ctxmenu, new_value)."
        if key not in self._opts_map:
            raise KeyError(f'Key {key!r} not found in menu options. Available keys: {list(self._opts_map.keys())}')
        self._handlers[key] = handler
    
    def select(self, key, state=None):
        """Select menu item by unique key in options and set state to True/False/None
        (optionally with a function on old state) if option is a toggle. Use update_state for no event trigger.
        """
        self.index = self.update_state(key, state)
    
    def update_state(self, key, state):
        """Update state of given key in options and return index without triggering selection. 
        State can be a function on old state or True/False/None.
        Use select() method if you want to trigger selection event as well.
        """
        index = None
        for i, (sk, sv) in enumerate(self.options):
            if key == sk:
                index = i
                value = state(sv) if callable(state) else state
                if isinstance(sv, bool) and value in (True, False):
                    self._state[key] = value
                
        self._set_opts() # reset options to trigger re-render
        return index

    def _set_opts(self, *keys):
        "Set options for given keys or all if none provided"
        self.options = [(k, v) for k,v in self._state.items() if not keys or k in keys] 
        self.index = None # reset index after options change to allow re-selection of same item
    
    def _istoggle(self, key):
        return bool(self._opts_map.get(key, {}).get("iconFalse", False))
    
    @observe('value')
    def _on_select(self, change):
        if change.new and isinstance(change.new, tuple):
            key, value = change.new
            # First update menu's visible state if not same
            self.update_state(key, lambda old: not old if self._istoggle(key) else old)
            value = self._state.get(key, None)
            if key in self._handlers:
                self._handlers.get(key, lambda ctx, val: None)(self, value)
            # Now update left over widgets
            elif key == 'laser':
                self.ws.htmls.pointer.active = value
            elif key == 'fscreen':
                self.ws.iw.msg_tojs = 'TFS' # we will get back [!]mode-fullscreen message
            elif key == 'draw':
                self.ws.drawer.toggle(True) # open drawing board
            elif key == 'panel':
                self.ws.iw._toggle_panel(self)
            elif key == 'toc':
                self.ws.panelbox.toggle(True) # open panel
                self.ws.panelbox.select_tab(1) # select toc tab
            elif key == 'ksc':
                self.ws._push_toast(htmlize(key_combs), timeout=15)
            elif key == 'info':
                self.ws.iw.send({
                    "content": html('',[instructions]).value,
                    "timeout": 120000 # 2 minutes
                })
            elif self.ws.htmls.loading.value: # Just a handy cleanup
                self.ws.iw.msg_tojs = "ClearLoading"

        
        self.index = None # reset index after selection to allow re-selection of same item
        self.hide() # hide menu on selection
        self.set_trait('value', {}) # reset value to allow re-selection of same item
        
class DrawWidget(ipw.Box):
    def __init__(self, ws, **kwargs):
        self.ws = ws
        btn = Button(icon='chevronu', tooltip='Close Drawing Board').add_class('Draw-Btn').add_class('Menu-Item')
        btn.on_click(lambda btn: self.toggle(False)) # open is by context menu only or draw_button used by user
        super().__init__(children = [TldrawWidget().add_class('Draw-Widget'), btn], **kwargs)
        self.add_class('Draw-Wrapper')
        
    def toggle(self, visible):
        "Show/hide drawing widget."
        self.layout.height = "100%" if visible else "0"
        if visible:
            if self.ws.theme.value == "Jupyter":
                self.ws.iw.msg_tojs = "THEME:jupyterlab" # make like that
        else:
            self.ws.mainbox.focus() # it doesn't stay their otherwise

class SidePanel(VBox):
    def __init__(self, ws, *args, **kwargs):
        self.ws = ws
        super().__init__(*args, **kwargs)
        self.add_class('SidePanel')
        self.toggle(False) # initially closed
        self._build_layout()
    
    def _build_layout(self):
        _html_layout = Layout(border_bottom='1px solid #8988', margin='8px 0 0 8px')
        settings = VBox([
            HTML('<b>Layout and Theme</b>',layout = _html_layout),
            self.ws.sliders.fontsize,
            self.ws.sliders.width,
            self.ws.theme,
            HTML('<b>Additional Features</b>',layout = _html_layout),
            self.ws.checks.focus, self.ws.checks.rebuild, self.ws.checks.notes,
            self.ws.checks.toast, self.ws.checks.reflow,
            HTML('<b>PDF Printing (Experimental) / HTML Export</b>',layout = _html_layout),
            HTML(html('details',[html('summary','Printing Info'), how_to_print]).value),
            self.ws.checks.inotes,
            self.ws.checks.merge,
            VBox([self.ws.buttons.print, self.ws.buttons.export],
                layout=Layout(margin='0 0 0 calc(var(--jp-widgets-inline-label-width) - 4px)')
            ),
            self.ws.checks.confirm,
            self.ws._tmp_out,
            self.ws.notes, # Just to be there for acting on a popup window
        ],layout=Layout(width='100%',height='100%',overflow_y='scroll',min_width='0',padding="8px"))
        
        self._tocsTab = VBox([],layout = Layout(width='100%',height='100%', overflow_y='auto',min_width='0')).add_class('TOC') # toc box will be filled later
        self._clipsTab = VBox([],layout = Layout(width='100%',height='100%',overflow_y='auto',min_width='0')) # clips box will be filled later
        self._tabs = TabsWidget(
            children=[settings, self._tocsTab, self._clipsTab],
            titles=['<i class="fa fa-settings"></i> Options','<i class="fa fa-bars"></i> Table of Contents','<i class="fa fa-camera"></i> Clips'],
            tabs_height='28px', # fixed height for tabs
        )
        btn = Button(icon='chevronl', tooltip='Close Side Panel').add_class('panel-close-btn')
        btn.on_click(lambda btn: self.toggle(False))
        self._head = HBox([HTML(get_logo("28px", "IPySlides")), btn], layout=Layout(justify_content='space-between', align_items='center', padding='0'))
        self.children = [self._head, self._tabs]
    
    def is_open(self):
        return self.layout.width != '0'
    
    def toggle(self, visible):
        "Show/hide side panel."
        self.ws._ctxmenu.update_state('panel', visible) # make icons consistent
        self.layout.width = "min(400px, 100%)" if visible else "0"
        self.layout.overflow = 'auto' if visible else 'hidden'
    
    def select_tab(self,index):
        "Select tab by index."
        self._tabs.selected_index = index
        
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
    prev    =  Button(icon='chevron-left',layout= Layout(width='auto',height='auto'),tooltip='Previous Slide [<]').add_class('Arrows').add_class('Prev-Btn')
    next    =  Button(icon='chevron-right',layout= Layout(width='auto',height='auto'),tooltip='Next Slide [>, Space]').add_class('Arrows').add_class('Next-Btn')
    export  =  Button(icon='file',description="Export to HTML File",layout= Layout(width='max-content'))
    print   =  Button(icon='file-pdf',description="Print Slides",layout= Layout(width='max-content'), tooltip='Ctrl + P')

@dataclass(frozen=True)
class _Htmls:
    """
    Instantiate under `Widgets` class only.
    """
    footer  = HTML(layout=Layout(margin='0')).add_class('Footer') # Zero margin is important
    theme   = HTML()
    main    = HTML() 
    loading = HTML(layout=Layout(display='none')).add_class('Loading') #SVG Animation in it
    logo    = HTML().add_class('LogoHtml') # somehow my defined class is not behaving well in this case
    pointer = LaserPointer() # For beautiful pointer
    hilite  = HTML() # Updated in settings on creation. For code blocks.
@dataclass(frozen=True)
class _Checks:
    """
    Instantiate under `Widgets` class only.
    """
    reflow  = ipw.Checkbox(value = False,description='Reflow Content',layout=auto_layout)
    inotes  = ipw.Checkbox(value = False,description='Inline Notes (PDF only)',layout=auto_layout,)
    merge   = ipw.Checkbox(value = False,description='Merge Parts (HTML/PDF)',layout=auto_layout)
    notes   = ipw.Checkbox(value = False,description='Notes Popup',layout=auto_layout) # do not observe, just keep track when slides work
    toast   = ipw.Checkbox(value = True, description='Notifications',layout=auto_layout)
    focus   = ipw.Checkbox(value = True, description='Auto Focus',layout=auto_layout)
    rebuild = ipw.Checkbox(value = True, description='Auto Rebuild',layout=auto_layout)
    confirm = ipw.Checkbox(value = False, description='Overwrite Existing File',layout=auto_layout)

@dataclass(frozen=True)
class _Sliders:
    """
    Instantiate under `Widgets` class only.
    """
    progress = ipw.IntSlider(min=0, max=0, continuous_update=False,readout=True)
    width    = ipw.IntSlider(**describe('Width (vw)'),min=20,max=100, value = 60,continuous_update=False).add_class('Width-Slider') 
    fontsize = ipw.IntSlider(**describe('Font Size'),min=8,max=64,step=1, value = 16,continuous_update=False, tooltip="If you need more larger/smaller font size, use `Slides.settings.fonts.size`")

class Widgets:
    """
    Instantiate under `Sides` class only and provide to other classes after built-up.
    """
    def __setattr__(self, name , value):
        if name in self.__dict__:
            raise AttributeError(f'{name} is a read-only attribute')
        
        self.__dict__[name] = value
        
    def __init__(self):
        self._tmp_out = Output(layout=dict(margin='0',width='0',height='0')) # For adding slide's CSS and animations
        self._progbar = ipw.Box([ipw.Box(layout={"width":"0"}).add_class("Progress")],layout=dict(width="100%",height="2px", visibility = "visible")).add_class("Progress-Box") # border not working everywhere
        self._snum   = Button(disabled=True, layout= Layout(width='auto',height='16px')).add_class("Slide-Number").add_class('Menu-Item')
        self.theme   = ipw.Dropdown(**describe('Theme'),options=[*[k for k in styles.theme_colors.keys() if k != 'Jupyter'],'Custom']).add_class("ThemeSelect") # Jupyter will be added on demand
        self.buttons = _Buttons() 
        self.sliders = _Sliders()
        self.checks  = _Checks()
        self.htmls   = _Htmls()
        self._timer  = JupyTimer()
        self.drawer  = DrawWidget(self)
        self._ctxmenu= CtxMenu(self, description='Shift + Right Click Browser Menu')
        self.iw      = InteractionWidget(self)
        self.notes   = NotesWidget(value = 'Notes Preview')
        self.drawer.layout = dict(width='100%',height='0',overflow='hidden') # height will be chnaged by button
        
        # Layouts build on these widgets
        self.controls = HBox([
            self.buttons.prev,
            ipw.Box([
                self.sliders.progress 
            ]).add_class('ProgBox') ,
            self.buttons.next
        ]).add_class('Controls') 

        self.footerbox = HBox([self.htmls.footer,]).add_class('FooterBox')   #class is must
        self.panelbox = SidePanel(self)
        self.slidebox = Box([
            # Slides are added here dynamically
        ],layout= Layout(min_width='100%',min_height='100%', overflow='hidden')).add_class('SlideBox') 
        
        self.mainbox = VBox([
            self.htmls.loading, 
            self.htmls.main,
            self.htmls.theme,
            self.iw,
            self._timer.widget(minimal=True),
            self.panelbox,
            self.htmls.pointer,
            self.htmls.hilite,
            HBox([ #Slide_box must be in a box to have animations work
                self.slidebox , 
            ],layout= Layout(width='100%',max_width='100%',height='100%',overflow='hidden')
            ).add_class('SBoxWrapper'), # overflow should be hidden for animation purpose, class added to handle print PDF
            self.controls, # Importnat for unique display
            self.drawer, 
            self.footerbox,
            self.htmls.logo,# on top of things
            self._snum,
            self._ctxmenu, # at top 
            self._progbar # progressbar should come last
            ],layout= Layout(width=f'{self.sliders.width.value}vw', height=f'{int(self.sliders.width.value*9/16)}vw',margin='auto') # 9/16 is default, will change by setting
        ).add_class('SlidesWrapper')  #Very Important to add this class

        for child in self.mainbox.children:
            if isinstance(child, HTML):
                child.layout.margin = "0" # Important to reclaim useless space

        for btn in [self.buttons.next, self.buttons.prev]:
            btn.style.button_color= 'transparent'
            btn.layout.min_width = 'max-content' #very important parameter
        
    def _push_toast(self,content,timeout=5):
        "Send inside notifications for user to know whats happened on some button click."
        if content and isinstance(content,str):
            to_send = {"content": "x"} if content == "x" else {'content': get_logo("2em","Notification") + "<br/>" + content}
            if isinstance(timeout,(int, float)):
                to_send['timeout'] = int(timeout*1000) # convert to ms
            elif timeout is not None:
                raise ValueError(f"timout should be int/float in seconds or None, got {timeout}")
            
            self.iw.send(to_send) # Send notification
        