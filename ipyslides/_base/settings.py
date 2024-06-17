"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

import math

from pathlib import Path
from inspect import signature
from IPython.display import Image

from ..formatters import fix_ipy_image, code_css
from ..xmd import parse
from ..utils import html, today, format_html, _sub_doc, _css_docstring
from . import intro, styles, _layout_css


class LayoutSettings:
    def __init__(self, _instanceSlides, _instanceWidgets):
        "Provide instance of LivSlides to work."
        self._slides = _instanceSlides
        self._widgets = _instanceWidgets
        self._custom_colors = {}
        self._font_family = {
            "code": "Cascadia Code",
            "text": "Roboto",
        }
        self._footer_kws = {
            "text": 'IPySlides | <a style="color:skyblue;" href="https://github.com/massgh/ipyslides">github-link</a>',
            "numbering": True,
            "date": "today",
        }
        
        self._layout = {'cwidth':100, 'scroll': True, 'centered': True, 'aspect': 16/9,'ncol_refs': 2}
        self._code_lineno = True
        self._bg_image = ""

        self.width_slider = self.widgets.sliders.width
        self.fontsize_slider = self.widgets.sliders.fontsize
        self.theme_dd = self.widgets.theme
        self.reflow_check = self.widgets.checks.reflow
        self.paste_check = self.widgets.checks.paste

        self.btn_window = self.widgets.toggles.window
        self.btn_fscreen = self.widgets.toggles.fscreen
        self.btn_zoom = self.widgets.toggles.zoom
        self.btn_laser = self.widgets.toggles.laser
        self.btn_draw = self.widgets.toggles.draw
        self.btn_menu = self.widgets.toggles.menu
        self.box = self.widgets.panelbox

        self.widgets.buttons.toc.on_click(self._toggle_tocbox)
        self.widgets.buttons.info.on_click(self._show_info)
        self.widgets.htmls.toast.observe(self._toast_on_value_change, names=["value"])
        self.theme_dd.observe(self._update_theme, names=["value"])
        self.fontsize_slider.observe(self._update_theme, names=["value"])
        self.width_slider.observe(self._update_size, names=["value"])
        self.btn_window.observe(self._toggle_viewport, names=["value"])
        self.btn_fscreen.observe(self._toggle_fullscreen, names=["value"])
        self.btn_fscreen.observe(self._on_icon_change, names=["icon"])
        self.btn_zoom.observe(self._push_zoom, names=["value"])
        self.btn_laser.observe(self._toggle_laser, names=["value"])
        self.reflow_check.observe(self._update_theme, names=["value"])
        self.paste_check.observe(self._toggle_paste_mode, names=["value"])
        self.btn_draw.observe(self._toggle_overlay, names=["value"])
        self.btn_menu.observe(self._toggle_menu, names = ["value"])
        self.widgets.checks.navgui.observe(self._toggle_nav_gui, names=["value"])
        self._update_theme(change = "aspect")  # Trigger Theme with aspect changed as well
        self.set_code_theme()  # Trigger CSS in it, must
        self.set_layout(center=True)  # Trigger this as well
        self._update_size(change=None)  # Trigger this as well
        self._toggle_paste_mode(change=None) # This should be enabled by default

    def _toggle_paste_mode(self, change):
        if self.paste_check.value:
            self._widgets.mainbox.add_class("PasteMode")
        else:
            self._widgets.mainbox.remove_class("PasteMode")

    def _close_quick_menu(self):
        "Need for actions on all buttons inside menu."
        if self.btn_menu.value:
            self.btn_menu.value = False
    
    def _toast_on_value_change(self, change):
        if change.new:
            if change.new == 'KSC': # Keyboard shortcute
                content = parse(intro.key_combs, returns = True)
                self.widgets._push_toast(content, timeout=15)

            self.widgets.htmls.toast.value = "" # Reset to make a new signal
    
    def _show_info(self, btn):
        self.widgets.iw.send({
            "content": format_html(intro.instructions).value,
            "timeout": 120000 # 2 minutes
        })

    @property
    def widgets(self):
        return self._widgets  # To avoid breaking code by user

    def _toggle_nav_gui(self, change):
        if change["new"]:  # It's checked then hide
            self.show_nav_gui(True)
        else:
            self.show_nav_gui(False)
    
    def set_toggles(self,
        nav_gui = True,
        reflow_content = False, 
        notes = False, 
        notifications = True, 
        proxy_buttons = True,
        auto_focus = True,
        ):
        for name, value in ({
            'navgui': nav_gui,
            'reflow': reflow_content,
            'notes': notes,
            'toast': notifications,
            'proxy': proxy_buttons,
            'focus': auto_focus,
        }).items():
            if (widget := getattr(self.widgets.checks,name, None)):
                widget.value = value # if condition for future additions check
        return self # for chaining set_methods

    def set_animation(self, main="slide_h", frame="appear"):
        "Set animation for slides and frames."
        if len(self._slides[:]) >= 1:
            self._slides[0]._set_overall_animation(main=main, frame=frame)
        else:
            raise RuntimeError("No slides yet to set animation.")
        return self # for chaining set_methods
    
    def set_theme(self, name:str):
        "Set prefered theme."
        themes = self.theme_dd.options
        if name not in themes:
            raise ValueError(f"name expect on the followings: {themes!r}")
        self.theme_dd.value = name 
        return self # for chaining set_methods

    @_sub_doc(colors=styles.theme_colors["Light"])
    def set_theme_colors(self, colors : dict):
        """Set theme colors. Only take effect when using custom theme.
        colors must be a dictionary with exactly like this:
        ```python
        {colors}
        ```
        """
        styles._validate_colors(colors)  # Validate colors before using and setting
        self._custom_colors = colors
        self.theme_dd.value = "Custom"  # Trigger theme update
        self._update_theme({'owner':self.theme_dd}) # This chnage is important to update layout theme as well
        return self # for chaining set_methods

    @_sub_doc(css_docstring=_css_docstring)
    def set_css(self, props: dict):
        """Set CSS for all slides. This loads on slides navigation, so you can include keyframes animations as well.
        Individual slide's CSS set by `slides[index].set_css` will override this.
        {css_docstring}
        """
        if len(self._slides[:]) >= 1:
            self._slides[0]._set_overall_css(props)
        else:
            raise RuntimeError("No slides yet to set CSS.")
        return self # for chaining set_methods

    def set_bg_image(self, src=None, opacity=0.25, filter='blur(2px)', contain = False):
        """Adds glassmorphic effect to the background with image. `src` can be a url or a local image path.
        Overall background will not be exported, but on each slides will be. This is to keep exported file size minimal.
        """
        if not src: 
            self.widgets.htmls.glass.value = ""  # clear
            self._bg_image = ""
            return

        self._bg_image = f"""
            <style>
                {_layout_css.glass_css(opacity= 1 - opacity, filter=filter, contain=contain)}
            </style>
            {self._slides.image(src,width='100%')}
            <div class="Front"></div>""" # opacity of layer would be opposite to supplied
        self.widgets.htmls.glass.value = self._bg_image
        return self # for chaining set_methods

    def set_code_theme(
        self,
        style="default",
        color=None,
        background=None,
        hover_color="var(--alternate-bg)",
        lineno=True,
    ):
        "Set code style CSS. Use background for better view of your choice. This is overwritten by theme change."
        self._code_lineno = lineno  # Used in theme to keep track
        self.widgets.htmls.hilite.value = code_css(
            style,
            color=color,
            background=background,
            lineno=lineno,
            hover_color=hover_color,
        )
        return self # for chaining set_methods

    def set_font_family(self, text=None, code=None):
        "Set main fonts for text and code."
        if text:
            self._font_family["text"] = text
        if code:
            self._font_family["code"] = code

        self._update_theme()  # Changes Finally
        return self # for chaining set_methods

    def set_font_size(self, value = 20, update_range=False):
        """Set font scale to increase or decrease text size. 1 is default. 
        You can update min/max if value is not in [8,64] interval by setting update_range = True"""
        if (not isinstance(value, int)) or (value < 1):
            raise TypeError("font size should be positive integer")
        
        if (value < self.fontsize_slider.min) or (value > self.fontsize_slider.max):
            if not update_range:
                raise ValueError(f"Given {value} is out of range. Use update_range = True to extend range as well")
            else:
                self.fontsize_slider.max = max(value, self.fontsize_slider.max)
                self.fontsize_slider.min = min(value, self.fontsize_slider.min)
        
        self.fontsize_slider.value = value
        return self # for chaining set_methods

    def set_logo(self, src, width=60, top=0, right=0):
        "`src` should be PNG/JPEG file name or SVG string or None. width, top, right can be given as int or in valid CSS units, e.g. '16px'."
        if not src: # give as None, '' etc
            self.widgets.htmls.logo.value = ''
            return None
        
        kwargs = {k:v for k,v in locals().items() if k not in ('self','src')}
        for k,v in kwargs.items():
            if isinstance(v, (int,float)):
                kwargs[k] = f"{v}px"
        
        if isinstance(src, Path):
            src = str(src)  # important for svg checking below
        
        if isinstance(src, str):
            if "<svg" in src and "</svg>" in src:
                image = src
            else:
                if src.startswith("clip:"):
                    src = self._slides.clips_dir / src[5:] # don't strip it
                image = fix_ipy_image( # Do not use big figure image syntax here, simple image only
                    Image(src, width=width), width=width
                ).value  
            self.widgets.htmls.logo.value = image 
            self.widgets.htmls.logo.layout = dict(**kwargs, height='max-content', margin='0 0 0 auto')
        return self # for chaining set_methods

    def set_footer(self, text="", numbering=True, date="today"):
        "Set footer text. `text` should be string. `date` should be 'today' or string of date. To skip date, set it to None or ''"
        self._footer_kws.update({"numbering": numbering, "date": date})
        if text is None or text == "":
            self._footer_kws["text"] = ""  # assign to text
        elif text and isinstance(text, str):
            self._footer_kws["text"] = text  # assign to text
        else:
            raise TypeError(f"text should be string or None, not {type(text)}")

        if self._slides._current:
            self._get_footer(
                self._slides._current, update_widget=True
            )  # Update footer immediately if slide there
        return self # for chaining set_methods

    def _get_footer(self, slide, update_widget=False):
        "Get footer text. `slide` is a slide object."
        if (type(slide).__name__ != "Slide") and (
            type(slide).__module__.split(".")[0] != "ipyslides"
        ):
            raise TypeError(f"slide should be Slide object, not {type(slide)}")

        text = self._footer_kws["text"]
        numbering = self._footer_kws["numbering"]
        date = self._footer_kws["date"]

        if any([text, date]):
            self._slides.widgets.navbox.add_class("Show")
        else:
            self._slides.widgets.navbox.remove_class("Show")

        if date:
            text += (
                " | " if text else ""
            ) + f'{today(fg = "var(--secondary-fg)") if date == "today" else date}'
        if numbering and update_widget:
            self._slides.widgets._snum.layout.display = ""
        else:
            self._slides.widgets._snum.layout.display = "none" # hide slide number

        text = f'<p style="white-space:nowrap;display:inline;margin-block:0;padding-left:0.7em;"> {text} </p>'  # To avoid line break in footer

        if update_widget:
            self.widgets.htmls.footer.value = text

        return text

    def set_layout(self, center=True, scroll=True, width=100, aspect = 16/9, ncol_refs = 2):
        """Aligment of slide is center-center by default. If center=False, top-center is applied. It becomes top-left if width=100.
        `ncol_refs` is used to determine number of columns in citations/footnotes
        """
        if (not isinstance(width, int)) or (width not in range(101)):
            raise ValueError("width should be int in range [0,100]")
        if not isinstance(aspect, (int,float)):
            raise TypeError("aspect should be int/float of ratio width/height.")
        self._layout = {'cwidth':width, 'scroll': scroll, 'centered': center, 'aspect': aspect, 'ncol_refs': ncol_refs}
        self._update_size(change = None) # will reset theme and send RESCALE message
        return self # for chaining set_methods

    def show_nav_gui(self, visible = True):
        """Show/Hide navigation GUI, keyboard still work. Hover on left-bottom corner to acess settings."""
        self.widgets.controls.layout.visibility = "visible" if visible else "hidden"
        self.widgets.checks.navgui.value = True if visible else False
        self.widgets.iw.msg_tojs = 'RESCALE' # sets padding etc

        if not visible:
            self._slides.notify("Navigation controls hidden. But keyboard is still working!")
        

    def _update_size(self, change):
        self.widgets.mainbox.layout.height = "{}vw".format(
            int(self.width_slider.value / self._layout["aspect"])
        )
        self.widgets.mainbox.layout.width = "{}vw".format(self.width_slider.value)
        self._update_theme(change="aspect")  # change aspect for Linked Output view too
        self.widgets.iw.msg_tojs = 'RESCALE'

    @property
    def text_size(self):
        "Text size in px."
        return f"{self.fontsize_slider.value}px"

    @property
    def colors(self):
        "Current theme colors."
        if self.theme_dd.value == "Custom":
            return self._custom_colors or styles.theme_colors["Inherit"]
        return styles.theme_colors[self.theme_dd.value]

    @property
    def light(self):
        "Lightness of theme. 20-255. NaN if theme is inherit or custom."
        self.set_code_theme("default", lineno=self._code_lineno) # in any case
        if self.theme_dd.value in ["Inherit", "Custom"]:
            return (
                math.nan
            )  # Use Fallback colors, can't have idea which themes colors would be there
        elif "Dark" in self.theme_dd.value:
            self.set_code_theme("monokai", color="#f8f8f2", lineno=self._code_lineno)
            return 120
        elif self.theme_dd.value == "Fancy":
            self.set_code_theme("borland", lineno=self._code_lineno)
            return 230
        else:
            return 250

    @property
    def theme_kws(self):
        return dict(
            colors=self.colors,
            light=self.light,
            text_size=self.text_size,
            text_font=self._font_family["text"],
            code_font=self._font_family["code"],
            **self._layout
        )

    def _update_theme(self, change=None):
        # Only update layout CSS if theme changes, not on each call
        if (change == "aspect") or (change and (change['owner'] == self.theme_dd)): # function called with owner without widget works too much
            self.widgets.htmls.main.value = html('style',
                _layout_css.layout_css(self.colors['accent_color'],self._layout['aspect'])
            ).value
        
        # Update Theme CSS
        theme_css = styles.style_css(**self.theme_kws)

        if self.reflow_check.value:
            theme_css = (
                theme_css + f"\n.SlideArea * {{max-height:max-content !important;}}\n"
            )

        self.widgets.htmls.theme.value = html("style", theme_css).value
        if self.widgets.checks.notes.value:
            self._slides.notes.display() # Update notes window if open
        
        if self.theme_dd.value == "Inherit":
            msg = "THEME:jupyterlab"
        else:
            msg = 'THEME:dark' if "Dark" in self.theme_dd.value else 'THEME:light'
        self.widgets.iw.msg_tojs = msg # changes theme of board

    def _toggle_tocbox(self, btn):
        if self.widgets.tocbox.layout.height == "0":
            self.widgets.tocbox.layout.height = f"min(calc(100% - 32px), {max(150, len(self.widgets.tocbox.children)*36)}px)"
            self.widgets.tocbox.layout.border = "1px solid var(--alternate-bg)"
            self.widgets.tocbox.layout.padding = "4px"
            self.widgets.buttons.toc.icon = "minus"
        else:
            self.widgets.tocbox.layout.height = "0"
            self.widgets.tocbox.layout.border = "none"
            self.widgets.tocbox.layout.padding = "0"
            self.widgets.buttons.toc.icon = "plus"

    def _toggle_viewport(self, change):
        self._push_zoom(change=None)  # Adjust zoom CSS for expected layout
        if self.btn_window.value:
            self.btn_window.icon = "minus"
            self.btn_window.tooltip = "Restore Viewport [V]"
            self.widgets.mainbox.add_class("FullWindow")  # to Full Window
            self.widgets.htmls.window.value = html(
                "style", _layout_css.viewport_css()
            ).value
        else:
            self.btn_window.icon = "plus"
            self.btn_window.tooltip = "Fill Viewport [V]"
            self.widgets.mainbox.remove_class("FullWindow")  # back to inline
            self.widgets.htmls.window.value = ""

        self._update_theme(change=None)  # For updating size zoom etc

    def _toggle_fullscreen(self, change):
        self.widgets.iw.msg_tojs = 'TFS' # goes to js, toggle fullscreen and chnage icon of button

    def _on_icon_change(self, change): # icon will changes when Javscript sends a message
        if change.new == 'minus':
            self._wsv = self.width_slider.value
            self.width_slider.value = 100
            self.widgets.mainbox.add_class('FullScreen')
            self.btn_fscreen.tooltip = "Exit Fullscreen [F]"
        else:
            if hasattr(self, '_wsv'):
                self.width_slider.value = self._wsv  # restore
            self.widgets.mainbox.remove_class('FullScreen')
            self.btn_fscreen.tooltip = "Enter Fullscreen [F]"
        
    def _toggle_laser(self, change):
        self.widgets.iw.msg_tojs = 'TLSR'
        if self.btn_laser.value:
            self.btn_laser.icon = "minus"
            self.btn_laser.tooltip = "Hide Laser Pointer [L]"
        else:
            self.btn_laser.icon = "plus"
            self.btn_laser.tooltip = "Show Laser Pointer [L]"

    def _push_zoom(self, change):
        if self.btn_zoom.value:
            self.btn_zoom.icon = "minus"
            self.btn_zoom.tooltip = "Disbale Zooming Items [Z]"
            self.widgets.htmls.zoom.value = f"<style>\n{_layout_css.zoom_hover_css()}\n</style>"

            # If at some point it may not work properly outside fullscreen use belowe
            # if self.btn_fscreen.value:
            #     self.widgets.htmls.zoom.value = f"<style>\n{_layout_css.zoom_hover_css()}\n</style>"
            # else:
            #     self.widgets.htmls.zoom.value = ""  # Clear zoom css immediately to avoid conflict
            #     self.widgets._push_toast("Objects are not zoomable in inline mode!", timeout=2)
        else:
            self.btn_zoom.icon = "plus"
            self.btn_zoom.tooltip = "Enable Zooming Items [Z]"
            self.widgets.htmls.zoom.value = ""

    def _toggle_overlay(self, change):
        if self.btn_draw.value:
            if self.theme_dd.value == "Inherit":
                self.widgets.iw.msg_tojs = "THEME:jupyterlab" # make like that

            self.btn_draw.icon = "minus"
            self.btn_draw.tooltip = "Close Drawing Panel"
            self.widgets.drawer.layout.height = "100%"
        else:
            self.btn_draw.icon = "plus"
            self.btn_draw.tooltip = "Open Drawing Panel"
            self.widgets.drawer.layout.height = "0"
            self.widgets.mainbox.focus() # it doesn't stay their otherwise

    def _toggle_menu(self, change):
        if self.btn_menu.value:
            self.btn_menu.icon = 'minus'
            self._hover_only = 'Hover-Only' in self.btn_menu._dom_classes
            self.btn_menu.remove_class('Hover-Only') # If navigation menu hidden by user
            self.widgets.quick_menu.layout.height = 'min(225px, calc(100% - 30px))'
            self.widgets.quick_menu.layout.border = "1px solid var(--alternate-bg)"
        else:
            self.btn_menu.icon = 'plus'
            self.widgets.quick_menu.layout.height = '0'
            self.widgets.quick_menu.layout.border = "none"

            if hasattr(self, '_hover_only') and self._hover_only:
                self.btn_menu.add_class('Hover-Only')

    def apply(self, **settings):
        """Apply multiple settings at once. Top level keys should be function names without 'set_' and 
        values should be dictionary of parameters to that function. For example:
        ```python
        Slides.settings.apply(
            layout = {"aspect":1.6, "scroll":False},
            footer = {0:"footer text", "numbering":True} # 0 key goes to first positional argument
        )
        ```
        """
        for key, kwargs in settings.items():
            func = getattr(self, f"set_{key}", None)
            if func is None:
                attrs = [a[4:] for a in dir(self) if a.startswith("set_")]
                raise AttributeError(f"Attribute {key!r} does not exists in settings!\nAllowed attributes are {attrs}.")
            else:
                if not isinstance(kwargs, dict):
                    raise TypeError(f"value of {key!r} should be a dictionary of paraemetrs!")
                
                for kw in kwargs:
                    if not isinstance(kw, (int, str)):
                        raise TypeError(f"key in value of {key!r} should be int (for args) or str (for kwargs), got {type(kw)}")
                
                args = sorted([v for k,v in kwargs.items() if isinstance(k, int)]) # positional args should be in order
                kwargs = {k:v for k,v in kwargs.items() if isinstance(k, str)} 
                params = {k:v.default for k,v in signature(func).parameters.items()} # has empty for no defualt

                if not set(kwargs).issubset(params):
                    raise ValueError(f"{key!r} accepts only following parameters {params}")
                
                func(*args, **kwargs) # apply function