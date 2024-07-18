"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""
import traitlets

from traitlets import HasTraits, Int, Unicode, Bool, Float, TraitError
from pathlib import Path
from inspect import Signature, Parameter
from IPython.display import Image, SVG
from ipywidgets.widgets.trait_types import InstanceDict

from ..formatters import pygments, fix_ipy_image, code_css
from ..xmd import parse
from ..utils import html, today
from . import intro, styles, _layout_css


class ConfigTraits(HasTraits):
    def _apply_change(self, change=None): raise NotImplementedError
        
    @traitlets.observe(traitlets.All)
    def _observe(self, change):
        self._apply_change(change)

    @property
    def props(self): return self.trait_values()

    @property
    def main(self): return Settings._instance

    def __repr__(self): 
        r = ", ".join(f"{k}={repr(v) if isinstance(v,str) else v.__class__.__name__ if isinstance(v, ConfigTraits) else  v}" for k,v in self.props.items())
        return f'{self.__class__.__name__}({r})'

    def _set_props(self, **kwargs):
        self.unobserve_all()
        try:
            for key, value in kwargs.items():
                if not self.has_trait(key):
                    raise TraitError(f"trait {key!r} does not exits!")
                self.set_trait(key, value)
            self._apply_change(None)
        finally:
            self.observe(self._observe, names=traitlets.All)
        return self.main # For method chaining
    
def fix_sig(cls):
    parameters=[Parameter('self', Parameter.POSITIONAL_ONLY), 
        *[Parameter(key, Parameter.POSITIONAL_OR_KEYWORD, default=value.default_value) for key,value in cls.class_traits().items()]]
    def set_props(self, **kwargs): return cls._set_props(self, **kwargs) 
    cls.__call__ = set_props # need new function each time
    cls.__call__.__signature__ = Signature(parameters) # can only be set over class level
    return cls

@fix_sig
class Colors(ConfigTraits):
    "Set theme colors. This changes theme to Custom. Each name will be changed to a CSS vairiable as --[name]-color"
    fg1 = Unicode('black')
    fg2 = Unicode('#454545')
    fg3 = Unicode('#00004d')
    bg1 = Unicode('white')
    bg2 = Unicode('whitesmoke')
    bg3 = Unicode('#e8e8e8')
    accent  = Unicode('#005090')
    pointer = Unicode('red')

    def _apply_change(self, change): 
        if change: # Don't at None
            self.main._widgets.theme.value = "Custom"  # Trigger theme update
            self.main._update_theme({'owner':self.main._widgets.theme}) # This chnage is important to update layout theme as well

@fix_sig
class StylePerTheme(ConfigTraits):
    "Pygment code block style for each theme. You mostly need to change for custom and inherit theme."
    inherit = Unicode('default')
    custom  = Unicode('default')
    light   = Unicode('friendly')
    dark    = Unicode('native')
    material_light = Unicode('perldoc')
    material_dark = Unicode('one-dark')

    def _apply_change(self, change): 
        if change and change.new in pygments.styles.get_all_styles(): # go there safely
            self.main._widgets.theme.value = change.name.replace('_',' ').title()
        self.main.code._apply_change(None) # works as validator too, run anyway
    
    def reset(self):
        "Reset all user set code block styles."
        with self.hold_trait_notifications():
            for key, value in zip(
                'inherit custom light dark material_light material_dark'.split(),
                'default default friendly native perldoc one-dark'.split()
                ):
                self.set_trait(key, value)
            self._apply_change(None)

@fix_sig
class Code(ConfigTraits):
    "Set code block styles. background and color may be needed for some styles."
    style_per_theme = InstanceDict(StylePerTheme, help="A pygment style for each theme.")
    color       = Unicode(allow_none=True)
    background  = Unicode('var(--bg2-color)', allow_none=True) # Some themes don't have it
    hover_color = Unicode("var(--bg3-color)")
    lineno      = Bool(True)

    def _apply_change(self, change): # need to set somewhere
        kwargs = {k:v for k,v in self.props.items() if k != 'style_per_theme'}
        kwargs['style'] = getattr(self.style_per_theme, self.main._widgets.theme.value.lower().replace(' ','_'))
        self.main._widgets.htmls.hilite.value = code_css(**kwargs)

