__all__ = ['suppress_stdout','details', 'set_dir', 'textbox', 'vspace', 'center',
            'image','svg','iframe', 'format_html','format_css','alert','colored','keep_format',
            'raw','enable_zoom','html','sig','doc','code','today','sub','sup']
__all__.extend(['rows','cols','block'])
__all__.extend([f'block_{c}' for c in 'rgbycma'])


import os, re
import datetime
import inspect
import textwrap
from html import escape # Builtin library
from io import BytesIO # For PIL image
from contextlib import contextmanager, suppress

from IPython.display import SVG, IFrame
from IPython.core.display import Image, display
from IPython.utils.capture import capture_output
import ipywidgets as ipw

from .formatter import fix_ipy_image, _HTML
from .writers import _fmt_write, _fix_repr


backtick = '&#96;'

@contextmanager
def suppress_stdout():
    "Suppress stdout in a block of code, especially unwanted print from functions in other modules. (2.1.0+)"
    with capture_output() as captured:
        yield 
    
    outputs = captured.outputs
    new_outputs = []
    for out in outputs:
        if 'text/html'in out.data and re.findall(r'class(.*)CustomPrint',out.data['text/html']):
            continue
        else:
            new_outputs.append(out)
    return display(*new_outputs)

    
@contextmanager
def set_dir(path):
    "Context manager to set working directory to given path and return to previous working directory when done."
    current = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(current)

def format_html(*columns,width_percents=None,className=None):
    'Same as `write` except it does not write xplicitly, provide in write function'
    return _HTML(_fmt_write(*columns,width_percents=width_percents,className=className))

def format_css(selector, **css_props):
    "Provide CSS values with - replaced by _ e.g. font-size to font_size. selector is a string of valid tag/class/id etc."
    _css_props = {k.replace('_','-'):f"{v}" for k,v in css_props.items()} #Convert to CSS string if int or float
    _css_props = {k: f"{v.replace('!important','').replace(';','')} !important;" for k,v in _css_props.items()}
    props_str = '\n'.join([f"    {k}: {v}" for k,v in _css_props.items()])
    out_str = f"<style>\n{selector} {{\n{props_str}\n}}\n</style>"
    return _HTML(out_str)
        
def details(str_html,summary='Click to show content'):
    "Show/Hide Content in collapsed html."
    return _HTML(f"""<details style='max-height:100%;overflow:auto;'><summary>{summary}</summary>{str_html}</details>""")

def __check_pil_image(data):
    "Check if data is a PIL Image or numpy array"
    if data.__repr__().startswith('<PIL'):
        im_bytes = BytesIO()
        data.save(im_bytes,data.format if data.format else 'PNG',quality=95) #Save image to BytesIO in format of given image
        return im_bytes.getvalue()
    return data # if not return back data

def image(data=None,width='80%',caption=None, zoomable=True,**kwargs):
    """Displays PNG/JPEG files or image data etc, `kwrags` are passed to IPython.display.Image. 
    You can provide following to `data` parameter:
        
    - An opened PIL image. Useful for image operations and then direct writing to slides. 
    - A file path to image file.
    - A url to image file.
    - A str/bytes object containing image data.  
    """
    if isinstance(width,int):
        width = f'{width}px'
    _data = __check_pil_image(data) #Check if data is a PIL Image or return data
    img = fix_ipy_image(Image(data = _data,**kwargs),width=width) # gievs _HTML object
    cap = f'<figcaption>{caption}</figcaption>' if caption else ''
    _IMG = html('figure', img.value + cap)  # Add caption,  _HTML + _HTML
    if zoomable:
        return _HTML(f'<div class="zoom-container">{_IMG}</div>')
    return _IMG # _HTML

def svg(data=None,caption=None,zoomable=True,**kwargs):
    "Display svg file or svg string/bytes with additional customizations. `kwrags` are passed to IPython.display.SVG. You can provide url/string/bytes/filepath for svg."
    svg = SVG(data=data, **kwargs)._repr_svg_()
    cap = f'<figcaption>{caption}</figcaption>' if caption else ''
    _SVG = html('figure', svg + cap)
    if zoomable:
        return _HTML(f'<div class="zoom-container">{_SVG}</div>')
    return _SVG # _HTML

def iframe(src, width='100%',height='auto',**kwargs):
    "Display `src` in an iframe. `kwrags` are passed to IPython.display.IFrame"
    f = IFrame(src,width,height, **kwargs)
    return _HTML(f._repr_html_())

def enable_zoom(obj):
    "Add zoom-container class to given object, whether a widget or html/IPYthon object"
    try:
        return ipw.Box([obj]).add_class('zoom-container')
    except:
        return _HTML(f'<div class="zoom-container">{_fix_repr(obj)}</div>')

