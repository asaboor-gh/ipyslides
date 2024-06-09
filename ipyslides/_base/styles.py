# Author: Abdul Saboor
# CSS for ipyslides
from ..utils import _build_css
from ..xmd import get_unique_css_class

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
  
def _validate_colors(colors):
    for key, value in colors.items():
        if not isinstance(value, str):
            raise TypeError(f'Color value for {key!r} must be a string')
        if not key in theme_colors['Light']:
            raise KeyError(f'Invalid color key {key!r}! Use one of {list(theme_colors["Light"].keys())}')
    
    for k1, k2 in zip(sorted(colors.keys()),sorted(theme_colors['Light'].keys())):
        if k1 != k2:
            raise ValueError(f'Invalid number of colors! Provide all colors like \n{theme_colors["Light"]}\n')
        
theme_colors = {
    'Inherit': {
        'heading_color':'var(--jp-inverse-layout-color1,black)',
        'primary_fg':'var(--jp-inverse-layout-color0,black)',
        'primary_bg':'var(--jp-layout-color0,white)',
        'secondary_bg':'var(--jp-layout-color2,whitesmoke)',
        'secondary_fg':'var(--jp-inverse-layout-color4,#454545)',
        'alternate_bg':'var(--jp-layout-color2,whitesmoke)',
        'hover_bg':'var(--jp-border-color1,#D1D9E1)',
        'accent_color':'var(--jp-brand-color1,gray)', # May be a neutral color is good for all themes for buttons
        'pointer_color':'var(--md-pink-A400,red)',
    },
    'Light': {
        'heading_color':'navy',
        'primary_fg':'black',
        'primary_bg':'white',
        'secondary_bg':'whitesmoke',
        'secondary_fg':'#454545',
        'alternate_bg':'whitesmoke',
        'hover_bg':'#D1D9E1',
        'accent_color':'navy',
        'pointer_color':'red',
    },
    'Dark': {
        'heading_color' : 'snow',
        'primary_fg' : 'white',
        'primary_bg' : 'black',
        'secondary_bg' : '#353535',
        'secondary_fg' : 'powderblue',
        'alternate_bg' : '#282828',
        'hover_bg' : '#264348',
        'accent_color' : '#f5e8b7',
        'pointer_color' : '#ff1744',
    },
    'Fancy': {
        'heading_color': '#105599',
	    'primary_fg': '#755',
	    'primary_bg': '#efefef',
	    'secondary_bg': '#d9d8df',
	    'secondary_fg': '#89E',
	    'alternate_bg': '#deddde',
	    'hover_bg': '#D1D9E1',
	    'accent_color': '#955200',
        'pointer_color': '#FF7722',
    },
    'Material Light': {
        'heading_color': '#4984c4',
	    'primary_fg': '#3b3b3b',
	    'primary_bg': '#fafafa',
	    'secondary_bg': '#e9eef2',
	    'secondary_fg': '#3b5e3b',
	    'alternate_bg': '#e9eef2',
	    'hover_bg': '#dae3ec',
	    'accent_color': '#4d7f43',
        'pointer_color': '#f50057',
    },
    'Material Dark': {
        'heading_color': '#aec7e3',
	    'primary_fg': '#bebebe',
	    'primary_bg': '#282828',
	    'secondary_bg': '#383838',
	    'secondary_fg': '#fefefe',
	    'alternate_bg': '#383838',
	    'hover_bg': '#484848',
	    'accent_color': 'teal',
        'pointer_color': '#e91e63',
    }   
}

