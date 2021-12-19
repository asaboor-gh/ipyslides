__all__ = ['print_context', 'write', 'iwrite', 'details', 'plt2html', 'set_dir', 'textbox',
            'image','svg','file2img','format_html','format_css','alert','colored','keep_format',
            'source','raw','enable_zoom','html_node','sig','doc']
__all__.extend(['rows','block'])
__all__.extend([f'block_{c}' for c in ['r','g','b','y','c','m','k','o','w','p']])


import sys, linecache, os, re
import textwrap
import inspect
from io import StringIO
from io import BytesIO # For PIL image
from contextlib import contextmanager
from IPython.core.getipython import get_ipython
from markdown import markdown
from IPython.display import HTML, display, Code, SVG
from IPython.utils.capture import capture_output
from IPython.core.display import Image, __all__ as __all
import ipywidgets as ipw
from .objs_formatter import format_object, syntax_css, _fix_code, fix_ipy_image
from .objs_formatter import plt2html # For backward cimpatibility and inside class

__reprs__ = [rep.replace('display_','') for rep in __all if rep.startswith('display_')] # Can display these in write command

__md_extensions = ['fenced_code','tables','codehilite','footnotes'] # For MArkdown Parser
class _HTML_Widget(ipw.HTML):
    "Class for HTML widgets based on ipywidgets.HTML, but with `_repr_html_` method."
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def _repr_html_(self):
        "Make it available in `write` command as well."
        return self.value
    
# Do not use this in main work, just inside a function
class _Source_Widget(ipw.HTML):
    "Source code widget for IPython, give html fixed code as value."
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._code = self.value # Save original code for later operations
        self.raw = '' # Raw code
    
    def _repr_html_(self):
        "Make it available in `write` command as well."
        return self.value
        
    def show_lines(self, lines):
        "Return source object with selected lines from list/tuple/range of lines."
        self.value = self._code # Reset to original code first
        if isinstance(lines,(list,tuple,range)):
            _lines, link = [],0
            for i, line in enumerate(self._code.split('<code>'), start = -1):
                if i == -1:
                    _lines.append(line) # start things
                elif i in lines:
                    if link + 1 != i and i > 0:
                        _lines.append(f'<code class="code-no-focus"> + {i - link} more lines ... </code>')
                    _lines.append('<code>' + line) # Do not pick altogther if not in lines
                    link = i
            # i will go up to some value, so we need to add the last lines
            if i > link:
                _last_line = self._code.split('</pre>')[-1] # Get closing characters to add
                _lines.append(f'<code class="code-no-focus"> + {i - link} more lines ... </code></pre>{_last_line}')
            
            self.value = ''.join(_lines)   # update value 

            return self
        else:
            raise TypeError(f'lines must be list, tuple or range, not {type(lines)}')
    
    def show_all(self):
        "Show all lines. Call this after you may consumed lines using `show_lines`."
        self.value = self._code
        return self
    
    def focus_lines(self, lines):
        "Return source object with focus on given list/tuple/range of lines."
        self.value = self._code # Reset to original code first
        if isinstance(lines,(list,tuple,range)):
            _lines = []
            for i, line in enumerate(self._code.split('<code>'), start = -1):
                if i == -1:
                    _lines.append(line) # start things
                elif i not in lines:
                    _lines.append('<code class="code-no-focus">' + line)
                else:
                    _lines.append('<code class="code-focus">' + line)
            
            self.value = ''.join(_lines)  # update value
            return self
        else:
            raise TypeError(f'lines must be list, tuple or range, not {type(lines)}')
        
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


def _fix_repr(obj):
    if isinstance(obj,str):
        _obj = obj.strip().replace('\n','  \n') #Markdown doesn't like newlines without spaces
        _html = markdown(_obj,extensions=__md_extensions) 
        return _fix_code(_html)
        
    else:
        # Next prefer custom methods of objects. 
        is_true, _html = format_object(obj)
        if is_true:
            return _html
        # Ipython objects
        _reprs_ = [rep for rep in [getattr(obj,f'_repr_{r}_',None) for r in __reprs__] if rep]   
        for _rep_ in _reprs_:
            _out_ = _rep_()
            if _out_: # If there is object in _repr_<>_, don't return None
                return _out_
        
        # Return __repr__ if nothing above
        return f"<div class='PyRepr'>{obj.__repr__()}</div>"
    
