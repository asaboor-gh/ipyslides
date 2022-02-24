__all__ = ['print_context',  'details', 'plt2html', 'set_dir', 'textbox',
            'image','svg','format_html','format_css','alert','colored','keep_format',
            'raw','enable_zoom','html_node','sig','doc']
__all__.extend(['rows','cols','block'])
__all__.extend([f'block_{c}' for c in 'rgbycmkowp'])


import os
import inspect
from io import BytesIO # For PIL image
from contextlib import contextmanager

from IPython.display import SVG
from IPython.utils.capture import capture_output
from IPython.core.display import Image
import ipywidgets as ipw

from .formatter import fix_ipy_image
from .writers import write, _HTML, _fmt_write, _fix_repr
 
        
@contextmanager
def print_context():
    "Use `print` or function printing with onside in this context manager to display in order."
    with capture_output() as cap:
        yield
    if cap.stderr:
        return cap.stderr
    write(raw(cap.stdout)) # clean whitspace preserved 
    
@contextmanager
def set_dir(path):
    current = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(current)

def format_html(*columns,width_percents=None,className=None):
    'Same as `write` except it does not display but give a dict object that can be passed to `write` and `iwrite`.'
    return _HTML(_fmt_write(*columns,width_percents=width_percents,className=className))

def format_css(selector, **css_props):
    "Provide CSS values with - replaced by _ e.g. font-size to font_size. selector is a string of valid tag/class/id etc."
    _css_props = {k.replace('_','-'):f"{v}" for k,v in css_props.items()} #Convert to CSS string if int or float
    _css_props = {k:v.replace('!important','').replace(';','') + '!important;' for k,v in _css_props.items()}
    props_str = '\n'.join([f"    {k}: {v}" for k,v in _css_props.items()])
    out_str = f"<style>\n{selector} {{\n{props_str}\n}}\n</style>"
    return _HTML(out_str)
        
def details(str_html,summary='Click to show content'):
    "Show/Hide Content in collapsed html."
    return f"""<details style='max-height:100%;overflow:auto;'><summary>{summary}</summary>{str_html}</details>"""

def __check_pil_image(data):
    "Check if data is a PIL Image or numpy array"
    if data.__repr__().startswith('<PIL'):
        im_bytes = BytesIO()
        data.save(im_bytes,data.format,quality=95) #Save image to BytesIO in format of given image
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
    img = fix_ipy_image(Image(data = _data,**kwargs),width=width)
    if caption:
        img = img + textbox(caption)  # Add caption
    if zoomable:
        return _HTML(f'<div class="zoom-container">{img}</div>')
    return _HTML(img)

def svg(data=None,caption=None,zoomable=True,**kwargs):
    "Display svg file or svg string/bytes with additional customizations. `kwrags` are passed to IPython.display.SVG. You can provide url/string/bytes/filepath for svg."
    svg = SVG(data=data, **kwargs)._repr_svg_()
    if caption:
        svg = svg + textbox(caption)  # Add caption 
    if zoomable:
        return _HTML(f'<div class="zoom-container">{svg}</div>')
    return _HTML(svg)

def enable_zoom(obj):
    "Add zoom-container class to given object, whether a widget or html/IPYthon object"
    try:
        return ipw.Box([obj]).add_class('zoom-container')
    except:
        return _HTML(f'<div class="zoom-container">{_fix_repr(obj)}</div>')
    
def html_node(tag,children = [],className = None,**node_attrs):
    """Returns html node with given children and node attributes like style, id etc.
    `tag` can be any valid html tag name.
    `children` expects:
        - str: A string to be added as node's text content.
        - html_node: A html_node to be added as child node.
        - list/tuple of [str, html_node]: A list of str and html_node to be added as child nodes.
    Example:
        html_node('img',src='ir_uv.jpg') #Returns IPython.display.HTML("<img src='ir_uv.jpg'></img>") and displas image if last line in notebook's cell.
        """
    if isinstance(children,str):
        content = children
    elif isinstance(children,(list,tuple)):
        content = ''.join(child if isinstance(child,str) else child._repr_html_() for child in children)
    else:
        try:
            content = children._repr_html_() #Try to get html representation of children if HTML object
        except:
            raise ValueError(f'Children should be a list/tuple of html_node or str, not {type(children)}')
    attrs = ' '.join(f'{k}="{v}"' for k,v in node_attrs.items()) # Join with space is must
    if className:
        attrs = f'class="{className}"' + ' ' + attrs # space is must after className
    return _HTML(f'<{tag} {attrs}>{content}</{tag}>')

 