def style_css(colors, *, light = 250, text_size = '22px', text_font = None, code_font = None, scroll = True, centered = True, aspect = 16/9, cwidth=100, ncol_refs = 2, _root = False):
    uclass = get_unique_css_class()
    margin = 'auto' if centered else 'unset'
    if (cwidth < 100) and (centered is False):
        margin = '0 auto' # if not 100%, horizontally still in center, vertically top

    _root_dict = {
        '--heading-color':f'{colors["heading_color"]}',
        '--primary-fg':f'{colors["primary_fg"]}',
        '--primary-bg':f'{colors["primary_bg"]}',
        '--secondary-bg':f'{colors["secondary_bg"]}',
        '--secondary-fg':f'{colors["secondary_fg"]}',
        '--alternate-bg':f'{colors["alternate_bg"]}',
        '--hover-bg':f'{colors["hover_bg"]}',
        '--accent-color':f'{colors["accent_color"]}',
        '--pointer-color':f'{colors["pointer_color"]}',
        '--text-size':f'{text_size}'
    }
    return _build_css(() if _root else (uclass,),{ # uclass is not used in root for exporting purpose
        **(_root_dict if not _root else {':root': _root_dict}),
        '^.SlidesWrapper, .SlideArea': {
            ':is(p,div,em,b,table,img,svg, i:not(.fa))': { # icons issue with i, but italic i should have fonts
                'font-family':f'{text_font!r}, "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" !important',
            },
            'code > span, .jp-RenderedHTMLCommon :is(pre, code)': {
                'font-family': f'{code_font!r}, "Cascadia Code", "Ubuntu Mono", "SimSun-ExtB", "Courier New" !important',
                'font-size':'90% !important',
            }, # Define color below at low specificity, otherwise it can overwrite code
            '*:not(mjx-c)': {'color':'var(--primary-fg)',}, 
            'mjx-c, .MathJax span': {"color":"inherit",}, # important to avoid heading color, MathJax span is for export
            '.tl-container, .tlui-icon, .tlui-button': {'color':'unset',},
        },
        '^.SlidesWrapper':{
            'container': 'slides / inline-size',
            'margin':'auto',
            'padding':'0px',
            'font-size':'var(--text-size) !important',
            'background':'var(--primary-bg)',
            'max-width':'100vw', # This is very important
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
            'hr': {
                'margin':'0 !important',
                'margin-block':'0.2em !important',
                'border':'none',
                'width':'auto',
                'height':'2px',
                'background':'linear-gradient(to right, var(--primary-bg),  var(--secondary-bg),var(--accent-color), var(--secondary-bg),var(--primary-bg))',
            },
            '> :not(div)': {'color':'var(--primary-fg)'}, # Do not change jupyterlab nav items
            ':is(h1, h2, h3, h4, h5, h6)': {
                'font-family':f'{text_font!r}, "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" !important',
                'font-weight':'normal',
                'color':'var(--heading-color)',
                'text-align':'center' if centered else 'left',
                'margin-block': '0.2em 0.3em !important', # Closer to the text of its own scope
                'line-height':'1.5em',
                'overflow':'hidden', # Firefox 
                'mjx-c, .MathJax span': {"color":"var(--heading-color)",}, # MathJax span is for export
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
                'color':'var(--primary-fg)!important',
                'background':'var(--primary-bg)!important',
                'border':'1px solid var(--alternate-bg) !important', # Makes it pleasant to view
                'tbody': {
                    'tr': {
                        '^:nth-child(odd)': {'background':'var(--alternate-bg)!important',},
                        '^:nth-child(even)': {'background':'var(--primary-bg)!important',},
                        '^:hover': {'background':'var(--hover-bg)!important',},
                    },
                },
            },
            'blockquote, blockquote > p': {
                'background':'var(--secondary-bg)',
                'color':'var(--secondary-fg)',
            },
        },
        '.raw-text': { # Should be same in notebook cell 
            'font-family': f'{code_font!r}, "Cascadia Code","Ubuntu Mono", "SimSun-ExtB", "Courier New" !important',
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
                'margin': f'{margin} !important',
                'padding': '0 !important',
                'padding-bottom': 'var(--paddingBottom, 0px) !important', # Set by JS dynamically
                'width': f'{cwidth}% !important',
                'max-width': f'{cwidth}% !important',
                'box-sizing': 'border-box !important',
                'overflow': 'auto !important' if scroll else 'hidden !important', # needs here too besides top
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
                    'background': 'var(--secondary-bg)',
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
            '.FirstTOC .toc-item.next' : {'opacity':'1',}, # In start, see full as same opacity
            'ul li::marker, ol li::marker': {'color':'var(--accent-color)',},
            '.raw-text': { # Should follow theme under slides 
                'font-family': f'{code_font!r}, "Cascadia Code","Ubuntu Mono", "SimSun-ExtB", "Courier New" !important', # Should be same in notebook cell
                'color':'var(--primary-fg) !important',
                'max-height':'400px',
                'white-space':'pre !important',
            },
            '.text-box': { # general text box for writing inline refrences etc. 
                'font-size':'0.85em !important', 
                'line-height':'0.99em !important',
                'position':'relative', 
                'left':'initial',
                'top':'initial',
                'padding':'2px 4px',
                'color':'var(--secondary-fg)',
                # Below are required to override behavior of span tag
                'display':'inline-block !important',
                'white-space':'break-spaces !important',
                '*': {'color':'var(--secondary-fg)',}, # should be same color 
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
                'line-height':'0.9em',
            },
            '.footnote ol': {'margin-top':'0.5em !important',},
            'pre': {
                'background':'none !important',
                'color':'var(--primary-fg) !important',
            },
            'figure': {
                'margin':'8px !important', # override default margin
                'object-fit':'scale-down !important',
                '^, > *':{
                    'display':'flex !important', # To align in center 
                    'flex-direction':'column !important', # To have caption at bottom 
                    'align-items':'center !important',
                    'justify-content':'center !important',
                },
                "img, svg" : {"margin": "auto",}, # keep in center if space available
            },
            'figcaption': {
                'font-size':'0.8em !important',
                'line-height':'1em !important',
                'padding':'0.5em 1.5em !important',
            },
            '.columns':{
                'width':'100%',
                'max-width':'100%',
                'display':'inline-flex',
                'flex-direction':'row',
                'column-gap':'0.2em',
                'height':'auto',
                '> *': {'box-sizing':'border-box !important',}
            },
        },
        '.highlight': {
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
                'padding':'8px 4px 8px 4px !important', 
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
                'min-width':'calc(90% - 2.2em)',
                'background':'transparent !important',
                'white-space':'pre !important',
                'overflow-wrap':'normal !important',
                'box-sizing':'border-box !important',
                '^:before': {
                    'content':'counter(line,decimal)',
                    'position':'sticky',
                    'top':'initial',
                    'left':'-4px',
                    'padding':'0 8px',
                    'display':'inline-block', # should be inline 
                    'text-align':'right',
                    '-webkit-user-select':'none',
                    'margin-left':'-3em',
                    'margin-right':'8px',
                    'font-size':'80% !important',
                    'opacity':'0.8 !important',
                },
                '> span': {
                    'white-space':'pre', #normal  for breaking words 
                    'word-break':'break-word', # for breaking words 
                },
                '^.code-no-focus': {'opacity':'0.3 !important'},
                '^.code-focus':{'text-shadow':'0 0 1px var(--primary-bg)'},
            },
            '^::-webkit-scrollbar': {'background':'var(--secondary-bg) !important',},
            '^::-webkit-scrollbar-corner': {'display': 'none',},
        },
        '.highlight, pre, .raw-text': {
            '^:hover::-webkit-scrollbar': {
                    'background':'var(--secondary-bg) !important'
                },
                '^:hover::-webkit-scrollbar-thumb': {
                    'background':'var(--hover-bg) !important'
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
        'a.citelink' : {
            'color': 'var(--accent-color)',
            '> sup': {'font-weight':'bold',},
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
            'background': ('var(--alternate-bg)',f'rgba({light-16},{light-10},{light-10},0.75)'), # Fallback  for Inherit and Custom theme
            '^.admonition > .admonition-title': {'display':'none !important'}, # Remove admonition title
            '^::before': {
                'content': '"📝 Note"',
                'display':'block',
                'color': 'var(--accent-color)',
                'border-bottom': '1px solid var(--hover-bg)',
                'box-sizing': 'border-box',
            },
            '^-info::before': {'content': '"❇️ Info" !important'},
            '^-warning::before': {'content': '"⚠️ Alert" !important'},
            '^-success::before': {'content': '"✅ Important" !important'},
            '^-error::before': {'content': '"⚡ Danger" !important'},
            '^-tip::before': {'content': '"💡 Tip" !important'},
        },
        '.block' : {
            'border-top': '3px solid var(--accent-color)',
            '^, ^-red,^-green,^-blue, ^-yellow, ^-magenta, ^-gray, ^-cyan': {
                'padding': '8px',
                'margin-bottom': '0.9em',
                'background': 'var(--secondary-bg)', # Fallback  for Inherit and Custom theme
            },
            '^-red' : {
                'border-top': ('3px solid red',f'3px solid rgb({light}, 0, 0)'), # Fallback  for Inherit and Custom theme
                'background':f'rgba({light},{light - 20},{light - 20},0.75)',
            },
            '^-green' : {
                'border-top': ('3px solid green',f'3px solid rgb(0, {light}, 0)'), # Fallback  for Inherit and Custom theme
                'background':f'rgba({light - 20},{light},{light - 20},0.75)',
            },
            '^-blue' : {
                'border-top': ('3px solid blue',f'3px solid rgb(0,0,{light})'), # Fallback  for Inherit and Custom theme
                'background':f'rgba({light -20},{light - 20},{light},0.75)',
            },
            '^-yellow' : {
                'border-top': ('3px solid yellow',f'3px solid rgb({light}, {light}, 0)'), # Fallback  for Inherit and Custom theme
                'background': f'rgba({light},{light},{light - 20},0.75)',
            },
            '^-magenta' : {
                'border-top': ('3px solid magenta',f'3px solid rgb({light}, 0, {light})'), # Fallback  for Inherit and Custom theme
                'background':f'rgba({light},{light - 20},{light},0.75)',
            },
            '^-cyan' : {
                'border-top': ('3px solid cyan',f'3px solid rgb(0, {light}, {light})'), # Fallback  for Inherit and Custom theme
                'background':f'rgba({light -20},{light},{light},0.75)',
            },
            '^-gray' : {
                'border-top': ('3px solid gray', f'3px solid rgb({light - 10}, {light - 10}, {light - 10})'),# Fallback  for Inherit and Custom theme
                'background':f'rgba({light -20},{light - 20},{light - 20},0.75)',
            },
        },
        'details': {
            'padding': '0.2em',
            '^, > summary': {'padding': '0.2em'},
            '> summary': {
                'padding-left': '0.2em !important',
                'color': 'var(--heading-color) !important',
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
    