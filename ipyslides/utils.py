from markdown import markdown
from IPython.display import HTML, display, Markdown, Code
import matplotlib.pyplot as plt, os
from io import BytesIO
from IPython.utils.capture import capture_output
from IPython.core.display import __all__
from contextlib import contextmanager
import ipywidgets as ipw
__reprs__ = [rep.replace('display_','') for rep in __all__ if rep.startswith('display_')] # Can display these in write command

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
    
def __fix_repr(obj):
    if not isinstance(obj,str):
        _reprs_ = [rep for rep in [getattr(obj,f'_repr_{r}_',None) for r in __reprs__] if rep]   
        if _reprs_:
            return _reprs_[0]()
        else:
            _methods = '<br/>'.join([f'<code>_repr_{rep}_</code>' for rep in __reprs__])
            return f"<blockquote>Can't write object <code>{obj}</code><br/> Expects a string or object with anyone of follwing methods:<br/>{_methods}</blockquote>"
    else:
        _obj = obj.strip().replace('\n','  \n') #Markdown doesn't like newlines without spaces
        return markdown(_obj,extensions=['fenced_code','tables','codehilite']) 
    
def _fmt_write(*columns,width_percents=None):
    if not width_percents:
        width_percents = [int(100/len(columns)) for _ in columns]
        
    _cols = ''.join([f"<div style='width:{w}%;overflow-x:auto;'>{__fix_repr(c)}</div>" 
                            for c,w in zip(columns,width_percents)])
    _cols = syntax_css() + _cols if 'codehilite' in _cols else _cols
    if len(columns) == 1:
        return _cols
    return f'''<div class="columns">{_cols}</div>'''
        
def write(*columns,width_percents=None): 
    '''Writes markdown strings or IPython object with method `_repr_<html,svg,png,...>_` in each column of same with. If width_percents is given, column width is adjusted.
    
    You can given a code object from ipyslides.get_cell_code() to it, syntax highlight is enabled.
    You can give a matplotlib figure to it using ipyslides.utils.plt2html().
    You can give an interactive plotly figure to it ipyslides.utils.plotly2html().
    You can give a pandas dataframe after converting to HTML.
    You can give an IPython object which has `_repr_<repr>_` method where <repr> is one of ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    
    Note: You can give your own type of data provided that it is converted to an HTML string, so you can
    extent beyond matplotlib or plotly.
    ''' 
    return display(HTML(_fmt_write(*columns,width_percents=width_percents)))

def ihtml(*columns,width_percents=None):
    "Returns an ipywidgets.HTML widget. Accepts content types same as in `write` command and can be changed on fly as `ihtml.value = 'content'` "
    return ipw.HTML(_fmt_write(*columns,width_percents=width_percents))

def _fmt_iwrite(*columns,width_percents=None):
    if not width_percents:
        width_percents = [int(100/len(columns)) for _ in columns]
        
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in columns] #Make list if single element
    children = [ipw.VBox(children = _c, layout = ipw.Layout(width=f'{_w}%')) for _c, _w in zip(_cols,width_percents)]
    return ipw.HBox(children = children).add_class('columns')

def iwrite(*columns,width_percents=None):
    "Each obj in columns should be an IPython widget like `ipywidgets`,`bqplots` etc or list/tuple of widgets. Text can be added with `ihtml`"
    display(_fmt_iwrite(*columns,width_percents=width_percents))

def fmt2cols(c1,c2,w1=50,w2=50):
    """Useful when you want to split a column in `write` command in small 2 columns, e.g displaying a firgure with text on left.
    Both `c1` and c2` should be in text format or have  `_repr_<repr>_` method where <repr> is one of 
    ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    `w1, w2` as their respective widths(int) in percents."""
    return f"""<div class='columns'>
        <div style='width:{w1}%;overflow-x:auto;'>{__fix_repr(c1)}</div>
        <div style='width:{w2}%;overflow-x:auto;'>{__fix_repr(c2)}</div></div>"""  
        
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

def file2code(filename,language='python',max_height='400px'):
    "Only reads plain text"
    if 'ython' in language:
        code = markdown(f'```{language}\n{file2text(filename)}\n```',extensions=['fenced_code','tables','codehilite'])
    else:
        code = Code(filename=filename,language=language)._repr_html_()
    return f'<div style="max-height:{max_height};overflow:auto;">{code}</div>'

def plotly2html(fig):
    """Writes plotly's figure as HTML string to use in `ipyslide.utils.write`.
    - fig : A plotly's figure object.
    """
    import uuid # Unique div-id required,otherwise jupyterlab renders at one place only and overwite it.
    div_id = "graph-{}".format(uuid.uuid1())
    fig_json = fig.to_json()
    return  f"""<div class='fig-container'>
        <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
        <div id='{div_id}'><!-- Plotly chart DIV --></div>
        <script>
            var data = {fig_json};
            var config = {{displayModeBar: true,scrollZoom: true}};
            Plotly.newPlot('{div_id}', data.data,data.layout,config);
        </script>
        </div>"""
        
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
    return f"<div class='fig-container'>{svg}</div>"


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
    return markdown("```python\n{}\n```".format('\n'.join(current_cell_code)),extensions=['fenced_code','tables','codehilite'])