def _fmt_write(*columns,width_percents=None,className=None):
    if not width_percents and len(columns) >= 1:
        widths = [f'{int(100/len(columns))}%' for _ in columns]
    else:
        widths = [f'{w}%' for w in width_percents]
    _class = className if isinstance(className,str) else ''
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in columns] 
    _cols = ''.join([f"""<div style='width:{w};overflow-x:auto;height:auto'>
                     {''.join([_fix_repr(row) for row in _col])}
                     </div>""" for _col,w in zip(_cols,widths)])
    _cols = syntax_css() + _cols if 'codehilite' in _cols else _cols
    if len(columns) == 1:
        return _cols.replace('<div', f'<div class = "{_class}"',1) if _class else _cols
    
    return f'''<div class="columns {_class}">{_cols}</div>''' if _class else f'''<div class="columns">{_cols}</div>'''
        
def write(*columns,width_percents=None,className=None): 
    '''Writes markdown strings or IPython object with method `_repr_<html,svg,png,...>_` in each column of same with. If width_percents is given, column width is adjusted.
    Each column should be a valid object (text/markdown/html/ have _repr_<format>_ or to_<format> method) or list/tuple of objects to form rows or explictly call `rows`. 
    
    - Pass int,float,dict,function etc. Pass list/tuple in a wrapped list for correct print as they used for rows writing too.
    - Give a code object from `ipyslides.get_cell_code()` to it, syntax highlight is enabled.
    - Give a matplotlib `figure/Axes` to it or use `ipyslides.utils.plt2html()`.
    - Give an interactive plotly figure.
    - Give a pandas dataframe `df` or `df.to_html()`.
    - Give any object which has `to_html` method like Altair chart. (Note that chart will not remain interactive, use display(chart) if need interactivity like brushing etc.)
    - Give an IPython object which has `_repr_<repr>_` method where <repr> is one of ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    - Give a function/class/module (without calling) and it will be displayed as a pretty printed code block.
    
    If an object is not in above listed things, `obj.__repr__()` will be printed. If you need to show other than __repr__, use `display(obj)` outside `write` command or use
    methods specific to that library to show in jupyter notebook.
    
    If you give a className, add CSS of it using `format_css` function and provide it to `write` function.
    
    Note: Use `keep_format` method to keep format of object for example `keep_format(altair_chart.to_html())`.
    Note: You can give your own type of data provided that it is converted to an HTML string.
    Note: `_repr_<format>_` takes precedence to `to_<format>` methods. So in case you need specific output, use `object.to_<format>`.
    
    ''' 
    return display(HTML(_fmt_write(*columns,width_percents=width_percents,className=className)))


def _fmt_iwrite(*columns,width_percents=None):
    if not width_percents:
        widths = [f'{int(100/len(columns))}%' for _ in columns]
    else:
        widths = [f'{w}%' for w in width_percents]
        
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in columns] #Make list if single element
    
    # Conver to other objects to HTML
    fixed_cols = []
    for j, _rows in enumerate(_cols):
        row = []
        for i, item in enumerate(_rows):
            try: 
                ipw.Box([item]) # Check for widget first 
                item._grid_location = {'row':i,'column':j}
                row.append(item)
            except:
                tmp = _HTML_Widget(value = _fix_repr(item))
                if '<script>' in tmp.value:
                    tmp.value,  = block_r('Error displaying object',f'Can not display object {item!r} as it needs Javascript. Use `write` or `display`.').values()

                tmp._grid_location = {'row':i,'column':j}
                row = [*row,tmp]
                
        fixed_cols.append(row)

    children = [ipw.VBox(children = _c, layout = ipw.Layout(width=f'{_w}')) for _c, _w in zip(fixed_cols,widths)]
    # Format things as given in input
    out_cols = tuple(tuple(row) if len(row) > 1 else row[0] for row in fixed_cols) 
    out_cols = tuple(out_cols) if len(out_cols) > 1 else out_cols[0]
    return ipw.HBox(children = children).add_class('columns'), out_cols #Return display widget and list of objects for later use

