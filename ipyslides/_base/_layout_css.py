# This should not be used by user, but is used by ipyslides to generate layout of slides

from ..utils import _build_css
from ..xmd import get_unique_css_class
from .icons import Icon
from ._widgets import focus_selectors

_icons_size = "1em"  # For all except Chevrons
_focus_css = { # Matplotlib by plt.show, self focus, child focus, plotly
    focus_selectors: {
        "^:hover:not(.mode-popup-active)": { # visual cue on hover to click
            "box-shadow": "0px 0px 1px 0.5px #8988 !important",
            "border-radius": "4px !important",
            "cursor": "zoom-in", # indicate clickable as well as it's useful as visual pointer
        },
        "^.mode-popup-active": {
            "position": "fixed", # This works because SlideArea has transform to contain it as fixed
            **{f"{k}backdrop-filter": "blur(100px)" for k in ('', '-webkit-')},
            "left": "0", # 1px less than slide padding to avoid edges overlap
            "top": "0",
            "z-index": 9999,  # above all, including fullscreen button of interactive
            "width": "100% !important",
            "height": "100% !important", # leave space for bottom controls
            "padding": "16px", # same as slide padding 
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
                "box-sizing": "border-box !important",
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
            "box-sizing": "border-box !important",
            "outline": "none !important",
            "background": "var(--bg1-color) !important",  # Avoids overlapping with other elements
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
                "^.SingleSlide .Controls": {
                    "display": "none !important",
                },
                "^:focus": {
                    "outline" : "none !important",
                },
                "^.Voila-Child, ^.mode-fullscreen": {
                    ".Width-Slider, .Source-Btn": {"display": "none !important"},
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
                    "z-index":"9",  # above slide content
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
                ".Loading": {
                    "position": "absolute",
                    "left": "0 !important",
                    "top": "0 !important",
                    "width": "100% !important",
                    "height": "100% !important",
                    "z-index": "11",  # Above all
                    "text-shadow": "0 0 2px white, 0 0 4px var(--bg2-color, black)",
                    "background": "var(--jp-layout-color0,white)", # colors are not yet there in start
                    ".widget-html-content": {
                        "width": "100% !important",
                        "height": "100% !important",
                        "display": "flex !important",
                        "align-items": "center !important",
                        "justify-content": "center !important",
                    },
                },
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
                    "box-sizing": "border-box !important",
                    ".jp-OutputPrompt.jp-OutputArea-prompt": {"display": "none !important",},
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
                    "^, *": {"box-sizing": "border-box !important",},
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
                "^, *": {
                    "box-sizing": "border-box",
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
                    "text-shadow": "0 0 1px var(--bg1-color), 0 0 2px var(--accent-color)",
                },
                ".widget-play .jupyter-button": {
                    "background": "var(--bg2-color)",
                    "color": "var(--accent-color) !important",
                },
                ".widget-dropdown": {
                    "> select, > select > option": {
                        "color": "var(--fg1-color) !important",
                        "font-family": "var(--jp-content-font-family) !important", # why system fonts here?
                        "background": "var(--bg1-color) !important",
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
                "@media print": {"position": "fixed !important","background":"var(--bg1-color) !important",},
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
                "bottom": "1px !important", # bring center at top of Navbox for symmetry
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
                "^, .jp-OutputArea-output": {  # For some themes
                    "background": "transparent !important",
                    "background-color": "transparent !important",
                    "margin": "0 !important",
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
                    "box-sizing": "border-box",
                },
                "> div": {
                    "width": "100% !important", # inner div issue, override
                    "height": "100% !important",
                },  
                'rect.tl-frame__body': { # Due to lack of dark mode in widget
                    'fill':'var(--bg1-color)',
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
                "box-sizing": "border-box !important",
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
        box-sizing:border-box !important;
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
