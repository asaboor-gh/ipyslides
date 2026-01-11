# This should not be used by user, but is used by ipyslides to generate layout of slides

from ..utils import _build_css
from ..xmd import get_unique_css_class
from .icons import Icon, _inline_svg
from ._widgets import focus_selectors
from .intro import get_logo


_focus_css = { # Matplotlib by plt.show, self focus, child focus, plotly
    focus_selectors: {
        "^:hover:not(.mode-popup-active)": { # visual cue on hover to click
            "box-shadow": "0px 0px 1px 0.5px #8988 !important",
            "border-radius": "4px !important",
        },
        "^.mode-popup-active": {
            "position": "fixed", # This works because SlideArea has transform to contain it as fixed
            **{f"{k}backdrop-filter": "blur(100px)" for k in ('', '-webkit-')},
            "left": "0", # 1px less than slide padding to avoid edges overlap
            "top": "0",
            "z-index": 9999,  # above all, including fullscreen button of interactive
            "width": "100% !important",
            "height": "100% !important", # leave space for bottom controls
            "padding": "8px", # same as slide padding 
            "object-fit": "scale-down !important",
            "outline": "none !important",
            "border-radius": "4px !important",
            "overflow": "scroll !important",  # Specially for dataframes
            ".vega-embed canvas, > .svg-container": {  # Vega embed canvas and plotly svg-container inside hoverabe
                "position": "fixed !important",  # Will be extra CSS but who cares
                "width": "100% !important",
                "height": "100% !important",  # Ovverider plotly and altair style
                "border-radius": "4px !important",
                "object-fit": "scale-down !important",
            },
        },
    },
    '.focus-child.mpl > svg.mode-popup-active': { # matplot size inches need special treatment
        "width": "100% !important",
        "height": "100% !important", 
        "object-fit": "scale-down !important",
    },
    # Nested focus classes should occupy full space because parent is focused too
    ".focus-self, .focus-child": {
        "^.mode-popup-active .vega-embed details": {
            "display": "none !important",
        },
        ".focus-self.mode-popup-active, .focus-child.mode-popup-active": {
            "left": "0px !important",
            "top": "0px !important",
            "width": "100% !important",
            "height": "100% !important",
            "outline": "none !important",
            "background": "var(--bg1-altcolor) !important",  # Avoids overlapping with other elements
        },
    },  
}

