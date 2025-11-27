# Author: Abdul Saboor
# CSS for ipyslides
from ..utils import _build_css
from ..xmd import get_unique_css_class
from .icons import Icon
from ._widgets import jupyter_colors

_flow_sels = (".jp-OutputArea-child", ".columns > div", "li") #":is(.highlight code, li, tr)"
_is_flowsel = ':is(' + ','.join(_flow_sels) + ')'
_nth_flowsel = ','.join(f".SlideBox > .SlideArea {sel}" for sel in _flow_sels)


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
.SlideBox {_is_flowsel} {{
    animation-name: appear;
    animation-timing-function: ease-in;
}}
@keyframes appear {{
    0% {{ opacity: 0; }}
    100% {{ opacity: 1; }}
}}
''' + _build_css((_nth_flowsel,), {
    f"^:nth-child({i + 1})":{"animation-duration": f"{int(200 + i*150)}ms"} for i in range(21)
}),
'slide_h': '''
.SlideBox {
    animation-name: slideH; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
.SlideBox.Prev { /* .Prev acts when moving slides backward */
    animation-name: slideHPrev; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
@keyframes slideH {
     from { transform: translateX(100%);}
     to { transform: translateX(0); }
}
@keyframes slideHPrev {
     from { transform: translateX(-100%);}
     to { transform: translateX(0); }
}
''',
'slide_v': '''
.SlideBox {
    animation-name: slideV; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
.SlideBox.Prev { /* .Prev acts when moving slides backward */
    animation-name: slideVPrev; animation-duration: 400ms;
    animation-timing-function: ease-in-out;
}
@keyframes slideV {
     from { transform: translateY(100%);}
     to { transform: translateY(0); }
}
@keyframes slideVPrev {
     from { transform: translateY(-100%);}
     to { transform: translateY(0); }
}
''',
'flow': f'''
.SlideBox {_is_flowsel} {{
    animation-name: flow;
    animation-timing-function: ease-in-out;
}}
.SlideBox.Prev {_is_flowsel} {{ /* .Prev acts when moving slides backward */
    animation-name: flowPrev;
    animation-timing-function: ease-in-out;
}}
@keyframes flow {{
    from {{ transform: translateX(50%); opacity: 0.5; }}
    to {{ transform: translateX(0); opacity: 1; }}
}}
@keyframes flowPrev {{
    from {{ transform: translateX(-50%); opacity: 0.5; }}
    to {{ transform: translateX(0); opacity: 1; }}
}}
''' + _build_css((_nth_flowsel,), {
    f"^:nth-child({i + 1})":{"animation-duration": f"{int(200 + i*150)}ms"} for i in range(21)
}) 
}

theme_colors = {
    'Jupyter': {
        k: f'var({jupyter_colors[k]}, {v})' 
        for k, v in ({
            'fg1':'black', 'fg2':'#454545', 'fg3':'#003366',
            'bg1':'white', 'bg2':'#f7f5f5', 'bg3':'#e8e8e8',
            'accent':'#8988', # May be a neutral color is good for all themes for buttons
            'pointer':'#d32f2f',
        }).items()
    },
    'Light': { 'fg1':'black', 'fg2':'#454545', 'fg3':'#003366', 
        'bg1':'white', 'bg2':'#f7f5f5', 'bg3':'#e8e8e8',
        'accent':'#005090','pointer':'#d32f2f',
    },
    'Dark': { 'fg1' : '#e0e0e0', 'fg2' : '#b0b0b0', 'fg3' : '#b3cfff',
        'bg1' : '#181a1b', 'bg2' : '#23272b', 'bg3' : '#2c313a',
        'accent' : '#90caf9', 'pointer' : '#ff5252',
    },
    'Material Light': { 'fg1': '#212121', 'fg2': '#757575', 'fg3': '#264d73',
        'bg1': '#fafafa', 'bg2': '#f5f5fa', 'bg3': "#e9e9ef",
        'accent': '#1976d2', 'pointer': '#d32f2f',
    },
    'Material Dark': {
        'fg1': '#e0e0e0','fg2': '#bdbdbd','fg3': "#d2ddfa",
        'bg1': "#1F2121",'bg2': "#1b2128",'bg3': "#25282e",
        'accent': "#94cefd",'pointer': '#ff5252',
    }   
}

def collapse_node(b):
    "Used to collapse div in frames navigation and print mode."
    css = {
        'height': '0' if b else 'unset',
        'min-height': '0' if b else 'unset', # unlike max height, it can't be none
        'max-height': '0' if b else 'none',
        'overflow': 'hidden' if b else 'unset',
        'border': 'none' if b else 'unset', # just to be safe, althout output areas don't have border and others below
        'outline': 'none' if b else 'unset',
        'padding': '0' if b else 'unset',
        'margin': '0' if b else 'unset',
    }
    return {k: f'{v} !important' for k, v in css.items()}

def hide_node(b): 
    "Used to hide div in frames navigation and print mode, but keep space."
    return {'^, ^ *': {'visibility': ('hidden' if b else 'inherit') + '!important'}}
        

def style_css(colors, fonts, layout, _root = False):
    uclass = get_unique_css_class()
    margin = 'auto' if layout.centered else 'unset'
    if (layout.width < 100) and (layout.centered is False):
        margin = '0 auto' # if not 100%, horizontally still in center, vertically top

    _root_dict = {**{f"--{k}-color":v for k,v in colors.items()}, # Only here change to CSS variables
        '--text-size':f'{fonts.size}px',
        '--jp-content-font-family': f'{fonts.text}, -apple-system, "BlinkMacSystemFont", "Segoe UI", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16"',
        '--jp-code-font-family': f'{fonts.code}, "Ubuntu Mono", "SimSun-ExtB", "Courier New"',
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
            '.widget-box': {'flex-shrink': 0}, # avoid collapse
            'hr': {
                'margin':'0 !important',
                'margin-block':'0.2em !important',
                'border':'none',
                'width':'auto',
                'height':'1px',
                'background':'linear-gradient(to right, var(--bg2-color),  var(--bg3-color),var(--accent-color), var(--bg3-color),var(--bg2-color))',
            },
            ':is(h1, h2, h3, h4, h5, h6)': {
                'font-family':f'{fonts.heading}, var(--jp-content-font-family) !important',
                'font-weight':'normal',
                'color':'var(--fg3-color)',
                'text-align':'center' if layout.centered else 'left',
                'margin-block': '0.2em 0.3em !important', # Closer to the text of its own scope
                'line-height':'1.5 !important',
                'overflow':'hidden', # Firefox 
                '.MJX-TEX, .MathJax span': {"color":"var(--fg3-color)",}, # MathJax span is for export
            },
            'h1': {'font-size':'2.2em'},
            'h2': {'font-size':'1.7em'},
            'h3': {'font-size':'1.5em'},
            'h4': {'font-size':'1.2em'},
            'h5': {'font-size':'1em'},
            'table, .grid-table': {
                'border-collapse':'collapse !important',
                'table-layout':'auto', # adjust width of columns automatically
                'font-size':'0.85em !important',
                'word-break':'break-all',
                'overflow':'auto',
                'margin': 'auto', # keep in center
                'color':'var(--fg1-color) !important',
                'background':'var(--bg1-color) !important',
                'border':'1px solid var(--bg3-color) !important', # Makes it pleasant to view
                'tr': {
                    '^:nth-child(odd)': {'background':'var(--bg2-color) !important',},
                    '^:nth-child(even)': {'background':'var(--bg1-color) !important',},
                    '^:hover': {'background':'var(--bg3-color) !important',},
                },
                '^.dataframe': {
                    'th, tr, td': {'border': 'none'},
                    'thead': {'border': 'inherit','border-bottom':'1px solid #8988 !important',},
                },
                'td, th': {'line-height': f'{1.2 if _root else 1.1} !important'},
                'td:empty': {'display': 'none'}, # extra create when rowspan, colspan used
            },
            '.grid-table': { 
                '> div': {
                    'padding':'0.25em 0.5em',
                    'display': 'flex !important',
                    'flex-direction': 'row !important',
                    '^:nth-child(odd)': {'background':'var(--bg2-color) !important',},
                    '^:nth-child(even)': {'background':'var(--bg1-color) !important',},
                    '^:hover': {'background':'var(--bg3-color) !important',},
                },
                '^.header > div': {
                    '^:first-child:first-child:first-child': { # emphasize first column CSS
                        'font-weight':'bold !important',
                        'background':'var(--bg2-color) !important',
                        'border-bottom':'1px solid #8988 !important',
                        '^:hover': {'background':'var(--bg3-color) !important',},
                    },
                    '^:nth-child(odd)': {'background':'var(--bg1-color) !important',}, # flip color for header case
                    '^:nth-child(even)': {'background':'var(--bg2-color) !important',},
                    '^:hover': {'background':'var(--bg3-color) !important',},
                }, # For header of grid table
            }, # For grid tables
            'blockquote, blockquote > p': {
                'background':'var(--bg2-color)',
                'color':'var(--fg2-color)',
            },
        },
        
        '.fa::before':  {'margin': '0 4px 0 2px', 'vertical-align': 'middle',}, # for exported font-awsome icons
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
            } if layout.centered else { # why above not working for top left alignment as flex-start???
                "align-items": "flex-start !important",
                "justify-content": "flex-start !important",
            }),
        },
        '.SlideArea': {
            **{f"--{k}-color":v for k,v in colors.items()}, # need for per slide based CSS set by user to not effect all
            'position': 'absolute !important',
            'width':'210mm !important', # A4 width letter page can have a little extra margin, important to have fixed width
            'height': f'{int(210/layout.aspect):.1f}mm !important',
            'transform-origin': 'center !important' if layout.centered else 'left top !important',
            'transform': 'translateZ(0) scale(var(--contentScale,1)) !important', # Set by Javascript , translateZ is important to avoid blurry text
            'box-sizing': 'border-box !important',
            'display':'flex !important',
            'flex-direction':'column !important',
            'align-items': 'center !important' if layout.centered else 'baseline !important', 
            'justify-content': 'flex-start !important', # Aligns the content to the top of box to avoid hiding things
            'padding' : '16px !important', # don't make 1em to avoid change size with fonts
            'padding-bottom': 'var(--paddingBottom, 23px) !important',
            'overflow': 'auto !important' if layout.scroll else 'hidden !important',
            '> .jp-OutputArea': {
                'position': 'relative !important', # absolute content should not go outside
                'margin': f'{margin} !important', # for frames margin-top will be defined, don't use here
                'padding': '0 !important',
                'width': f'{layout.width}% !important',
                'max-width': f'{layout.width}% !important',
                'box-sizing': 'border-box !important',
                'overflow': 'auto !important' if layout.scroll else 'hidden !important', # needs here too besides top
                '@media print': { # For PDF printing of frames, data-hidden set by JS, first sellectors works for rows too beside top level
                    'margin': f'{margin} !important', # reinforce for clones in print
                    'overflow': 'hidden !important', # no need to scroll in print
                    '.jp-OutputArea-child[data-hidden], .columns.writer > div[data-hidden]': hide_node(True),
                },
            },
            '@media print': { # For PDF printing dynamically set page size
                'padding-bottom': 'var(--printPadding, var(--paddingBottom, 23px)) !important',
                '@page': {
                    'margin': '0 !important',
                    'size': f'210mm {int(210/layout.aspect):.1f}mm !important', # 1pt ~ 0.35mm, so no more than one decimal required
                },
            },
            **({'^:not(.n0) > .jp-OutputArea': { # no yoffset on title slide, leave it centered globally
                    "top": f"{layout.yoffset}% !important", 
                    "margin-top": "0 !important", 
                }
            } if layout.yoffset is not None else {}),# global yoffset, even centered
            **({'*': {
                'max-height':'max-content !important',
                }
            } if layout._reflow else {}), # clean way to reflow all content
            '.speaker-notes': {
                **({} if layout._inotes else {'display':'none !important',}), # hide notes if not choosen to include in print
                'border-radius':'0.2em !important',
                'background':'var(--bg2-color) !important',
                'border':'1px dashed var(--pointer-color) !important',
                'padding':'0.4em 0.2em 0.2em 0.2em !important',
                'font-size':'1.5em !important',
                'position':'relative !important',
                'margin-top':'0.5em !important',
                '^::before': {
                    'content': '"Speaker Notes"',
                    'font-size':'0.6em !important', # 60% of note size
                    'position': 'absolute !important',
                    'top': '-0.8em !important',
                    'left': '0.5em !important',
                    'background': 'var(--pointer-color) !important',
                    'color': 'var(--bg1-color) !important',
                    'padding': '0 0.5em !important',
                    'border-radius': '0.2em !important',
                }, 
            },
            '.slide-link, .link-button': {
                'color':'var(--accent-color)',
                'text-decoration':'none !important',
                'text-shadow': '0 1px var(--bg1-color)',
            },
            '.slide-link:not(.citelink), .link-button': {
                'background': 'var(--bg2-color)',
                'border-radius': '0.2em',
                'padding': '0 0.2em',
                'margin': '0 0.2em',
                'border': '1px solid var(--bg3-color)',
            },
            '.slide-link:empty': {'display': 'inline-block !important', # height width needs a block display
                'width': '0 !important', 'height': '0 !important',
                'padding':'0 !important', 'margin': '0 !important'
            }, # avoid empty links to show, but still need to work in pdf
            ':is(ul,ol)': {
                'margin-block': '0.2em !important' # avoid extra space, just add as much as column gap
            },
            'dl': {
                'display': 'grid',
                'margin-block':'0.5em',
                'font-family':'var(--jp-content-font-family) !important',
                'font-size':'var(--text-size) !important', # somwhow gets different font size
            }, # Jupyterlab fix
            'dl > dt': {
                'color': 'var(--fg3-color)',
                'font-weight': 'bold', 
                'width':'max-content',  # override 20% width
                'text-shadow': '0 1px var(--bg2-color)',
            },
            'dl > dd': {'margin-inline-start': '16px', 'display': 'block', 'width':'calc(100% - 16px)'},
            'a': {
                'color': 'var(--accent-color) !important',
                '^:not(.citelink,.slide-link,.link-button):visited': {
                    'color': 'var(--fg2-color) !important',
                    'opacity': '0.75 !important',
                },
                '^:not(.citelink,.slide-link,.link-button)': {
                    'text-decoration': 'underline !important', 
                },
                '^.citelink': {'color': 'var(--fg1-color) !important',},
                '^.citelink': {
                    '> sup': {'font-weight':'bold',},
                    'text-shadow': '0 1px var(--bg2-color)',
                },
                '^.link-button': {
                    'padding': '0 24px !important', # make it like button, others from slide-link
                }, # link-button is used for links in slides
            },
            '.link-button.draw-button > :is(button, a)': {
                'padding': '0 24px !important', # make it like button under draw button too
            },
            '.link-button, .slide-link': {'^, *': {
                f'{k}user-select':'none !important' for k in ['','-moz-','-ms-','-webkit-']
                },
            }, # avoid selection
            '.Citations' : {
                'column-count' :f'{layout.ncol_refs} !important',
                'column-gap':'1em',
                'border-top':'1px solid #8988', # for all colors
                'margin-block':'0.5em',
            },
            '.citetext': { # subtle difference from normal text
                'border-radius':'4px',
                'border-left': '1px solid var(--fg2-color)',
                'border-right': '1px solid var(--fg2-color)',
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
                'display':'inline !important',
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
                '^.Error': {
                    'background': 'hsl(from var(--bg2-color) 10 50% l) !important','padding': '4px !important',
                    '.Error': {'background': 'none !important', 'padding': '4px 0 !important'}, # nested errors blocks
                },
            },
            'figure': {
                'margin':'8px', # override default margin
                'object-fit':'scale-down',
                'display':'flex', # To align in center 
                'flex-direction':'column', # To have caption at bottom 
                'align-items':'center',
                'justify-content':'center',
                "img, svg" : {"margin": "auto",}, # keep in center if space available
            },
            'figcaption': {
                'font-size':'0.8em',
                'line-height':'1',
                'padding':'0.25em',
            },
            '.columns':{
                'width':'100%',
                'max-width':'100%',
                'display':'inline-flex',
                'flex-direction':'row',
                'column-gap':'0.2em',
                'height':'auto',
                'box-sizing':'border-box !important',
                '> *': {'box-sizing':'border-box !important','min-width':'0 !important',}, # avoid overflow due to stubborn elements
                'table': {'width':'calc(100% - 0.5em)'}, # make table full width inside columns with some padding
            },
        },
        'code': {
            'color': 'var(--fg2-color) !important',
            'font-family': 'var(--jp-code-font-family) !important',
            '^.dim': {'opacity':'0.3 !important'}, # should work outside block too
        }, # external code tags
        'span.sig': {
            'color': 'var(--accent-color) !important',
            'font-family': 'var(--jp-code-font-family) !important',
            'text-shadow': '0 1px var(--bg1-color)',
            '> b': {'color': 'var(--fg1-color) !important',},
            '+ code.inline': {'padding': '1px !important',},
        },
        'code.highlight.inline': {
            'border': 'none !important',
            'text-shadow': '0 1px var(--bg2-color)',
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
            'max-height':'100%', # Try avoiding important here, approach contaier
            'height': 'auto',
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
                'display':'inline-block !important', # should be on new line 
                'width':'auto',
                'background':'transparent !important',
                'white-space':'pre !important',
                'overflow-wrap':'normal !important',
                'box-sizing':'border-box !important',
                '^:hover, ^:hover::before': {
                    'background': 'var(--bg3-color)',
                },
                '> span': {
                    'text-shadow': '0 1px var(--bg1-color)',
                    'white-space':'pre', #normal  for breaking words 
                    'word-break':'break-word', # for breaking words 
                    '^.err, ^.nn, ^.nc' : {'background': 'none !important', 'text-decoration': 'none !important',}, 
                },
            },
        },
        '.highlight.numbered code': {
            'counter-increment':'line',
            '^:before': {
                'content':'counter(line,decimal)',
                'position':'sticky',
                'top':'initial',
                'left':'-1px',
                'padding':'0 8px',
                'display':'inline-block', # should be inline 
                'text-align':'right',
                **{f'{k}user-select':'none !important' for k in ['','-moz-','-ms-','-webkit-']},
                'margin-right':'8px',
                'font-size':'80% !important',
                'text-shadow': '0 1px var(--bg1-color)',
            },  
        },
        '.highlight, pre, .raw-text': {
            '^:hover::-webkit-scrollbar-thumb': {
                'background':'#8988 !important'
            },
        },
        '.lang-name': {
            'color':'var(--accent-color)',
            'font-size':'0.6em',
            'padding':'4px',
            'text-shadow':'0 1px var(--bg1-color)',
            '^:empty': {'display':'none !important',},
        },
        '.docs': { # docs have Python code only, so no need to have fancy things there
            'margin-bottom':'1em !important',
            '.highlight': {'border':'none !important',},
            '.lang-name': {'display':'none !important',},
        },
        '.InlinePrint': {
            'margin-block':'0.5px !important', # Two adjacant prints should look closer 
        },
        '.align-center:not(.columns), .align-center > *:not(.columns)': {
            '^, .jp-OutputArea-output > *': {
                'margin-left':'auto !important', 
                'margin-right':'auto !important', 
            },
            'width':'auto', # don't make it important
            '^, p': {'text-align':'center !important'},
        },
        '.align-left:not(.columns)': { 
            '^, .jp-OutputArea-output > *': {'margin-right':'auto !important'}, 
            '^, p': {'text-align':'left !important'},
        },
        '.align-right:not(.columns)': { 
            '^, .jp-OutputArea-output > *': {'margin-left':'auto !important'}, 
            '^, p': {'text-align':'right !important'},
        },
        '.align-right:not(.columns), .align-left:not(.columns), .align-center:not(.columns)': {
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
                'padding': '4px',
                'border-radius': '8px',
                'margin': '0.5em 0',
                'background': 'hsl(from var(--bg-color) h s l / 0.7)', 
            },
            **({
                '^-red':     {'--bg-color': 'hsl(from var(--bg2-color) 10 100% l)'},
                '^-yellow':  {'--bg-color': 'hsl(from var(--bg2-color) 60 95% l)'}, 
                '^-green':   {'--bg-color': 'hsl(from var(--bg2-color) 120 80% l)'},
                '^-cyan':    {'--bg-color': 'hsl(from var(--bg2-color) 180 90% l)'}, 
                '^-blue':    {'--bg-color': 'hsl(from var(--bg2-color) 210 100% l)'},
                '^-magenta': {'--bg-color': 'hsl(from var(--bg2-color) 310 100% l)'},
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
        '.click-wrapper': { # PDF/HTML -only clicker at bottom right
            'position': 'absolute !important',
            '@media print': {'position': 'fixed !important',},
            'right': '28px !important', # space for slide number
            'bottom': '2px !important',
            'width': 'auto !important',
            'height': '21px !important',
            'display': 'inline-flex', # no impportant as in print-only display is none
            'flex-direction': 'row !important',
            'align-items': 'center !important',
            'z-index': '6 !important',
            'justify-content': 'flex-end !important', # align to right
            '.clicker': {
                'display':'inline-block',
                'padding':'0 8px !important', # PDF safe
                'flex-grow':'1',
                'color':'var(--accent-color)',
                'text-align':'center',
                'font-size':'14px',
                'text-decoration':'none !important',
                'opacity':'0.4',
                '^:hover': { # for exported html interactivity
                    'color':'var(--fg1-color)',
                    'opacity':'1',
                },
            },    
        },
    })
    