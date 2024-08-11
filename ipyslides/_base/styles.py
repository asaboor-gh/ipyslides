# Author: Abdul Saboor
# CSS for ipyslides
from ..utils import _build_css
from ..xmd import get_unique_css_class
from .icons import Icon

_flow_selector = ":is(.jp-OutputArea-child, .columns > div, li)" #":is(.highlight code, li, tr)"

# Animations are fixed for instnace on the fly, no need uclass thing here
animations = {'zoom':'''
.SlideBox {
    animation-name: zoom; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
@keyframes zoom {
     0% { transform: scale(0.05); }
    25% { transform: scale(0.35); }
    50% { transform: scale(0.55); }
	75% { transform: scale(0.85); }
   100% { transform: scale(1); }
}
''',
'appear': f'''
.SlideBox {_flow_selector} {{
    animation-name: appear;
    animation-timing-function: ease-in;
}}
''' + _build_css((f".SlideBox {_flow_selector}",), {
    **{f"^:nth-child({i + 1})":{"animation-duration": f"{int(400 + i*200)}ms"} for i in range(21)},
    "@keyframes appear" : {
        "0%" : { "opacity": 0},
        "50%" : { "opacity": 0},
        "100%" : { "opacity": 1},
    },
}),
'slide_h': '''
.SlideBox {
    animation-name: slide; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
.SlideBox.Prev { /* .Prev acts when moving slides backward */
    animation-name: slidePrev; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
@keyframes slide {
     from { transform: translateX(100%);}
     to { transform: translateX(0); }
}
@keyframes slidePrev {
     from { transform: translateX(-100%);}
     to { transform: translateX(0); }
}
''',
'slide_v': '''
.SlideBox {
    animation-name: slide; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
.SlideBox.Prev { /* .Prev acts when moving slides backward */
    animation-name: slidePrev; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
@keyframes slide {
     from { transform: translateY(100%);}
     to { transform: translateY(0); }
}
@keyframes slidePrev {
     from { transform: translateY(-100%);}
     to { transform: translateY(0); }
}
''',
'flow': f'''
.SlideBox {_flow_selector} {{
    animation-name: flow;
    animation-timing-function: ease-in-out;
}}
.SlideBox.Prev {_flow_selector} {{ /* .Prev acts when moving slides backward */
    animation-name: flowPrev;
    animation-timing-function: ease-in-out;
}}
''' + _build_css((f".SlideBox {_flow_selector}",), {
    **{f"^:nth-child({i + 1})":{"animation-duration": f"{int(400 + i*200)}ms"} for i in range(21)},
    '@keyframes flow':{
        'from' : {'transform': 'translateX(50%)', 'opacity': 0},
        'to' : {'transform': 'translateX(0)', 'opacity': 1}
    },
    '@keyframes flowPrev':{
        'from' : {'transform': 'translateX(-50%)', 'opacity': 0},
        'to' : {'transform': 'translateX(0)', 'opacity': 1}
    },
}) 
}
  

theme_colors = {
    'Inherit': {
        'fg1':'var(--jp-content-font-color0,black)',
        'fg2':'var(--jp-content-font-color3, #454545)', 
        'fg3':'var(--jp-content-font-color2,#00004d)',
        'bg1':'var(--jp-layout-color0,white)',
        'bg2':'var(--jp-cell-editor-background,whitesmoke)',
        'bg3':'var(--jp-layout-color2,#e8e8e8)',
        'accent':'var(--jp-brand-color1,#8988)', # May be a neutral color is good for all themes for buttons
        'pointer':'var(--jp-error-color1,red)',
    },
    'Light': { 'fg1':'black', 'fg2':'#454545', 'fg3':'#00004d', 
        'bg1':'white', 'bg2':'whitesmoke', 'bg3':'#e8e8e8',
        'accent':'#005090','pointer':'red',
    },
    'Dark': { 'fg1' : 'white', 'fg2' : '#8A8989', 'fg3' : 'snow',
        'bg1' : 'black', 'bg2' : '#353535', 'bg3' : '#282828',
        'accent' : '#d7e1e5', 'pointer' : '#ff1744',
    },
    'Material Light': { 'fg1': '#3b3b3b', 'fg2': '#838181', 'fg3': '#6389B1',
	    'bg1': '#fafafa', 'bg2': '#e9eef2', 'bg3': '#d9dee2',
	    'accent': '#345376', 'pointer': '#f50057',
    },
    'Material Dark': { 'fg1': '#bebebe', 'fg2': '#fefefe', 'fg3': '#C3D9F1',
	    'bg1': '#282828', 'bg2': '#383838', 'bg3': '#242424',
	    'accent': '#92C1F4', 'pointer': '#e91e63',
    }   
}