def layout_css(accent_color, aspect):
    uclass = get_unique_css_class()
    return _build_css(
        (uclass,),
        {
            "a.jp-InternalAnchorLink": {"display": "none !important"},
            "<.SlidesContainer": {"padding": "2px !important",}, # for box-shadow to appear all sides
            "^.SlidesWrapper": {
                "container": "slides / inline-size !important",
                "overflow": "hidden !important", # contain stuff inside
                "@media print": {"overflow": "auto !important",}, # for print all should be visible
                "z-index": "1 !important",
                "aspect-ratio": f"{aspect} !important", # important in notebook context, where width collpases to cell
                "box-shadow": "var(--jp-border-color1,#8988) 0px 0px 1px 0.5px !important", 
                "^:not(:fullscreen)": {
                    # Smoothly animate the box resizing, this also helps initial loading
                    "transition": "height 0.8s cubic-bezier(0.9, 0, 0.5, 1), width 0.4s ease-in-out !important", 
                },
                "^:fullscreen":{ # fast height transition while going in fullscreen
                     "transition": "height 0.4s cubic-bezier(0.9, 0, 0.5, 1) !important", 
                },
                "^.SingleSlide .Controls": {
                    "display": "none !important",
                },
                "^:focus": {
                    "outline" : "none !important",
                },
                "^.Voila-Child, ^.mode-fullscreen": {
                    ".Width-Slider, .Warn": {"display": "none !important"},
                },
                ".Warn::after": {
                    "display": "block",
                    "content": "'ℹ️ This warning is not visible in fullscreen/PDF/HTML!'",
                    "color": "var(--accent-color)",
                    "font-size": "0.7em !important",
                },
                "^.InView-Title .Arrows.Prev-Btn, ^.InView-Last .Arrows.Next-Btn, ^.InView-Title .Slide-Number, ^.InView-Title .Progress-Box": {
                    "display": "none !important",
                },
                "^.mouse-swipe-enabled": {
                    "^, *": {f'{k}user-select':'none !important' for k in ['','-moz-','-ms-','-webkit-']}, # avoid selecting text while swiping
                    "^.mouse-swipe-active::after": {
                        "content": "''",
                        "display": "block",
                        "position": "absolute",
                        "top": "0",
                        "left": "0",
                        "right": "0",
                        "bottom": "0",
                        "pointer-events": "auto",
                        "touch-action": "none !important", # still alow touch swipes
                        "cursor": "grabbing !important",
                        "background": "rgba(0,0,0,0.01)", # slight overlay to indicate swipe mode
                        "z-index": 99999, # above all, also it does not let pointer events pass through
                    },    
                },
                ".Slide-Number" : { # slide number
                    "position": "absolute !important",
                    "right": "0 !important",
                    "bottom": "0 !important",
                    "padding": "0 2px !important",
                    "font-size": "12px", 
                    "z-index": "4",  # below matplotlib fullsreen
                    "cursor": "help",
                    "^.Menu-Item":{"color": "var(--fg2-color) !important",},
                    "^:focus,^:active": {"box-shadow": "none !important"},
                    "@media print": {"display": "none !important",}, # each slide gets its own slide number
                },
                ".Progress-Box": {
                    "margin": "0 !important",
                    "padding": "0 !important",
                    "position": "absolute !important",
                    "left":"0 !important",
                    "bottom": "0 !important",
                    "background": "var(--bg2-color) !important",
                    "@media print": {"display": "none !important",}, # each slide gets its own progressbar
                    ".Progress" : {
                        "margin": "0 !important",
                        "padding": "0 !important",
                        "transition": "width 250ms ease-in-out !important",
                        "background": "var(--accent-color) !important",
                    },
                },
                ".ToastMessage, .TOC, .SidePanel": {
                    "--text-size": "20px", # Don't need these to be changed with slide text size
                },
                ".ToastMessage" : {
                    "position":"absolute",
                    "bottom": "4px", # right is set by JS
                    "height": "max-content",
                    "max-height": "min(400px, 65%)",
                    "width":"min(400px, 65%)",
                    "display": "grid", # grid can contain a child div even wihout defined height
                    "grid-template-rows": "1fr", # to make child div take full height
                    "z-index":"10",  # above slide content
                    "border-radius": "8px",
                    "padding":"8px",
                    "overflow":"auto",
                    "transition": "right 300ms ease-in-out",
                    **{f"{k}backdrop-filter": "blur(20px)" for k in ('', '-webkit-')},
                    "box-shadow": "0 0 5px 0 rgba(255,255,255,0.2), 0 0 10px 0 rgba(0,0,0,0.2)",
                    "border-image": "linear-gradient(to bottom,rgba(0,0,0,0) 0, rgba(0,0,0,0) 10%, var(--accent-color) 10% , var(--accent-color) 90%, rgba(0,0,0,0) 90%, rgba(0,0,0,0) 100%) 1/ 0 0 0 2px",
                    "> div": {"overflow":"auto", "height":"100%", "*": {"font-size": "16px !important",},},
                    "> button": {
                        "position":"absolute",
                        "right":"4px",
                        "top":"4px",
                        "width":"28px",
                        "height":"28px",
                        "border":"none",
                        "backdrop-filter":"blur(4px)",
                        "border-radius":"50% !important",
                        "font-size":"20px",
                        "cursor":"pointer",
                        "^:hover": { "scale":"1.1", "color":"var(--accent-color) !important",},
                    },
                    "table": {"width": "100% !important",}, # override width
                    ":is(h1, h2, h3, h4, h5, h6, th)" : {"text-align": "left !important"},
                },
                ".LogoHtml": {
                    "position": "absolute !important",
                    "^, .widget-html-content": {"line-height": "0 !important"},
                    "@media print": {"position": "fixed !important",},
                }, # other properties are set internally
                ".popup-close-btn": {
                    "position": "absolute",
                    "top": "8px",
                    "right": "8px",
                    "z-index": "10",  # above focused element
                    "border": "none",
                    "padding": "4px 8px",
                    "backdrop-filter": "blur(4px)",
                },
                "^.mode-inactive": { # clean up view
                    ".FooterBox, .Controls, .Slide-Number": {"display": "none !important",},
                },
                "> .Build-Btn": {"visibility": "hidden !important",}, # hide build button by default
                "^:has(.SlideArea.Stale) > .Build-Btn": {
                    "visibility": "visible !important",
                    "position": "absolute",
                    "bottom": "36px", # above navigation controls 
                    "right": "2px",
                    "padding":"2px 4px",
                    "border-radius":"4px",
                    "color": "hsl(from var(--accent-color) 40 100% l) !important",
                    "font-family": "var(--code-font) !important",
                    "font-size": "10px",
                    "letter-spacing": "1px",
                    "z-index": 5, # above controls 
                    "^:hover": {
                        "letter-spacing": "2px",
                        "transition": "letter-spacing 200ms ease-in-out",
                    },
                    "> i": {"color": "inherit !important",},
                },
                ".SlideBox, .SlideBox *": {
                    "touch-action": "none !important", # disable default touch actions to allow custom swipe handling
                },
                ".SlideArea": {
                    "^.Out-Sync > .jp-OutputArea::before" : {
                        "content": "'⛓️‍💥 Rebuild slide to update citations!'",
                        "color":"red",
                    },
                    "^.HideSlide *": {"visibility": "hidden !important",},
                    "@media print": {
                        "^.HideSlide": {"visibility": "visible !important",},
                        "^.HideSlide *": {"visibility": "inherit !important",},
                    },
                    **_focus_css,
                },
                ".jp-OutputArea": {
                    "width": "100% !important",
                    "height": "auto !important", # This is must for layout
                    ".jp-OutputPrompt.jp-OutputArea-prompt": {"display": "none !important",},
                    ".jp-OutputArea-output": { # clean reveal after loading skeleton ends
                        "animation": "ips-reveal 0.5s ease-in-out",
                    }
                },  # Otherwise it shrinks small columns
                "kbd" : {
                    "color":"var(--fg2-color)",
                    "background": "var(--bg2-color)",
                    "border": "1px solid var(--bg3-color)",
                    "border-radius": "0.2em",
                    "padding": "0 0.2em",
                    "box-shadow": "inset 0 -0.1em 0 var(--bg3-color)",
                    "font-size": "0.9em",
                },
                ".export-only, .print-only": {
                    "display": "none !important",
                    "@media print": {"display": "revert !important",},
                    },
                ".widget-inline-hbox": {
                    ".widget-label": {"color": "var(--fg1-color)"},
                    ".widget-readout": {
                        "color": "var(--fg1-color) !important",
                        "box-shadow": "none",
                        "min-width": "auto !important",
                    },
                },
                ".widget-slider": {
                    ".noUi-base": {
                        "background": "transparent",
                        "border": "none",
                    },
                    ".noUi-connects": {
                        "background": "var(--accent-color)",
                        "border-color": "var(--accent-color)",
                    },
                    ".noUi-handle": {
                        "background": "var(--accent-color)",
                        "border-color": "var(--accent-color)",
                        "^:hover, ^:focus": {
                            "background": "var(--bg3-color) !important",
                            "border-color": "var(--bg3-color) !important",
                        },
                    },
                    ".noUi-connect.noUi-draggable": { # for ranger sliders
                        "background": "var(--accent-color)",
                    },
                },
                ".widget-html": {
                    ".widget-html-content > div": {
                        "font-size": "var(--text-size) !important",
                    },
                    ".widget-html-content": {
                        "pre, code, p": {
                            "font-size": "100% !important",
                        },  # otherwise it is so small
                    },
                },
                ".SidePanel": {
                    "background": "var(--bg3-color)",
                    "backdrop-filter": "blur(10px)",
                    "position": "absolute",
                    "transform": "translateZ(0)", # to create new stacking context for absolute children
                    "border": "none",
                    "padding": "0 !important",
                    "height": "100% !important",
                    "width": "0", # set by Python, don't add important here
                    "z-index": "10",
                    "top": "0px !important",
                    "left": "0px !important",
                    "transition": "width 400ms ease-in-out",
                    "overflow": "hidden !important",
                    "> div:first-child": {"line-height": "1 !important",}, # avoid extra height from default line-height
                    ".widget-html-content": {"font-size": "var(--jp-widgets-font-size) !important",}, 
                    "> *": {"transition": "padding-top 400ms ease-in-out",},
                    ".list-widget": {"font-size": "16px !important","flex-wrap": "nowrap !important",},
                    ".panel-close-btn": {
                        "width": "28px !important",
                        "height": "28px !important",
                        "border": "none !important",
                        "outline": "none !important",
                        "font-size": "24px",
                        "background": "transparent !important",
                        "> i": {
                            "color": "var(--accent-color) !important",
                        },
                    },
                },
                ".SlideBox :is(button, .jupyter-button)": {
                    "border": "1px solid var(--accent-color)",
                    "border-radius": "4px",
                    "min-height": "28px",
                    "min-width": "28px",
                },
                "button:not(.tlui-button)": {
                    "color": "var(--accent-color) !important",
                    "border-radius": "0px",
                    "background": "transparent !important",
                    "display": "flex",
                    "align-items": "center",  # center the icon vertically
                    "justify-content": "center",
                    "> i": {
                        "color": "var(--accent-color) !important",
                    },
                    '@media print': { "opacity": "0.3",},# want to make it look like disabled in print, no important here as some buttons need to be visible
                },
                ".jupyter-button:hover:enabled, .jupyter-button:focus:enabled": {
                    "outline": "none !important",
                    "opacity": "1 !important",
                    "box-shadow": "none !important",
                    "background": "var(--bg3-color)",
                    "text-shadow": "0 0 1px var(--bg2-color), 0 0 2px var(--accent-color)",
                },
                ".widget-play .jupyter-button": {
                    "background": "var(--bg2-color)",
                    "color": "var(--accent-color) !important",
                },
                ".widget-dropdown": {
                    "> select": { # Jupyter theme variables need additional fallbacks for dropdown
                        "color": "var(--fg1-color, var(--jp-content-font-color0)) !important",
                        "background": "var(--bg1-altcolor, var(--jp-cell-editor-background)) !important",
                        "border": "1px solid var(--bg3-color, var(--jp-layout-color2)) !important",
                        "border-radius": "4px !important",
                        "padding": "4px 8px !important",
                        "box-shadow": "none !important",
                        "outline": "none !important",
                    },
                    "> select > option": {
                        "color": "var(--fg1-color, var(--jp-content-font-color0)) !important",
                        "background": "var(--bg1-altcolor, var(--jp-cell-editor-background)) !important",
                    },
                },
                ".jupyter-widgets:not(button)": {
                    "color": "var(--fg1-color) !important"
                },  # All widgets text color
            },
            ".FooterBox": {
                "max-width": "100% !important",
                "position": "absolute !important",
                "left": "0 !important",
                "bottom": "2px !important", # leave space for progressbar
                "width": "100% !important",
                "@media print": {"position": "fixed !important",},
                "^,^ > .Footer": {
                    "padding": "0px",
                    "margin": "0px",
                    "overflow": "hidden",
                    "max-width": "100%",
                },
                ".Footer": {
                    "overflow": "hidden !important",
                    ".widget-html-content": {
                        "display": "flex",
                        "align-items": "center",
                        "justify-content": "flex-start",
                        "line-height": "1.5 !important",
                    },
                    "p": {
                        "font-size": "14px !important",
                    },
                },
            },
            ".Controls": {
                "position": "absolute",
                "right": "8px !important",
                "bottom": "0 !important", # bring buttons center at top edge for symmetry
                "z-index": "4",  # below matplotlib fullsreen
                "padding": "0 !important",
                "justify-content": " flex-end !important",
                "align-items": "center !important",
                "color": " var(--accent-color) !important",
                ".widget-button > i": {
                    "color": "var(--accent-color) !important",
                },
                ".Arrows": {
                    "opacity": "0.4",
                    "font-size": "36px",
                    "padding": "2px",
                    "^:hover, ^:focus": {"opacity": 1},
                },
                ".ProgBox": {
                    "width": "16px",
                    "padding": "0px 8px",
                    "opacity": 0,
                    "overflow": "hidden",
                    "transition": "width 0.4s", #on exit hover
                    "^:hover, ^:focus": {
                        "width": "50%",
                        "min-width": "30%",  # This is very important to force it
                        "justify-content": "center",
                        "opacity": 1,
                        "transition": "width 0.4s", # on enter
                    },
                },
            },
            ".TOC": {  # Table of contents panel
                "display": "table-column-group !important", # This to avoid collapsing divs
                "transition": "padding-bottom 400ms ease-in-out",
                ".list-item": {
                    "display": "flex",
                    "flex-direction": "row",
                    "flex-wrap": "nowrap",
                    "justify-content": "space-between !important",
                    "height": "auto",
                    "width": "auto",
                    "font-size": "16px !important", # A litle larger
                },
            },
            ".CtxMenu": {
                "position": "absolute",
                "z-index": "11",  # above all
                "backdrop-filter": "blur(50px)",
                "box-shadow": "0 0 5px 0 rgba(255,255,255,0.2), 0 0 10px 0 rgba(0,0,0,0.2)",
                "border-radius": "4px",
                "padding-top": "1.2em", # for top description
                "overflow-y": "auto",
                "width": "min(200px, 90%) !important", # very small screens should show a graceful menu
                "height": "max-content !important",
                "max-height": "min(600px, 90%) !important",
                "transform": "translate(-4px,-4px)", # subtle edge views
                "transition": "top 200ms ease-in-out, visibility 200ms ease-in-out",
                "^, .list-item.list-item":  {
                    "border-top": "1px solid var(--bg3-color) !important",
                    "font-size": "14px !important", # fixed size
                },
                "^.list-widget:hover .list-item": {
                    "border": "none !important",
                    "border-radius": "0 !important",
                    "margin":"0.5px !important", # keep size same on hover
                }, 
                ".list-item:hover, .list-item.selected": {
                    "background": "var(--bg3-color) !important",
                    "box-shadow": "none !important",
                    "border-radius": "0 !important",
                    "border": "none !important",
                    "font-weight": "normal !important",
                },
            },
            "<.jp-OutputArea-child": {
                "^, .jp-OutputArea-output": {  # For some themes, but do not use important here
                    "background": "transparent",
                    "background-color": "transparent",
                    "margin": "0",
                },
            },
            ".jp-RenderedHTMLCommon": {
                "padding": 0,
                "padding-right": "0 !important",  # important for central layout
                "font-size": "var(--text-size)",
                ":not(pre) > code": {
                    "background": "var(--bg2-color) !important",
                    "color": "var(--fg2-color)",
                },
                ":not(pre) > code, :not(pre) > span": {  # To avoid overflow due to large words
                    "word-break": "normal !important",
                    "overflow-wrap": "break-word !important",
                },
                "p": {
                    "margin-bottom": "0.2em !important",
                },
                "pre, code": {
                    "color": "var(--fg1-color)",
                },
            },
            ".jp-RenderedText": {
                "*": {"font-size": "0.9em !important",},
                "^, pre": {
                    "color": "var(--fg1-color) !important",
                },
            },
            ".Draw-Wrapper": { # height is set dynamically
                "position": "absolute !important",
                "left": 0,
                "top":0,
                "z-index": "8 !important",
                "overflow": "hidden !important",
                "transition": "height 200ms",
                **{f"{k}backdrop-filter": "blur(50px)" for k in ('', '-webkit-')},
                "> .Draw-Btn" : {
                    "position": "absolute !important",
                    "left": 0,
                    "top":0,
                    "z-index": "9 !important",
                    "width": "36px !important",
                    "^:active, ^.mod-active": {"box-shadow": "none !important","opacity": "1 !important",},
                },
            },
            ".Draw-Widget": {
                **{f"{k}backdrop-filter": "blur(50px)" for k in ('', '-webkit-')},
                "margin": 0,
                "z-index": 6,
                "overflow": "hidden !important",
                "transition": "height 200ms",
                "^, > div": {
                    "position": "absolute !important",
                    "left": "0",
                    "top": "0",
                    "width": "100%",
                    "height": "100%",
                },
                "> div": {
                    "width": "100% !important", # inner div issue, override
                    "height": "100% !important",
                },  
                'rect.tl-frame__body': { # Due to lack of dark mode in widget
                    'fill':'var(--bg1-altcolor)',
                    'stroke':'var(--bg2-color)',
                },
            },
            ".Arrows": {
                ".fa.fa-chevron-left": Icon(
                    "chevronl", color=accent_color, size="36px"
                ).css,
                ".fa.fa-chevron-right": Icon(
                    "chevronr", color=accent_color, size="36px"
                ).css,
            },
            "<.Scroll-Btn": { # top level
                "color": "var(--jp-brand-color1,skyblue) !important",
                "background": "transparent !important",
                "font-size": "0.8em !important",
                "opacity": "0 !important",
                "height": "auto !important", # for show when slide shown
                "transition": "all 400ms ease-in-out !important",
                "^:hover": {"font-weight": "bold !important","font-size": "0.9em !important",},
                "^:hover, ^:focus, ^:active, ^.mod-active" : {
                    "box-shadow": "none !important",
                    "opacity": "1 !important",
                    "outline": "none !important",
                },
            },
            "@media print": { # Needs modification
                ".SlidesWrapper": {
                    "^, ^.Voila-Child": {
                        "height": "auto !important",
                    },
                },
                ".Controls": {
                    "display": "none !important",
                },
                "pre, .SlideBox, .SlidesWrapper, .SlideArea": {
                    "height": "auto !important",
                },
                ".SlidesWrapper .highlight, .SlideArea .raw-text": {
                    "max-height": "auto !important",  # Flow itself
                },
                ".SlideArea": {
                    "width": "100% !important",
                },
            },  # @media print
            "<body.Voila-App": {  # Voila
                "background": "var(--bg3-color)",
                "^, .SlidesWrapper.Voila-Child": {
                    "position": "fixed !important",
                    "top": "0 !important",
                    "left": "0 !important",
                    "right": "0 !important",
                    "bottom": "0 !important",
                    "@media print": {"all": "unset !important",}, # need to reset for print
                },
                "^, *": {
                    "color": "var(--fg1-color)",
                },
                "::-webkit-scrollbar": {
                    "height": "4px",
                    "width": "4px",
                    "background": "transparent !important",
                    "^:hover": {
                        "background": "var(--bg2-color) !important",
                    },
                },
                "::-webkit-scrollbar-thumb": {
                    "background": "transparent !important",
                    "^:hover": {
                        "background": "#8988 !important",
                    },
                },
                "::-webkit-scrollbar-corner": {
                    "display": "none !important",
                },
                '#rendered_cells, .SlidesWrapper.Voila-Child': {
                    "width": "100vw !important",
                    "height": "100vh !important",
                },
                '.Slides.Wrapper.Voila-Child': {"z-index": "100 !important",},
            },
            # Other issues
            "<#jp-top-panel, #jp-bottom-panel, #jp-menu-panel": {"color": "inherit"},
            "<.CodeMirror": {
                "padding-bottom": "8px !important",
                "padding-right": "8px !important",
            },  # Jupyter-Lab make space in input cell
            "<.cell-output-ipywidget-background": {  # VSCode issue  
                "background": "var(--theme-background,inherit) !important",
                "margin": "8px 0px",
            },
            "<.jp-LinkedOutputView": {
                "> .jp-OutputArea > .jp-OutputArea-child": { # avoid collapse
                    "width":"100% !important",
                    "height": "100% !important",
                    "overflow": "hidden !important",
                    "@media print": {"all": "unset !important",}, # need to show all outputs
                },
                ".SlidesContainer": {
                    "container-type": "size !important",
                    "container-name": "resize-box !important",
                    "overflow": "hidden !important",
                    "@media print": {"all": "unset !important",}, # need to fully reset for print
                    "width": "100% !important",
                    "height": "100% !important",
                    "> .SlidesWrapper": {
                        "width": "100% !important",
                        "height": "auto !important",
                        "aspect-ratio": f"{aspect} !important",
                        "margin": "auto !important",
                        f"@container resize-box (aspect-ratio > {aspect})": {
                            "width": "auto !important",
                            "height": "100% !important",
                        },
                        ".Width-Slider": {"display": "none !important",},
                    },
                },
            },
            "<#ipython-main-app .SlidesWrapper .output_scroll": {  # For classic Notebook output
                "height": "unset !important",
                **{f"{k}box-shadow": "none !important" for k in ('', '-webkit-')},
            },
        },
    ) 

