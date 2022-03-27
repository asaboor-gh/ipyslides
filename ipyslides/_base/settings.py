"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

import os 
import datetime
from IPython import get_ipython
from IPython.display import display, Image
from ..writers import write
from ..formatter import fix_ipy_image, code_css
from ..extended_md import parse_xmd
from ..utils import set_dir, html
from . import scripts, intro, styles

class LayoutSettings:
    def __init__(self, _instanceWidgets):
        "Provide instance of LivSlides to work."
        self.widgets = _instanceWidgets
        self.animation = styles.animations['slide']
        self.font_scale = 1
        self._font_family = {'code':'var(--jp-code-font-family)','text':'sans-serif'}
        self._footer_text = 'IPySlides | <a style="color:skyblue;" href="https://github.com/massgh/ipyslides">github-link</a>'
        self._content_width = '90%' #Better
        self._breakpoint_width = '650px'
        
        self.height_slider = self.widgets.sliders.height
        self.width_slider  = self.widgets.sliders.width
        self.scale_slider  = self.widgets.sliders.scale
        self.theme_dd = self.widgets.ddowns.theme
        self.reflow_check = self.widgets.checks.reflow
        
        self._instructions = self.widgets.outputs.intro
        self.out_fixed = self.widgets.outputs.fixed
        self.out_renew = self.widgets.outputs.renew
        self.btn_fs    = self.widgets.toggles.fscrn
        self.btn_zoom  = self.widgets.toggles.zoom
        self.btn_timer = self.widgets.toggles.timer
        self.box = self.widgets.panelbox
        self.box.on_displayed(self._on_displayed) # First attempt of Javascript to work
        
        self.theme_dd.observe(self._update_theme,names=['value'])
        self.scale_slider.observe(self.__set_font_scale,names=['value'])
        self.height_slider.observe(self.__update_size,names=['value'])
        self.width_slider.observe(self.__update_size,names=['value'])
        self.btn_fs.observe(self._push_fullscreen,names=['value'])
        self.btn_zoom.observe(self._push_zoom,names=['value'])
        self.reflow_check.observe(self._update_theme,names=['value'])
        self.sidebar_switch = self.widgets.toggles.display
        self.sidebar_switch.observe(self._toggle_sidebar,names=['value'])        
        self.sidebar_switch.value = 0 # Initial Call must be inline, so that things should be shown outside Jupyterlab always
        
        self._update_theme() #Trigger Theme and Javascript in it
        self.set_code_style() #Trigger CSS in it, must
        self.set_layout(center = True) # Trigger this as well
        
    def _on_displayed(self,change):
        self.__add_js()
        self._instructions.clear_output(wait=True) # This make sure that instructions are not duplicated
        with self._instructions:
            parse_xmd(intro.instructions, display_inline = True)
            
    def set_animation(self,name):
        "Set animation style or pass None to disable animation."
        if name is None:
            self.animation = '' #Disable animation
        elif name in styles.animations:
            self.animation = styles.animations[name]
        else:
            print(f'Animation {name!r} not found. Pass None or any of {list(styles.animations.keys())}.')
    
    def set_code_style(self,style='default',background='var(--secondary-bg)'):
        "Set code style CSS. Use background for better view of your choice."
        self.widgets.htmls.hilite.value = code_css(style,background=background)
      
    def set_font_family(self,text_font=None,code_font=None):
        "Set main fonts for text and code."
        if text_font:
            self._font_family['text'] = text_font
        if code_font:
            self._font_family['code'] = code_font  
        self._update_theme() # Changes Finally 
    

    def set_font_scale(self,font_scale=1):
        "Set font scale to increase or decrease text size. 1 is default."
        self.scale_slider.value = font_scale 
        
    def set_logo(self,src,width=80,top=0,right=16):
        "`src` should be PNG/JPEG file name or SVG string. width,top,right are pixels, should be integer."
        if isinstance(src,str):
            if '<svg' in src and '</svg>' in src:
                image = src
            else:
                image = fix_ipy_image(Image(src,width=width),width=width) #width both in Image and its fixing

            self.widgets.htmls.logo.value = f"""<div style='position:absolute;right:{right}px;top:{top}px;width:{width}px;height:auto;'>
                                        {image}</div>"""
                                    
    def set_footer(self, text = '', show_slideno=True, show_date=True, _number_str=''):
        "Set footer text. `text` should be string. `show_slideno` and `show_date` are booleans."
        if text:
            self._footer_text = text #assign to text
            _text = text 
        else:
            _text = self._footer_text
            
        if show_date:
            _text += f' | <text style="color:var(--secondary-fg);">' + datetime.datetime.now().strftime('%b-%d-%Y')+ '</text>'
        if show_slideno: #Slide number should be replaced from __number__ 
            _text += '<b style="color:var(--accent-color);white-space:pre;">  __number__<b>'
        _text = f'<p style="white-space:nowrap;"> {_text} </p>'
        
        self.widgets.htmls.footer.value = _text.replace('__number__',_number_str)
        
    def code_lineno(self,b=True):
        "Set code line numbers to be shown or not."
        if b:
            return display(html('style', 'code:before{ display:inline-block !important; }'))
        return display(html('style', 'code:before{ display:none !important; }'))
    
    def set_layout(self,center = True, content_width = None):
        "Central aligment of slide by default. If False, left-top aligned."
        self._content_width = content_width if content_width else self._content_width # user selected
        style_dict = {'display':'block','width':content_width} #block is must
        if center:
            style_dict.update(dict(margin = 'auto',align_items = 'center',justify_content = 'center'))
        else: #container still should be in the center horizontally with auto margin
            style_dict.update(dict(margin = '8px auto',align_items = 'baseline',justify_content = 'flex-start'))
        
        for k,v in style_dict.items():
            setattr(self.widgets.outputs.slide.layout, k, v)
        
        self._update_theme(change=None) # Trigger CSS in it to make width change
            
    def __add_js(self):
        with self.out_fixed: 
            display(scripts.navigation_js)
    
    def _emit_resize_event(self):
        with self.out_renew: 
            self.out_renew.clear_output(wait=True)
            display(scripts.resize_js)
        
    def __update_size(self,change):
        self.widgets.mainbox.layout.height = '{}px'.format(self.height_slider.value)
        self.widgets.mainbox.layout.width = '{}vw'.format(self.width_slider.value)  
        self._toggle_sidebar(change=None) #modify width of sidebar or display it inline
        self._emit_resize_event() # Although its in _toggle_sidebar, but for being safe, do this
        
        if not self.btn_fs.value: #If not fullscreen, then update breakpoint, so that it can be used in CSS
            self._breakpoint_width = f'{int(100*650/self.width_slider.value)}px'
        
        self._update_theme(change=None) # For updating size and breakpoints
            
                     
    def __set_font_scale(self,change):
        # Below line should not be in _update_theme to avoid loop call.
        self.font_scale = self.widgets.sliders.scale.value
        self._update_theme(change=None)
        
        
    def _update_theme(self,change=None): 
        text_size = '{}px'.format(int(self.font_scale*16))
        
        if self.theme_dd.value != 'Custom':
            theme_css =  styles.style_html(styles.theme_roots[self.theme_dd.value])
        else: # In case of Custom CSS
            with set_dir(get_ipython().starting_dir):
                if not os.path.isfile('custom.css'):
                    with open('custom.css','w') as f:
                        f.write('/* Author: Abdul Saboor */\n' + styles.style_html( styles.theme_roots['Light']))
                else: # Read CSS from file otherwise
                    with open('custom.css','r') as f:
                        theme_css = ''.join(f.readlines())
                 
        # Replace font-size and breakpoint size
        theme_css = theme_css.replace(
                        '__text_size__',text_size).replace(
                        '__textfont__',self._font_family['text']).replace(
                        '__codefont__',self._font_family['code']).replace(
                        '__content_width__',self._content_width).replace(
                        '__breakpoint_width__', self._breakpoint_width  
                        )
        
        # Update CSS
        if self.reflow_check.value:
            theme_css = theme_css + f"\n.SlideArea * {{max-height:max-content !important;}}\n"
        
        self.widgets.htmls.theme.value = f'<style>\n{theme_css}\n</style>'
        self._toggle_sidebar(change=None) #modify width of sidebar or display it inline, must call
        self._emit_resize_event()
        
    def _toggle_sidebar(self,change): 
        """Pushes this instance of LiveSlides to sidebar and back inline."""
        # Only push to sidebar if not in fullscreen
        if self.btn_fs.value or self.sidebar_switch.value == 0:
            self.widgets.htmls.sidebar.value = '' # Should be empty to avoid competition of style
            self.height_slider.layout.display = 'inline-flex' #Very impprtant
        else:
            self.widgets.htmls.sidebar.value =  html('style',styles.sidebar_layout_css(span_percent=self.width_slider.value)).value
            self.height_slider.layout.display = 'none'

        return self._emit_resize_event() # Must return this event so it work in other functions.
    
    def _push_fullscreen(self,change):  
        if self.btn_fs.value:
            self._breakpoint_width = '650px'
            self.btn_fs.icon = 'compress'
            self.widgets.mainbox.add_class('FullScreen') # to fullscreen
        else:
            self._breakpoint_width = f'{int(100*650/self.width_slider.value)}px'
            self.btn_fs.icon = 'expand'
            self.widgets.mainbox.remove_class('FullScreen') # back to inline
            
        self.widgets.htmls.fscrn.value = html('style', styles.fullscreen_css if self.btn_fs.value else '').value
        self._emit_resize_event() # Resize before waiting fo update-theme
        self._update_theme(change=None) # For updating size and breakpoints
    
    def _push_zoom(self,change):
        if self.btn_zoom.value:
            if self.btn_fs.value:
                self.btn_zoom.icon= 'toggle-on'
                self.widgets.htmls.zoom.value = f'<style>\n{styles.mpl_fs_css}\n</style>'
            else:
                self.widgets._push_toast('Objects are only zoomable in Fullscreen mode!',timeout=2)
        else:
            self.btn_zoom.icon= 'toggle-off'
            self.widgets.htmls.zoom.value = ''
        
