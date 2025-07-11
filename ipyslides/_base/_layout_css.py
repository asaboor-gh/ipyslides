# This should not be used by user, but is used by ipyslides to generate layout of slides

from ..utils import _build_css
from ..xmd import get_unique_css_class
from .icons import Icon

_zoom_ables = ".jp-RenderedImage > img, .zoom-self, .zoom-child > *:not(.no-zoom), .plot-container.plotly"
_icons_size = "1em"  # For all except Chevrons


def layout_css(accent_color, aspect):
    uclass = get_unique_css_class()
    return _build_css(
        (uclass,),
        {
            "a.jp-InternalAnchorLink": {"display": "none !important"},
            "<.SlidesContainer": {"padding": "2px !important",}, # for box-shadow to appear all sides
            "^.SlidesWrapper": {
                "container": "slides / inline-size !important",
                "z-index": "1 !important",
                "aspect-ratio": f"{aspect} !important", # important in notebook context, where width collpases to cell
                "box-shadow": "var(--jp-border-color1,#8988) 0px 0px 1px 0.5px !important", 
                "^.SingleSlide .Controls": {
                    "display": "none !important",
                },
                "^:focus": {
                    "outline" : "none !important",
                },
                "^.Voila-Child, ^.FullScreen": {
                    ".Width-Slider, .Source-Btn": {"display": "none !important"},
                },
                "^.InView-Title .Arrows.Prev-Btn, ^.InView-Last .Arrows.Next-Btn, ^.InView-Title .Slide-Number, ^.InView-Title .Progress-Box": {
                    "display": "none !important",
                },  # still should be clickable
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
                },
                ".Progress-Box": {
                    "margin": "0 !important",
                    "padding": "0 !important",
                    "position": "absolute !important",
                    "left":"0 !important",
                    "bottom": "0 !important",
                    "background": "var(--bg2-color) !important",
                    ".Progress" : {
                        "margin": "0 !important",
                        "padding": "0 !important",
                        "transition": "width 250ms ease-in-out !important",
                        "background": "var(--accent-color) !important",
                    },
                },
                ".Toast, .TOC, .SidePanel": {
                    "--text-size": "20px", # Don't need these to be zoomed in
                },
                ".Toast" : {
                    "position":"absolute",
                    "right":"4px", # top is made for animation via javascript
                    "top": "-120px", # Hides on load
                    "max-width":"65%",
                    "min-width":"300px",
                    "min-height":"100px",
                    "max-height":"65%", 
                    "z-index":"10000",
                    "border-radius": "8px",
                    "padding":"8px",
                    "overflow":"auto",
                    **{f"{k}backdrop-filter": "blur(20px)" for k in ('', '-webkit-')},
                    "box-shadow": "0 0 5px 0 rgba(255,255,255,0.2), 0 0 10px 0 rgba(0,0,0,0.2)",
                    "border-image": "linear-gradient(to bottom,rgba(0,0,0,0) 0, rgba(0,0,0,0) 10%, var(--accent-color) 10% , var(--accent-color) 90%, rgba(0,0,0,0) 90%, rgba(0,0,0,0) 100%) 1/ 0 0 0 2px",
                    "> button": {
                        "position":"absolute",
                        "right":"4px",
                        "top":"4px",
                        "border":"none",
                        "background":"none",
                        "border-radius":"50%",
                        "font-size":"20px",
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
                "div.LaserPointer": {  # For laser pointer
                    "position": "absolute !important",
                    "width": "12px",
                    "height": "12px",
                    "left": "-50px",  # Hides when not required , otherwise handled by javascript*/
                    "z-index": "9",  # below side panel but above zoomed image */
                    "border-radius": "50%",
                    "border": " 2px solid white",
                    "background": " var(--pointer-color)",
                    "box-shadow": " 0 0 4px 2px white, 0 0 6px 6px var(--pointer-color)",
                    "display": "none",  # Initial setup. Display will be set using javascript only */
                    "overflow": "hidden !important",  # To hide at edges */
                },
                ".SlideArea": {
                    "^.Out-Sync > .jp-OutputArea::before" : {
                        "content": "'citations got out of sync, rerun corresponding slide source to update'",
                        "color":"red",
                        "border": "1px solid red",
                        "display": "block",
                    },
                    ".export-only": {"display": "none !important"},
                    ".jp-OutputArea": {
                        "width": "100% !important",
                        "height": "auto !important", # This is must for layout
                        "box-sizing": "border-box !important",
                    },  # Otherwise it shrinks small columns
                    _zoom_ables: {
                        "^:hover": {
                           "box-shadow": "0px 0px 1px 0.5px #8988 !important",
                           "border-radius": "8px !important",
                        },
                    },
                },
                "kbd" : {
                    "color":"var(--fg2-color)",
                    "background": "var(--bg2-color)",
                    "border": "1px solid var(--bg3-color)",
                    "border-radius": "0.2em",
                },
                ".export-only": {"display": "none !important"},
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
                    "border": "none",
                    "padding": "0 !important",
                    "width": "min(400px, 100%) !important",
                    "z-index": "10",
                    "top": "0px !important",
                    "left": "0px !important",
                    "transition": "height 400ms ease-in-out",
                    "overflow": "hidden !important",
                    "@container slides (max-width: 400px)": {"width": "100% !important"}, # reinforce width
                    ".widget-html-content": {"font-size": "var(--jp-widgets-font-size) !important",},
                    ":not(.TopBar)": {
                        ":is(button, .jupyter-button)": {
                            "width": "max-content !important",
                            "min-height": "28px !important",
                        },
                    },
                    ".header": {
                        "background": "var(--bg3-color) !important",
                        "box-shadow": "0 1px 2px #8984 !important", # subtle shadow
                        "button": {"direction": "rtl !important"}, # why toggle buttons icons are on right? flipping direction to fix
                    }, 
                    "> *": {"transition": "padding-top 400ms ease-in-out",},
                    "^, *": {"box-sizing": "border-box !important",},
                    ".Panel-Btn": {
                        "border": "none !important",
                        "outline": "none !important",
                        "font-size": "20px",
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
            ".NavWrapper": {
                "max-width": "100% !important",
                "position": "absolute !important",
                "left": "0 !important",
                "bottom": "2px !important", # leave space for progressbar
                "width": "100% !important",
                "@media print": {"position": "fixed !important","background":"var(--bg1-color) !important",},
                "^,^ > div": {
                    "padding": "0px",
                    "margin": "0px",
                    "overflow": "hidden",
                    "max-width": "100%",
                },
                ".NavBox": {
                    "position": "relative !important", # for menubox
                    "overflow": "hidden",
                    "align-items": "center",
                    "height": "max-content",
                    "justify-content": "flex-start",
                    ".Menu-Item": {
                        "font-size": "18px !important",
                        "overflow": "hidden",
                        "opacity": "0.7",
                        "z-index": "3",
                        "^:hover": {
                            "opacity": "1",
                        },
                        "^:active, ^.mod-active": {
                            "box-shadow": "none !important",
                            "opacity": "1 !important",
                        },
                    },
                    ".Menu-Box": {
                        "position": "absolute !important",
                        "z-index": "3 !important",
                        **{f"{k}backdrop-filter": "blur(10px)" for k in ('', '-webkit-')},
                        "width": "0 !important",
                        "transition": "width 400ms ease-in-out", # transition on exit
                        "overflow": "hidden !important", # needs to not jump on chnage of width
                    },
                    "^:hover, ^:focus, ^:active, ^.mod-active" : {
                        ".Menu-Box" : {
                            "width": "148px !important", # 4*32 + margin + paddings
                            "transition": "width 400ms ease-in-out", # transition on enter hover
                             "overflow": "hidden !important", # avoid jump on hover too
                        },
                    },
                    ".Toc-Btn, .Menu-Btn, .Draw-Btn, .Source-Btn": {
                        "min-width": "28px",
                        "width": "28px", # need this too
                    },  # Avoid overflow in small screens
                    ".Footer": {
                        "overflow": "hidden !important",
                        ".widget-html-content": {
                            "display": "flex",
                            "align-items": "center",
                            "justify-content": "flex-start",
                        },
                        "p": {
                            "font-size": "14px !important",
                        },
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
            ".TopBar.Outside, .TopBar > div": {
                "display": "flex",
                "overflow-x": "auto",
                "overflow-y": "hidden", # hides useless scrollbars
                "min-height": "36px !important",
                "align-items": "center !important",
                "justify-content": "space-around !important",
                "padding": "4px !important",
                "box-sizing": "border-box !important",
                "button": {
                    "font-size": "14px !important",
                    "min-width": "max-content !important",
                    "width": "auto !important", # To make equal widths
                    "flex-grow": "1 !important",
                    "flex-shrink": "1 !important",
                    "height": "28px !important",
                    "outline": "none !important",
                    "border": "none !important",
                    "box-shadow": "none !important",
                    "background": "transparent !important",
                    "> i": {
                        "color": "var(--accent-color) !important",
                    },
                    "^:disabled,^[disabled]": {
                        "display": "none !important",
                    },
                    "^:active, ^.mod-active": {
                        "border-bottom": "1px solid var(--accent-color) !important", # like a navbar
                    },
                },
            },
            ".TopBar.Outside": {
                "position": "absolute !important",
                "z-index": "7 !important",  # below matplotlib fullsreen
                "left" : "4px !important",
                "bottom": "30px !important", 
                "padding": "0 !important",
                "min-height": "0 !important", #override panel top bar
                "max-height": "calc(100% - 30px) !important",
                "overflow-y": "auto !important",
                "overflow": "hidden", # hides scrollbars with single button
                "background": "var(--bg2-color) !important",
                "box-sizing": "border-box !important",
                "border-radius": "4px",
                "transition": "height 400ms ease-in-out",
                "display": "table-column-group !important", # avoid collapse
                "> .widget-hbox": { # upper buttons
                    "border-bottom": "1px solid #8988",
                    "margin": "0 4px !important",
                    "> button" : {
                        "width": "36px !important",
                        "^.Menu-Btn" : {"margin-left": "auto !important"}, # keep cross right most
                        "^:active, ^.mod-active": {"border-bottom": "none !important",}, # remove border on click outside
                    },
                },
                "> button > i": {"margin-right": "8px !important",}, # Make uniform
                "> button::after":{
                    "content": "attr(title)",
                    "font-size": "14px !important",
                    "color": "var(--fg1-color) !important",
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
            ".Panel-Btn": {
                ".fa.fa-plus": Icon("panel", color=accent_color, size=_icons_size).css,
                ".fa.fa-minus": Icon("close", color=accent_color, size=_icons_size).css,
            },
            ".Toc-Btn": {
                ".fa.fa-plus": Icon("bars", color=accent_color, size=_icons_size).css,
                ".fa.fa-minus": Icon("close", color=accent_color, size=_icons_size).css,
            },
            ".Draw-Btn": {
                ".fa.fa-plus": Icon(
                    "pencil", color=accent_color, size=_icons_size, rotation=45
                ).css,
                ".fa.fa-minus": Icon(
                    "arrowl", color=accent_color, size=_icons_size
                ).css,
            },
            ".FullScreen-Btn": {
                ".fa.fa-plus": Icon("expand", color=accent_color, size=_icons_size).css,
                ".fa.fa-minus": Icon(
                    "compress", color=accent_color, size=_icons_size
                ).css,
            },
            ".Refresh-Btn": {
                ".fa.fa-plus": Icon(
                    "refresh", color=accent_color, size=_icons_size
                ).css,
                ".fa.fa-minus": Icon(
                    "loading", color=accent_color, size=_icons_size
                ).css,
            },
            ".Laser-Btn": {
                ".fa.fa-plus": Icon("laser", color=accent_color, size=_icons_size).css,
                ".fa.fa-minus": Icon(
                    "circle", color=accent_color, size=_icons_size
                ).css,
            },
            ".Zoom-Btn": {
                ".fa.fa-plus": Icon(
                    "zoom-in", color=accent_color, size=_icons_size
                ).css,
                ".fa.fa-minus": Icon(
                    "zoom-out", color=accent_color, size=_icons_size
                ).css,
            },
            ".Menu-Btn": {
                ".fa.fa-plus": Icon(
                    "dots", color=accent_color, size=_icons_size
                ).css,
                ".fa.fa-minus": Icon(
                    "close", color=accent_color, size=_icons_size
                ).css,
            },
            ".Source-Btn": {
                ".fa.fa-plus": Icon(
                    "code", color=accent_color, size=_icons_size
                ).css,
            },
            ".Home-Btn": {
                ".fa.fa-plus": Icon(
                    "arrowbl", color=accent_color, size=_icons_size
                ).css,
            },
            ".End-Btn": {
                ".fa.fa-plus": Icon(
                    "arrowbr", color=accent_color, size=_icons_size
                ).css,
            },
            ".Info-Btn": {
                ".fa.fa-plus": Icon(
                    "info", color=accent_color, size=_icons_size,
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
                ".Controls, .NavWrapper button, div.LaserPointer": {
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
            "<.cell-output-ipywidget-background": {  # VSCode issue */
                "background": "var(--theme-background,inherit) !important",
                "margin": "8px 0px",
            },
            "<.jp-LinkedOutputView": {
                "> .jp-OutputArea > .jp-OutputArea-child": { # avoid collapse
                    "width":"100% !important",
                    "height": "100% !important",
                    "overflow": "hidden !important",
                },
                ".SlidesContainer": {
                    "container-type": "size !important",
                    "container-name": "resize-box !important",
                    "overflow": "hidden !important",
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

def zoom_hover_css():
    return _build_css(
        (".SlideArea",),
        {
            # Matplotlib by plt.show, self zoom, child zoom, plotly
            _zoom_ables: {
                "^:hover, ^:focus": {
                    "position": "fixed",
                    **{f"{k}backdrop-filter": "blur(50px)" for k in ('', '-webkit-')},
                    "left": "50px",
                    "top": "50px",
                    "z-index": 8,
                    "width": "calc(100% - 100px)",
                    "height": "calc(100% - 100px)",
                    "object-fit": "scale-down !important",
                    "box-shadow": "-1px -1px 1px rgba(250,250,250,0.5), 1px 1px 1px rgba(10,10,10,0.5) !important",
                    "border-radius": "8px",
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
            '.zoom-child.mpl > svg:hover,.zoom-child.mpl > svg:focus': { # matplot size inches need special treatment
                "width": "calc(100% - 100px) !important",
                "height": "calc(100% - 100px) !important",
                "object-fit": "scale-down !important",
            },
            # Nested zoom classes should occupy full space because parent is zoomed too
            ".zoom-self, .zoom-child": {
                "^:focus .vega-embed details, ^:hover .vega-embed details": {
                    "display": "none !important",
                },
                ".zoom-self, .zoom-child": {
                    "^:hover, ^:focus": {
                        "left": "0px !important",
                        "top": "0px !important",
                        "width": "100% !important",
                        "height": "100% !important",
                        "box-sizing": "border-box !important",
                        "background": "var(--bg1-color) !important",  # Avoids overlapping with other elements
                    },
                },
            },
        },
    )


def background_css(opacity=0.75, filter='blur(2px)', contain=False):
    if filter and not '(' in str(filter):
        raise ValueError(f"blur expects a CSS filter function like 'blur(2px)', 'invert()' etc. or None, got {filter}")
    
    uclass = get_unique_css_class()
    return f"""{uclass} .BackLayer {{
        position: absolute !important;
        top:0 !important;
        left:0 !important;
        width: 100% !important;
        height: 100% !important;
        box-sizing:border-box !important;
        overflow:hidden;
        margin:0;
    }}
    {uclass} .BackLayer :is(img, svg) {{
        position: absolute;
        left:50% !important;
        top:50% !important;
        transform: translate(-50%,-50%) !important; /* Make at center */
        width: 100%;
        height: 100%;
        object-fit:{('contain' if contain else 'cover')} !important;
        filter: {filter};
        opacity:{opacity};
    }}
    {uclass} .BackLayer svg {{
        max-width: {('100%' if contain else '')} !important;
        max-height: {('100%' if contain else '')} !important;
        width: {('' if contain else 'auto')} !important;
        min-width: {('' if contain else '100%')} !important;
        min-height: {('' if contain else '100%')} !important;
    }}
    {uclass} .BackLayer.jupyter-widgets-disconnected {{
        display:none;
    }}
    """