def background_css(sel, opacity=0.75, filter='blur(2px)', contain=False, uclass=''):
    if filter and not '(' in str(filter):
        raise ValueError(f"blur expects a CSS filter function like 'blur(2px)', 'invert()' etc. or None, got {filter}")
    
    # sel depends on where image is placed
    return f"""{sel} .BackLayer {{
        position: absolute !important;
        top:0 !important;
        left:0 !important;
        width: 100% !important;
        height: 100% !important;
        overflow:hidden;
        margin:0;
    }}
    {sel} .BackLayer :is(img, svg) {{
        position: absolute;
        left:50% !important;
        top:50% !important;
        transform: translate(-50%,-50%) !important; /* Make at center */ 
        width: 100%;
        height: 100%;
    }}
    {sel} .{uclass}.BackLayer :is(img, svg) {{
        object-fit:{('contain' if contain else 'cover')} !important;
        filter: {filter};
        opacity:{opacity};
    }}  
    {sel} .{uclass}.BackLayer svg {{
        max-width: {('100%' if contain else '')} !important;
        max-height: {('100%' if contain else '')} !important;
        width: {('' if contain else 'auto')} !important;
        min-width: {('' if contain else '100%')} !important;
        min-height: {('' if contain else '100%')} !important;
    }}
    {sel} .BackLayer.jupyter-widgets-disconnected {{
        display:none;
    }}
    """

