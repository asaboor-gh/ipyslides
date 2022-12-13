# This should not be used by user, but is used by ipyslides to generate layout of slides

from ..utils import _build_css
def layout_css(breakpoint):
    return _build_css((),{
        'a.jp-InternalAnchorLink': {'display': 'none !important'},
        '.SlidesWrapper': {
            'z-index': '10 !important',
            '^.FullWindow': {
                '.Height-Slider, .Width-Slider, .DisplaySwitch': {'display': 'none !important'},
            },
            '^.SideMode': {
                '.Height-Slider': {'display': 'none !important'},
            },
            '^:not(.FullWindow):not(.SideMode)': {
                'border': '2px inset var(--secondary-bg)',
            },
            '^:not(.FullWindow) .DisplaySwitch': {'display': 'block !important'},
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
            '.widget-html':{
                '^.jupyter-widgets-disconnected': { 'display': 'none !important' },
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
                'height': 'calc(100% - 48px) !important',
                'box-shadow': '0 0 20px 20px var(--secondary-bg)',
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
                '.SidePanel-Btn': {
                    'border':'none !important',
                    'outline':'none !important',
                    'font-size': '24px',
                    'background': 'transparent !important',
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
                    'color': 'var(--accent-color)',
                    'font-weight': 'bold',
                    '^::marker': {'content': '""',},
                    '^::after': {
                        'content': '"show/hide"',
                        'color': 'var(--secondary-fg)',
                        'font-weight':'normal',
                        'font-size': '80%',
                        'float':'right',
                        'padding': '0.2em',  
                    },
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
            },
        },
        '.FloatControl': {
            'position': ' absolute',
            'right': '0',
            'top': '0',
            'width': '32px',
            'height': '32px',
            'z-index': ' 51',
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
            'z-index':'98', # below matplotlib fullsreen 
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
            '.Menu-Item': {'font-size': '24px !important',},
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
        # Order of these is important
        ':is(body[data-base-url], .jp-LabShell, body[data-retro], body[data-notebook]) .DisplaySwitch': {
            'display': 'block !important', # Do not add important here
            'position': 'absolute !important',
            'padding': '4px !important',
            'width': 'max-content !important',
            'background': 'transparent !important',
            'border': 'none !important',
            'outline': 'none !important',
            'font-size': '24px',
            'box-shadow': 'none !important',
            'color': 'var(--accent-color) !important',
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
            '^:not(pre) > code': {
                'background-color': 'var(--secondary-bg)', 
                'color':'var(--secondary-fg)',
            },
            'p': {'margin-bottom': '0.2em !important',},
        },
        '.jp-RenderedText': {
            '^, pre': {
                'color':'var(--primary-fg) !important',
            }, 
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
            'color': 'var(--primary-fg)',
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

def zoom_hover_css(breakpoint):
    return f'''
/* Pop out matplotlib's SVG on click/hover */
div.zoom-container > *:focus, div.zoom-container > *:hover {{
    position:fixed;
    background: var(--primary-bg);
    left:100px;
    top:0px;
    z-index:100;
    width: calc(100% - 200px);
    height: 100%;
    object-fit: scale-down !important;
    box-shadow: 0px 0px 200px 200px rgba(15,20,10,0.8); 
}}

@media screen and (max-width: {breakpoint}) {{ /* Computed dynamically */
    div.zoom-container > *:focus, div.zoom-container > *:hover {{
        background: var(--primary-bg);
        width:100%;
        height: calc(100% - 200px);
        top: 100px;
        left:0px;
    }}
}}
'''

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
    }}'''