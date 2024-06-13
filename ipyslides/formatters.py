"""Format objects like different charting libraries and IPython display object to HTML representation.

"""
import sys
import textwrap
import inspect, re, json
from io import BytesIO
import pygments
import ipywidgets as ipw

from IPython.display import display, HTML 
from IPython.core.display import __all__ as _all
from IPython import get_ipython

from ._base._widgets import HtmlWidget


__reprs = [rep.replace('display_','') for rep in _all if rep.startswith('display_')] # Can display these in write command

supported_reprs = tuple(__reprs) # don't let user change it

class XTML(HTML):
    def __init__(self, *args,**kwargs):
        "This HTML will be diplayable, printable and formatable. Use `self.as_widget()` to get a widget with same content."
        super().__init__(*args,**kwargs)
        
    def __format__(self, spec):
        return f'{self._repr_html_():{spec}}'
    
    def __repr__(self):
        return repr(self._repr_html_())
    
    def __str__(self):
        return str(self._repr_html_())
    
    def display(self):
        "Display this HTML object."
        display(self)
    
    @property
    def value(self):
        "Returns HTML string."
        return self._repr_html_()
    
    def as_widget(self, click_handler=None):
        "Returns HtmlWidget with same data."
        return HtmlWidget(self.value, click_handler=click_handler)
        

def plt2html(plt_fig = None,transparent=True,width = '95%', caption=None):
    """Write matplotib figure as HTML string to use in `ipyslide.utils.write`.
    **Parameters**
    
    - plt_fig    : Matplotlib's figure instance, auto picks as well.
    - transparent: True of False for fig background.
    - width      : CSS style width.
    - caption    : Caption for figure.
    """
    # First line is to remove depedency on matplotlib if not used
    plt = sys.modules.get('matplotlib.pyplot', __import__('matplotlib.pyplot'))
    _fig = plt_fig or plt.gcf()
    plot_bytes = BytesIO()
    _fig.savefig(plot_bytes,format='svg',transparent = transparent)
    _fig.clf() # Clear image to avoid other display
    plt.close() #AVoids throwing text outside figure
    width = f'width:{width}px;' if isinstance(width,int) else f'width:{width};'
    svg = f'<svg style="{width}"' + plot_bytes.getvalue().decode('utf-8').split('<svg')[1]
    
    cap = ''
    if caption:
        from .xmd import _fig_caption # avoid circular import and only on demenad
        cap = _fig_caption(caption)

    return XTML(f"<figure class='zoom-child'>{svg + cap}</figure>")

def _plt2htmlstr(plt_fig=None,transparent=True,width="95%", caption=None):
    return plt2html(plt_fig=plt_fig,transparent=transparent,width=width, caption=caption).value


def bokeh2html(bokeh_fig,title=""):
    """Write bokeh figure as HTML string to use in `ipyslide.utils.write`.
    **Parameters**
    
    - bokeh_fig : Bokeh figure instance.
    - title     : Title for figure.
    """
    from bokeh.resources import CDN
    from bokeh.embed import file_html
    return XTML(f'<div class="zoom-child">{file_html(bokeh_fig, CDN, title)}</div>')

def _bokeh2htmlstr(bokeh_fig,title=""):
    return bokeh2html(bokeh_fig,title).value

def fix_ipy_image(image,width='100%'): # Do not add zoom class here, it's done in util as well as below
    img = image._repr_mimebundle_() # Picks PNG/JPEG/etc
    _src,=[f'data:{k};base64, {v}' for k,v in img[0].items()]
    return XTML(f"<img src='{_src}' width='{width}' height='auto'/>") # width is important, height auto fixed

def _ipy_imagestr(image,width='100%'): # Zoom for auto output
    return f'<div class="zoom-child">{fix_ipy_image(image,width=width).value}</div>'


def code_css(style='default',color = None, background = None, hover_color = 'var(--alternate-bg)', css_class = None, lineno = True):
    """Style code block with given style from pygments module. `color` and `background` are optional and will be overriden if pygments style provides them.
    """
    _class = '.highlight' if css_class is None else f'.highlight.{css_class}'
    
    from .xmd import get_unique_css_class # Avoid circular import
    _class = get_unique_css_class() + ' ' + _class # Add unique class to avoid conflict with other slides in Jupyter lab
        
    if style not in pygments.styles.get_all_styles():
        raise KeyError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
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
     
    return f"""<style>\n{_style}
    {_class} {{ 
        background: {bg}; 
        color: {fg}; 
        border-left: 0.2em solid {hover_color};
        border-radius: 0.2em;
    }}
    span.err {{border: none !important;}}
    
    {_class} code {{
        padding-left: {'2.2em' if lineno else '0.5em'};
    }}
    {_class} code:hover {{
        background: {hover_color} !important; /* Important to override default hover */
    }}
    {_class} code:before {{
        opacity: 0.8 !important;
        width: {'1.2em' if lineno else '0'};
        color: {fg};
        font-size: 80% !important;
        display:{'inline-block' if lineno else 'none'} !important;
    }}\n</style>"""