# This is used in slide content loading placeholder
loading_style = """
<style>
.skeleton-wrapper {
    padding: 16px;
    background: transparent;
    height: max-content;
    min-height: 250px;
    overflow: hidden;
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 20px; /* Space between Header and Columns */
}

.skeleton-header {
    width: 100%;
    border-bottom: 1px solid var(--jp-border-color2, rgba(128,128,128,0.2));
    padding-bottom: 15px;
}
.skeleton-columns { display: flex; gap: 30px; flex: 1; }
.skeleton-left { flex: 3; display: flex; flex-direction: column; gap: 12px; }
.skeleton-right { flex: 2; display: flex; }

.skeleton-item {
    background: var(--bg3-color, var(--jp-layout-color2, #262626)); 
    border-radius: 8px; 
}

/* Heights for different levels */
.skeleton-item.header-bar { height: 36px; }
.skeleton-item.title { height: 24px; }
.skeleton-item.text { height: 12px; }
.skeleton-item.media { width: 100%; height: 100%; min-height: 200px; }

.ips-loading { position: relative; overflow: hidden; }
.ips-loading::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, 
        var(--bg3-color, var(--jp-layout-color2, #262626)), 
        hsl(from var(--bg2-color, var(--jp-layout-color2, #bbb)) h calc(s*0.75) calc(l*0.75)), 
        var(--bg3-color, var(--jp-layout-color2, #262626))
    );
    background-size: 200% 100%;
    animation: skeleton-swipe 2s infinite linear;
}

@keyframes skeleton-swipe {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

@keyframes ips-reveal {
    0% {
        opacity: 0;
        transform: scale(0.95);
    }
    99% {
        opacity: 1;
        transform: scale(1);
    }
    100% {
        /* Explicitly unset to collapse the stacking context */
        opacity: unset;
        transform: unset;
    }
}

.skeleton-footer { 
    margin-top: 20px; 
    color: var(--fg2-color, var(--jp-ui-font-color2, #888)); 
    font-size: 10px; 
    font-family: var(--jp-ui-font-family, sans-serif);
}
</style>
"""

