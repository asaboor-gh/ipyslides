"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

from contextlib import suppress
import os
import math
from IPython import get_ipython
from IPython.display import Image
from IPython.utils.capture import capture_output

from ..formatters import fix_ipy_image, code_css
from ..xmd import parse
from ..utils import html, today, _sub_doc, _css_docstring
from . import intro, styles, _layout_css


class LayoutSettings:
    def __init__(self, _instanceSlides, _instanceWidgets):
        "Provide instance of LivSlides to work."
        self._slides = _instanceSlides
        self._widgets = _instanceWidgets
        self._custom_colors = {}
        self._font_family = {
            "code": "var(--jp-code-font-family)",
            "text": "STIX Two Text",
        }
        self._footer_kws = {
            "text": 'IPySlides | <a style="color:skyblue;" href="https://github.com/massgh/ipyslides">github-link</a>',
            "numbering": True,
            "date": "today",
        }
        self._content_width = "90%"  # Better
        self._centered = True
        self._code_lineno = True

        self.width_slider = self.widgets.sliders.width
        self.aspect_dd = self.widgets.ddowns.aspect
        self.scale_slider = self.widgets.sliders.scale
        self.theme_dd = self.widgets.ddowns.theme
        self.reflow_check = self.widgets.checks.reflow

        self.btn_window = self.widgets.toggles.window
        self.btn_fscreen = self.widgets.toggles.fscreen
        self.btn_zoom = self.widgets.toggles.zoom
        self.btn_laser = self.widgets.toggles.laser
        self.btn_overlay = self.widgets.toggles.overlay
        self.box = self.widgets.panelbox
        self._setup()  # Fix up and start up things

        self.widgets.buttons.toc.on_click(self._toggle_tocbox)
        self.widgets.buttons._inview.on_click(self.__block_post_run)
        self.widgets.htmls.toast.observe(self._toast_on_value_change, names=["value"])
        self.theme_dd.observe(self._update_theme, names=["value"])
        self.scale_slider.observe(self._update_theme, names=["value"])
        self.aspect_dd.observe(self._update_size, names=["value"])
        self.width_slider.observe(self._update_size, names=["value"])
        self.btn_window.observe(self._toggle_viewport, names=["value"])
        self.btn_fscreen.observe(self._toggle_fullscreen, names=["value"])
        self.btn_fscreen.observe(self._on_icon_change, names=["icon"])
        self.btn_zoom.observe(self._push_zoom, names=["value"])
        self.btn_laser.observe(self._toggle_laser, names=["value"])
        self.reflow_check.observe(self._update_theme, names=["value"])
        self.btn_overlay.observe(self._toggle_overlay, names=["value"])
        self.widgets.checks.postrun.observe(self._set_show_always, names=["value"])
        self.widgets.checks.navgui.observe(self._toggle_nav_gui, names=["value"])
        self.widgets.checks.proxy.observe(self._toggle_proxy_buttons, names=["value"])
        self._update_theme()  # Trigger Theme and Javascript in it
        self.set_code_style()  # Trigger CSS in it, must
        self.set_layout(center=True)  # Trigger this as well
        self._update_size(change=None)  # Trigger this as well

    def __block_post_run(self, btn):
        self.widgets.checks.postrun.value = False  # Uncheck it
        self.widgets.checks.postrun.disabled = True  # Disable it
        self.widgets.navbox.children = [
            w for w in self.widgets.navbox.children if w is not btn
        ]
        dh = getattr(self._slides._display_box, "_DH", None)  # Get display handler
        self._slides._display_box = self._slides.alert("Slides → Linked Output View").as_widget()  # Swap display box by info, still widget to be closable
        if dh is not None:
            dh.update(self._slides._display_box) 
    
    def _toast_on_value_change(self, change):
        if change.new:
            if change.new == 'KSC': # Keyboard shortcute
                content = parse(intro.key_combs, display_inline=False)
                self.widgets._push_toast(content, timeout=15)

            self.widgets.htmls.toast.value = "" # Reset to make a new signal

    def _setup(self): 
        # Only add this if in notebook, not in terminal
        shell = get_ipython()
        if shell and shell.__class__.__name__ != "TerminalInteractiveShell":
            with capture_output() as cap:
                with suppress(BaseException):
                    parse(intro.instructions, display_inline=True)

            self.widgets.htmls.intro.value = "\n".join(o.data.get("text/html", "") for o in cap.outputs)
            self.widgets.htmls.intro.add_class("Intro")

    @property
    def widgets(self):
        return self._widgets  # To avoid breaking code by user

    @property
    def breakpoint(self):
        span = 100 if self.btn_window.value else self.width_slider.value
        return f"{int(100*650/span)}px"

    def set(self, **kwargs):
        """Add multiple settings at once. keys in kwargs should be name of a function after `Slides.settings.set_`
        and values should be dictionary or tuple of arguments for that function. See examples below.
        ```python
        Slides.settings.set(
            glassmorphic = dict(image_src='image_src'),
            css = ({},), # note trailing comma to make it tuple
            layout = dict(center=True, content_width='80%'),
        )
        ```
        """
        for k, v in kwargs.items():
            if not isinstance(v, (dict, tuple)):
                raise TypeError(f"values in kwargs should be dict or tuple, got {v!r}")
            func = getattr(self, f"set_{k}", False)
            if func is False:
                raise AttributeError(f"No such function {k!r} in settings")
            func(**v) if isinstance(v, dict) else func(
                *v
            )  # Call function with arguments

    def show_always(self, b: bool = True):
        """If True (default), slides are shown after each cell execution where a slide constructor is present (other view will be closed).
        Otherwise only when `slides.show()` is called or `slides` is the last line in a cell.
        :::note
            In JupyterLab, right click on the slides and select `Create New View for Output` and follow next step there to optimize display.
        """
        if not isinstance(b, bool):
            raise TypeError(f"Expected bool, got {b!r}")
        self._slides._post_run_enabled = (
            True if b else False
        )  # Do not rely on user if they really give bool or not

    def _set_show_always(self, change):
        if change["new"]:
            self.show_always(True)
            self._slides.notify("Post run cell enabled!")
        else:
            self.show_always(False)
            self._slides.notify("Post run cell disabled!")

    def _toggle_nav_gui(self, change):
        if change["new"]:  # It's checked then hide
            self.hide_navigation_gui()
        else:
            self.show_navigation_gui()

    def _toggle_proxy_buttons(self, change):
        if change["new"]:
            self.widgets.mainbox.remove_class("PresentMode")  # Show if checked
        else:
            self.widgets.mainbox.add_class("PresentMode")

    def set_animation(self, main="slide_h", frame="slide_v"):
        "Set animation for slides and frames."
        if len(self._slides[:]) >= 1:
            self._slides[0]._set_overall_animation(main=main, frame=frame)
        else:
            raise RuntimeError("No slides yet to set animation.")

    @_sub_doc(colors=styles.theme_colors["Light"])
    def set_theme_colors(self, colors={}):
        """Set theme colors. Only take effect when using custom theme.
        colors must be a dictionary with exactly like this:
        ```python
        Slides.settings.set_theme_colors({colors})
        ```
        """
        styles._validate_colors(self._custom_colors)  # Validate colors before using
        self._custom_colors = colors
        self.theme_dd.value = "Custom"  # Trigger theme update
        self._update_theme()

    @_sub_doc(css_docstring=_css_docstring)
    def set_css(self, css_dict={}):
        """Set CSS for all slides. This loads on slides navigation, so you can include keyframes animations as well.
        Individual slide's CSS set by `slides[index].set_css` will override this.
        {css_docstring}
        """
        if len(self._slides[:]) >= 1:
            self._slides[0]._set_overall_css(css_dict=css_dict)
        else:
            raise RuntimeError("No slides yet to set CSS.")

    def set_citation_mode(self, mode="global"):
        "Set mode for citations form ['global', 'inline', 'footnote']."
        if mode not in ["global", "inline", "footnote"]:
            raise ValueError(
                f'citation mode must be one of "global", "inline", "footnote" but got {mode}'
            )
        self._slides._citation_mode = mode

    def set_glassmorphic(self, image_src, opacity=0.85, blur_radius=50):
        "Adds glassmorphic effect to the background. `image_src` can be a url or a local image path. `opacity` and `blur_radius` are optional."
        if not image_src:
            self.widgets.htmls.glass.value = ""  # Hide glassmorphic
            return None

        if not os.path.isfile(image_src):
            raise FileNotFoundError(f"Image not found at {image_src!r}")

        self.widgets.htmls.glass.value = f"""<style>
        {_layout_css.glass_css(opacity=opacity, blur_radius=blur_radius)}
        </style>
        {self._slides.image(image_src,width='100%')}
        <div class="Front"></div>
        """

    def set_code_style(
        self,
        style="default",
        color=None,
        background=None,
        hover_color="var(--hover-bg)",
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

    def set_font_family(self, text_font=None, code_font=None):
        "Set main fonts for text and code."
        if text_font:
            self._font_family["text"] = text_font
        if code_font:
            self._font_family["code"] = code_font

        self._update_theme()  # Changes Finally

    def set_font_scale(self, font_scale=1):
        "Set font scale to increase or decrease text size. 1 is default."
        self.scale_slider.value = font_scale

    def set_logo(self, src, width=80, top=0, right=0):
        "`src` should be PNG/JPEG file name or SVG string. width, top, right can be given as int or in valid CSS units, e.g. '16px'."
        kwargs = {k:v for k,v in locals().items() if k not in ('self','src')}
        for k,v in kwargs.items():
            if isinstance(v, (int,float)):
                kwargs[k] = f"{v}px"

        if isinstance(src, str):
            if "<svg" in src and "</svg>" in src:
                image = src
            else:
                image = fix_ipy_image(
                    Image(src, width=width), width=width
                ).value  
            self.widgets.htmls.logo.layout = dict(**kwargs, height='max-content')
            self.widgets.htmls.logo.value = image 

    def set_footer(self, text="", numbering=True, date="today"):
        "Set footer text. `text` should be string. `date` should be 'today' or string of date. To skip date, set it to None or ''"
        self._footer_kws.update({"numbering": numbering, "date": date})
        if text is None or text == "":
            self._footer_kws["text"] = ""  # assign to text
        elif text and isinstance(text, str):
            self._footer_kws["text"] = text  # assign to text
        else:
            raise TypeError(f"text should be string or None, not {type(text)}")

        if self._slides.current:
            self.get_footer(
                self._slides.current, update_widget=True
            )  # Update footer immediately if slide there

    def get_footer(self, slide, update_widget=False):
        "Get footer text. `slide` is a slide object."
        if (type(slide).__name__ != "Slide") and (
            type(slide).__module__.split(".")[0] != "ipyslides"
        ):
            raise TypeError(f"slide should be Slide object, not {type(slide)}")

        number = (
            f"{slide.label} / {self._slides._nslides}" if slide.label != "0" else ""
        )
        text = self._footer_kws["text"]
        numbering = self._footer_kws["numbering"]
        date = self._footer_kws["date"]

        if date:
            text += (
                " | " if text else ""
            ) + f'{today(fg = "var(--secondary-fg)") if date == "today" else date}'
        if numbering:
            text += (
                f'<b style="color:var(--accent-color);white-space:pre;">  {number}</b>'
            )
        text = f'<p style="white-space:nowrap;display:inline;"> {text} </p>'  # To avoid line break in footer

        if update_widget:
            self.widgets.htmls.footer.value = text

        return text

    def set_layout(self, center=True, content_width=None):
        "Central aligment of slide by default. If False, left-top aligned."
        self._content_width = (
            content_width if content_width else self._content_width
        )  # user selected
        self._centered = center if center is True else False  # user selected

        self._update_theme(change=None)  # Trigger CSS in it to make width change

    def hide_navigation_gui(self):
        "Hide all navigation elements, but keyboard or touch still work."
        self.widgets.controls.layout.display = "none"
        self.widgets.footerbox.layout.display = "none"

    def show_navigation_gui(self):
        "Show all navigation elements."
        self.widgets.controls.layout.display = ""
        self.widgets.footerbox.layout.display = ""


    def _update_size(self, change):
        if change and change["owner"] == self.width_slider:
            # Update Layout CSS
            self.widgets.htmls.main.value = html(
                "style",
                _layout_css.layout_css(
                    self.breakpoint,
                    accent_color=self.colors["accent_color"],
                ),
            ).value

        self.widgets.mainbox.layout.height = "{}vw".format(
            int(self.width_slider.value * self.aspect_dd.value)
        )
        self.widgets.mainbox.layout.width = "{}vw".format(self.width_slider.value)
        self._update_theme(
            change=None
        )  # For updating size and breakpoints and zoom CSS

    @property
    def text_size(self):
        "Text size in px."
        return f"{int(self.scale_slider.value*20)}px"

    @property
    def colors(self):
        "Current theme colors."
        if self.theme_dd.value == "Custom":
            return self._custom_colors or styles.theme_colors["Inherit"]
        return styles.theme_colors[self.theme_dd.value]

    @property
    def light(self):
        "Lightness of theme. 20-255. NaN if theme is inherit or custom."
        if self.theme_dd.value in ["Inherit", "Custom"]:
            return (
                math.nan
            )  # Use Fallback colors, can't have idea which themes colors would be there
        elif "Dark" in self.theme_dd.value:
            self.set_code_style("monokai", color="#f8f8f2", lineno=self._code_lineno)
            return 120
        elif self.theme_dd.value == "Fancy":
            self.set_code_style("borland", lineno=self._code_lineno)
            return 230
        else:
            self.set_code_style("default", lineno=self._code_lineno)
            return 250

    @property
    def theme_kws(self):
        return dict(
            colors=self.colors,
            light=self.light,
            text_size=self.text_size,
            text_font=self._font_family["text"],
            code_font=self._font_family["code"],
            breakpoint=self.breakpoint,
            content_width=self._content_width,
            centered=self._centered,
        )

    def _update_theme(self, change=None):
        # Update Layout CSS
        layout_css = _layout_css.layout_css(
            breakpoint=self.breakpoint,
            accent_color=self.colors["accent_color"],
        )
        self.widgets.htmls.main.value = html("style", layout_css).value

        # Update Theme CSS
        theme_css = styles.style_css(**self.theme_kws)

        if self.reflow_check.value:
            theme_css = (
                theme_css + f"\n.SlideArea * {{max-height:max-content !important;}}\n"
            )

        self.widgets.htmls.theme.value = html("style", theme_css).value
        if self.widgets.checks.notes.value:
            self._slides.notes.display() # Update notes window if open

    def _toggle_tocbox(self, btn):
        if self.widgets.tocbox.layout.display == "none":
            self.widgets.tocbox.layout.display = "unset"
            self.widgets.buttons.toc.icon = "minus"
        else:
            self.widgets.tocbox.layout.display = "none"
            self.widgets.buttons.toc.icon = "plus"

    def _toggle_viewport(self, change):
        self._push_zoom(change=None)  # Adjust zoom CSS for expected layout
        if self.btn_window.value:
            self.btn_window.icon = "minus"
            self.widgets.mainbox.add_class("FullWindow")  # to Full Window
            self.widgets.htmls.window.value = html(
                "style", _layout_css.viewport_css()
            ).value
        else:
            self.btn_window.icon = "plus"
            self.widgets.mainbox.remove_class("FullWindow")  # back to inline
            self.widgets.htmls.window.value = ""

        self._update_theme(change=None)  # For updating size and breakpoints

    def _toggle_fullscreen(self, change):
        self.widgets.iw.msg_tojs = 'TFS' # goes to js, toggle fullscreen and chnage icon of button

    def _on_icon_change(self, change): # icon will changes when Javscript sends a message
        if change.new == 'minus':
            self.widgets.mainbox.add_class('FullScreen')
        else:
            self.widgets.mainbox.remove_class('FullScreen')
        
    def _toggle_laser(self, change):
        self.widgets.iw.msg_tojs = 'TLSR'
        if self.btn_laser.value:
            self.btn_laser.icon = "minus"
        else:
            self.btn_laser.icon = "plus"

    def _push_zoom(self, change):
        if self.btn_zoom.value:
            self.btn_zoom.icon = "minus"
            self.widgets.htmls.zoom.value = f"<style>\n{_layout_css.zoom_hover_css()}\n</style>"

            # If at some point it may not work properly outside fullscreen use belowe
            # if self.btn_fscreen.value:
            #     self.widgets.htmls.zoom.value = f"<style>\n{_layout_css.zoom_hover_css()}\n</style>"
            # else:
            #     self.widgets.htmls.zoom.value = ""  # Clear zoom css immediately to avoid conflict
            #     self.widgets._push_toast("Objects are not zoomable in inline mode!", timeout=2)
        else:
            self.btn_zoom.icon = "plus"
            self.widgets.htmls.zoom.value = ""

    def _toggle_overlay(self, change):
        _which_disable = [self.btn_laser, self.btn_zoom, self.widgets.buttons.refresh]
        if self.btn_overlay.value:
            self.btn_overlay.icon = "minus"
            self.widgets.htmls.overlay.layout.height = "100%"
            for btn in _which_disable:
                btn.disabled = True  # Disable all buttons

        else:
            self.btn_overlay.icon = "plus"
            self.widgets.htmls.overlay.layout.height = "0px"
            for btn in _which_disable:
                btn.disabled = False  # Enable all buttons
