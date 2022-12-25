# This should not be used by user, but is used by ipyslides to generate layout of slides

from ..utils import _build_css
from .icons import Icon

_zoom_ables = '.jp-RenderedImage > img, .zoom-self, .zoom-child > *:not(.no-zoom), .plot-container.plotly'
_icons_size = '1em' # For all except Chevrons

def layout_css(breakpoint, accent_color, show_laser_pointer = False): # Defult is off
    return _build_css((),{
        'a.jp-InternalAnchorLink': {'display': 'none !important'},
        '.SlidesWrapper': {
            'z-index': '10 !important',
            '^.CaptureMode': {
                '.SlideArea .goto-button, .TopBar.Outside': {'display':'none !important'}, # Hide in screenshot
            },
            '^.FullWindow': {
                '.Height-Dd, .Width-Slider, .SideBar-Btn': {'display': 'none !important'},
            },
            '^.FullScreen': {
                '.SideBar-Btn, .FullWindow-Btn': {'display': 'none !important'},
            },
            '^.SideMode': {
                '.Height-Dd': {'display': 'none !important'},
            },
            '@keyframes heart-beat': {
                '0%': {'transform': 'scale(1)','opacity': '0.5','filter': 'drop-shadow(0 0 2px var(--hover-color))'},
                '50%': {'transform': 'scale(0.7)', 'opacity': '1','filter': 'drop-shadow(0 0 4px var(--pointer-color))'},
            },
            '^.InView-Title .Arrows.Prev-Btn, ^.InView-Last .Arrows.Next-Btn': {'opacity': '0.02',}, # still should be clickable
            '^.InView-Title .Arrows.Next-Btn, ^.InView-Other .Arrows.Next-Btn': {
                'animation-name': 'heart-beat',
                'animation-duration': '2s',
                'animation-iteration-count': 'infinite',
                'animation-timing-function': 'ease-in-out',
            },
            '^.InView-Other .Arrows.Next-Btn': {
                'animation-delay': '60s', # Beet at 60 seconds if left on slide
                'animation-iteration-count': '15', # 5 times to show 1.5 minute passed
            },
            '.SlideArea': {
                'align-items': 'center',
                f'@media screen and (max-width: {breakpoint})': {
                'min-width' : '100% !important', # can't work without min-width
                'width':'100% !important', 
                'padding-bottom': '50px !important',
                },
                '.report-only': {
                    'display': 'none !important'
                },
                _zoom_ables: {'cursor':'zoom-in',},
            },
            '.export-only': { 'display': 'none !important' },
            '.widget-inline-hbox': {
                '.widget-label': { 'color': 'var(--primary-fg)' },
                '.widget-readout': { 
                    'color': 'var(--primary-fg) !important',
                    'box-shadow': 'none',
                    'min-width':'auto !important',
                },
            },
            '.widget-html': {
                '^:not(div.LaserPointer), .widget-html-content > div' :{
                    'display': 'grid !important',
                    'font-size': 'var(--text-size) !important',
                },
                '.widget-html-content': {
                    'pre, code, p': {'font-size': '100% !important',}, #otherwise it is so small
                },
            },
            '.SidePanel': {
                'backdrop-filter': 'blur(200px)',
                'position': 'absolute',
                'border': 'none',
                'padding': '8px !important',
                'width': '60% !important',
                'z-index': '102',
                'top': '0px !important',
                'left': '0px !important',
                'height': '100% !important',
                'box-shadow': '0 0 4px 4px var(--secondary-bg)',
                f'@media screen and (max-width: {breakpoint})': {'width': '100% !important'},
                '.CaptureHtml' : {
                    'border': '1px solid var(--secondary-fg)',
                    'figure' : {
                        'width': '100% !important',
                        'margin': '0',
                        'padding': '0', 
                        'background': 'var(--secondary-bg)'
                    },
                },
                '.Settings-Btn': {
                    'border':'none !important',
                    'outline':'none !important',
                    'font-size': '20px',
                    'background': 'transparent !important',
                    '> i': { 'color': 'var(--accent-color) !important',},
                },
                '.SidePanel-Text .widget-html-content': {'line-height': 'inherit !important',},
            },
            ':is(.SlideBox, .SidePanel) :is(button, .jupyter-button)': { 
                'border': '1px solid var(--accent-color)',
                'border-radius':'4px',
                'min-height':'28px',
                'min-width':'28px',  
            },
            '^, *': {'box-sizing': 'border-box',},
            'button': {
                'color': 'var(--accent-color)!important',
                'border-radius':'0px',
                'background': 'transparent !important',
                'display': 'flex',
                'align-items': 'center', # center the icon vertically
                'justify-content': 'center',
                '> i': {'color': 'var(--accent-color) !important',},
            },
            '.jupyter-button:hover:enabled, .jupyter-button:focus:enabled': {
                'outline':'none !important',
                'opacity':'1 !important',
                'box-shadow':'none !important',
                'background':'var(--hover-bg)',
                'text-shadow': '0 0 2px var(--primary-bg), 0 0 4px var(--accent-color)',
            },
            '.widget-play .jupyter-button': {
                'background': 'var(--secondary-bg)',
                'color': 'var(--accent-color)!important',
            },
            '.widget-dropdown': {
                '> select, > select > option': {
                    'color': 'var(--primary-fg)!important',
	                'background': 'var(--primary-bg)!important',
                },
            },
            '.widget-hslider' : {
                '.ui-slider, .ui-slider-handle': {
                    'background': 'var(--accent-color)',
                    'border': '1px solid var(--accent-color)',  
                },
            },
            '.jupyter-widgets:not(button)': { 'color': 'var(--primary-fg) !important'}, # All widgets text color
            '.Intro': {
                'summary': {
                    'background': 'var(--secondary-bg)',
                    'padding-left':'0.2em',
                    'color': 'var(--heading-color)',
                    'font-weight': 'bold',
                },
            },
        },
        'div.LaserPointer': { # For laser pointer 
            'position':'absolute !important',
            'width':'12px',
            'height':'12px',
            'left':'-50px', # Hides when not required , otherwise handled by javascript*/
            'z-index':'101', # below side panel but above zoomed image */
            'border-radius':'50%',
            'border':' 2px solid white',
            'background':' var(--pointer-color)',
            'box-shadow':' 0 0 4px 2px white, 0 0 6px 6px var(--pointer-color)',
            'display':'none', # Initial setup. Display will be set using javascript only */
            'overflow':'hidden !important', # To hide at edges */
            'opacity': f'{1 if show_laser_pointer else 0} !important',
        },
        '.NavWrapper': {
            'max-width': '100% !important',
            '.progress': {
                'background': 'var(--secondary-bg) !important',
                '.progress-bar': { 'background': 'var(--accent-color) !important' },
            },
            '.NavBox': {
                'align-items': 'center',
                'height':'max-content',
                'justify-content': 'flex-start',
                '.Toc-Btn': {'min-width':'40px',}, # Avoid overflow in small screens
            },
        },
        '.FloatControl': {
            'position': ' absolute',
            'right': '0',
            'top': '0',
            'width': '32px',
            'height': '32px',
            'z-index': '51',
            'background': 'var(--primary-bg)',
            'opacity': '0',
            'overflow': 'hidden',
            'padding': '4px',
            '^:hover, ^:focus': {
                'width':'max-content',
                'height':'50%',
                'opacity':1,
                
            },   
        },
        '.Controls' : {
            'position':'absolute',
            'right':'16px !important',
            'bottom':'0px !important',
            'z-index':'95', # below matplotlib fullsreen 
            'padding':'0 !important',
            'justify-content':' flex-end !important',
            'align-items':'center !important',
            'margin-bottom':'16px !important',
            'color':' var(--accent-color) !important',
            f'@media screen and (max-width: {breakpoint})': {
                    'bottom': '30px !important',
                    'right': '0 !important',
                    'width' : '100%',
                    'justify-content': 'space-around !important',
                    'button' : {'width': '30% !important'},
            },
            '.widget-button > i': { 'color': 'var(--accent-color) !important',},
            '.Arrows': {
                'opacity':'0.4',
                'font-size': '36px',
                'padding':'4px',
                '^:hover, ^:focus': {'opacity': 1}, 
            },
            '.ProgBox': {
                'width': '16px',
                'padding': '0px 4px',
                'opacity':0,
                'overflow': 'hidden',
                'transition': 'width 0.4s',
                '^:hover, ^:focus': {
                    'width': '50%',
                    'min-width': '30%', # This is very important to force it 
                    'justify-content': 'center',
                    'opacity': 1,
                },
                f'@media screen and (max-width: {breakpoint})': {'width': '40%', 'opacity': 0,},
            },
        },
        '.TOC': { # Table of contents panel
            'backdrop-filter':' blur(200px)',
            'margin':' 4px 36px', 
            'padding':' 0.5em',
            'position':' absolute',
            'min-width':' 60% !important',
            'height':' calc(100% - 8px) !important',
            'box-sizing':'border-box',
            'z-index':' 100',
            'border-radius':' 4px',
            'border':' 1px solid var(--hover-bg)',
            f'@media screen and (max-width: {breakpoint})': {'min-width': 'calc(100% - 72px) !important'},
            '.goto-box': {
                'justify-content': 'space-between',
                'height': 'auto',
                'width': 'auto',
                'box-sizing':'border-box !important',
                '^:hover': {'font-weight':'bold',},
            },
            '.goto-button': {
                'position': 'absolute',
                'width': '100%',
                'height': '100%',
                'box-sizing':'border-box',
                'padding': 0,
                'margin':0,
            },
            '.Menu-Item': {'font-size': '18px !important',},
            '.goto-html': {
                'width':'100%',
                'height':'max-content',
                'box-sizing':'border-box',
                '.widget-html-content': {
                    'box-sizing': 'border-box',
                    'padding-left':'2em !important',
                    'display': 'flex',
                    'flex-direction': 'row',
                    'flex-wrap':'nowrap',
                    'justify-content':'space-between !important',
                    'align-items':'top',
                    'span:first-of-type': {
                       'position':'absolute',
                       'top':'0 !important', # must have thing 
                       'height':'100%',
                       'margin-left':'-2em !important',
                  }, 
               }, 
            },
        },
        '.CaptureHtml *': {
            'font-size': '0.9em',
            'line-height': '0.9em  !important',
        },
        '.TopBar': {
            'margin-top': '8px !important', # Avoid overlap with topbar outside
            'display':'flex',
            'overflow': 'scroll',
            'min-height': '36px !important',
            'align-items': 'center !important',
            'padding-top': '4px !important',
            'box-sizing': 'border-box !important',
            'button': {
                'font-size': '18px !important',
                'padding-top':'2px !important',
                'min-width': 'max-content !important',
                'outline': 'none !important',
                'border': 'none !important',
                'box-shadow': 'none !important',
                'background': 'transparent !important',
                'backdrop-filter': 'blur(20px)',
                '> i': { 'color': 'var(--accent-color) !important',},
                '^:disabled,^[disabled]': {'display': 'none !important',},
            },
        },
        '.TopBar.Outside': {
            'position': 'absolute !important',
            'z-index': '98 !important', # below matplotlib fullsreen
            'top': '0 !important',
            'margin': '0 !important',
            'min-height': '32px !important',
            'width': '60px !important',
            'padding-top': '0 !important',
            'transition': 'width 400ms',
            '^:hover, ^:focus': {
                'min-height': '32px !important',
                'width': '60% !important',
                f'@media screen and (max-width: {breakpoint})': {'width': 'calc(100% - 16px) !important'}, # There is 8px margin
                '> .Settings-Btn' : {
                    'width': 'auto !important',
                    'opacity': '1 !important',
                    'margin-right': 'unset !important', # Unset after hover, foucs
                },
            }, # Should be same as side panel
            '> .Settings-Btn' : {
                'width': '30px !important',
                'margin-right': '30px !important', # need for hover, foucs
                'opacity': '0.4 !important' # make same as other buttons
            },
            '> *:not(.Settings-Btn)' : {'display': 'none !important'},
            '^:hover > *:not(:disabled), ^:focus > *:not(:disabled)': { 'display': 'unset !important'},
        },
        '.Inline-Notes': {
            'background': 'var(--primary-bg)',
            'color': 'var(--primary-fg)',
            'border': '1px solid var(--accent-color)',
            'border-radius':'4px',
            'width': '85% !important', # To see all of the text
            'box-sizing': 'border-box',
            '> div': {
                'display': 'flex',
                'flex-direction':'column',
                'justify-content': 'space-between',
                'padding':'4px',
            },
        },
        '.jp-OutputArea-child': {
            '^, .jp-OutputArea-output': { # For some themes
                'background': 'transparent !important',
                'background-color': 'transparent !important', 
                'margin': '0 !important', 
            },  
        },
        '.jp-RenderedHTMLCommon': {
            'padding': 0,
            'padding-right': '0 !important', # important for central layout
            'font-size': 'var(--text-size)',
            ':not(pre) > code': {
                'background': 'var(--secondary-bg) !important', 
                'color':'var(--secondary-fg)',
            },
            ':not(pre) > code, :not(pre) > span': { # To avoid overflow due to large words
                'word-break': 'normal !important',
                'overflow-wrap': 'break-word !important',
            },
            'p': {'margin-bottom': '0.2em !important',},
            'pre, code': {'color':'var(--primary-fg)',},
        },
        '.jp-RenderedText': {
            '^, pre': {
                'color':'var(--primary-fg) !important',
            }, 
        },
        '.OverlayHtml': {
            'backdrop-filter': 'blur(50px)',
            'margin':0,
            'z-index': 97,
            'overflow': 'hidden !important',
            'transition': 'height 200ms',
            '^, > div': {
               'position': 'absolute !important',
               'left': '0',
               'top': '0',
               'width': '100%',
               'box-sizing': 'border-box',
            },
            '> div': { 'height': '100% !important',}, # Do not set height for .OverlayHtml, it is done by widgets
            '.widget-html-content > div': {
                '> span': {
                    'height': '32px !important',
                    'overflow': 'hidden !important',
                    'position': 'absolute',
                    'top': 0,
                    'padding-left': '36px !important',
                    'padding-right': '8px',
                    'padding-top': '2px !important',
                    'color': 'var(--secondary-fg)',
                    'background': 'var(--secondary-bg) !important',
                    'font-size': '18px',
                    'border': '1px solid var(--hover-bg)',
                    'border-bottom': 'none',
                    'border-radius': '0.4em 0.4em 0 0',    
                },
                '> iframe, > .block': {
                    'position': 'absolute',
                    'top': '32px !important',
                    'height': 'calc(100% - 32px) !important',
                },
                '> .block': {
                    '^, .docs': { 'overflow': 'scroll !important',},
                },
            },
        },
        '.Arrows': {
                '.fa.fa-chevron-left': Icon('chevron', color=accent_color, size='36px', rotation=180).css,
                '.fa.fa-chevron-right': Icon('chevron', color=accent_color, size='36px',rotation=0).css,
                '.fa.fa-chevron-up': Icon('chevron', color=accent_color, size='36px',rotation=-90).css, # Why SVG rotation is clockwise?
                '.fa.fa-chevron-down': Icon('chevron', color=accent_color, size='36px',rotation=90).css,
        },
        '.Settings-Btn': {
            '.fa.fa-plus': Icon('dots', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('close', color=accent_color, size=_icons_size).css,
        },
        '.Toc-Btn': {
            '.fa.fa-plus': Icon('bars', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('close', color=accent_color, size=_icons_size).css,
        },
        '.Overlay-Btn': {
            '.fa.fa-plus': Icon('pencil', color=accent_color, size=_icons_size, rotation=45).css,
            '.fa.fa-minus': Icon('arrow', color=accent_color, size=_icons_size, rotation=180).css,
        },
        '.FullScreen-Btn': {
            '.fa.fa-plus': Icon('expand', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('compress', color=accent_color, size=_icons_size).css,
        },
        '.Timer-Btn': {
            '.fa.fa-plus': Icon('play', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('pause', color=accent_color, size=_icons_size).css,
        },
        '.Screenshot-Btn .fa.fa-camera': Icon('camera', color=accent_color, size=_icons_size).css,
        '.Laser-Btn': {
            '.fa.fa-plus': Icon('laser', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('circle', color=accent_color, size=_icons_size).css,
        },
        '.Zoom-Btn': {
            '.fa.fa-plus': Icon('zoom-in', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('zoom-out', color=accent_color, size=_icons_size).css,
        },
        '.FullWindow-Btn': {
            '.fa.fa-plus': Icon('win-maximize', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('win-restore', color=accent_color, size=_icons_size).css,
        },
        '.SideBar-Btn': {
            '.fa.fa-plus': Icon('columns', color=accent_color, size=_icons_size).css,
            '.fa.fa-minus': Icon('rows', color=accent_color, size=_icons_size).css,
        },
        '@media print': {
            '.SlidesWrapper':{
                '^, ^.FullWindow': { 
                    'height': 'auto !important',
                },  
            },
            '.Controls, .NavWrapper button, .FloatControl, div.LaserPointer': {
                'display':'none !important',
            },
            '.NavWrapper p': {
                'margin-left':'16px',
            },
            'pre, .SlideBox, .SlidesWrapper, .SlideArea': {
                'height': 'auto !important',
            },
            '.SlidesWrapper .highlight, .SlideArea .raw-text': {
                'max-height':'auto !important', # Flow itself 
            },
            '.SlideArea': {
                'width': '100% !important',
            },
        }, # @media print
        'body[data-base-url]': { #Voila
            'position': 'fixed !important',
            'top': '0 !important',
            'left': '0 !important',
            'right': '0 !important',
            'bottom': '0 !important',
            'background': 'var(--alternate-bg)',
            '^, *':{ 
                'color':'var(--primary-fg)',
                'scrollbar-width':'thin', # FireFox <3
                'scrollbar-color':'var(--alternate-bg) transparent',
            },
            '::-webkit-scrollbar': {
                'height':'4px',
                'width':'4px',
                'background':'transparent !important', 
                '^:hover': {'background':'var(--secondary-bg) !important',},
            },
            '::-webkit-scrollbar-thumb': {
                'background':'transparent !important',
                '^:hover': {'background':'var(--hover-bg) !important',},
            },
            '::-webkit-scrollbar-corner': {'display':'none',},
            '.widget-text input': {
                'background':'var(--primary-bg)',
                'color':'var(--primary-fg)',
            },
            '#rendered_cells': {
                'height': '100% !important',
                'overflow': 'auto !important',
                '.raw-text': { 'color': 'var(--primary-fg)',},
            },
        },
        # Other issues
        '#jp-top-panel, #jp-bottom-panel, #jp-menu-panel': {'color': 'inherit'},
        '.CodeMirror': {
            'padding-bottom':'8px !important',
            'padding-right':'8px !important',
        }, # Jupyter-Lab make space in input cell
        '.cell-output-ipywidget-background': { # VSCode issue */
            'background': 'var(--theme-background,inherit) !important',
            'margin': '8px 0px',
        },
        '.ExtraControls': {'background':'var(--secondary-bg) !important','padding-left':'8px !important'},
        '.jp-LinkedOutputView': {
            '.SlidesWrapper': {
                'display': 'none !important', # Double Display does not work properly
            },
            '.ExtraControls': {
                'display': 'block !important', 
                'box-sizing': 'border-box',
                '^:before': {
                    'content': '"Multiple views of slides do not behave properly, you can use this area for notes though!"',
                    'display': 'block !important',
                    'color': 'var(--secondary-fg)',
                },
            },   
        },
        '#ipython-main-app .SlidesWrapper .output_scroll': { # For classic Notebook output
            'height': 'unset !important',
            '-webkit-box-shadow': 'none !important',
            'box-shadow': 'none !important',
        },
    })

def sidebar_layout_css(span_percent = 40):
    return f'''
.jp-LabShell, 
body[data-base-url], /* For Voila */
body[data-retro]>div#main, 
body[data-notebook]>div#main {{ /* Retrolab will also rise Notebook 7 */ 
    right: {span_percent}vw !important;
    margin-right:1px !important;
    min-width: 0 !important;
}}
body[data-kaggle-source-type] .jp-Notebook {{ /* For Kaggle */
    min-width: 0 !important;
    padding-right: {span_percent}vw !important;
}}
.jp-LabShell .SlidesWrapper,
body[data-base-url] .SlidesWrapper, /* For Voila */
body[data-retro] .SlidesWrapper,
body[data-notebook] .SlidesWrapper{{
    position:fixed;
    top:0px !important;
    right:0px !important;
    height: 100% !important;
    width: {span_percent}vw !important; 
}}

/* Very important to keep slides ON even Notebook hidden */
.jp-LabShell .jp-NotebookPanel.p-mod-hidden {{
    display:block !important;
    height:0 !important;
    min-height:0 !important;
    border:none !important;
}}
/* Override hiding on scroll in Notebook V7 and associated view of Jupyter lab*/
.jp-WindowedPanel-window > div.jp-Cell {{
    display: block !important; 
}}
'''

def zoom_hover_css(span_percent):
    return _build_css(('.SlideArea',), {
        # Matplotlib by plt.show, self zoom, child zoom, plotly
        _zoom_ables: {
            '^:hover, ^:focus': {
                'cursor': 'default', # Ovverride zoom-in cursor form main layout
                'position': 'fixed',
                'backdrop-filter': 'blur(200px)',
                'left':f'calc({100-span_percent}% + 50px)',
                'top':'50px',
                'z-index':100,
                'width': f'calc({span_percent}% - 100px)',
                'height': 'calc(100% - 100px)',
                'object-fit': 'scale-down !important',
                'box-shadow': '-1px -1px 1px rgba(250,250,250,0.5), 1px 1px 1px rgba(10,10,10,0.5)',
                'border-radius': '4px',
                'overflow':'scroll !important', # Specially for dataframes 
                '.vega-embed canvas, > .svg-container': { # Vega embed canvas and plotly svg-container inside hoverabe
                    'position': 'fixed !important', # Will be extra CSS but who cares
                    'width': '100% !important',
                    'height': '100% !important', # Ovverider plotly and altair style
                    'border-radius': '4px !important',
                    'object-fit': 'scale-down !important',
                    'box-sizing': 'border-box !important',
                },
            },
        },
        # Nested zoom classes should occupy full space because parent is zoomed too
        '.zoom-self, .zoom-child': {
            '^:focus .vega-embed details, ^:hover .vega-embed details': {'display': 'none !important',},
            '.zoom-self, .zoom-child': {
                '^:hover, ^:focus': {
                    'left': '0px !important',
                    'top': '0px !important',
                    'width': '100% !important',
                    'height': '100% !important',
                    'box-sizing': 'border-box !important',
                    'background': 'var(--primary-bg) !important', # Avoids overlapping with other elements 
                },
            },
        },
    })
        

def glass_css(opacity = 0.75,blur_radius = 50):
    return f'''.BackLayer, .BackLayer .Front {{
        position: absolute !important;
        top:0 !important;
        left:0 !important;
        width: 100% !important;
        height: 100% !important;
        box-sizing:border-box !important;
        overflow:hidden;
        margin:0;
    }}
    .BackLayer img{{
        position: absolute;
        left:0;
        top:0;
        width: 100%;
        height: 100%;
        object-fit:cover;
        filter: blur({blur_radius}px);
    }}
    .BackLayer .Front {{
        background: var(--primary-bg);
        opacity:{opacity};
    }}
    .BackLayer.jupyter-widgets-disconnected {{
        display:none;
    }}
    '''