def iwrite(*columns,width_percents=None,className=None):
    """Each obj in columns could be an IPython widget like `ipywidgets`,`bqplots` etc 
    or list/tuple (or wrapped in `rows` function) of widgets to display as rows in a column. 
    Other objects (those in `write` command) will be converted to HTML widgets if possible. 
    Object containing javascript code may not work, use `write` command for that.
    
    If you give a className, add CSS of it using `format_css` function and provide it to `iwrite` function. 
    
    **Returns**: grid,columns as reference to use later and update. rows are packed in columns.
    
    **Examples**:
    grid, x = iwrite('X')
    grid, (x,y) = iwrite('X','Y')
    grid, (x,y) = iwrite(['X','Y'])
    grid, [(x,y),z] = iwrite(['X','Y'],'Z')
    #We unpacked such a way that we can replace objects with new one using `grid.update`
    new_obj = grid.update(x, 'First column, first row with new data') #You can update same `new_obj` with it's own widget methods. 
    """
    
    _grid, _objects = _fmt_iwrite(*columns,width_percents=width_percents)
    if isinstance(className,str):
        _grid.add_class(className)
        
    display(_grid) # Actually display the widget
    
    def update(self, old_obj, new_obj):
        "Updates `old_obj`  with `new_obj`. Returns reference to created/given widget, which can be updated by it's own methods."
        row, col = old_obj._grid_location['row'], old_obj._grid_location['column']
        widgets_row = list(self.children[col].children)
        try: 
            ipw.Box([new_obj]) # Check for widget first 
            tmp = new_obj
        except:
            tmp = _HTML_Widget(value = _fix_repr(new_obj))
            if '<script>' in tmp.value:
                tmp.value, = block_r('Error displaying object',f'Can not update object {new_obj!r} as it needs Javascript. Use `write` or `display` commands').values()
                return # Don't update
        
        tmp._grid_location = old_obj._grid_location # Keep location
        widgets_row[row] = tmp
        self.children[col].children = widgets_row
        return tmp
    
    _grid.update = update.__get__(_grid,type(_grid)) #attach update method to grid
    return _grid, _objects
    

def format_html(*columns,width_percents=None,className=None):
    'Same as `write` except it does not display but give a dict object that can be passed to `write` and `iwrite`.'
    return keep_format(_fmt_write(*columns,width_percents=width_percents,className=className))

def format_css(selector, **css_props):
    "Provide CSS values with - replaced by _ e.g. font-size to font_size. selector is a string of valid tag/class/id etc."
    _css_props = {k.replace('_','-'):f"{v}" for k,v in css_props.items()} #Convert to CSS string if int or float
    _css_props = {k:v.replace('!important','').replace(';','') + '!important;' for k,v in _css_props.items()}
    props_str = ''.join([f"{k}:{v}" for k,v in _css_props.items()])
    out_str = "<style>\n" + f"{selector} " + "{" + props_str + "\n}\n</style>"
    return keep_format(out_str)
        
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
        return f'<div class="zoom-container">{img}</div>'
    return img

def svg(data=None,caption=None,zoomable=True,**kwargs):
    "Display svg file or svg string/bytes with additional customizations. `kwrags` are passed to IPython.display.SVG. You can provide url/string/bytes/filepath for svg."
    svg = SVG(data=data, **kwargs)._repr_svg_()
    if caption:
        svg = svg + textbox(caption)  # Add caption 
    if zoomable:
        return f'<div class="zoom-container">{svg}</div>'
    return svg

