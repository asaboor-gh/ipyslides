"""Format objects like different charting libraries and IPython display object to HTML representation.

"""
import sys
import textwrap
import inspect, re, json
from io import BytesIO
import matplotlib.pyplot as plt
import pygments
import ipywidgets as ipw
from IPython.display import display, HTML 
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
    
    def display(self):
        "Display this HTML object inline"
        display(self)
    
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
    
    def display(self):
        "Display this HTML widget inline"
        display(self)


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


def code_css(style='default',color = None, background = None, accent_color = 'var(--tr-hover-bg)', className = None, lineno = True):
    """Style code block with given style from pygments module. `color` and `background` are optional and will be overriden if pygments style provides them.
    """
    if style not in pygments.styles.get_all_styles():
        raise ValueError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
    _class = '.highlight' if className is None else f'.highlight.{className}'
    _style = pygments.formatters.HtmlFormatter(style = style).get_style_defs(_class)
    if style == 'default':
        _bg_fg = {'background': 'var(--secondary-bg)', 'color': 'var(--primary-fg)'} # Should match inherit theme
    else: # Override color and background if provided by theme
        _bg_fg = {} 
        items = [b.strip().split() for b in ''.join(re.findall(f'{_class}\s+?{{(.*?)}}',_style)).replace(':',' ').rstrip(';').split(';')]
        for item in items:
            if len(item) == 2 and item[0] in ('background','color'):
                _bg_fg[item[0]] = item[1]      
    
    # keep user preferences               
    bg = background if background else _bg_fg.get('background','var(--secondary-bg)')
    fg = color if color else _bg_fg.get('color','var(--primary-fg)')
    
    gradient = f'linear-gradient(to right, {accent_color}, {accent_color} 2.2em, {bg} 2.2em, {bg} 100%)'
        
    return f"""<style>\n{_style}
    {_class} {{ 
        background: {gradient if lineno else bg}; 
        color: {fg}; 
        border-left: 2px solid {accent_color};
    }}
    span.err {{border: none !important;}}
    
    {_class} code {{
        padding-left: {'2.2em' if lineno else '0.5em'};
    }}
    {_class} code:hover {{
        background: {accent_color} !important; /* Important to override default hover */
    }}
    {_class} code:before {{
        opacity: 0.95;
        background: {accent_color};
        width: {'1.2em' if lineno else '0'};
        color: {fg};
        display:{'inline-block' if lineno else 'none'} !important;
    }}\n</style>"""

def highlight(code, language='python', name = None, className = None, style='default', color = None, background = None, accent_color = 'var(--tr-hover-bg)', lineno = True):
    """Highlight code with given language and style. style only works if className is given.
    If className is given and matches any of pygments.styles.get_all_styles(), then style will be applied immediately.
    color is used for text color as some themes dont provide text color.
    New in version 1.4.3"""
    if style not in pygments.styles.get_all_styles():
        raise ValueError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
    if className in pygments.styles.get_all_styles():
        style = className
        
    formatter = pygments.formatters.HtmlFormatter(style = style)
    _style = code_css(style=style, color = color, background = background, accent_color = accent_color,className=className, lineno = lineno) if className else ''
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
    
class Serializer:
    def __init__(self):
        """HTML serializer for an object to use inside LiveSlides.write/iwrite."""
        self._libs = []
    
    def register(self, obj_type, verbose = True):
        """Decorator to register html serializer for an object type. 
        Decoracted function accepts one argument that will take `obj_type` and should return html string.
        This definition will take precedence over any other in the module.
        All regeisted serializers only exist for the lifetime of the module in a namespace.
        Only a single serializer can be registered for an object type.
        
        **Usage**
        ```python
        class MyObject:
            def __repr__(self):
                return 'My object is awesome'
        
        ls = ipyslides.LiveSlides()
        @ls.serializer.register(MyObject)
        def parse_myobject(obj):
            return f'<h1>{obj!r}</h1>'
            
        my_object = MyObject()
        ls.write(my_object) #This will write "My object is awesome" as main heading
        parse_myobject(my_object) #This will return "<h1>My object is awesome</h1>"
        ```
        
        **Note**: Serializer function should return html string. It is not validated for correct code on registration time.
        """
        def _register(func):
            if obj_type is str:
                raise TypeError("Cannot register serializer for string type! Use custom class to encapsulate string the way you want.")
            item = {'obj': obj_type, 'func': func}
            already = False
            for i, _lib in enumerate(self._libs):
                if item['obj'] is _lib['obj']:
                    self._libs[i] = item
                    if verbose:
                        print(f'Updated: {item["obj"]} → {item["func"].__name__}({item["obj"]})')
                    already = True
                    break
                    
            if not already:
                self._libs.append(item)
                if verbose:
                    print(f'Registered: {item["obj"]} → {item["func"].__name__}({item["obj"]})')
                
            return func
        return _register
    
    def unregister(self, obj_type):
        "Unregister all serializer handlers for a type."
        for item in self._libs:
            if obj_type is item['obj']:
                self._libs.remove(item)
    
    def __repr__(self):
        return 'Serializer(\n\t' + '\n\t'.join(f'{item["obj"]} → {item["func"].__name__}({item["obj"]})' for item in self._libs) + '\n)'

serializer = Serializer()
del Serializer # Make sure this is not used by user

    
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
    for _lib in serializer._libs:
        if isinstance(obj, _lib['obj']):
            return True, _lib['func'](obj)
    
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