def loading_skeleton(info="Loading ..."):
    # Randomize widths
    import random
    widths = [random.randint(70, 98) for _ in range(3)]
    main_header_width = random.randint(30, 50) # The new top-level title
    column_title_width = random.randint(40, 70) 
    
    # Randomly flip layout
    flex_direction = random.choice(["row", "row-reverse"])
    return f"""{loading_style}
    <div class="skeleton-wrapper">
        <div class="skeleton-header">
            <div class="skeleton-item header-bar ips-loading" style="width: {main_header_width}%;"></div>
        </div>

        <div class="skeleton-columns" style="flex-direction: {flex_direction};">
            <div class="skeleton-left">
                <div class="skeleton-item title ips-loading" style="width: {column_title_width}%;"></div>
                <div class="skeleton-item text ips-loading" style="width: {widths[0]}%;"></div>
                <div class="skeleton-item text ips-loading" style="width: {widths[1]}%;"></div>
                <div class="skeleton-item text ips-loading" style="width: {widths[2]}%;"></div>
                <div class="skeleton-item text ips-loading" style="width: {random.randint(30, 50)}%; margin-top: 10px;"></div>
            </div>
            
            <div class="skeleton-right">
                <div class="skeleton-item media ips-loading"></div>
            </div>
        </div>
        <div class="skeleton-footer">IPySlides | {info}</div>
    </div>
    """ 
