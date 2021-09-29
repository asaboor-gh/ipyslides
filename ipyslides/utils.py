__all__ = ['print_context', 'write', 'iwrite', 'ihtml', 'details', 'plt2html', 'set_dir', 'textbox','file2image','file2tex','file2code','fmt2cols','alert','colored','keep_format']
__all__.extend(['block'])
__all__.extend([f'block_{c}' for c in ['r','g','b','y','c','m','k','o','w','p']])

from markdown import markdown
from IPython.display import HTML, display, Markdown, Code
import matplotlib.pyplot as plt, os
from io import BytesIO
from IPython.utils.capture import capture_output
from IPython.core.display import __all__ as __all
from contextlib import contextmanager
import ipywidgets as ipw
from .objs_formatter import format_object , libraries
from .objs_formatter import plt2html # For backward cimpatibility and inside class

__reprs__ = [rep.replace('display_','') for rep in __all if rep.startswith('display_')] # Can display these in write command

__md_extensions = ['fenced_code','tables','codehilite','footnotes'] # For MArkdown Parser
@contextmanager
def print_context():
    "Use `print` or function printing with onside in this context manager to display in order."
    with capture_output() as cap:
        yield
    display(Markdown(f'```shell\n{cap.stdout}\n{cap.stderr}```'))
    
@contextmanager
def set_dir(path):
    current = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(current)

def syntax_css():
    keywords = 'n k kc mi mf kn nn p c1 o nf sa s1 si nb nc se'.split()
    weights = ['bold' if k in ['k','kc'] else 'normal' for k in keywords]
    colors = 'inherit #008000 #008000 #080 #080 #ff7f0e #2ca02c #d62728 #5650b5 #AA22FF olive #7f7f7f #BA2121 #2800ff #1175cb #337ab7 red'.split()
    css = [f'.codehilite .{k} {{color:{c};font-weight:{w};}}' for k,c,w in zip(keywords,colors,weights)]
    css = '.codehighlite span {font-family: Monaco,"Lucida Console","Courier New";}\n' + '\n'.join(css)
    return "<style>\n{}\n</style>".format(css)

def _fix_repr(obj):
    if not isinstance(obj,str):
        # First prefer keep_format method. 
        if isinstance(obj,dict) and '__keep_format__' in obj:
            return obj['__keep_format__']
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
        
        # Return info if nothing above
        _objects = ', '.join([f"<code>{lib['name']}.{lib['obj']}</code>" for lib in libraries])
        _methods = ', '.join([f'<code>_repr_{rep}_</code>' for rep in __reprs__])
        return f"""<blockquote>Can't write object <code>{obj}</code><br/> 
                Expects any of :<br/> <code>Text/Markdown/HTML</code>, <code>matplotlib.pyplot.Axes</code>, {_objects}<br/>
                or any object with anyone of follwing methods:<br/>{_methods}<br/>
                Use <code>display(*objs)</code> or library's specific method used to display in Notebook. 
                </blockquote>"""
    else:
        _obj = obj.strip().replace('\n','  \n') #Markdown doesn't like newlines without spaces
        return markdown(_obj,extensions=__md_extensions) 
    
def _fmt_write(*columns,width_percents=None):
    if not width_percents and len(columns) >= 1:
        widths = [f'{int(100/len(columns))}%' for _ in columns]
    else:
        widths = [f'{w}%' for w in width_percents]
        
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in columns] 
    _cols = ''.join([f"""<div style='width:{w};overflow-x:auto;height:auto'>
                     {''.join([_fix_repr(row) for row in _col])}
                     </div>""" for _col,w in zip(_cols,widths)])
    _cols = syntax_css() + _cols if 'codehilite' in _cols else _cols
    if len(columns) == 1:
        return _cols
    return f'''<div class="columns">{_cols}</div>'''
        