@fix_sig
class Theme(ConfigTraits):
    "Set theme value. colors and code have their own nested traits."
    value  = Unicode('Inherit')
    colors = InstanceDict(Colors)

    def _apply_change(self, change):
        self.main._update_theme() # otherwise colors don't apply

    @traitlets.validate('value')
    def _value(self, proposal):
        themes = self.main._widgets.theme.options
        if proposal["value"] not in themes:
            raise ValueError(f"Theme value expect on the followings: {themes!r}")
        self.main._widgets.theme.value = proposal["value"] # It will update theme itself
        return proposal["value"]  

@fix_sig
class Fonts(ConfigTraits):
    "Set fonts of text and code and size."
    text = Unicode("Roboto", allow_none=True)
    code = Unicode("Cascadia Code", allow_none=True)
    size = Int(20, help="Can use any large/small value that CSS supports!")

    def _apply_change(self, change):
        self.main._update_theme()

    @traitlets.validate('text','code')
    def _fix_font(self, proposal):
        return ", ".join(repr(t.strip().strip('\"').strip("\'")) for t in proposal["value"].split(','))
    
    @traitlets.validate('size')
    def _change_slider_values(self, proposal):
        value, slider = proposal["value"], self.main._widgets.sliders.fontsize
        slider.max = max(value, min(64, slider.max))
        slider.min = min(value, max(8,slider.min))
        slider.value = value # Keep values in default [8,64] range when possible
        return value 

@fix_sig    
class Footer(ConfigTraits):
    "Set footer attributes of slides."
    text = Unicode('IPySlides | <a style="color:skyblue;" href="https://github.com/massgh/ipyslides">github-link</a>')
    numbering = Bool(True)
    date = Unicode("today", allow_none=True)

    def _apply_change(self,change):
        if self.main._slides._current:
            self.main._get_footer(self.main._slides._current, update_widget=True)

@fix_sig
class Layout(ConfigTraits):
    "Set layout of slides."
    centered = Bool(True)
    scroll   = Bool(True)
    width    = Int(100)
    aspect   = Float(16/9)
    ncol_refs = Int(2)

    @traitlets.validate('width')
    def _limit_width(self, proposal):
        if not proposal["value"] in range(101):
            raise ValueError("width should in range [0,100]")
        return proposal["value"]
  
    def _apply_change(self, change):
        self.main._update_size(change = None) # will reset theme and send RESCALE message

@fix_sig
class Toggle(ConfigTraits):
    "Toggle ON/OFF checks in settings panel."
    navgui = Bool(True) 
    reflow = Bool(False)
    notes  = Bool(False)
    toast  = Bool(True)
    focus  = Bool(True)
    paste  = Bool(True)

    def _apply_change(self, change):
        if change and (widget := getattr(self.main._widgets.checks, change.name, None)):
            widget.value = change.new

@fix_sig
class Logo(ConfigTraits):
    "Set logo for all slides."
    src   = Unicode(allow_none=True)
    width = traitlets.Union([Unicode('60px'), Int(), Float()])
    top   = traitlets.Union([Unicode('4px'), Int(), Float()])
    right = traitlets.Union([Unicode('4px'), Int(), Float()])

    @traitlets.validate('src')
    def _fix_path(self, proposal):
        if isinstance(proposal["value"], Path):
            return str(Path)
        return proposal["value"]
    
    @traitlets.validate('width','top','right')
    def _fix_number(self, proposal):
        if isinstance(proposal["value"], (int, float)):
            return f'{proposal["value"]}px'
        return proposal["value"]
    
    def _apply_change(self,change):
        if not self.src: # give as None, '' etc
            self.main._widgets.htmls.logo.value = ''
        elif (image := self.main._resolve_img(self.src, self.width)):
            self.main._widgets.htmls.logo.value = image 
            self.main._widgets.htmls.logo.layout = dict(**{k:v for k,v in self.props.items() if k !='src'}, height='max-content', margin='0 0 0 auto')
        

