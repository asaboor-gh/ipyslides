"""Format objects like different charting libraries and IPython display object to HTML representation.

"""
import sys
import inspect, re, json
from io import BytesIO
import matplotlib.pyplot as plt
from markdown import markdown

def plt2html(plt_fig=None,transparent=True,caption=None):
    """Write matplotib figure as HTML string to use in `ipyslide.utils.write`.
    - **Parameters**
        - plt_fig    : Matplotlib's figure instance, auto picks as well.
        - transparent: True of False for fig background.
    """
    if plt_fig==None:
        plt_fig = plt.gcf()
    plot_bytes = BytesIO()
    plt.savefig(plot_bytes,format='svg',transparent=transparent)
    plt.clf() # Clear image to avoid other display
    plt.close() #AVoids throwing text outside figure
    svg = '<svg' + plot_bytes.getvalue().decode('utf-8').split('<svg')[1]
    if caption:
        svg = svg + f'<p style="font-size:80% !important;">{caption}</p>'
    return f"<div class='zoom-container'>{svg}</div>"

def bokeh2html(bokeh_fig,title=""):
    from bokeh.resources import CDN
    from bokeh.embed import file_html
    return file_html(bokeh_fig, CDN, title)

def fix_ipy_image(image,width='100%'):
    img = image._repr_mimebundle_() # Picks PNG/JPEG/etc
    _src,=[f'data:{k};base64, {v}' for k,v in img[0].items()]
    return f"<img src='{_src}' width='{width}' height='auto'/>" # width is important, height auto fixed

def syntax_css():
    color_keys = {
        'inherit': 'n',
        '#008000': 'k ow kc',
        '#080': 'mi mf',
        '#ff7f0e': 'kn',
        '#2ca02c': 'nn',
        '#d62728': 'p',
        '#5650b5': 'c1 sd',
        '#AA22FF': 'o',
        'olive': 'nf',
        'red': 'se',
        '#337ab7': 'nc',
        '#1175cb': 'nb',
        '#BA2121': 's1 s2',
        '#7f7f7f': 'sa',
        '#2800ff': 'si',   
    }
    kcw = [[(_v,c,'bold') if _v in ['k','kc'] else (_v,c,'normal') for _v in k.split()] for c,k in color_keys.items()]
    kcw = [v for vs in kcw for v in vs] # Flatten
    css = '\n'.join([f'.codehilite .{k} {{color:{c};font-weight:{w};}}' for k,c,w in kcw]) # Fonts are declared in main CSS
    return "<style>\n{}\n</style>".format(css)

def _fix_code(_html):
    "Fix code highlighting for given _html string"
    _arr = [_h.split('</code>') for _h in _html.split('<code>')]
    _arr = [v for vs in _arr for v in vs] # Flatten
    _arr = ['<code>'+_a.replace('\n','</code><code>') + '</code>' if i % 2 != 0 else _a for i, _a in enumerate(_arr)] 
    return ''.join(_arr).replace('<span></span>','').replace('<code></code></pre>','</pre>') # Remove empty spans and last code line


# ONLY ADD LIBRARIEs who's required objects either do not have a _repr_html_ method or need ovverride

libraries = [
    {'name':'matplotlib.pyplot','obj':'Figure','func':plt2html,'args':(),'kwargs': {}},
    {'name':'altair','obj':'Chart','func': 'to_html','args':(),'kwargs': {}},
    {'name':'pygal','obj':'Graph','func':'render','args':{},'kwargs':{'is_unicode':True}},
    {'name':'pydeck','obj':'Deck','func':'to_html','args':(),'kwargs': {'as_string':True}},
    {'name':'pandas','obj':'DataFrame','func':'to_html','args':(),'kwargs': {}},
    {'name':'bokeh.plotting','obj':'Figure','func':bokeh2html,'args':(),'kwargs':{'title':''}},
    {'name':'IPython.display','obj':'Image','func':fix_ipy_image,'args':(),'kwargs':{'width':'100%'}}
    
]

def format_object(obj):
    try: # If matplotlib axes given
        _fig = obj.get_figure()
        return True,plt2html(_fig)
    except: pass
    
    # Some builtin types
    if isinstance(obj,dict):
        # First prefer keep_format method. 
        if '__keep_format__' in obj:
            return True, obj['__keep_format__']
        else:
            return  True, f"<div class='PyRepr'>{json.dumps(obj,indent=4)}</div>"    
    elif isinstance(obj,(set,list,tuple,int,float)): # Then prefer other builtins
        return True, f"<div class='PyRepr'>{obj}</div>"
    
    # If Code object given
    for _type in ['class','function','module','method','builtin','generator']:
        if getattr(inspect,f'is{_type}')(obj):
            try:
                source = inspect.getsource(obj)
                source = re.sub(r'^#\s+','#',source) # Avoid Headings in source
                # Create HTML
                source = syntax_css() + markdown(f'```python\n{source}\n```',extensions=['fenced_code','codehilite'])
                source = _fix_code(source) # Avoid empty spans/last empty line and make linenumbering possible
            except:
                source = f'Can not get source code of:\n{obj}'
            
            return (True, source)
    
    # Other Libraries   
    try: module_name = obj.__module__
    except: module_name = '' #str, int etc don't have __module__
    
    for lib in libraries:
        if lib['name'].split('.')[0] in module_name: #MATCH NAMES
            _module = sys.modules.get(lib['name'],None) # Already imported
            
            if not _module:
                get_ipython().run_cell(f"import {lib['name']} as _module") # Need import to compare
                
            _obj = getattr(_module,lib['obj'],None)
            if isinstance(obj, _obj):
                if not isinstance(lib['func'],str): # Handle Matplotlib, bokeh, df etc here by making handling functions
                    return True, lib['func'](obj, *lib['args'],**lib['kwargs'])
                else:
                    _func = getattr(obj, lib['func'],None)
                    if _func:
                        return True, _func(*lib['args'],**lib['kwargs'])

    # If Nothing found
    return False, NotImplementedError(f"{obj}'s html representation is not implemented yet!")       

 
            