def center(obj):
    "Align a given object at center horizontally, whether a widget or html/IPYthon object"
    try:
        return ipw.Box([obj]).add_class('Center')
    except:
        return _HTML(f'<div class="Center">{_fix_repr(obj)}</div>')
    
def html(tag, children = None,className = None,**node_attrs):
    """Returns html node with given children and node attributes like style, id etc. If an ttribute needs '-' in its name, replace it with '_'.     
    `tag` can be any valid html tag name. A `tag` that ends with `/` will be self closing e.g. `hr/` will be `<hr/>`.     
    `children` expects:
    
    - If None, returns node such as 'image' -> <img alt='Image'></img> and 'image/' -> <img alt='Image' />
    - str: A string to be added as node's text content.
    - list/tuple of [objects]: A list of objects that will be parsed and added as child nodes. Widgets are not supported.
    
    Example:
    ```python
    html('img',src='ir_uv.jpg') #Returns IPython.display.HTML("<img src='ir_uv.jpg'></img>") and displas image if last line in notebook's cell.
    ```
    """
    if tag in 'hr/':
        return _HTML(f'<hr/>') # Special case for hr
    
    if children and tag.endswith('/'):
        raise ValueError(f'Parametr `children` should be None for self closing tag {tag!r}')
    
    node_attrs = {'style':"background:inherit;color:inherit;",**{k.replace('_','-'):v for k,v in node_attrs.items()}} # replace _ with - in keys, and add default style
    attrs = ' '.join(f'{k}="{v}"' for k,v in node_attrs.items()) # Join with space is must
    if className:
        attrs = f'class="{className}" {attrs}'
    
    if tag.endswith('/'): # Self closing tag
        return _HTML(f'<{tag[:-1]} {attrs} />' if attrs else f'<{tag[:-1]}/>')
    
    if children is None:
        content = ''
    elif isinstance(children,str):
        content = children
    elif isinstance(children,(list,tuple)):
        content = '\n'.join(_fix_repr(child) for child in children) # Convert to html nodes in sequence of rows
    else:
        raise ValueError(f'Children should be a list/tuple of objects or str, not {type(children)}')
        
    tag_in =  f'<{tag} {attrs}>' if attrs else f'<{tag}>' # space is must after tag, strip attrs spaces
    return _HTML(f'{tag_in}{content}</{tag}>')

def vspace(em = 1):
    "Returns html node with given height in em\nNew in version 1.4.2"
    return html('div',style=f'height:{em}em;')
 
def textbox(text, **css_props):
    """Formats text in a box for writing e.g. inline refrences. `css_props` are applied to box and `-` should be `_` like `font-size` -> `font_size`. 
    `text` is not parsed to general markdown i.e. only bold italic etc. applied, so if need markdown, parse it to html before. You can have common CSS for all textboxes using class `TextBox`."""
    css_props = {'display':'inline-block','white-space': 'pre', **css_props} # very important to apply text styles in order
    # white-space:pre preserves whitspacing, text will be viewed as written. 
    _style = ' '.join([f"{key.replace('_','-')}:{value};" for key,value in css_props.items()])
    return _HTML(f"<span class='TextBox' style = {_style!r}>{text}</span>")  # markdown="span" will avoid inner parsing

def alert(text):
    "Alerts text!"
    return _HTML(f"<span style='color:#DC143C;'>{text}</span>")
    
def colored(text,fg='blue',bg=None):
    "Colored text, `fg` and `bg` should be valid CSS colors"
    return _HTML(f"<span style='background:{bg};color:{fg};padding: 0.1em;border-radius:0.1em;'>{text}</span>")

def keep_format(plaintext_or_html):
    "Bypasses from being parsed by markdown parser. Useful for some graphs, e.g. keep_raw(obj.to_html()) preserves its actual form."
    if not isinstance(plaintext_or_html,str):
        return plaintext_or_html # if not string, return as is
    return _HTML(plaintext_or_html) 

def raw(text, className=None):
    "Keep shape of text as it is (but apply dedent), preserving whitespaces as well. "
    _class = className if className else ''
    escaped_text = escape(textwrap.dedent(text).strip('\n')) # dedent and strip newlines on top and bottom
    return _HTML(f"<div class='RawText {_class}'>{escaped_text}</div>")

def rows(*objs, className=None):
    "Returns tuple of objects. Use in `write`, `iwrite` for better readiability of writing rows in a column."
    return format_html(objs,className = className) # Its already a tuple, so will show in a column with many rows

def cols(*objs,width_percents=None, className=None):
    "Returns HTML containing multiple columns of given width_percents."
    return format_html(*objs,width_percents=width_percents,className = className)

