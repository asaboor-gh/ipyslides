"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

from contextlib import suppress
import os
from IPython.display import display, Image, Javascript
from IPython.utils.capture import capture_output
from ipywidgets import Layout

from ..formatters import fix_ipy_image, code_css
from ..extended_md import parse_xmd
from ..utils import set_dir, html, details, today
from . import scripts, intro, styles, _layout_css

class LayoutSettings:
    def __init__(self, _instanceSlides, _instanceWidgets):
        "Provide instance of LivSlides to work."
        self._slides = _instanceSlides
        self.widgets = _instanceWidgets
        self.font_scale = 1
        self._font_family = {'code':'var(--jp-code-font-family)','text':'STIX Two Text'}
        self._footer_text = 'IPySlides | <a style="color:skyblue;" href="https://github.com/massgh/ipyslides">github-link</a>'
        self._content_width = '90%' #Better
        self._breakpoint_width = f'{int(100*650/self.widgets.sliders.width.value)}px' # Whatever was set initially
        self._code_lineno = True
        self._slide_layout = Layout(height='auto',margin='auto',overflow='auto',padding='0.2em 2em')
        
        self.height_slider = self.widgets.sliders.height
        self.width_slider  = self.widgets.sliders.width
        self.scale_slider  = self.widgets.sliders.scale
        self.theme_dd = self.widgets.ddowns.theme
        self.reflow_check = self.widgets.checks.reflow
        
        self.btn_fs    = self.widgets.toggles.fscrn
        self.btn_zoom  = self.widgets.toggles.zoom
        self.btn_timer = self.widgets.toggles.timer
        self.box = self.widgets.panelbox
        self._on_load_and_refresh() # First attempt of Javascript to work
        
        self.widgets.buttons.toc.on_click(self._toggle_tocbox)
        self.theme_dd.observe(self._update_theme,names=['value'])
        self.scale_slider.observe(self.__set_font_scale,names=['value'])
        self.height_slider.observe(self.__update_size,names=['value'])
        self.width_slider.observe(self.__update_size,names=['value'])
        self.btn_fs.observe(self._push_fullscreen,names=['value'])
        self.btn_zoom.observe(self._push_zoom,names=['value'])
        self.reflow_check.observe(self._update_theme,names=['value'])
        self.sidebar_switch = self.widgets.toggles.display
        self.sidebar_switch.observe(self._toggle_sidebar,names=['value'])        
        self.sidebar_switch.value = False # Initial Call must be inline, so that things should be shown outside Jupyterlab always
        
        self._update_theme() #Trigger Theme and Javascript in it
        self.set_code_style() #Trigger CSS in it, must
        self.set_layout(center = True) # Trigger this as well
        
        
    def _on_load_and_refresh(self): # on_displayed is not working in in 8.0.0+
        self.__add_js()
        
        with capture_output() as cap:
            with suppress(BaseException): # When ipython is not running, avoid errors
                parse_xmd(intro.instructions,display_inline=True)
        # Only do this if it's in Jupyter, otherwise throws errors
        self.widgets.htmls.intro.value = details('\n'.join(o.data['text/html'] for o in cap.outputs), summary="Instructions").value
        self.widgets.htmls.intro.add_class('Intro')
        
    def set_animation(self, main = 'slide_h',frame = 'slide_v'):
        "Set animation for slides and frames. (2.0.8+)"
        if len(self._slides[:]) >= 1:
            self._slides[0]._set_overall_animation(main = main,frame = frame)
        else:
            raise ValueError("No slides yet to set animation.")
        
    def set_css(self,props_dict={}):
        """Set CSS for all slides. This loads on slides navigation, so you can include keyframes animations as well. 
        Individual slide's CSS will override this. (2.1.8+)  
        
        `props_dict` is a nested dict of css properties.      
        **Example:** 
        ```python
        props_dict ={
            'slide':{'background':'#000'}, # 'slide', '.slide' or '' is a special selector for the slide itself
            'p': {'color':'#fff', 'animation': '0.2sec animation_name'}, # content selector
            '@keyframe animation_name':{ 
                '0%': {'transform':'scale(0.5)'} 
                '100%': {'transform':'scale(1)'}
            }, 
            '@media screen and (max-width: 600px)': {
                'p': {'color':'#000'}
            }
        }
        ```          
        """
        if len(self._slides[:]) >= 1:
            self._slides[0]._set_overall_css(props_dict = props_dict)
        else:
            raise ValueError("No slides yet to set CSS.")
        
        
    def set_glassmorphic(self, image_src, opacity=0.75, blur_radius=50):
        "Adds glassmorphic effect to the background. `image_src` can be a url or a local image path. `opacity` and `blur_radius` are optional. (2.0.8+)"
        if not image_src:
            self.widgets.htmls.glass.value = '' # Hide glassmorphic
            return None
        
        if not os.path.isfile(image_src):
            raise FileNotFoundError(f'Image not found at {image_src!r}')
        
        self.widgets.htmls.glass.value = f"""<style>
        {_layout_css.glass_css(opacity=opacity, blur_radius=blur_radius)}
        </style>
        {self._slides.image(image_src,width='100%',zoomable=False)}
        <div class="Front"></div>
        """
            
    def set_code_style(self,style='default',color = None,background = None, hover_color = 'var(--tr-hover-bg)',lineno = True):
        "Set code style CSS. Use background for better view of your choice. This is overwritten by theme change."
        self._code_lineno = lineno # Used in theme to keep track 
        self.widgets.htmls.hilite.value = code_css(style,color = color,background = background, lineno = lineno, hover_color = hover_color)
      
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
            _text += f' | {today(color = "var(--secondary-fg)")}'
        if show_slideno: #Slide number should be replaced from __number__ 
            _text += '<b style="color:var(--accent-color);white-space:pre;">  __number__<b>'
        _text = f'<p style="white-space:nowrap;display:inline;"> {_text} </p>' # To avoid line break in footer
        
        self.widgets.htmls.footer.value = _text.replace('__number__',_number_str)
        
    def set_layout(self,center = True, content_width = None):
        "Central aligment of slide by default. If False, left-top aligned."
        self._content_width = content_width if content_width else self._content_width # user selected
        style_dict = {'display':'block','width':content_width} #block is must
        if center:
            style_dict.update(dict(margin = 'auto',align_items = 'center',justify_content = 'center'))
        else: #container still should be in the center horizontally with auto margin
            style_dict.update(dict(margin = '8px auto',align_items = 'baseline',justify_content = 'flex-start'))
        
        for k,v in style_dict.items():
            setattr(self._slide_layout,k,v)
        
        self._update_theme(change=None) # Trigger CSS in it to make width change
        
    def hide_navigation_gui(self):
        "Hide all navigation elements, but keyboard or touch still work."
        self.widgets.controls.layout.display = 'none'
        self.widgets.footerbox.layout.display = 'none'
    
    def show_navigation_gui(self):
        "Show all navigation elements."
        self.widgets.controls.layout.display = ''
        self.widgets.footerbox.layout.display = ''
            
    def __add_js(self):
        with self.widgets.outputs.fixed: 
            display(Javascript(scripts.navigation_js))
    
    def _emit_resize_event(self):
        self.widgets._exec_js(scripts.resize_js)
        
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
        text_size = '{}px'.format(int(self.font_scale*20))
        
        if self.theme_dd.value != 'Custom':
            theme_css =  styles.style_css(styles.theme_roots[self.theme_dd.value])
        else: # In case of Custom CSS
            with set_dir(self.widgets.assets_dir):
                if not os.path.isfile('custom.css'):
                    with open('custom.css','w') as f:
                        f.write('/* Author: Abdul Saboor */\n' + styles.style_css( styles.theme_roots['Light']))
                    self._slides.notify(f'File: {os.path.join(self._slides.assets_dir,"custom.css")!r} created. Edit it and change theme dropdown back and forth to see effect.',timeout=5)
                        
                # Read CSS from file now
                with open('custom.css','r') as f:
                    theme_css = ''.join(f.readlines())
        
        if 'Dark' in self.theme_dd.value:
            self.set_code_style('monokai',color='#f8f8f2',lineno=self._code_lineno)
            light = '120'
        elif self.theme_dd.value == 'Fancy':
            self.set_code_style('borland',lineno=self._code_lineno) 
            light = '230'
        else:
            self.set_code_style('default',lineno=self._code_lineno)
            light = '250'
            
        if self.theme_dd.value in ['Inherit', 'Custom']:
            light = '-' # Use Fallback colors, can't have idea which themes colors would be there
               
        # Replace font-size and breakpoint size
        theme_css = theme_css.replace(
                        '__text_size__',text_size).replace(
                        '__textfont__',self._font_family['text']).replace(
                        '__codefont__',self._font_family['code']).replace(
                        '__content_width__',self._content_width).replace(
                        '__breakpoint_width__', self._breakpoint_width).replace(
                        '__light__',light
                        )
        # Update Layout CSS
        layout_css = _layout_css.layout_css.replace('__breakpoint_width__', self._breakpoint_width)
        self.widgets.htmls.main.value = f'<style>\n{layout_css}\n</style>'
        
        # Update CSS
        if self.reflow_check.value:
            theme_css = theme_css + f"\n.SlideArea * {{max-height:max-content !important;}}\n"
            
        self.widgets.htmls.theme.value = f'<style>\n{theme_css}\n</style>'
        self._toggle_sidebar(change=None) #modify width of sidebar or display it inline, must call
        self._emit_resize_event()
        
    def _toggle_tocbox(self,btn):
        if self.widgets.tocbox.layout.display == 'none':
            self.widgets.tocbox.layout.display = 'unset'
            self.widgets.buttons.toc.description = '✕'
        else:
            self.widgets.tocbox.layout.display = 'none'
            self.widgets.buttons.toc.description = '\u2630'
        
    def _toggle_sidebar(self,change): 
        """Pushes this instance of Slides to sidebar and back inline."""
        # Only push to sidebar if not in fullscreen
        if self.btn_fs.value or self.sidebar_switch.value == False:
            self.widgets.mainbox.remove_class('SideMode')
            self.widgets.htmls.sidebar.value = '' # Should be empty to avoid competition of style
            self.height_slider.layout.display = 'inline-flex' #Very important
            self.sidebar_switch.description = '◨'
        else:
            self.widgets.mainbox.add_class('SideMode')
            self.widgets.htmls.sidebar.value =  html('style',_layout_css.sidebar_layout_css(span_percent=self.width_slider.value)).value
            self.height_slider.layout.display = 'none'
            self.sidebar_switch.description = '▣'
            
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
            if self.btn_zoom.value:
                self.btn_zoom.value = False # Unzoom to avoid jerks in display
                
        self.widgets.htmls.fscrn.value = html('style', _layout_css.fullscreen_css if self.btn_fs.value else '').value
        self._emit_resize_event() # Resize before waiting fo update-theme
        self._update_theme(change=None) # For updating size and breakpoints
    
    def _push_zoom(self,change):
        if self.btn_zoom.value:
            if self.btn_fs.value:
                self.btn_zoom.icon= 'toggle-on'
                self.widgets.htmls.zoom.value = f'<style>\n{_layout_css.zoom_hover_css}\n</style>'
            else:
                self.widgets._push_toast('Objects are only zoomable in Fullscreen mode!',timeout=2)
        else:
            self.btn_zoom.icon= 'toggle-off'
            self.widgets.htmls.zoom.value = ''
        
