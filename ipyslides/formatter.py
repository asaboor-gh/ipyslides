"""Format objects like different charting libraries and IPython display object to HTML representation.

"""
import sys
import inspect, re, json
from io import BytesIO
import matplotlib.pyplot as plt
from markdown import markdown
from pygments.formatters import HtmlFormatter
from pygments.styles import get_all_styles
import ipywidgets as ipw
from IPython.display import HTML
from IPython import get_ipython

class _HTML(HTML):
    def __init__(self, *args,**kwargs):
        "This HTML will be diplayable, printable and formatable. Can add other HTML object or string to it."
        super().__init__(*args,**kwargs)
        
    def __format__(self, spec):
        return f'{self._repr_html_():{spec}}'
    
    def __repr__(self):
        return repr(self._repr_html_())
    
    def __str__(self):
        return str(self._repr_html_())
    
    def __add__(self, other):
        if isinstance(other,_HTML):
            return _HTML(self._repr_html_() + other._repr_html_())
        elif isinstance(other,str):
            return _HTML(self._repr_html_() + other)
    
    @property
    def value(self):
        "Returns HTML string."
        return self._repr_html_()
    
class _HTML_Widget(ipw.HTML):
    "Class for HTML widgets based on ipywidgets.HTML, but with `_repr_html_` method. Usable in format string. Can add other HTML object or string to it."
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def _repr_html_(self):
        "Make it available in `write` command as well."
        return self.value
    
    def __format__(self, spec):
        return f'{self._repr_html_():{spec}}'
    
    def __repr__(self):
        return repr(self.value)
    
    def __str__(self):
        return str(self.value)
    
    def __add__(self, other):
        if isinstance(other,_HTML_Widget):
            return _HTML(self._repr_html_() + other._repr_html_())
        elif isinstance(other,str):
            return _HTML(self._repr_html_() + other)


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
    return _HTML(f"<div class='zoom-container'>{svg}</div>")

def _plt2htmlstr(plt_fig=None,transparent=True,caption=None):
    return plt2html(plt_fig=plt_fig,transparent=transparent,caption=caption).value


def bokeh2html(bokeh_fig,title=""):
    from bokeh.resources import CDN
    from bokeh.embed import file_html
    return _HTML(file_html(bokeh_fig, CDN, title))

def _bokeh2htmlstr(bokeh_fig,title=""):
    return bokeh2html(bokeh_fig,title).value

def fix_ipy_image(image,width='100%'):
    img = image._repr_mimebundle_() # Picks PNG/JPEG/etc
    _src,=[f'data:{k};base64, {v}' for k,v in img[0].items()]
    return _HTML(f"<img src='{_src}' width='{width}' height='auto'/>") # width is important, height auto fixed

def _ipy_imagestr(image,width='100%'):
    return fix_ipy_image(image,width=width).value


def code_css(style='default',background='var(--secondary-bg)'):
    "Style code block with given style from pygments module and background color."
    if style not in get_all_styles():
        raise ValueError(f"Style {style!r} not found in {list(get_all_styles())}")
    _style = HtmlFormatter(style=style).get_style_defs('.codehilite')

    return f"""
    <style>
    div.codehilite {{
        box-shadow: 0 1.6em 0 0 {background} inset !important;
    }}
    div.codehilite pre, 
    div.codehilite::before, 
    div.codehilite pre>code::before {{
        background: {background} !important;
    }}
    {_style}
    </style>"""

def _fix_code(_html):
    "Fix code highlighting for given _html string"
    _arr = [_h.split('</code>') for _h in _html.split('<code>')]
    _arr = [v for vs in _arr for v in vs] # Flatten
    _arr = ['<code>'+_a.replace('\n','</code><code>') + '</code>' if i % 2 != 0 else _a for i, _a in enumerate(_arr)] 
    return ''.join(_arr).replace('<span></span>','').replace('<code></code></pre>','</pre>') # Remove empty spans and last code line


# ONLY ADD LIBRARIEs who's required objects either do not have a _repr_html_ method or need ovverride

libraries = [
    {'name':'matplotlib.pyplot','obj':'Figure','func':_plt2htmlstr,'args':(),'kwargs': {}},
    {'name':'altair','obj':'Chart','func': 'to_html','args':(),'kwargs': {}},
    {'name':'pygal','obj':'Graph','func':'render','args':{},'kwargs':{'is_unicode':True}},
    {'name':'pydeck','obj':'Deck','func':'to_html','args':(),'kwargs': {'as_string':True}},
    {'name':'pandas','obj':'DataFrame','func':'to_html','args':(),'kwargs': {}},
    {'name':'bokeh.plotting','obj':'Figure','func':_bokeh2htmlstr,'args':(),'kwargs':{'title':''}},
    {'name':'IPython.display','obj':'Image','func':_ipy_imagestr,'args':(),'kwargs':{'width':'100%'}}  
]

def format_object(obj):
    "Returns string of HTML for given object."
    # If matplotlib axes given, handle it separately
    if hasattr(obj,'get_figure'): 
        return True,_plt2htmlstr(obj.get_figure())
    
    # Some builtin types
    if isinstance(obj,dict):
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
                source = markdown(f'```python\n{source}\n```',extensions=['fenced_code','codehilite'])
                source = _fix_code(source) # Avoid empty spans/last empty line and make linenumbering possible
            except:
                source = f'Can not get source code of:\n{obj}'
            
            return (True, source)
    
    # Other Libraries   
    module_name = obj.__module__ if hasattr(obj,'__module__') else '' #str, int etc don't have __module__
    
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