def enable_zoom(obj):
    "Add zoom-container class to given object, whether a widget or html/IPYthon object"
    try:
        return ipw.Box([obj]).add_class('zoom-container')
    except:
        return {'__keep_format__': f'<div class="zoom-container">{_fix_repr(obj)}</div>'}
    
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
    return HTML(f'<{tag} {attrs}>{content}</{tag}>')


def _file2code(filename,language='python',name=None):
    "Only reads plain text or StringIO, return source object with `show_lines` and `focus_lines` methods."
    try:
        text = filename.read() # if stringIO
    except:
        with open(filename,'r') as f:
            text = f.read()
            
    if isinstance(name,str):
        _title = name
    else:
        _title = language[0].capitalize() + language[1:]
    
    _class = _title.replace('.','').replace('\s+','')
    if 'ython' in language:
        code = markdown(f'```{language}\n{text}\n```',extensions=__md_extensions)
    else:
        code = Code(data = text,language=language)._repr_html_() 
            
        _arr = [_h.split('</pre>') for _h in code.split('<pre>')]
        start, middle, end = [v for vs in _arr for v in vs] # Flatten
        middle = ''.join(f'<code>{line}</code>' for line in middle.strip().splitlines())
        code = f'<div class="codehilite {_class}"> {start} <pre> {middle} </pre> {end} </div>'
    
    code = f'''<style> div.codehilite.{_class}::before {{
                content: '🔴 🟡 🟢  {_title}' !important;
            }}</style>''' + code
    out = _Source_Widget(value = _fix_code(code))
    out.raw = text 
    return out

def _str2code(text,language='python',name=None):
    "Only reads plain text source code, return source object with `show_lines` and `focus_lines` methods."
    s = StringIO(text)
    return _file2code(s,language=language,name=name)
 
def textbox(text, **css_props):
    """Formats text in a box for writing e.g. inline refrences. `css_props` are applied to box and `-` should be `_` like `font-size` -> `font_size`. 
    `text` is not parsed to general markdown i.e. only bold italic etc. applied, so if need markdown, parse it to html before. You can have common CSS for all textboxes using class `TextBox`."""
    css_props = {'display':'inline-block','white-space': 'pre', **css_props} # very important to apply text styles in order
    # white-space:pre preserves whitspacing, text will be viewed as written. 
    _style = ' '.join([f"{key.replace('_','-')}:{value};" for key,value in css_props.items()])
    return f"<span class='TextBox' style = {_style!r}> {text} </span>"  # markdown="span" will avoid inner parsing

def alert(text):
    "Alerts text!"
    return f"<span style='color:#DC143C;'>{text}</span>"
    
def colored(text,fg='blue',bg=None):
    "Colored text, `fg` and `bg` should be valid CSS colors"
    return f"<span style='background:{bg};color:{fg};'>{text}</span>"

def keep_format(plaintext_or_html):
    "Bypasses from being parsed by markdown parser. Useful for some graphs, e.g. keep_raw(obj.to_html()) preserves its actual form."
    if not isinstance(plaintext_or_html,str):
        return plaintext_or_html # if not string, return as is
    return {'__keep_format__':plaintext_or_html} 

def raw(text):
    "Keep shape of text as it is, preserving whitespaces as well."
    return {'__keep_format__':f"<div class='PyRepr'>{text}<div>"}

def rows(*objs):
    "Returns tuple of objects. Use in `write`, `iwrite` for better readiability of writing rows in a column."
    return objs # Its already a tuple

