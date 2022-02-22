"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

import os 
import datetime
from IPython import get_ipython
from IPython.display import display, Image, HTML
from ..writers import write
from ..formatter import fix_ipy_image
from ..utils import set_dir
from . import scripts, intro, styles


class LayoutSettings:
    def __init__(self, _instanceWidgets):
        "Provide instance of LivSlides to work."
        self.widgets = _instanceWidgets
        self.animation = styles.animations['slide']
        self.font_scale = 1
        self._font_family = {'code':'var(--jp-code-font-family)','text':'sans-serif'}
        self._footer_text = 'Abdul Saboor | <a style="color:blue;" href="www.google.com">google@google.com</a>'
        
        self.height_slider = self.widgets.sliders.height
        self.width_slider  = self.widgets.sliders.width
        self.scale_slider  = self.widgets.sliders.scale
        self.theme_dd = self.widgets.ddowns.theme
        self.reflow_check = self.widgets.checks.reflow
        
        self.__instructions = self.widgets.outputs.intro
        self.out_js_fix = self.widgets.outputs.js_fix
        self.out_js_var = self.widgets.outputs.js_var
        self.btn_fs    = self.widgets.toggles.fscrn
        self.btn_zoom  = self.widgets.toggles.zoom
        self.btn_timer = self.widgets.toggles.timer
        self.box = self.widgets.panelbox
        self.box.on_displayed(lambda change: self.__add_js()) # First attempt of Javascript to work
        
        with self.__instructions:
            write(intro.instructions) 
        
        self.theme_dd.observe(self.update_theme)
        self.scale_slider.observe(self.__set_font_scale)
        self.height_slider.observe(self.__update_size,names=['value'])
        self.width_slider.observe(self.__update_size,names=['value'])
        self.btn_fs.observe(self.update_theme,names=['value'])
        self.btn_zoom.observe(self.update_theme,names=['value'])
        self.reflow_check.observe(self.update_theme)
        self.sidebar_switch = self.widgets.toggles.display
        self.sidebar_switch.observe(self._toggle_sidebar,names=['value'])        
        self.sidebar_switch.value = 0 # Initial Call must be inline, so that things should be shown outside Jupyterlab always
        
    
        self.update_theme() #Trigger Theme and Javascript in it
        
    def set_animation(self,name):
        if name in styles.animations:
            self.animation = styles.animations[name]
        else:
            print(f'Animation {name!r} not found. Use any of {list(styles.animations.keys())}.')
      
    def set_font_family(self,text_font=None,code_font=None):
        "Set main fonts for text and code."
        if text_font:
            self._font_family['text'] = text_font
        if code_font:
            self._font_family['code'] = code_font  
        self.update_theme() # Changes Finally 
    

    def set_font_scale(self,font_scale=1):
        self.scale_slider.value = font_scale 
        
    def set_logo(self,src,width=80,top=0,right=16):
        "`src` should be PNG/JPEG file name or SVG string. width,top,right are pixels, should be integer."
        if '<svg' in src and '</svg>' in src:
            image = src
        else:
            image = fix_ipy_image(Image(src,width=width),width=width) #width both in Image and its fixing
            
        self.widgets.htmls.logo.value = f"""<div style='position:absolute;right:{right}px;top:{top}px;width:{width}px;height:auto;'>
                                    {image}</div>"""
                                    
    def set_footer(self, text = '', show_slide_number=True, show_date=True, _number_str=''):
        # For dynamic change of footer text
        if text:
            self._footer_text = text #assign to text
            _text = text 
        else:
            _text = self._footer_text
            
        if show_date:
            _text += f' | <text style="color:var(--secondary-fg);">' + datetime.datetime.now().strftime('%b-%d-%Y')+ '</text>'
        if show_slide_number: #Slide number should be replaced from __number__ 
            _text += '<b style="color:var(--accent-color);white-space:pre;">  __number__<b>'
        _text = f'<p style="white-space:nowrap;"> {_text} </p>'
        
        self.widgets.htmls.info.value = _text.replace('__number__',_number_str)
        
    def code_line_numbering(self,b=True):
        if b:
            return display(HTML('<style> code:before{ display:inline-block !important; } </style>'))
        return display(HTML('<style> code:before{ display:none !important; } </style>'))
    
    def align8center(self,b=True):
        "Central aligment of slide by default. If False, left-top aligned."
        if b:
            self.widgets.outputs.slide.layout.margin = 'auto'
            self.widgets.outputs.slide.layout.width = 'auto'
            self.widgets.outputs.slide.layout.max_width = '100%'
        else:
            self.widgets.outputs.slide.layout.margin = '2px 8px 2px 8px'
            self.widgets.outputs.slide.layout.width = '100%'
            
    def __add_js(self):
        with self.out_js_fix: 
            display(scripts.navigation_js)
    
    def emit_resize_event(self):
        with self.out_js_var: 
            self.out_js_var.clear_output(wait=True)
            display(scripts.resize_js)
        
    def __update_size(self,change):
        self.widgets.mainbox.layout.height = '{}px'.format(self.height_slider.value)
        self.widgets.mainbox.layout.width = '{}vw'.format(self.width_slider.value)  
        self._toggle_sidebar(change=None) #modify width of sidebar or display it inline
        self.emit_resize_event() # Although its in _toggle_sidebar, but for being safe, do this
        self.update_theme(change=None) # For updating size and breakpoints
            
                     
    def __set_font_scale(self,change):
        # Below line should not be in update_theme to avoid loop call.
        self.font_scale = self.widgets.sliders.scale.value
        self.update_theme(change=None)
        
        
    def update_theme(self,change=None):  
        text_size = '{}px'.format(int(self.font_scale*16))
        if self.theme_dd.value == 'Custom': # In case of Custom CSS
            with set_dir(get_ipython().starting_dir):
                if not os.path.isfile('custom.css'):
                    with open('custom.css','w') as f:
                        _str =  styles.style_html( styles.theme_roots['Light']).replace('<style>','').replace('</style>','')
                        f.writelines(['/* Author: Abdul Saboor */'])
                        f.write(_str)
                # Read CSS from file
                with open('custom.css','r') as f:
                    theme_css = '<style>' + ''.join(f.readlines()) + '</style>'
        else:
            theme_css =  styles.style_html( styles.theme_roots[self.theme_dd.value])
            
        # Replace font-size and breakpoint size
        theme_css = theme_css.replace(
                        '__text_size__',text_size).replace(
                        '__textfont__',self._font_family['text']).replace(
                        '__codefont__',self._font_family['code'])
        if self.reflow_check.value:
            theme_css = theme_css.replace('</style>','') + f".SlideArea.{self.widgets.uid} * "+ "{max-height:max-content !important;}\n</style>"
        
        # Zoom Container 
        if self.btn_zoom.value:
            if self.btn_fs.value:
                self.btn_zoom.icon= 'toggle-on'
                theme_css = theme_css.replace('</style>','\n') +  styles.mpl_fs_css.replace('<style>','')
            else:
                self.widgets._push_toast('Objects are only zoomable in Fullscreen mode!',timeout=2)
        else:
            self.btn_zoom.icon= 'toggle-off'
        
        # Catch Fullscreen too.
        if self.btn_fs.value:
            theme_css = theme_css.replace('__breakpoint_width__','650px').replace('</style>','\n') +  styles.fullscreen_css.replace('<style>','')
            self.btn_fs.icon = 'compress'
            self.widgets.mainbox.add_class('FullScreen') # Add this to fullscreen
            
        else:
            theme_css = theme_css.replace('__breakpoint_width__',f'{int(100*650/self.width_slider.value)}px') #Will break when slides is 650px not just window
            self.btn_fs.icon = 'expand'
            self.widgets.mainbox.remove_class('FullScreen')
        
        
        self.widgets.htmls.theme.value = theme_css
        self._toggle_sidebar(change=None) #modify width of sidebar or display it inline, must call
        self.emit_resize_event()
        
    def _toggle_sidebar(self,change): 
        """Pushes this instance of LiveSlides to sidebar and back inline."""
        # Only push to sidebar if not in fullscreen
        if self.btn_fs.value or self.sidebar_switch.value == 0:
            self.widgets.htmls.sidebar.value = '' # Should be empty to avoid competition of style
            self.height_slider.layout.display = 'inline-flex' #Very impprtant
        else:
            self.widgets.htmls.sidebar.value =  styles.sidebar_layout_css(span_percent=self.width_slider.value)
            self.height_slider.layout.display = 'none'

        return self.emit_resize_event() # Must return this event so it work in other functions.