class Settings:
    """
    Apply settings to slides programatically. Fewer settings are available as widgets.

    Settings can be nested or individual attributes as set as well. For example:
    ```python
    Slides.settings(layout = {"aspect": 16/10}) # Top 
    Slides.settings.layout(aspect = 16/10) # Individual
    Slides.settings.layout.aspect = 16/10  # Attribute
    ```
    All settings calls including top level returns settings instance to apply method chaining.
    e.g. `Slides.settings.layout(aspect = 16/10).footer(text="ABC").logo(...)`.
    """
    _instance = None
    def __init__(self, _instanceSlides, _instanceWidgets):
        self._slides = _instanceSlides
        self._widgets = _instanceWidgets
        self.__class__._instance = self # After _widgets, _slides to enable access
        self.code   = Code()
        self.theme  = Theme() # Don't set colors yet
        self.fonts  = Fonts()
        self.footer = Footer()
        self.layout = Layout()
        self.toggle = Toggle()
        self.logo   = Logo()
        
        self._wslider = self._widgets.sliders.width # Used in multiple places
        self._tgl_fscreen = self._widgets.toggles.fscreen
        self._tgl_menu = self._widgets.toggles.menu

        self._widgets.sliders.fontsize.observe(lambda c: self.fonts(size=c.new), names=["value"])
        self._widgets.theme.observe(self._update_theme, names=["value"])
        self._widgets.checks.reflow.observe(self._update_theme, names=["value"])
        self._widgets.checks.paste.observe(self._toggle_paste_mode, names=["value"])
        self._widgets.buttons.toc.on_click(self._toggle_tocbox)
        self._widgets.buttons.info.on_click(self._show_info)
        self._widgets.htmls.toast.observe(self._toast_on_value_change, names=["value"])
        self._wslider.observe(self._update_size, names=["value"])
        self._widgets.toggles.window.observe(self._toggle_viewport, names=["value"])
        self._tgl_fscreen.observe(self._toggle_fullscreen, names=["value"])
        self._tgl_fscreen.observe(self._on_icon_change, names=["icon"])
        self._widgets.toggles.zoom.observe(self._push_zoom, names=["value"])
        self._widgets.toggles.laser.observe(self._toggle_laser, names=["value"])
        self._widgets.toggles.draw.observe(self._toggle_overlay, names=["value"])
        self._tgl_menu.observe(self._toggle_menu, names = ["value"])
        self._widgets.checks.navgui.observe(self._toggle_nav_gui, names=["value"])
        self._update_theme({'owner':'layout'})  # Trigger Theme with aspect changed as well
        self._update_size(change=None)  # Trigger this as well
        self._toggle_paste_mode(change=None) # This should be enabled by default

        self._traits = [key for key, value in self.__dict__.items() if isinstance(value, ConfigTraits)]
        parameters=[Parameter('self', Parameter.POSITIONAL_ONLY), 
        *[Parameter(key, Parameter.POSITIONAL_OR_KEYWORD, default=None) for key in self._traits]]
        type(self).__call__.__signature__ = Signature(parameters) # can only be set over class level

    def __call__(self, **kwargs):
        "Apply many settings at once! Can apply individual traits in a setting with assignment as well."
        for key, value in kwargs.items():
            if not key in self._traits:
                raise AttributeError(f"Settings has not trait attribute {key!r}")
            if value and not isinstance(value, dict):
                raise TypeError(f"{key} expects a dict, got {type(value)}")
            getattr(self, key)(**value)
        return self # For chaining

    def __setattr__(self, name: str, value):
        if not name.startswith('_') and hasattr(self, name):
            raise AttributeError(f"Can't reset attribute {name!r} on {self!r}")
        self.__dict__[name] = value

    def _toggle_paste_mode(self, change):
        if self._widgets.checks.paste.value:
            self._widgets.mainbox.add_class("PasteMode")
        else:
            self._widgets.mainbox.remove_class("PasteMode")

    def _close_quick_menu(self):
        if self._tgl_menu.value:
            self._tgl_menu.value = False
    
    def _toast_on_value_change(self, change):
        if change.new:
            if change.new == 'KSC': # Keyboard shortcute
                content = parse(intro.key_combs, returns = True)
                self._widgets._push_toast(content, timeout=15)

            self._widgets.htmls.toast.value = "" # Reset to make a new signal
    
    def _show_info(self, btn):
        self._widgets.iw.send({
            "content": html('',[intro.instructions]).value,
            "timeout": 120000 # 2 minutes
        })

    def _toggle_nav_gui(self, change):
        visible = change.new
        self._widgets.controls.layout.visibility = "visible" if visible else "hidden"
        self._widgets.iw.msg_tojs = 'RESCALE' # sets padding etc

        if not visible:
            self._slides.notify("Navigation controls hidden. But keyboard is still working!")
    
    def _resolve_img(self, src, width):
        if isinstance(src, Path):
            src = str(src)  # important for svg checking below
        
        if isinstance(src, str):
            if "<svg" in src and "</svg>" in src:
                return src.replace('<svg', f'<svg style="width:{width};height:auto" ') # extra space at end
            else:
                if src.startswith("clip:"):
                    src = self._slides.clips_dir / src[5:] # don't strip it
                try:
                    return fix_ipy_image(Image(src, width=width), width=width).value
                except:
                    return self._resolve_img(SVG(src)._repr_svg_(), width=width)
        return ''

    def _get_footer(self, slide, update_widget=False):
        "Get footer text. `slide` is a slide object."
        if (type(slide).__name__ != "Slide") and (
            type(slide).__module__.split(".")[0] != "ipyslides"
        ):
            raise TypeError(f"slide should be Slide object, not {type(slide)}")

        text, numbering, date = self.footer.text, self.footer.numbering, self.footer.date

        if any([text, date]):
            self._slides._box.add_class("ShowFooter")
        else:
            self._slides._box.remove_class("ShowFooter")

        if date:
            text += (
                " | " if text else ""
            ) + f'{today(fg = "var(--fg2-color)") if date == "today" else date}'
        
        if numbering and update_widget:
            self._slides.widgets._snum.layout.display = ""
        else:
            self._slides.widgets._snum.layout.display = "none" # hide slide number

        text = f'<p style="white-space:nowrap;display:inline;margin-block:0;padding-left:8px;"> {text} </p>'  # To avoid line break in footer

        if update_widget:
            self._widgets.htmls.footer.value = text

        return text

    def _update_size(self, change):
        self._widgets.mainbox.layout.height = "{}vw".format(
            int(self._wslider.value / self.layout.aspect)
        )
        self._widgets.mainbox.layout.width = "{}vw".format(self._wslider.value)
        self._update_theme({'owner':'layout'})  # change aspect for Linked Output view too
        self._widgets.iw.msg_tojs = 'RESCALE'

    @property
    def _colors(self):
        if self._widgets.theme.value == "Custom" and hasattr(self, 'theme'): # May not be there yet
            return self.theme.colors.props
        return styles.theme_colors[self._widgets.theme.value]

    @property
    def _theme_kws(self):
        return dict(
            colors=self._colors,
            text_size= f"{self.fonts.size}px",
            text_font=self.fonts.text,
            code_font=self.fonts.code,
            **self.layout.props
        )

    def _update_theme(self, change=None):
        # Only update layout CSS if theme changes, not on each call
        if change and change['owner'] in ('layout',self._widgets.theme): # function called with owner without widget works too much
            self._widgets.htmls.main.value = html('style',
                _layout_css.layout_css(self._colors['accent'],self.layout.aspect)
            ).value
        
        theme_css = styles.style_css(**self._theme_kws)

        if self._widgets.checks.reflow.value:
            theme_css = (
                theme_css + f"\n.SlideArea * {{max-height:max-content !important;}}\n"
            )

        self._widgets.htmls.theme.value = html("style", theme_css).value
        if self._widgets.checks.notes.value:
            self._slides.notes.display() # Update notes window if open
        
        self._widgets.sync_jupyter_colors() # Will enable/disable a button
        
        if self._widgets.theme.value == "Inherit":
            msg = "THEME:jupyterlab"
        else:
            msg = 'THEME:dark' if "Dark" in self._widgets.theme.value else 'THEME:light'
        self._widgets.iw.msg_tojs = msg # changes theme of board
        self.code._apply_change(None) # Update code theme


    def _toggle_tocbox(self, btn):
        if self._widgets.tocbox.layout.height == "0":
            self._widgets.tocbox.layout.height = f"min(calc(100% - 32px), {max(150, len(self._widgets.tocbox.children)*36)}px)"
            self._widgets.tocbox.layout.border = "1px solid var(--bg3-color)"
            self._widgets.tocbox.layout.padding = "4px"
            self._widgets.buttons.toc.icon = "minus"
        else:
            self._widgets.tocbox.layout.height = "0"
            self._widgets.tocbox.layout.border = "none"
            self._widgets.tocbox.layout.padding = "0"
            self._widgets.buttons.toc.icon = "plus"

    def _toggle_viewport(self, change):
        self._push_zoom(change=None)  # Adjust zoom CSS for expected layout
        tgl = self._widgets.toggles.window
        if tgl.value:
            tgl.icon = "minus"
            tgl.tooltip = "Restore Viewport [V]"
            self._widgets.mainbox.add_class("FullWindow")  # to Full Window
            self._widgets.htmls.window.value = html(
                "style", _layout_css.viewport_css()
            ).value
        else:
            tgl.icon = "plus"
            tgl.tooltip = "Fill Viewport [V]"
            self._widgets.mainbox.remove_class("FullWindow")  # back to inline
            self._widgets.htmls.window.value = ""

        self._update_theme(change=None)  # For updating size zoom etc

    def _toggle_fullscreen(self, change):
        self._widgets.iw.msg_tojs = 'TFS' # goes to js, toggle fullscreen and chnage icon of button

    def _on_icon_change(self, change): # icon will changes when Javscript sends a message
        if change.new == 'minus':
            self._wsv = self._wslider.value
            self._wslider.value = 100
            self._widgets.mainbox.add_class('FullScreen')
            self._tgl_fscreen.tooltip = "Exit Fullscreen [F]"
        else:
            if hasattr(self, '_wsv'):
                self._wslider.value = self._wsv  # restore
            self._widgets.mainbox.remove_class('FullScreen')
            self._tgl_fscreen.tooltip = "Enter Fullscreen [F]"
        
    def _toggle_laser(self, change):
        self._widgets.iw.msg_tojs = 'TLSR'
        tgl = self._widgets.toggles.laser
        if tgl.value:
            tgl.icon = "minus"
            tgl.tooltip = "Hide Laser Pointer [L]"
        else:
            tgl.icon = "plus"
            tgl.tooltip = "Show Laser Pointer [L]"

    def _push_zoom(self, change):
        tgl = self._widgets.toggles.zoom
        if tgl.value:
            tgl.icon = "minus"
            tgl.tooltip = "Disbale Zooming Items [Z]"
            self._widgets.htmls.zoom.value = f"<style>\n{_layout_css.zoom_hover_css()}\n</style>"

            # If at some point it may not work properly outside fullscreen use belowe
            # if self._tgl_fscreen.value:
            #     self._widgets.htmls.zoom.value = f"<style>\n{_layout_css.zoom_hover_css()}\n</style>"
            # else:
            #     self._widgets.htmls.zoom.value = ""  # Clear zoom css immediately to avoid conflict
            #     self._widgets._push_toast("Objects are not zoomable in inline mode!", timeout=2)
        else:
            tgl.icon = "plus"
            tgl.tooltip = "Enable Zooming Items [Z]"
            self._widgets.htmls.zoom.value = ""

    def _toggle_overlay(self, change):
        tgl = self._widgets.toggles.draw
        if tgl.value:
            if self._widgets.theme.value == "Inherit":
                self._widgets.iw.msg_tojs = "THEME:jupyterlab" # make like that

            tgl.icon = "minus"
            tgl.tooltip = "Close Drawing Panel"
            self._widgets.drawer.layout.height = "100%"
        else:
            tgl.icon = "plus"
            tgl.tooltip = "Open Drawing Panel"
            self._widgets.drawer.layout.height = "0"
            self._widgets.mainbox.focus() # it doesn't stay their otherwise

    def _toggle_menu(self, change):
        if self._tgl_menu.value:
            self._tgl_menu.icon = 'minus'
            self._hover_only = 'Hover-Only' in self._tgl_menu._dom_classes
            self._tgl_menu.remove_class('Hover-Only') # If navigation menu hidden by user
            self._widgets.quick_menu.layout.height = 'min(225px, calc(100% - 30px))'
            self._widgets.quick_menu.layout.border = "1px solid var(--bg3-color)"
        else:
            self._tgl_menu.icon = 'plus'
            self._widgets.quick_menu.layout.height = '0'
            self._widgets.quick_menu.layout.border = "none"

            if hasattr(self, '_hover_only') and self._hover_only:
                self._tgl_menu.add_class('Hover-Only')