def write(*columns,width_percents=None): 
    '''Writes markdown strings or IPython object with method `_repr_<html,svg,png,...>_` in each column of same with. If width_percents is given, column width is adjusted.
    Each column should be a valid object (text/markdown/html/ have _repr_<format>_ or to_<format> method) or list/tuple of objects to form rows. 
    You can given a code object from ipyslides.get_cell_code() to it, syntax highlight is enabled.
    You can give a matplotlib figure to it using ipyslides.utils.plt2html().
    You can give an interactive plotly figure.
    You can give a pandas dataframe `df` or `df.to_html()`.
    You can give any object which has `to_html` method like Altair chart. 
    You can give an IPython object which has `_repr_<repr>_` method where <repr> is one of ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    
    Note: Use `keep_format` method to keep format of object for example `keep_format(altair_chart.to_html())`.
    Note: You can give your own type of data provided that it is converted to an HTML string.
    Note: `_repr_<format>_` takes precedence to `to_<format>` methods. So in case you need specific output, use `object.to_<format>`.
    
    ''' 
    return display(HTML(_fmt_write(*columns,width_percents=width_percents)))

def ihtml(*columns,width_percents=None):
    "Returns an ipywidgets.HTML widget. Accepts content types same as in `write` command but does not allow javascript, so interactive graphs may not render."
    return ipw.HTML(_fmt_write(*columns,width_percents=width_percents))

def _fmt_iwrite(*columns,width_percents=None):
    if not width_percents:
        widths = ['auto' for _ in columns]
    else:
        widths = [f'{w}%' for w in width_percents]
        
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in columns] #Make list if single element
    children = [ipw.VBox(children = _c, layout = ipw.Layout(width=f'{_w}')) for _c, _w in zip(_cols,widths)]
    return ipw.HBox(children = children).add_class('columns')

def iwrite(*columns,width_percents=None):
    """Each obj in columns should be an IPython widget like `ipywidgets`,`bqplots` etc or list/tuple of widgets to display as rows in a column. 
    Text and other rich IPython content like charts can be added with `ihtml`"""
    display(_fmt_iwrite(*columns,width_percents=width_percents))

def fmt2cols(c1,c2,w1=50,w2=50):
    """Useful when you want to split a column in `write` command in small 2 columns, e.g displaying a firgure with text on left.
    Both `c1` and c2` should be in text format or have  `_repr_<repr>_` method where <repr> is one of 
    ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    `w1, w2` as their respective widths(int) in percents."""
    return f"""<div class='columns'>
        <div style='width:{w1}%;overflow-x:auto;'>{_fix_repr(c1)}</div>
        <div style='width:{w2}%;overflow-x:auto;'>{_fix_repr(c2)}</div></div>"""  
        
def details(str_html,summary='Click to show content'):
    "Show/Hide Content in collapsed html."
    return f"""<details style='max-height:100%;overflow:auto;'><summary>{summary}</summary>{str_html}</details>"""

def file2img(filename,width='100%'):
    "Displays png/jpeg/jpg etc. images from file"
    return f'<img src="{filename}" alt="{filename}" width="{width}" height="auto">'

def file2text(filename):
    "Only reads plain text, not bytes"
    with open(filename,'r') as f:
        text = ''.join(f.readlines())   
    return text

def file2code(filename,language='python',max_height='300px'):
    "Only reads plain text"
    if 'ython' in language:
        code = markdown(f'```{language}\n{file2text(filename)}\n```',extensions=__md_extensions)
    else:
        code = Code(filename=filename,language=language)._repr_html_()
    return f'<div style="max-height:{max_height};overflow:auto;">{code}</div>'

def _cell_code(shell,line_number=True,this_line=True,magics=False,comments=False,lines=None):
    "Return current cell's code in slides for educational purpose. `lines` should be list/tuple of line numbers to include if filtered."
    try:
        current_cell_code = shell.get_parent()['content']['code'].splitlines()
    except:
        return '<pre>get_cell_code / _cell_code</pre><p style="color:red;">can only return code from a cell execution, not from a function at run time</p>'
        
    if isinstance(lines,(list,tuple,range)):
        current_cell_code = [line for i, line in enumerate(current_cell_code) if i+1 in lines]
    if not this_line:
        current_cell_code = [line for line in current_cell_code if '_cell_code' not in line]
    if not magics:
        current_cell_code = [line for line in current_cell_code if not line.lstrip().startswith('%')]
    if not comments:
        current_cell_code = [line for line in current_cell_code if not line.lstrip().startswith('#')]
    return markdown("```python\n{}\n```".format('\n'.join(current_cell_code)),extensions=__md_extensions)

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

def block(title,*objs,bg='olive'):
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

    