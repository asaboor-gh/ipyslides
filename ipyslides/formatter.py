"""Format objects like different charting libraries and IPython display object to HTML representation.

"""
import sys
import textwrap
import inspect, re, json
from io import BytesIO
import matplotlib.pyplot as plt
import pygments
import ipywidgets as ipw
from IPython.display import HTML 
from IPython.core.display import __all__ as _all
from IPython import get_ipython

__reprs__ = [rep.replace('display_','') for rep in _all if rep.startswith('display_')] # Can display these in write command
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
    **Parameters**
    
    - plt_fig    : Matplotlib's figure instance, auto picks as well.
    - transparent: True of False for fig background.
    - caption    : Caption for figure.
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
    """Write bokeh figure as HTML string to use in `ipyslide.utils.write`.
    **Parameters**
    
    - bokeh_fig : Bokeh figure instance.
    - title     : Title for figure.
    """
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


def code_css(style='default',background='var(--secondary-bg)',className = None):
    """Style code block with given style from pygments module and background color.
    """
    if style not in pygments.styles.get_all_styles():
        raise ValueError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
    _class = '.highlight' if className is None else f'.highlight.{className}'
    _style = pygments.formatters.HtmlFormatter(style = style).get_style_defs(_class)
    

    return f"""<style>\n{_style}
    div{_class} pre, div{_class} code:before {{
        background: {background} !important;
    }}
    div{_class} code:hover::before {{
        background: none !important;
    }}\n</style>"""

def highlight(code, language='python', name = None, className = None, style='default', background = 'var(--secondary-bg)'):
    """Highlight code with given language and style. style only works if className is given.
    If className is given and matches any of pygments.styles.get_all_styles(), then style will be applied immediately.
    New in version 1.4.3"""
    if style not in pygments.styles.get_all_styles():
        raise ValueError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
    if className in pygments.styles.get_all_styles():
        style = className
        
    formatter = pygments.formatters.HtmlFormatter(style = style)
    _style = code_css(style=style, background = background, className=className) if className else ''
    _code = pygments.highlight(textwrap.dedent(code), # dedent make sure code blocks at any level are picked as well
                               pygments.lexers.get_lexer_by_name(language),
                               formatter)
    
    start, mid_end = _code.split('<pre>')
    middle, end = mid_end.split('</pre>')
    lines = middle.strip().replace('<span></span>','').splitlines()
    code_ = '\n' + '\n'.join([f'<code>{line}</code>' for line in lines]) # start with newline is important
    _title = name if name else language.title()
    
    if isinstance(className, str):
        start = start.replace('class="highlight"',f'class="highlight {className}"')
    
    return _HTML(f'''<div>
        <span class='lang-name'>{_title}</span>
        {_style}\n{start}
        <pre>{code_}
        </pre>\n{end}</div>''')
    
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
    elif isinstance(obj,(int,float, bool)):
        return True, str(obj)  
    elif isinstance(obj,(set,list,tuple)): # Then prefer other builtins
        return True, f"<div class='PyRepr'>{obj}</div>"
    
    # If Code object given
    for _type in ['class','function','module','method','builtin','generator']:
        if getattr(inspect,f'is{_type}')(obj):
            try:
                source = inspect.getsource(obj)
                source = re.sub(r'^#\s+','#',source) # Avoid Headings in source
                source = highlight(source,language='python',style='default',className=None).value
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


def stringify(obj):
    """Returns string of HTML for given object.
    New in 1.4.5"""
    if isinstance(obj,str):
        raise ValueError('can not stringify string')
    elif isinstance(obj,(_HTML, _HTML_Widget)):
        return obj._repr_html_() #_repr_html_ is a method of _HTML, _HTML_Widget, it is quick   
    else:
        # Next prefer custom methods of objects as they are more frequently used
        is_true, _html = format_object(obj)
        if is_true:
            return _html # it is a string
        
        # Ipython objects
        _reprs_ = [rep for rep in [getattr(obj,f'_repr_{r}_',None) for r in __reprs__] if rep]   
        for _rep_ in _reprs_:
            _out_ = _rep_()
            if _out_: # If there is object in _repr_<>_, don't return None
                return _out_
        
        # Return __repr__ if nothing above
        return f"<div class='PyRepr'>{obj.__repr__()}</div>"