def block(title,*objs,bg = 'olive'):
    "Format a block like in LATEX beamer. *objs expect to be writable with `write` command."
    _title = f"""<center style='background:var(--secondary-bg);margin:0px -4px;'>
                <b>{title}</b></center>"""
    _out = _fmt_write(objs) # single column
    return keep_format(f"""<div style='padding:4px' class='block'>
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


class source:
    current: None
    def __init__(self):
        raise Exception("""This class is not meant to be instantiated.
        Use source.context() to get a context manager for source.
        Use source.current to get the current source object.
        Use source.from_file(filename) to get a source object from a file.
        Use source.from_string(string) to get a source object from a string.
        Use source.from_callable(callable) to get a source object from a callable.
        """)
    @classmethod
    def from_string(cls,text,language='python',name=None):
        "Creates source object from string. `name` is alternate used name for language"
        cls.current = _str2code(text,language=language,name=name)
        return cls.current
    
    @classmethod
    def from_file(cls, filename,language='python',name=None):
        "Returns source object with `show_lines` and `focus_lines` methods. `name` is alternate used name for language"
        cls.current = _file2code(filename,language=language,name=name)
        return cls.current
    
    @classmethod       
    def from_callable(cls, callable):
        "Returns source object from a given callable [class,function,module,method etc.] with `show_lines` and `focus_lines` methods."
        for _type in ['class','function','module','method','builtin','generator']:
            if getattr(inspect,f'is{_type}')(callable):
                source = inspect.getsource(callable)
                cls.current = _str2code(source,language='python',name=None)
                return cls.current
    
    @classmethod
    @contextmanager
    def context(cls, collapsed = False, focus_lines = None):
        """Excute and displays source code in the context manager. Set `collapsed = True` to display in collapse.
        `foucs_lines` is a list/tuple/range of line index to be highlighted. Useful when source is written inside context manager itself.
        **Usage**:
        ```python
        with source.context() as s: #if not used as `s`, still it is stored in variable `__current_source_code__` that you can acess by this name or from `LiveSlides.current_source`
            do_something()
            #s is the source code that will be avaialble outside the context manager
        write(s)
        #s.raw, s.value are accesible attributes.
        #s.focus_lines, s.show_lines are methods that return object of same type.
        # iwite(s) will update the source even inside the context manager.
        ```
        """     
        def frame():
            "This is better than traceback as it works same for IPython and script.py"
            return (sys._getframe().f_back.f_back.f_back.f_code.co_filename,
                    sys._getframe().f_back.f_back.f_back.f_lineno) #should be in function and go back three times

        file, l1 = frame()
        _alert = alert('You can get code once you exit context manager for `write` command <center>OR</center>use it will auto update inside `iwrite` command')
        return_obj = _Source_Widget(value=_alert)
        return_obj.raw = ''

        cls.current = return_obj # add to user namespace, this does not create extra object, just points to same
        try:
            yield return_obj
        finally:
            file, l2 = frame()
            lines = linecache.getlines(file)[l1:l2]

            code = textwrap.dedent(''.join(lines))
            return_obj.raw = code
            out_code = _str2code(code).value #needs further processing

            if collapsed:
                return_obj._code =  details(out_code,summary='Show Code')
            else:
                return_obj._code = out_code 
                
            return_obj.value = return_obj._code # Update the value of the widget
        
        if isinstance(focus_lines,(list,tuple,range)):
            _ = return_obj.focus_lines(focus_lines) # highlight lines, no need to return self here

def sig(callable,prepend_str = None):
    "Returns signature of a callable. You can prepend a class/module name."
    try:
        _sig = f'<b>{callable.__name__}</b><span style="font-size:85%;color:var(--secondary-fg);">{str(inspect.signature(callable))}</span>'
        if prepend_str: 
            _sig = alert(prepend_str + '.') + _sig
        return {'__keep_format__':_sig}
    except:
        raise TypeError(f'Object {callable} is not a callable')

def doc(callable,prepend_str = None):
    "Returns documentation of a callable. You can prepend a class/module name."
    try:
        _doc = _fix_repr(inspect.getdoc(callable))
        _sig = sig(callable,prepend_str)['__keep_format__']
        return {'__keep_format__':f"<div class='PyRepr'>{_sig}<br>{_doc}</div>"}
    except:
        raise TypeError(f'Object {callable} is not a callable')
    
def float_obj(obj,x,y,width,height,zindex, box_shadow = True, **css_props):
    ...
