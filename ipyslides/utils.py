from markdown import markdown
from IPython.display import HTML, display, Markdown
import matplotlib.pyplot as plt
from io import BytesIO
from IPython.utils.capture import capture_output
from contextlib import contextmanager

@contextmanager
def print_context():
    "Use `print` or function printing with onside in this context manager to display in order."
    with capture_output() as cap:
        yield
    display(Markdown(f'```shell\n{cap.stdout}\n{cap.stderr}```'))

def syntax_css():
    keywords = 'n k kc mi mf kn nn p c1 o nf sa s1 si nb nc se'.split()
    weights = ['bold' if k in ['k','kc'] else 'normal' for k in keywords]
    colors = 'inherit #008000 #008000 #080 #080 #ff7f0e #2ca02c #d62728 #5650b5 #AA22FF olive #7f7f7f #BA2121 #2800ff #1175cb #337ab7 red'.split()
    css = [f'.codehilite .{k} {{color:{c};font-weight:{w};}}' for k,c,w in zip(keywords,colors,weights)]
    css = '.codehighlite span {font-family: Monaco,"Lucida Console","Courier New";}\n' + '\n'.join(css)
    return "<style>\n{}\n</style>".format(css)
    
def __fix_repr(obj):
    if not isinstance(obj,str):
        _reprs_ = ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex')
        _repr_ = [rep for rep in [getattr(obj,f'_repr_{r}_',None) for r in _reprs_] if rep]   
        if _repr_:
            return _repr_[0]()
        else:
            return f"<p style='color:red;'>Can't write object {obj} it is not a string or does not have `_repr_{_reprs_!r}_` method</p>"
    else:
        _obj = obj.strip().replace('\n','  \n') #Markdown doesn't like newlines without spaces
        return markdown(_obj.replace('\n','  \n'),extensions=['fenced_code','tables','codehilite']) 
        
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
    style = syntax_css()
    if not width_percents:
        width_percents = [int(100/len(columns)) for _ in columns]
        
    _cols = ''.join([f"<div style='width:{w}%;overflow-x:auto;'>{__fix_repr(c)}</div>\n" 
                            for c,w in zip(columns,width_percents)])
    if len(columns) == 1:
        return display(HTML(style + _cols))
    return display(HTML(f'''<div class="columns">\n{style}{_cols}\n</div>'''))

def fmt2cols(c1,c2,w1=50,w2=50):
    """Useful when you want to split a column in `write` command in small 2 columns, e.g displaying a firgure with text on left.
    Both `c1` and c2` should be in text format or have  `_repr_<repr>_` method where <repr> is one of 
    ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    `w1, w2` as their respective widths(int) in percents."""
    return f"""<div class='columns'>
        <div style='width:{w1}%;overflow-x:auto;'>{__fix_repr(c1)}</div>
        <div style='width:{w2}%;overflow-x:auto;'>{__fix_repr(c2)}</div></div>"""  

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
        svg = svg + f'<p style="font-size:70% !important;">{caption}</p>'
    return f"<div class='fig-container'>{svg}</div>"