def highlight(code, language='python', name = None, css_class = None, style='default', color = None, background = None, hover_color = 'var(--alternate-bg)', lineno = True):
    """Highlight code with given language and style. style only works if css_class is given.
    If css_class is given and matches any of `pygments.styles.get_all_styles()`, then style will be applied immediately.
    color is used for text color as some themes dont provide text color."""
    if style not in pygments.styles.get_all_styles():
        raise KeyError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
    if css_class in pygments.styles.get_all_styles():
        style = css_class
        
    formatter = pygments.formatters.HtmlFormatter(style = style)
    _style = code_css(style=style, color = color, background = background, hover_color = hover_color,css_class=css_class, lineno = lineno) if css_class else ''
    _code = pygments.highlight(textwrap.dedent(code).strip('\n'), # dedent make sure code blocks at any level are picked as well
                               pygments.lexers.get_lexer_by_name(language),
                               formatter)
    
    start, mid_end = _code.split('<pre>')
    middle, end = mid_end.split('</pre>')
    lines = middle.strip().replace('<span></span>','').splitlines()
    code_ = '\n' + '\n'.join([f'<code>{line}</code>' for line in lines]) # start with newline is important
    _title = name if name else language.title()
    
    if isinstance(css_class, str):
        start = start.replace('class="highlight"',f'class="highlight {css_class}"')
    
    return XTML(f'''<div>
        <span class='lang-name'>{_title}</span>
        {_style}\n{start}
        <pre>{code_}
        </pre>\n{end}</div>''')

def _inline_style(kws_or_widget):
    "CSS inline style from keyword arguments having _ inplace of -. Handles widgets layout keys automatically."
    if isinstance(kws_or_widget, ipw.DOMWidget):
        kws = {k:v for k,v in kws_or_widget.layout.get_state().items() if v and (k[0]!='_')}
    elif isinstance(kws_or_widget, dict):
        kws = kws_or_widget
    else:
        raise TypeError("expects dict or ipywidgets.Layout!")
    out = ''.join(f"{k.replace('_','-')}:{v};" for k,v in kws.items())
    return f'style="{out}"'
    
