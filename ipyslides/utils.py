__all__ = ['bullets','suppress_output','suppress_stdout','details', 'set_dir', 'textbox', 'vspace', 'center',
            'image','svg','iframe', 'format_html','format_css','alert','colored','keep_format', 'run_doc',
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

from .formatters import fix_ipy_image, _HTML
from .writers import _fmt_write, _fix_repr

def _sub_doc(**kwargs):
    "Substitute docstring with given kwargs."
    def _inner(func):
        func.__doc__ = func.__doc__.format(**kwargs)
        return func
    return _inner

_css_docstring = """`css_dict` is a nested dict of css selectors and properties. There are few special rules in `css_dict`:

- All nested selectors are joined with space, so '.A': {'.B': ... } becomes '.A .B {...}' in CSS.
- A '^' in start of a selector joins to parent selector without space, so '.A': {'^:hover': ...} becomes '.A:hover {...}' in CSS. You can also use '.A:hover' directly but it will restrict other nested keys to hover only.
- A '+' in start of a key allows using same key in dict for CSS fallback, so '.A': {'font-size': '20px','+font-size': '2em'} becomes '.A {font-size: 20px; font-size: 2em;}' in CSS.

Read about specificity of CSS selectors [here](https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity).

**Python** 
```python
{
    '.A': { # .A is repeated nowhere! But in CSS it is a lot
        'z-index': '2',
        '.B': {
            'font-size': '24px',
            '+font-size': '2em', # Overwrites previous in CSS, note + in start, add many more + for more overwrites
            '^:hover': {'opacity': '1'}, # Attach pseudo class to parent by prepending ^, or .B:hover works too
        },
        '> div': { # Direct nesting by >
            'padding': '0',
            '@media screen and (min-width: 650px)' : { # This will take above selectors inside and move itself out
                'padding': '2em',
            },
        },
        '.C p': {'font-size': '14px'},
    },
    '.D': {
        'transform': 'translate(-2px,1px)',
        '^, h1': { # caret ^ in start of key joins to parent without space
            'background': 'red',
            'span, i': { # Heavy nesting
                'color':'whitemoke',
                '@keyframes animation-name': { # This will not stay inside nesting
                    'from': {'opacity':0},
                    'to': {'opacity':1}
                },
            },
        },  
    },
}
```
**CSS** (output of `...format_css`,`...set_css` functions)
```css
<style>
.SlideArea .A {
    z-index : 2;
}
.SlideArea .A .B {
    font-size : 24px;
    font-size : 2em;
}
.SlideArea .A .B:hover {
    opacity : 1;
}
.SlideArea .A > div {
    padding : 0;
}
@media screen and (min-width: 650px) {
    .SlideArea .A > div {
        padding : 2em;
    }
}
.SlideArea .A .C p {
    font-size : 14px;
}
.SlideArea .D {
    transform : translate(-2px,1px);
}
.SlideArea .D,
.SlideArea .D  h1 {
    background : red;
}
.SlideArea .D span,
.SlideArea .D  i,
.SlideArea .D h1 span,
.SlideArea .D h1  i {
    color : whitemoke;
}
@keyframes animation-name {
    from {
        opacity : 0;
    }
    to {
        opacity : 1;
    }
}
</style>
```
"""

def _filter_prints(outputs):
    new_outputs, new_prints = [], []
    for out in outputs:
        if 'text/html'in out.data and re.findall(r'class(.*)custom-print',out.data['text/html']):
            new_prints.append(out)
        else:
            new_outputs.append(out)
    return new_outputs, new_prints

@contextmanager
def suppress_output(keep_stdout = False):
    "Suppress output of a block of code. If `keep_stdout` is True, only display data is suppressed."
    with capture_output() as captured:
        yield # Do not yield
    
    if keep_stdout:
        outputs = captured.outputs
        _, new_prints = _filter_prints(outputs)
        if new_prints:
            return display(*new_prints) # under slides
        elif captured.stdout:
            return print(captured.stdout) # outside slides


@contextmanager
def suppress_stdout():
    "Suppress stdout in a block of code, especially unwanted print from functions in other modules."
    with capture_output() as captured:
        yield # do not yield, we want to suppress under and outside slides
    
    outputs = captured.outputs
    new_outputs, _ = _filter_prints(outputs)
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

def _validate_key(key):
    "Validate key for CSS,allow only string or tuple of strings. commas are allowed only in :is(.A,#B),:has(.A,#B) etc."
    if not isinstance(key,str):
        raise ValueError(f'key should be string, got {key!r}')

    if ',' in key:
        all_matches = re.findall(r'\((.*?)\)',key,flags=re.DOTALL)
        for match in all_matches:
            key = key.replace(f'{match}',match.replace(',','$'),1)  # Make safe from splitting with comma
    return key

def _build_css(selector, data):
    "selctor is tuple of string(s), data contains nested dictionaries of selectors, attributes etc."
    content = '\n' # Start with new line so style tag is above it
    children = []
    attributes = []
    
    for key, value in data.items():
        key = _validate_key(key) # Just validate key
        if isinstance(value, dict):
            children.append( (key, value) )
        else:
            attributes.append( (key, value) )

    if attributes:
        content += re.sub(r'\s+\^','', (' '.join(selector) + " {\n").lstrip()) # Join nested tags to parent if it starts with ^
        content += '\n'.join(f"\t{key.lstrip('+')} : {value};"  for key, value in attributes)  #  + is multiple keys handler
        content += "\n}\n"

    for key, value in children:
        if key.startswith('@media'): # Media query can be inside a selector and will be
            content += f"{key} {{\n\t"
            content += _build_css(selector, value).replace('\n','\n\t').rstrip('\t') # last tab is bad
            content += "}\n"
        elif key.startswith('@'): # Page, @keyframes etc.
            content += f"{key} {{\n\t"
            content += _build_css((), value).replace('\n','\n\t').rstrip('\t')
            content += "}\n"
        elif  key.startswith(':root'): # This is fine
            content+= _build_css((key,), value)
        else:
            old_sels = re.sub(r'\s+', ' ',' '.join(selector)).replace('\n','').split(',') # clean up whitespace
            sels = ',\n'.join([f"{s} {k}".strip() for s in old_sels for k in key.split(',')]) # Handles all kind of nested selectors
            content += _build_css((sels,), value)

    
    content = re.sub(r'\$', ',', content) # Replace $ with ,
    content = re.sub(r'\n\s+\n|\n\n','\n', content) # Remove empty lines after tab is replaced above
    content = re.sub('\t', '    ', content) # 4 space instead of tab is bettter option
    content = re.sub(r'\^',' ', content) # Remove left over ^ from start of main selector
        
    return content

def _format_css(css_dict, allow_root_attrs = False):
    _all_css = '' # All css
    root_attrs = {k:v for k,v in css_dict.items() if not isinstance(v,dict)}
    if allow_root_attrs:
        if root_attrs:
            attrs_str = '\n'.join(f'\t{k} : {v};' for k,v in root_attrs.items())
            _all_css += f'\n.SlidesWrapper, .BackLayer .Front {{\n{attrs_str}\n}}' # Set background for slide
    if root_attrs and not allow_root_attrs:
        print(f'Skipping attributes: \n{root_attrs}\nat root level of css_dict!')
    
    css_dict = {k:v for k,v in css_dict.items() if isinstance(v,dict)} # Remove root attrs after they are set above for background, no more use
    _all_css += _build_css(('.SlideArea',),css_dict) # Build css from dict
    return html('style', _all_css)
    
@_sub_doc(css_docstring = _css_docstring)
def format_css(css_dict):
    "{css_docstring}"
    return _format_css(css_dict, allow_root_attrs = False)
        
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

def image(data=None,width='80%',caption=None, **kwargs):
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
    cap = f'<figcaption class="no-zoom">{caption}</figcaption>' if caption else ''
    return html('figure', img.value + cap, className='zoom-child')  # Add caption,  _HTML + _HTML

def svg(data=None,caption=None,**kwargs):
    "Display svg file or svg string/bytes with additional customizations. `kwrags` are passed to IPython.display.SVG. You can provide url/string/bytes/filepath for svg."
    svg = SVG(data=data, **kwargs)._repr_svg_()
    cap = f'<figcaption class="no-zoom">{caption}</figcaption>' if caption else ''
    return html('figure', svg + cap, className='zoom-child')


def iframe(src, width='100%',height='auto',**kwargs):
    "Display `src` in an iframe. `kwrags` are passed to IPython.display.IFrame"
    f = IFrame(src,width,height, **kwargs)
    return _HTML(f._repr_html_())

def enable_zoom(obj):
    "Wraps are given obj in a parent with 'zoom-child' class, whether a widget or html/IPYthon object"
    try:
        return ipw.Box([obj]).add_class('zoom-child')
    except:
        return _HTML(f'<div class="zoom-child">{_fix_repr(obj)}</div>')

def center(obj):
    "Align a given object at center horizontally, whether a widget or html/IPYthon object"
    try:
        return ipw.Box([obj]).add_class('align-center')
    except:
        return _HTML(f'<div class="align-center">{_fix_repr(obj)}</div>')
    
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
    
    if tag == 'style':
        node_attrs = {} # Ignore node_attrs for style tag
    else:
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
    "Returns html node with given height in `em`."
    return html('div',style=f'height:{em}em;')
 
def textbox(text, **css_props):
    """Formats text in a box for writing e.g. inline refrences. `css_props` are applied to box and `-` should be `_` like `font-size` -> `font_size`. 
    `text` is not parsed to general markdown i.e. only bold italic etc. applied, so if need markdown, parse it to html before. You can have common CSS for all textboxes using class `text-box`."""
    css_props = {'display':'inline-block','white-space': 'pre', **css_props} # very important to apply text styles in order
    # white-space:pre preserves whitspacing, text will be viewed as written. 
    _style = ' '.join([f"{key.replace('_','-')}:{value};" for key,value in css_props.items()])
    return _HTML(f"<span class='text-box' style = {_style!r}>{text}</span>")  # markdown="span" will avoid inner parsing

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
    return _HTML(f"<div class='raw-text {_class}'>{escaped_text}</div>")

def rows(*objs, className=None):
    "Returns tuple of objects. Use in `write`, `iwrite` for better readiability of writing rows in a column."
    return format_html(objs,className = className) # Its already a tuple, so will show in a column with many rows

def cols(*objs,width_percents=None, className=None):
    "Returns HTML containing multiple columns of given width_percents."
    return format_html(*objs,width_percents=width_percents,className = className)

def block(*objs,className = 'block'):
    """Format a block like in LATEX beamer. *objs expect to be writable with `write` command.   
    ::: block
        - Shortcut functions with pre-specified background colors are available: `block_<r,g,b,y,c,m,a>`.
        - You can create blocks just by CSS classes in markdown as {.block}, {.block-red}, {.block-green}, etc.
    """
    return _HTML(f"<div class='{className}'>{_fmt_write(objs)}</div>")
    
def block_r(*objs): return block(*objs,className = 'block-red')
def block_b(*objs): return block(*objs,className = 'block-blue')
def block_g(*objs): return block(*objs,className = 'block-green')
def block_y(*objs): return block(*objs,className = 'block-yellow')
def block_c(*objs): return block(*objs,className = 'block-cyan')
def block_m(*objs): return block(*objs,className = 'block-magenta')
def block_a(*objs): return block(*objs,className = 'block-gray')

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
    _full_doc = f"<div class='docs'>{_sig}<br>{_doc}\n</div>" if itself == True else ''
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

def run_doc(obj,prepend_str = None):
    "Execute python code block inside docstring of an object. Block should start with '\`\`\`python run'."
    sig(obj,prepend_str = prepend_str).display()
    from .extended_md import parse_xmd # Import here to avoid circular import
    parse_xmd(inspect.getdoc(obj), display_inline = True)
    
def code(callable):
    "Returns full code of a callable, you can just pass callable into `write` command or use `ipyslides.Slides().source.from_callable`."
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

def bullets(iterable, ordered = False,marker = None, className = None):
    """A powerful bullet list. `iterable` could be list of anything that you can pass to `write` command.    
    `marker` could be a unicode charcter or string, only effects unordered list.
    """
    _bullets = []
    for it in iterable:
        start = f'<li style="list-style-type:\'{marker} \';">' if (marker and not ordered) else '<li>'
        _bullets.append(f'{start}{_fmt_write(it)}</li>')
    return html('div',children=[html('ol' if ordered else 'ul',_bullets, style='')],className = className) # Don't use style, it will remove effect of className