def textbox(text, **css_props):
    """Formats text in a box for writing e.g. inline refrences. `css_props` are applied to box and `-` should be `_` like `font-size` -> `font_size`. 
    `text` is not parsed to general markdown i.e. only bold italic etc. applied, so if need markdown, parse it to html before. You can have common CSS for all textboxes using class `TextBox`."""
    css_props = {'display':'inline-block','white-space': 'pre', **css_props} # very important to apply text styles in order
    # white-space:pre preserves whitspacing, text will be viewed as written. 
    _style = ' '.join([f"{key.replace('_','-')}:{value};" for key,value in css_props.items()])
    return _HTML(f"<span class='TextBox' style = {_style!r}> {text} </span>")  # markdown="span" will avoid inner parsing

def alert(text):
    "Alerts text!"
    return _HTML(f"<span style='color:#DC143C;'>{text}</span>")
    
def colored(text,fg='blue',bg=None):
    "Colored text, `fg` and `bg` should be valid CSS colors"
    return _HTML(f"<span style='background:{bg};color:{fg};'>{text}</span>")

def keep_format(plaintext_or_html):
    "Bypasses from being parsed by markdown parser. Useful for some graphs, e.g. keep_raw(obj.to_html()) preserves its actual form."
    if not isinstance(plaintext_or_html,str):
        return plaintext_or_html # if not string, return as is
    return _HTML(plaintext_or_html) 

def raw(text):
    "Keep shape of text as it is, preserving whitespaces as well."
    return _HTML(f"<div class='PyRepr'>{text}<div>")

def rows(*objs):
    "Returns tuple of objects. Use in `write`, `iwrite` for better readiability of writing rows in a column."
    return objs # Its already a tuple

def cols(*objs,width_percents=None):
    "Returns HTML containing multiple columns of given width_percents."
    return format_html(*objs,width_percents=width_percents)

def block(title,*objs,bg = 'olive'):
    "Format a block like in LATEX beamer. *objs expect to be writable with `write` command."
    _title = f"""<center style='background:var(--secondary-bg);margin:0px -4px;'>
                <b>{title}</b></center>"""
    _out = _fmt_write(objs) # single column
    return _HTML(f"""<div style='padding:4px' class='block'>
        <div style='border-top:4px solid {bg};box-shadow: 0px 0px 4px {bg};border-radius:4px;padding:0 4px;'>
        {_title}
        {_out}
        </div></div>""")
    
def block_r(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='crimson')
def block_b(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='navy')
def block_g(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='#006400')
def block_y(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='#E4D00A')
def block_o(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='orange')
def block_p(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='purple')
def block_c(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='#48d1cc')
def block_m(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='magenta')
def block_w(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='whitesmoke')
def block_k(title,*objs):
    "See documentation of `block`."
    return block(title,*objs,bg='#343434')

def sig(callable,prepend_str = None):
    "Returns signature of a callable. You can prepend a class/module name."
    try:
        _sig = f'<b>{callable.__name__}</b><span style="font-size:85%;color:var(--secondary-fg);">{str(inspect.signature(callable))}</span>'
        if prepend_str: 
            _sig = alert(prepend_str + '.') + _sig
        return _HTML(_sig)
    except:
        raise TypeError(f'Object {callable} is not a callable')

def doc(callable,prepend_str = None):
    "Returns documentation of a callable. You can prepend a class/module name."
    try:
        _doc = _fix_repr(inspect.getdoc(callable))
        _sig = sig(callable,prepend_str)._repr_html_()
        return _HTML(f"<div class='PyRepr'>{_sig}<br>{_doc}</div>")
    except:
        raise TypeError(f'Object {callable} is not a callable')
    