class Serializer:
    def __init__(self):
        """HTML serializer for an object to use inside Slides.write."""
        self._libs = []
    
    def register(self, obj_type, verbose = True):
        """Decorator to register html serializer for an object type.
        
        - Decoracted function accepts one argument that will take `obj_type` and should return HTML string.
        - This definition will take precedence over any other in the module.
        - All regeisted serializers only exist for the lifetime of the module in a namespace.
        - Only a single serializer can be registered for an object type.
        
        **Usage**
        ```python
        class MyObject:
            def __repr__(self):
                return 'My object is awesome'
        
        slides = ipyslides.Slides()
        @slides.serializer.register(MyObject)
        def parse_myobject(obj):
            return f'<h1>{obj!r}</h1>'
            
        my_object = MyObject()
        slides.write(my_object) #This will write "My object is awesome" as main heading
        parse_myobject(my_object) #This will return "<h1>My object is awesome</h1>"
        
        #This is equivalent to above for custom objects(builtin objects can't be modified)
        class MyObject:
            def _repr_html_(self):
                return '<h1>My object is awesome</h1>'
                
        my_object = MyObject()
        slides.write(my_object)
        ```
        ::: note
            - Serializer function should return html string. It is not validated for correct code on registration time.       
            - Serializer is useful for buitin types mostly, for custom objects, you can always define a `_repr_html_` method which works as expected.
            - Serialzers for widgets are equivalent to `Slides.alt(func, widget)` inside `write` command for export purpose. Other commands such as `Slides.format_html` will pick oldest value only.
            - Use `Slides.display(obj)` to display as it is and export html from metadata instead of IPython's display.
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
    
    @property
    def available(self):
        "Tuple of all registered types."
        return tuple(self._libs)
    
    @property
    def types(self):
        "Tuple of all registered types."
        return tuple(item['obj'] for item in self._libs)
    
    def get_func(self, obj_type):
        "Get serializer function for a type. Returns None if not found."
        if type(obj_type) in serializer.types: # Do not check instance here, need specific information
            for item in serializer.available:
                if type(obj_type) == item['obj']:
                    return item['func']
        # Check instance for ipywidgets.HTML/Output after user defined types
        elif isinstance(obj_type, ipw.Box):
            return self._alt_box
        elif isinstance(obj_type, ipw.Output):
            return self._alt_output
        elif isinstance(obj_type, (ipw.HTML, ipw.HTMLMath, HtmlWidget)): # Instance here is fine to include subclasses as they will behave same
            return self._alt_html
        return None
    
    def get_metadata(self, obj_type):
        "Get metadata for a type to use in `display(obj, metadata)` for export purpose. This take precedence over object's own html representation. Returns {} if not found."
        if (func := self.get_func(obj_type)):
            return {'text/html': func(obj_type)}
        return {}
    
    def display(self, obj):
        "Display an object with metadata if a serializer available. Same as display(obj, metadata = serializer.get_metadata(obj)))"
        if (metadata := self.get_metadata(obj)):
            display(obj, metadata = metadata)
        else:
            display(obj)
    
    def _alt_box(self, box_widget):
        if not isinstance(box_widget, ipw.Box):
            raise TypeError(f"Expects ipywidget's Box and subclasses, got {type(box_widget)}")
        
        kwargs = dict(width='100%', gap="0.2em") # avoid collapse in export, defult layouts are None there
        if isinstance(box_widget,ipw.HBox):
            kwargs.update(dict(display="flex",flex_flow="row nowrap"))
        elif isinstance(box_widget,ipw.VBox):
            kwargs.update(dict(display="flex",flex_flow="column nowrap"))
        
        kwargs.update({k:v for k,v in box_widget.layout.get_state().items() if v and k[0]!='_'}) # only those if not None
        css_class = ' '.join(box_widget._dom_classes) # To keep style of HTML widget, latest as well
        content = '\n'.join((self.get_func(child) or (lambda child: ''))(child) for child in box_widget.children)
        return f'<div class="{css_class}" {_inline_style(kwargs)}>{content}</div>'
    
    def _alt_html(self, html_widget):
        """Convert ipywidgets.HTML object to HTML string."""
        if not isinstance(html_widget,(ipw.HTML,ipw.HTMLMath,HtmlWidget)):
            raise TypeError(f"Expects ipywidgets.(HTML/HTMLMath) or ipyslides's HtmlWidget, got {type(html_widget)}")

        css_class = ' '.join(html_widget._dom_classes) # To keep style of HTML widget, latest as well
        return f'<div class="{css_class}" {_inline_style(html_widget)}>{html_widget.value}</div>' 
    
    def _alt_output(self, output_widget):
        "Convert objects in ipywidgets.Output to HTML string."
        if not isinstance(output_widget, ipw.Output):
            raise TypeError(f"Expects Output widget instnace, got {type(output_widget)}")
        
        from .xmd import raw # avoid circular import
        
        css_class = ' '.join(output_widget._dom_classes) # To keep style of Output widget, latest as well
        content = ''
        for d in output_widget.outputs:
            if 'text' in d:
                content += raw(d['text']).value
            elif 'data' in d:
                if 'text/html' in d['data']:
                    content += d['data']['text/html']  
                elif 'text/latex' in d['data']:
                    content += d['data']['text/latex']
        
        return f'<div class="{css_class}" {_inline_style(output_widget)}>{content}</div>' 
    

    def unregister(self, obj_type):
        "Unregister all serializer handlers for a type."
        for item in self._libs:
            if obj_type is item['obj']:
                self._libs.remove(item)
    
    def unregisterall(self):
        "Unregister all serializer handlers."
        self._libs = []
    
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
    if (func := serializer.get_func(obj)):
        return True, func(obj)
    
    # If matplotlib axes given, handle it separately
    if hasattr(obj,'get_figure'): 
        return True,_plt2htmlstr(obj.get_figure())
    
    # Some builtin types
    if isinstance(obj,dict):
        return  True, f"<div class='raw-text'>{json.dumps(obj,indent=4)}</div>"  
    elif isinstance(obj,(int,float, bool)):
        return True, str(obj)  
    elif isinstance(obj,(set,list,tuple)): # Then prefer other builtins
        return True, f"<div class='raw-text'>{obj}</div>"
    
    # If Code object given
    for _type in ['class','function','module','method','builtin','generator']:
        if getattr(inspect,f'is{_type}')(obj):
            try:
                source = textwrap.dedent(inspect.getsource(obj)).strip('\n') # dedent is must
                source = re.sub(r'^#\s+','#',source) # Avoid Headings in source
                source = highlight(source,language='python',style='default',css_class=None).value
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
                if not isinstance(lib['func'],str): # Handle Matplotlib, bokeh, df etc here by making handling functions, they are zoom enabled
                    return True, lib['func'](obj, *lib['args'],**lib['kwargs'])
                else:
                    _func = getattr(obj, lib['func'],None)
                    if _func:
                        _output = _func(*lib['args'],**lib['kwargs'])
                        return True, f'<div class="zoom-self">{_output}</div>' # enbable zoom-self here, not child

    # If Nothing found
    return False, NotImplementedError(f"{obj}'s html representation is not implemented yet!")       


def htmlize(obj):
    "Returns string of HTML representation for given object."
    if isinstance(obj,str):
        from .xmd import parse # Avoid circular import
        return parse(obj, returns = True)
    elif isinstance(obj,XTML):
        return obj._repr_html_() #_repr_html_ is a method of XTML and it is quick   
    else:
        # Next prefer custom methods of objects as they are more frequently used
        is_true, _html = format_object(obj)
        if is_true:
            return _html # it is a string
        
        # Ipython objects
        _reprs_ = [rep for rep in [getattr(obj,f'_repr_{r}_',None) for r in __reprs] if rep]   
        for _rep_ in _reprs_:
            _out_ = _rep_()
            if _out_: # If there is object in _repr_<>_, don't return None
                return _out_
        
        # Return __repr__ if nothing above
        return f"<div class='raw-text'>{obj.__repr__()}</div>"