def style_css(colors, *, text_size = '22px', text_font = None, code_font = None, scroll = True, centered = True, aspect = 16/9, width=100, ncol_refs = 2, _root = False):
    uclass = get_unique_css_class()
    margin = 'auto' if centered else 'unset'
    if (width < 100) and (centered is False):
        margin = '0 auto' # if not 100%, horizontally still in center, vertically top

    _root_dict = {**{f"--{k}-color":v for k,v in colors.items()}, # Only here change to CSS variables
        '--text-size':f'{text_size}',
        '--jp-content-font-family': f'{text_font}, -apple-system, "BlinkMacSystemFont", "Segoe UI", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16"',
        '--jp-code-font-family': f'{code_font}, "Ubuntu Mono", "SimSun-ExtB", "Courier New"',
    }
    return _build_css(() if _root else (uclass,),{ # uclass is not used in root for exporting purpose
        **(_root_dict if not _root else {':root': _root_dict}),
        '^.SlidesWrapper, .jupyter-widgets, .jp-RenderedHTMLCommon': { # widgets have their own fonts, but make same
            'font-family': 'var(--jp-content-font-family) !important',
            'color': 'var(--fg1-color)', # important to put here for correct export
            # Reset these vars under slides if not Inherit theme, otherwise it won't work
            **({} if '--jp-content-font-color0' in colors['fg1'] else {
                '--jp-content-font-color0': 'var(--fg1-color)',
                '--jp-content-font-color1': 'var(--fg1-color)', # same as primary
                '--jp-content-font-color2': 'var(--fg3-color)',
                '--jp-content-font-color3': 'var(--fg2-color)',
                '--jp-widgets-label-color': 'var(--fg1-color)', # That's also needed
            }),
            '.raw-text, code > span, .jp-RenderedHTMLCommon :is(pre, code)': {
                'font-family': 'var(--jp-code-font-family) !important',
                'font-size':'90% !important',   
            }, # Define color below at low specificity, otherwise it can overwrite code
        },
        '.jp-RenderedHTMLCommon :is(pre:not(.Error), code)': {'line-height': '1.5 !important','background': 'none !important'}, # Avoid a white background set by jupyter
        '^.SlidesWrapper':{
            'container': 'slides / inline-size',
            'margin':'auto',
            'padding':'0px',
            'font-size':'var(--text-size) !important',
            'background':'var(--bg1-color)',
            'max-width':'100vw', # This is very important
            '::-webkit-scrollbar': {
                'height':'4px',
                'width':'4px',
                'background':'transparent !important', 
                '^:hover': {'background':'var(--bg2-color) !important',},
            },
            '::-webkit-scrollbar-thumb': {
                'background':'transparent !important',
                '^:hover': {'background':'#8988 !important',},
            },
            '::-webkit-scrollbar-corner': {'display':'none',},
            '.widget-text input': {
                'background':'var(--bg1-color)',
                'color':'var(--fg1-color)',
            },
            'hr': {
                'margin':'0 !important',
                'margin-block':'0.2em !important',
                'border':'none',
                'width':'auto',
                'height':'2px',
                'background':'linear-gradient(to right, var(--bg1-color),  var(--bg2-color),var(--accent-color), var(--bg2-color),var(--bg1-color))',
            },
            ':is(h1, h2, h3, h4, h5, h6)': {
                'font-family':'var(--jp-content-font-family) !important',
                'font-weight':'normal',
                'color':'var(--fg3-color)',
                'text-align':'center' if centered else 'left',
                'margin-block': '0.2em 0.3em !important', # Closer to the text of its own scope
                'line-height':'1.5',
                'overflow':'hidden', # Firefox 
                '.MJX-TEX, .MathJax span': {"color":"var(--fg3-color)",}, # MathJax span is for export
            },
            'h1': {'font-size':'2.2em'},
            'h2': {'font-size':'1.7em'},
            'h3': {'font-size':'1.5em'},
            'h4': {'font-size':'1.2em'},
            'h5': {'font-size':'1em'},
            'table': {
                'border-collapse':'collapse !important',
                'font-size':'0.85em',
                'word-break':'break-all',
                'overflow':'auto',
                'margin': 'auto', # keep in center
                'color':'var(--fg1-color) !important',
                'background':'var(--bg1-color) !important',
                'border':'1px solid var(--bg3-color) !important', # Makes it pleasant to view
                'tbody': {
                    'tr': {
                        '^:nth-child(odd)': {'background':'var(--bg2-color) !important',},
                        '^:nth-child(even)': {'background':'var(--bg1-color) !important',},
                        '^:hover': {'background':'var(--bg3-color) !important',},
                    },
                },
            },
            'blockquote, blockquote > p': {
                'background':'var(--bg2-color)',
                'color':'var(--fg2-color)',
            },
        },
        
        '.fa::before':  {'margin': '0 4px 0 2px', 'vertical-align': 'middle',}, # for exported font-awsome icons
        '.fa:empty::before': {'padding': '0 10px',},
        **{f".fa.fa-{k}::before": Icon(k, color=colors['accent']).css for k in Icon.available}, # needed in export too
        '.raw-text': { # Should be same in notebook cell 
            'font-family': 'var(--jp-code-font-family) !important',
            'font-size':'90% !important',
            'display':'block !important',
            'margin':'4px !important',
            'height':'auto !important',
            'overflow':'auto !important',
            'overflow-wrap':'break-word !important',
            'padding':'0 0.3em !important',
        },
        '.SlideBox': { # This needs to be exported as well
            "position": "relative !important",
            'display': 'flex !important',
            "flex-direction": "column !important",
            "overflow":"hidden !important", 
            "box-sizing": "border-box !important",
            **({
                "align-items": "center !important",
                "justify-content": "center !important",
            } if centered else { # why above not working for top left alignment as flex-start???
                "align-items": "flex-start !important",
                "justify-content": "flex-start !important",
            }),

        },
        '^.ShowFooter .SlideArea' : {
            'padding-bottom': 'var(--paddingBottom, 23px) !important', # 20px navbar + 3px progressbar
        },
        '.SlideArea': {
            'position': 'absolute !important',
            'width':'254mm !important',
	        'height': f'{int(254/aspect)}mm !important',
            'transform-origin': 'center !important' if centered else 'left top !important',
            'transform': 'translateZ(0) scale(var(--contentScale,1)) !important', # Set by Javascript , translateZ is important to avoid blurry text
	        'box-sizing': 'border-box !important',
            'display':'flex !important',
            'flex-direction':'column !important',
            'align-items': 'center !important' if centered else 'baseline !important', 
            'justify-content': 'flex-start !important', # Aligns the content to the top of box to avoid hiding things
            'padding' : '16px !important', # don't make 1em to avoid zoom with fonts
            'overflow': 'auto !important' if scroll else 'hidden !important',
            '> .jp-OutputArea': {
                'position': 'relative !important', # absolute content should not go outside
                'margin': f'{margin} !important', # for frames margin-top will be defined, don't use here
                'padding': '0 !important',
                'width': f'{width}% !important',
                'max-width': f'{width}% !important',
                'box-sizing': 'border-box !important',
                'overflow': 'auto !important' if scroll else 'hidden !important', # needs here too besides top
            },
            ':is(ul,ol)': {
                'margin-block': '0.2em !important' # avoid extra space, just add as much as column gap
            },
            'dl': {'display': 'grid'}, # Jupyterlab fix
            'dl > dt': {
                'color': 'var(--fg3-color)',
                'font-weight': 'bold', 
                'width':'max-content',  # override 20% width
                'text-shadow': '0 1px var(--bg2-color)',
                'margin-block-start': '0.5em'},
            'dl > dd': {'margin-inline-start': '16px', 'display': 'block', 'width':'100%'},
            'a': {
                'color': 'var(--accent-color) !important',
                '^:not(.citelink,.goto-button):visited': {
                    'color': 'var(--fg2-color) !important',
                    'opacity': '0.75 !important',
                },
                '^:not(.citelink,.goto-button)': {
                    'text-decoration': 'underline !important', 
                },
                '^.citelink': {'color': 'var(--fg1-color) !important',},
                '^.citelink > sup': {'font-weight':'bold',},
            },
            '.Citations' : {
                'column-count' :f'{ncol_refs} !important',
                'column-gap':'1em',
                'border-top':'1px solid #8988', # for all colors
                'margin-block':'0.5em',
            },
            '.columns > div': {"position": "relative !important"}, # keep absolute items inside column itself
            '.toc-list.toc-extra' : {
                'margin-right': '1em',
                '.toc-item.this' : {
                    'background': 'var(--bg2-color)',
                    'padding': '0 0.5em',
                    'font-size': '110%', # Make more prominent
                    'border-left': '2px solid var(--accent-color)',
                },
            },
            '.toc-item': { # Table of contents on slides 
                'padding-right':'0.5em', # To make distance from the border
                '^.this': {
                    'font-weight':'bold !important',
                }, 
                '^.next': {'opacity':'0.5',},
            },
            '^.FirstTOC .toc-item.next' : {'opacity':'1',}, # In start, see full as same opacity
            'ul li::marker, ol li::marker': {'color':'var(--accent-color)',},
            '.raw-text': { # Should follow theme under slides 
                'color':'var(--fg1-color) !important',
                'max-height':'400px',
                'white-space':'pre !important',
            },
            '.text-box': { # general text box for writing inline refrences etc. 
                'font-size':'0.85em !important', 
                'line-height':'1.2 !important',
                'position':'relative', 
                'left':'initial',
                'top':'initial',
                'padding':'2px 4px',
                'color':'var(--fg2-color)',
                # Below are required to override behavior of span tag
                'display':'inline-block !important',
                'white-space':'break-spaces !important',
                '*': {'color':'var(--fg2-color)',}, # should be same color 
            },
            ".text-tiny" : {
                "font-size": "0.5em !important",
            },
            ".text-small" : {
                "font-size": "0.8em !important",
            },
            ".text-big" : {
                "font-size": "1.2em !important",
            },
            ".text-large" : {
                "font-size": "1.5em !important",
            },
            ".text-huge" : {
                "font-size": "2em !important",
            },
            '.citation': {
                'font-size':'0.9em !important',
                'display':'flex !important',
                'flex-direction':'row !important',
                '> a': {'margin-right':'0.3em !important'},
                '> p': {'margin':'0 !important'}, # Otherwise it will be huge space
            },
            '.footnote *, .footnote li::marker': {
                'font-size':'0.9em',
                'line-height':'1',
            },
            '.footnote ol': {'margin-top':'0.5em !important',},
            'pre': {
                'background':'none !important',
                'color':'var(--fg1-color) !important',
                '^.Error': {'background': 'hsl(from var(--bg2-color) 10 100% l) !important','padding': '4px !important',},
            },
            'figure': {
                'margin':'8px !important', # override default margin
                'object-fit':'scale-down !important',
                'display':'flex', # To align in center 
                'flex-direction':'column', # To have caption at bottom 
                'align-items':'center',
                'justify-content':'center',
                "img, svg" : {"margin": "auto",}, # keep in center if space available
            },
            'figcaption': {
                'font-size':'0.8em !important',
                'line-height':'1 !important',
                'padding':'0.5em 1.5em !important',
            },
            '.columns':{
                'width':'100%',
                'max-width':'100%',
                'display':'inline-flex',
                'flex-direction':'row',
                'column-gap':'0.2em',
                'height':'auto',
                'box-sizing':'border-box !important',
                '> *': {'box-sizing':'border-box !important',}
            },
        },
        'span.sig': {
            'color': 'var(--accent-color) !important',
            'font-family': 'var(--jp-code-font-family) !important',
            'text-shadow': '0 1px var(--bg1-color)',
            '> b': {'color': 'var(--fg1-color) !important',},
            '+ code.inline': {'padding': '1px !important',},
        },
        'code.highlight.inline': {
            'border': 'none !important',
            'text-shadow': '0 1px var(--bg1-color)',
            'background': 'none !important', # Export fix
            'span.n': {'color': 'var(--fg1-color) !important',},
        },
        '.highlight:not(.inline)': {
            'min-width':'100% !important',
            'width':'100% !important',
            'max-width':'100vw !important',
            'box-sizing':'border-box !important',
            'overflow':'auto !important',
            'padding':'0 !important',
            'margin':'4px 0px !important', # Opposite to padding to balance it 
            'max-height':'400px', # Try avoiding important here 
            'height':'auto !important',
            # colors are set via settigs.set_code_theme
            'pre': {  # works for both case, do not use > 
                'display':'grid !important',
                'overflow':'auto !important',
                'width':'auto !important',
                'box-sizing':'border-box !important',
                'height':'auto',
                'margin':'0px !important',
                'counter-reset':'line', # important to add line numbers 
                'background':'none !important', # This should be none as will given by the code_css 
            },
            'code': {
                'counter-increment':'line',
                'display':'inline-block !important', # should be on new line 
                'width':'auto',
                'background':'transparent !important',
                'white-space':'pre !important',
                'overflow-wrap':'normal !important',
                'box-sizing':'border-box !important',
                '^:before': {
                    'content':'counter(line,decimal)',
                    'position':'sticky',
                    'top':'initial',
                    'left':'-1px',
                    'padding':'0 8px',
                    'display':'inline-block', # should be inline 
                    'text-align':'right',
                    '-webkit-user-select':'none',
                    'margin-right':'8px',
                    'font-size':'80% !important',
                    'text-shadow': '0 1px var(--bg1-color)',
                },
                '> span': {
                    'text-shadow': '0 1px var(--bg1-color)',
                    'white-space':'pre', #normal  for breaking words 
                    'word-break':'break-word', # for breaking words 
                    '^.err, ^.nn, ^.nc' : {'background': 'none !important', 'text-decoration': 'none !important',}, 
                },
                '^.code-no-focus': {'opacity':'0.3 !important'},
            },
        },
        '.highlight, pre, .raw-text': {
            '^:hover::-webkit-scrollbar-thumb': {
                'background':'#8988 !important'
            },
        },
        'span.lang-name': {
            'color':'var(--accent-color)',
            'font-size':'0.8em',
        },
        '.docs': { # docs have Python code only, so no need to have fancy things there
            'margin-bottom':'1em !important',
            '.highlight': {'border':'none !important',},
            'span.lang-name': {'display':'none !important',},
        },
        '.InlinePrint': {
            'margin-block':'0.5px !important', # Two adjacant prints should look closer 
        },
        '.align-center:not(.columns), .align-center > *:not(.columns)': {
            'display':'table !important',
            'margin':'0 auto !important',
            'width':'auto !important', # max-content creates oveflow, do not use it 
        },
        '.align-left:not(.columns)': { 
            'margin-right':'auto !important', 
            'text-align':'left !important',
        },
        '.align-right:not(.columns)': { 
            'margin-left':'auto !important', 
            'text-align':'right !important',
        },
        '.align-right:not(.columns), .align-left:not(.columns), .align-center:not(.columns)': {
            'display':'table !important',
            'width':'auto !important',
            '> *:last-child': {'margin-bottom':'0.1em !important',}, 
        },
        '.rtl, .rtl > *': {
            'text-align':'right !important',
            'padding':'0 12px !important', # to avoid cuts in rtl 
        },
        '.info, .warning, .success, .error, .note, .tip': {
            '^ > *:last-child': {'margin-bottom':'0.1em !important'},
            '^.admonition > .admonition-title': {'display':'none !important'}, # Remove admonition title if get overlapped
        },
        '.warning, .warning *:not(span)': {'color':'#FFAC1C !important',},
        '.success, .success *:not(span)': {'color':'green !important',},
        '.error, .error *:not(span)': {'color':'red !important',},
        '.info, .tip, .info *:not(span), .tip *:not(span)' : {'color':'skyblue !important',},
        '.note, .note-info, .note-warning, .note-success, .note-error, .note-tip' : {
            'padding-left': '0.5em',
            'padding-right': '0.5em',
            'box-sizing': 'border-box',
            'border-radius': '2px',
            'border-left': '2px inset var(--accent-color)',
            'margin-top': '0.5em',
            'margin-bottom': '0.7em !important',
            'background': 'hsl(from var(--bg3-color) h s l / 0.9)',
            '^.admonition > .admonition-title': {'display':'none !important'}, # Remove admonition title
            '^::before': {
                'content': '"📝 Note"',
                'display':'block',
                'color': 'var(--accent-color)',
                'border-bottom': '1px solid #8988',
                'box-sizing': 'border-box',
            },
            '^-info::before': {'content': '"❇️ Info" !important'},
            '^-warning::before': {'content': '"⚠️ Alert" !important'},
            '^-success::before': {'content': '"✅ Important" !important'},
            '^-error::before': {'content': '"⚡ Danger" !important'},
            '^-tip::before': {'content': '"💡 Tip" !important'},
        },
        '.block' : {
            '^, ^-red,^-green,^-blue, ^-yellow, ^-magenta, ^-cyan': {
                '--bg-color': 'var(--bg2-color)',
                'padding': '8px',
                'border-radius': '4px',
                'margin-bottom': '0.9em',
                'box-shadow': '0px 0px 1px 0.5px hsl(from var(--bg-color) h s 40% / 0.9) inset !important',
                'background': 'hsl(from var(--bg-color) h s l / 0.9)', 
            },
            **({f'^-{c}': {
                '--bg-color': f'hsl(from var(--bg2-color) {h} {s} l)'} 
                for c,h, s in [
                    ('red', 10, '100%'), 
                    ('yellow', 60, '85%'), 
                    ('green', 120, '70%'), 
                    ('cyan', 180, '85%'), 
                    ('blue', 210, '100%'), 
                    ('magenta',310, '100%'),
                ]
            }),
        },
        'details': {
            'padding': '0.2em',
            '^, > summary': {'padding': '0.2em'},
            '> summary': {
                'padding-left': '0.2em !important',
                'color': 'var(--fg3-color) !important',
                '^::marker': {
                    'content':'"≚  "',
                    'color': 'var(--accent-color) !important',
                    },
                },
            '^[open]': {
                'border-left': '2px solid var(--accent-color)',
                'max-height': '400px !important',
                'overflow': 'auto',
                'padding-bottom': '1em', # for close button
                '> summary::marker': {
                    'content':'"≙  "',
                    'color': 'var(--accent-color) !important',
                },
                '> summary::after': {
                    'display':'block',
                    'content': '"≙"',
                    'color': 'var(--accent-color) !important',
                    'position': 'absolute',
                    'left': 0,
                    'bottom': 0,
                    'padding-left': '0.4em',
                },
            },
        },
        '.pygal-chart':{
            'min-width':'300px',
            'width':'100%',
            'height':'auto',    
        },
    })
    