def block(*objs,className = 'Block'):
    """Format a block like in LATEX beamer. *objs expect to be writable with `write` command.   
    Shortcut functions with pre-specified background colors are available: `block_<r,g,b,y,c,m,a>`.
    In 1.7.5+, you can create blocks just by CSS classes in markdown as {.Block}, {.Block-red}, {.Block-green}, etc.
    """
    return _HTML(f"<div class='{className}'>{_fmt_write(objs)}</div>")
    
def block_r(*objs): return block(*objs,className = 'Block-red')
def block_b(*objs): return block(*objs,className = 'Block-blue')
def block_g(*objs): return block(*objs,className = 'Block-green')
def block_y(*objs): return block(*objs,className = 'Block-yellow')
def block_c(*objs): return block(*objs,className = 'Block-cyan')
def block_m(*objs): return block(*objs,className = 'Block-magenta')
def block_a(*objs): return block(*objs,className = 'Block-gray')

def sig(callable,prepend_str = None):
    "Returns signature of a callable. You can prepend a class/module name."
    try:
        _sig = f'<b>{callable.__name__}</b><span style="font-size:85%;color:var(--secondary-fg);">{str(inspect.signature(callable))}</span>'
        if prepend_str: 
            _sig = f'{colored(prepend_str,"var(--accent-color)")}.{_sig}' # must be inside format string
        return _HTML(_sig)
    except:
        raise TypeError(f'Object {callable} is not a callable')


def doc(obj,prepend_str = None, members = None, itself = True):
    "Returns documentation of an `obj`. You can prepend a class/module name. members is True/List of attributes to show doc of."
    if obj is None:
        return _HTML('') # Must be _HTML to work on memebers
    
    _doc, _sig, _full_doc = '', '', ''
    if itself == True:
        with suppress(BaseException): # if not __doc__, go forwards
            _doc += _fix_repr((inspect.getdoc(obj) or '').replace('{','\u2774').replace('}','\u2775'))

        with suppress(BaseException): # This allows to get docs of module without signature
            _sig = sig(obj,prepend_str)
    
    # If above fails, try to get name of module/object
    _name = obj.__name__ if hasattr(obj,'__name__') else type(obj).__name__
    if _name == 'property':
        _name = obj.fget.__name__
        
    _pstr = f'{str(prepend_str) + "." if prepend_str else ""}{_name}'
    
    if _name.startswith('_'): # Remove private attributes
        return _HTML('') # Must be _HTML to work on memebers
    
    _sig = _sig or colored(_pstr,"var(--accent-color)") # Picks previous signature if exists
    _full_doc = f"<div class='Docs'>{_sig}<br>{_doc}\n</div>" if itself == True else ''
    _pstr = (prepend_str or _pstr) if itself == False else _pstr # Prefer given string if itself is not to doc
    
    _mems = []
    if members == True:
        if hasattr(obj,'__all__'):
            _mems = [getattr(obj, a, None) for a in obj.__all__]
        else: # if no __all__, show all public members
            for attr in [getattr(obj, d) for d in dir(obj) if not d.startswith('_')]:
                if inspect.ismodule(obj): # Restrict imported items in docs
                    if hasattr(attr, '__module__')  and attr.__module__ == obj.__name__:
                        _mems.append(attr) 
                elif inspect.isclass(obj):
                    if inspect.ismethod(attr) or inspect.isfunction(attr) or type(attr).__name__ == 'property':
                        _mems.append(attr)
                else:
                    with suppress(BaseException):
                        if attr.__module__ == obj.__module__: # Most useful
                            _mems.append(attr)
                
    elif isinstance(members, (list, tuple, set)):
        for attr in members:
            if not hasattr(obj,attr):
                raise AttributeError(f'Object {obj} does not have attribute {attr!r}')
            else:
                _mems.append(getattr(obj,attr))
    
    # Collect docs of members
    for attr in _mems:
        with suppress(BaseException):
            _class_members = inspect.ismodule(obj) and (inspect.isclass(attr) and (attr.__module__ == obj.__name__)) # Restrict imported classes in docs
            _full_doc += doc(attr, prepend_str = _pstr, members = _class_members, itself = True).value
    
    return _HTML(_full_doc)

def code(callable):
    "Returns full code of a callable. Added in 1.7.9, you can just pass callable into `write` command or use `ipyslides.Slides().source.from_callable`."
    try:
        return _HTML(_fix_repr(callable))
    except:
        raise TypeError(f'Object {callable} is not a callable')

def today(fmt = '%b %d, %Y',color = 'inherit'): # Should be inherit color for markdown flow
    "Returns today's date in given format."
    return colored(datetime.datetime.now().strftime(fmt),fg=color, bg = None)

def sub(text):
    return html('sub',text,style="font-size:70%;color:inherit;")

def sup(text):
    return html('sup',text,style="font-size:70%;color:inherit;")