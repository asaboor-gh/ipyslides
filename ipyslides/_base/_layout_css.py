# This should not be used by user, but is used by ipyslides to generate layout of slides

from ..utils import _build_css
from ..xmd import get_unique_css_class
from .icons import Icon

_zoom_ables = ".jp-RenderedImage > img, .zoom-self, .zoom-child > *:not(.no-zoom), .plot-container.plotly"
_icons_size = "1em"  # For all except Chevrons


def layout_css(accent_color):#TODO: should be updated in theme as well
    uclass = get_unique_css_class()
    return _build_css(
        (uclass,),
        {
            "a.jp-InternalAnchorLink": {"display": "none !important"},
            "^.SlidesWrapper": {
                "container": "slides / inline-size",
                "z-index": "1 !important",
                "^.SingleSlide .Controls": {
                    "display": "none !important",
                },
                "^:focus": {
                    "outline" : "none !important",
                },
                "^.CaptureMode": {
                    ".TopBar.Outside, .SlideArea .goto-button, .Sfresh-Btn": {
                        "visibility": "hidden !important"
                    },  # Hide in screenshot
                    ".Menu-Box" : {"display": "none !important",},
                },
                "^.PresentMode .SlideBox .SlideArea .ProxyPasteBtns": {
                    "display": "none !important"
                },  # Hide in presentation mode
                "^.FullWindow, ^.FullScreen": {
                    ".Width-Slider, .Source-Btn": {"display": "none !important"},
                },
                "^.FullScreen": {
                    ".FullWindow-Btn": {"display": "none !important"},
                },
                "@keyframes heart-beat": {
                    "from": {
                        "transform": "translateX(-16px)",
                        "opacity": "0.5",
                    },
                    "to": {
                        "transform": "translateX(0)",
                        "opacity": "1",
                    },
                },
                "^.InView-Title .Arrows.Prev-Btn, ^.InView-Last .Arrows.Next-Btn": {
                    "display": "none !important",
                },  # still should be clickable
                "^.InView-Title .Arrows.Next-Btn, ^.InView-Other .Arrows.Next-Btn": {
                    "animation-name": "heart-beat",
                    "animation-duration": "2s",
                    "animation-iteration-count": "10", # 10 times to catch attention of speaker
                    "animation-timing-function": "steps(8, end)",
                    "animation-delay": "20s",
                },
                "^.InView-Other .Arrows.Next-Btn": {
                    "animation-delay": "60s",  # Beet at 60 seconds if left on slide
                },
                ".Slide-Number" : { # slide number
                    "position": "absolute !important",
                    "right": "0 !important",
                    "bottom": "0 !important",
                    "backdrop-filter": "blur(8px)",
                },
                ".Progress-Box": {
                    "margin": "0 !important",
                    "padding": "0 !important",
                    "position": "absolute !important",
                    "left":"0 !important",
                    "bottom": "0 !important",
                    "background": "var(--secondary-bg) !important",
                    ".Progress" : {
                        "margin": "0 !important",
                        "padding": "0 !important",
                        "transition": "width 250ms ease-in-out !important",
                        "background": "var(--accent-color) !important",
                    }
                },
                ".Toast, .TOC, .SidePanel": {
                    "--text-size": "20px", # Don't need these to be zoomed in
                },
                ".Toast" : {
                    "position":"absolute",
                    "right":"4px", # top is made for animation via javascript
                    "top": "-120px", # Hides on load
                    "max-width":"55%",
                    "min-width":"300px",
                    "min-height":"100px",
                    "max-height":"65%", # so that a screenshot can show full
                    "z-index":"10000",
                    "border-radius": "8px",
                    "padding":"8px",
                    "overflow":"auto",
                    "backdrop-filter": "blur(20px)",
                    "box-shadow": "0 0 5px 0 rgba(255,255,255,0.2), 0 0 10px 0 rgba(0,0,0,0.2)",
                    "border-image": "linear-gradient(to bottom,rgba(0,0,0,0) 0, rgba(0,0,0,0) 10%, var(--accent-color) 10% , var(--accent-color) 90%, rgba(0,0,0,0) 90%, rgba(0,0,0,0) 100%) 1/ 0 0 0 3px",
                    "> button": {
                        "position":"absolute",
                        "right":"4px",
                        "top":"4px",
                        "border":"none",
                        "background":"none",
                        "border-radius":"50%",
                        "font-size":"20px",
                    },
                    ":is(h1, h2, h3, h4, h5, h6)" : {"text-align": "left !important"},
                },
                ".LogoHtml": {"position": "absolute !important",}, # other properties are set internally
                ".Loading": {
                    "position": "absolute",
                    "left": "50%",
                    "top": "50%",
                    "transform": "translate(-50%,-50%)",
                    "z-index": "11",  # Above all
                    "text-shadow": "0 0 4px white, 0 0 8px var(--secondary-bg)",
                    "border-radius": "50%",
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
                    "^.Out-Sync" : {
                        "visibility": "visible !important",
                        "z-index": "12 !important",
                        "height": "50% !important", # see behind
                        "width": "50% !important", # see behind
                        "border": "2px solid red !important",
                        "background": "#fdd",
                        "^:nth-child(1)" : {"translate": "-16px -16px !important"},
                        "^:nth-child(2)" : {"translate": "-8px -8px !important"},
                        "^::before" : {
                            "content": "'citations got out of sync, rerun corresponding slides to update'",
                            "font-size": "120%",
                            "color":"red",
                        }
                    },
                    ".export-only": {"display": "none !important"},
                    ".jp-OutputArea": {
                        "width": "100% !important",
                        "height": "auto !important", # This is must for layout
                        "box-sizing": "border-box !important",
                    },  # Otherwise it shrinks small columns
                    _zoom_ables: {
                        "cursor": "zoom-in",
                    },
                    ".Sfresh-Box": {
                        "column-gap": "0.2em",
                    },
                    ".Sfresh-Out": {
                        "width": "100%",
                        "box-sizing": "border-box",
                    },  # Otherwise it is too close to border
                    ".Sfresh-Btn": {
                        "display": "flex",
                        "align-items": "center",
                        "font-size": "14px !important",  # it is bit larger than other buttons, so decrease font size
                        "min-height": "24px",
                        "z-index": "5",  # Above controls if collide
                        "width": "24px !important",  # Make it round
                        "min-width": "24px !important",
                        "border-radius": "50% !important",
                        "border": "none !important",
                        "transition": "transform 0.2s ease-in-out",
                        "^.Hidden": {"display": "none !important"},
                        "^:hover": {
                            "transform": "scale(1.2)",
                        },
                    },
                },
                "kbd" : {
                    "color":"var(--secondary-fg)",
                    "background": "var(--secondary-bg)",
                    "border": "1px solid var(--hover-bg)",
                    "border-radius": "0.2em",
                },
                ".export-only": {"display": "none !important"},
                ".widget-inline-hbox": {
                    ".widget-label": {"color": "var(--primary-fg)"},
                    ".widget-readout": {
                        "color": "var(--primary-fg) !important",
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
                            "background": "var(--hover-bg) !important",
                            "border-color": "var(--hover-bg) !important",
                        },
                    },
                },
                ".widget-html": {
                    "^:not(div.LaserPointer), .widget-html-content > div": {
                        "display": "grid !important",
                        "font-size": "var(--text-size) !important",
                    },
                    ".widget-html-content": {
                        "pre, code, p": {
                            "font-size": "100% !important",
                        },  # otherwise it is so small
                    },
                },
                ".SidePanel": {
                    "background": "var(--alternate-bg)",
                    "position": "absolute",
                    "border": "none",
                    "padding": "0 !important",
                    "width": "60% !important",
                    "z-index": "10",
                    "top": "0px !important",
                    "left": "0px !important",
                    "transition": "height 400ms ease-in-out",
                    "border-right" : "2px inset var(--alternate-bg)",
                    "@container slides (max-width: 650px)": {"width": "100% !important"},
                    ".CaptureHtml": {
                        "border": "1px solid var(--secondary-fg)",
                        "figure": {
                            "width": "100% !important",
                            "margin": "0",
                            "padding": "0",
                            "background": "var(--secondary-bg)",
                        },
                    },
                    ".Settings-Btn": {
                        "border": "none !important",
                        "outline": "none !important",
                        "font-size": "20px",
                        "background": "transparent !important",
                        "> i": {
                            "color": "var(--accent-color) !important",
                        },
                    },
                },
                ":is(.SlideBox, .SidePanel) :is(button, .jupyter-button)": {
                    "border": "1px solid var(--accent-color)",
                    "border-radius": "4px",
                    "min-height": "28px",
                    "min-width": "28px",
                },
                "^, *": {
                    "box-sizing": "border-box",
                },
                "button:not(.tlui-button)": {
                    "color": "var(--accent-color)!important",
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
                    "background": "var(--hover-bg)",
                    "text-shadow": "0 0 2px var(--primary-bg), 0 0 4px var(--accent-color)",
                },
                ".widget-play .jupyter-button": {
                    "background": "var(--secondary-bg)",
                    "color": "var(--accent-color)!important",
                },
                ".widget-dropdown": {
                    "> select, > select > option": {
                        "color": "var(--primary-fg)!important",
                        "background": "var(--primary-bg)!important",
                    },
                },
                ".jupyter-widgets:not(button)": {
                    "color": "var(--primary-fg) !important"
                },  # All widgets text color
            },
            ".NavWrapper": {
                "max-width": "100% !important",
                "position": "absolute !important",
                "left": "0 !important",
                "bottom": "3px !important", # leave space for progressbar
                "background": "var(--primary-bg)", # Do not use important, let user change it with set_css
                "width": "100% !important",
                "^,^ > div": {
                    "padding": "0px",
                    "margin": "0px",
                    "overflow": "hidden",
                    "max-width": "100%",
                },
                ".NavBox": {
                    "z-index": "2",
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
                        "width": "0 !important",
                        "transition": "width 400ms ease-in-out", # transition on exit
                        "overflow": "hidden !important", # needs to not jump on chnage of width
                    },
                    "^:hover, ^:focus, ^:active, ^.mod-active, ^.Active-Start" : {
                        ".Menu-Box" : {
                            "width": "132px !important", # 4*28 + margin + paddings
                            "transition": "width 400ms ease-in-out", # transition on enter hover
                             "overflow": "hidden !important", # avoid jump on hover too
                        },
                    },
                    ".Toc-Btn, .Menu-Btn, .Screenshot-Btn": {
                        "min-width": "28px",
                        "width": "28px", # need this too
                    },  # Avoid overflow in small screens
                    ".Footer": {
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
                "right": "16px !important",
                "bottom": "0px !important",
                "z-index": "4",  # below matplotlib fullsreen
                "padding": "0 !important",
                "justify-content": " flex-end !important",
                "align-items": "center !important",
                "margin-bottom": "16px !important",
                "color": " var(--accent-color) !important",
                ".widget-button > i": {
                    "color": "var(--accent-color) !important",
                },
                ".Arrows": {
                    "opacity": "0.4",
                    "font-size": "36px",
                    "padding": "4px",
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
                "position":"absolute",
                "left": "0",
                "bottom": "0",
                "display": "table-column-group !important", # This to avoid collapsing divs
                "background": "var(--secondary-bg)",
                "backdrop-filter": " blur(50px)",
                "margin": "4px 36px",
                "position": " absolute",
                "min-width": "60% !important",
                "box-sizing": "border-box !important",
                "z-index": "8",
                "border-radius": "4px",
                "transition": "height 400ms ease-in-out",
                "@container slides (max-width: 650px)": {"min-width": "calc(100% - 72px) !important"},
                ".goto-box": {
                    "justify-content": "space-between",
                    "height": "auto",
                    "width": "auto",
                    "padding-right": "8px",
                    "border-right": "4px solid var(--alternate-bg)",
                    "box-sizing": "border-box !important",
                    "^:hover": {
                        "font-weight": "bold",
                        "border-right": "4px solid var(--alternate-bg)",
                        "background": "var(--alternate-bg)",
                    },
                },
                ".goto-button": {
                    "min-width": "max-content",
                    "position": "absolute",
                    "width": "100%",
                    "height": "100%",
                    "box-sizing": "border-box",
                    "padding": 0,
                    "margin": 0,
                },
                ".Menu-Item": {
                    "font-size": "18px !important",
                },
                ".goto-html": {
                    "width": "100%",
                    "height": "max-content",
                    "box-sizing": "border-box",
                    ".custom-html": {
                        "box-sizing": "border-box",
                        "padding-left": "2em !important",
                        "display": "flex",
                        "flex-direction": "row",
                        "flex-wrap": "nowrap",
                        "justify-content": "space-between !important",
                        "align-items": "top",
                        "span:first-of-type": {
                            "position": "absolute",
                            "top": "0 !important",  # must have thing
                            "height": "100%",
                            "margin-left": "-2em !important",
                        },
                    },
                },
            },
            ".CaptureHtml *": {
                "font-size": "0.9em",
                "line-height": "0.9em  !important",
            },
            ".TopBar": {
                "margin-top": "8px !important",  # Avoid overlap with topbar outside
                "display": "flex",
                "overflow-x": "auto",
                "overflow-y": "hidden", # hides useless scrollbars
                "min-height": "36px !important",
                "align-items": "center !important",
                "padding-top": "4px !important",
                "box-sizing": "border-box !important",
                "^.Inside": {"padding-left": "12px","padding-right": "12px"},
                "button": {
                    "font-size": "18px !important",
                    "padding-top": "2px !important",
                    "min-width": "max-content !important",
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
                "background": "var(--secondary-bg) !important",
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
                    },
                },
                "> button > i": {"margin-right": "8px !important",}, # Make uniform
                "> button::after":{
                    "content": "attr(title)",
                    "font-size": "14px !important",
                    "color": "var(--primary-fg) !important",
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
                    "background": "var(--secondary-bg) !important",
                    "color": "var(--secondary-fg)",
                },
                ":not(pre) > code, :not(pre) > span": {  # To avoid overflow due to large words
                    "word-break": "normal !important",
                    "overflow-wrap": "break-word !important",
                },
                "p": {
                    "margin-bottom": "0.2em !important",
                },
                "pre, code": {
                    "color": "var(--primary-fg)",
                },
            },
            ".jp-RenderedText": {
                "*": {"font-size": "0.9em !important",},
                "^, pre": {
                    "color": "var(--primary-fg) !important",
                },
            },
            ".Draw-Wrapper": { # height is set dynamically
                "position": "absolute !important",
                "left": 0,
                "top":0,
                "z-index": "8 !important",
                "overflow": "hidden !important",
                "transition": "height 200ms",
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
                "backdrop-filter": "blur(50px)",
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
                    'fill':'var(--primary-bg)',
                    'stroke':'var(--secondary-bg)',
                },
            },
            ".Arrows": {
                ".fa.fa-chevron-left": Icon(
                    "chevron", color=accent_color, size="36px", rotation=180
                ).css,
                ".fa.fa-chevron-right": Icon(
                    "chevron", color=accent_color, size="36px", rotation=0
                ).css,
                ".fa.fa-chevron-up": Icon(
                    "chevron", color=accent_color, size="36px", rotation=-90
                ).css,  # Why SVG rotation is clockwise?
                ".fa.fa-chevron-down": Icon(
                    "chevron", color=accent_color, size="36px", rotation=90
                ).css,
            },
            ".Settings-Btn": {
                ".fa.fa-plus": Icon("settings", color=accent_color, size=_icons_size).css,
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
                    "arrow", color=accent_color, size=_icons_size, rotation=180
                ).css,
            },
            ".FullScreen-Btn": {
                ".fa.fa-plus": Icon("expand", color=accent_color, size=_icons_size).css,
                ".fa.fa-minus": Icon(
                    "compress", color=accent_color, size=_icons_size
                ).css,
            },
            ".Refresh-Btn, .Sfresh-Btn": {
                ".fa.fa-plus": Icon(
                    "refresh", color=accent_color, size=_icons_size
                ).css,
                ".fa.fa-minus": Icon(
                    "loading", color=accent_color, size=_icons_size
                ).css,
            },
            ".Screenshot-Btn .fa.fa-camera": Icon(
                "camera", color=accent_color, size=_icons_size
            ).css,
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
            ".FullWindow-Btn": {
                ".fa.fa-plus": Icon(
                    "win-maximize", color=accent_color, size=_icons_size
                ).css,
                ".fa.fa-minus": Icon(
                    "win-restore", color=accent_color, size=_icons_size
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
                    "arrow-bar", color=accent_color, size=_icons_size, rotation=180,
                ).css,
            },
            ".End-Btn": {
                ".fa.fa-plus": Icon(
                    "arrow-bar", color=accent_color, size=_icons_size
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
                "^:hover": {"font-weight": "bold !important","font-size": "0.9em !important",},
                "^:hover, ^:focus, ^:active, ^.mod-active" : {
                    "box-shadow": "none !important",
                    "outline": "none !important",
                },
            },
            "@media print": { # Needs modification
                ".SlidesWrapper": {
                    "^, ^.FullWindow": {
                        "height": "auto !important",
                    },
                },
                ".Controls, .NavWrapper button, div.LaserPointer": {
                    "display": "none !important",
                },
                ".NavWrapper p": {
                    "margin-left": "16px",
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
            "<body[data-base-url]": {  # Voila
                "position": "fixed !important",
                "top": "0 !important",
                "left": "0 !important",
                "right": "0 !important",
                "bottom": "0 !important",
                "background": "var(--alternate-bg)",
                "^, *": {
                    "color": "var(--primary-fg)",
                },
                "::-webkit-scrollbar": {
                    "height": "4px",
                    "width": "4px",
                    "background": "transparent !important",
                    "^:hover": {
                        "background": "var(--secondary-bg) !important",
                    },
                },
                "::-webkit-scrollbar-thumb": {
                    "background": "transparent !important",
                    "^:hover": {
                        "background": "var(--hover-bg) !important",
                    },
                },
                "::-webkit-scrollbar-corner": {
                    "display": "none !important",
                },
                ".widget-text input": {
                    "background": "var(--primary-bg)",
                    "color": "var(--primary-fg)",
                },
                "#rendered_cells": {
                    "height": "100% !important",
                    "overflow": "auto !important",
                    ".raw-text": {
                        "color": "var(--primary-fg)",
                    },
                },
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
            ".InView-Btn": {
                "display": "none !important",
            },
            "<.jp-LinkedOutputView > .jp-OutputArea > .jp-OutputArea-child": {
                "height": "100% !important", # This needs to in same selector order to not effect slide content
                ".SlidesWrapper, .DisplayBox": {
                    "min-width": "100% !important",
                    "width": "100% !important",
                    "min-height": "100% !important",
                    "height": "100% !important",
                    "box-sizing": "border-box !important",
                    ".InView-Btn": {
                        "display": "block !important",
                        "position": "absolute",
                        "top": "0",
                        "left": "0",
                        "z-index": "10",
                        "color": "white !important",
                        "background": "green !important",
                        "font-size": "14px !important",  # Avoid this button font scaling
                    },
                    ".Width-Slider": {
                        "display": "none !important",
                    },
                },
            },
            "<#ipython-main-app .SlidesWrapper .output_scroll": {  # For classic Notebook output
                "height": "unset !important",
                "-webkit-box-shadow": "none !important",
                "box-shadow": "none !important",
            },
        },
    )


def viewport_css(): 
    uclass = get_unique_css_class()
    return f"""
    html, body {{ /* Voila is handled separately */
        height: 100vh !important;
        max-height: 100vh !important;
        box-sizing: border-box !important;
    }}
    .jp-LinkedOutputView {uclass}.SlidesWrapper, /* It can handle sidecar as well, besides intended options */
    .jp-MainAreaWidget {uclass}.SlidesWrapper, /* Somehow notebook (and other panels) itself is treated as viewport in JupyterLab, override it */
    body[data-base-url] {uclass}.SlidesWrapper {{ /* for voila */
        position: fixed !important;
        left: 0 !important;
        top:0 !important;
        width:100vw !important;
        height:100vh !important;
        z-index: 100 !important; /* Show on top of everything */
    }}
    #menubar-container {{ display: none !important; }} /* For classic Notebook */
    body[data-kaggle-source-type] .jp-Notebook {{ /* For Kaggle */
        min-width: 0 !important;
        padding-right: 100vw !important;
    }}
    """


def zoom_hover_css():
    return _build_css(
        (".SlideArea",),
        {
            # Matplotlib by plt.show, self zoom, child zoom, plotly
            _zoom_ables: {
                "^:hover, ^:focus": {
                    "cursor": "auto",  # Ovverride zoom-in cursor form main layout
                    "position": "fixed",
                    "backdrop-filter": "blur(50px)",
                    "left": "50px",
                    "top": "50px",
                    "z-index": 8,
                    "width": "calc(100% - 100px)",
                    "height": "calc(100% - 100px)",
                    "object-fit": "scale-down !important",
                    "box-shadow": "-1px -1px 1px rgba(250,250,250,0.5), 1px 1px 1px rgba(10,10,10,0.5)",
                    "border-radius": "4px",
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
                        "background": "var(--primary-bg) !important",  # Avoids overlapping with other elements
                    },
                },
            },
        },
    )


def glass_css(opacity=0.75, blur_radius=50):
    uclass = get_unique_css_class()
    return f"""{uclass} .BackLayer, {uclass} .BackLayer .Front {{
        position: absolute !important;
        top:0 !important;
        left:0 !important;
        width: 100% !important;
        height: 100% !important;
        box-sizing:border-box !important;
        overflow:hidden;
        margin:0;
    }}
    {uclass} .BackLayer img{{
        position: absolute;
        left:0;
        top:0;
        width: 100%;
        height: 100%;
        object-fit:cover;
        filter: blur({blur_radius}px);
    }}
    {uclass} .BackLayer .Front {{
        background: var(--primary-bg);
        opacity:{opacity};
    }}
    {uclass} .BackLayer.jupyter-widgets-disconnected {{
        display:none;
    }}
    """
