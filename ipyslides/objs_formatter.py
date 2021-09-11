"""Format objects like different charting libraries and IPython display object to HTML representation.

"""
import sys
from io import BytesIO
import matplotlib.pyplot as plt

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

libraries = [
    {'name':'matplotlib.pyplot','obj':'Figure','func':plt2html,'args':(),'kwargs': {}},
    {'name':'altair','obj':'Chart','func': 'to_html','args':(),'kwargs': {}},
    {'name':'pygal','obj':'Graph','func':'render','args':{},'kwargs':{'is_unicode':True}},
    {'name':'pydeck','obj':'Deck','func':'to_html','args':(),'kwargs': {'as_string':True}},
    {'name':'pandas','obj':'DataFrame','func':'to_html','args':(),'kwargs': {}},
    {'name':'IPython.display','obj':'HTML','func':'_repr_html_','args':(),'kwargs': {}},
    {'name':'IPython.display','obj':'Markdown','func':'_repr_html_','args':(),'kwargs': {}},
    {'name':'IPython.display','obj':'Code','func':'_repr_html_','args':(),'kwargs': {}},
    {'name':'IPython.display','obj':'SVG','func':'_repr_svg_','args':(),'kwargs': {}},
    {'name':'IPython.display','obj':'YouTubeVideo','func':'_repr_html_','args':(),'kwargs': {}},
    {'name':'plotly.graph_objects','obj':'Figure','func':'_repr_html_','args':(),'kwargs': {}},
    {'name':'plotly.graph_objects','obj':'FigureWidget','func':'_repr_html_','args':(),'kwargs': {}},
    
    
]

def format_object(obj):
    if isinstance(obj,plt.Axes):
        obj_in = obj.get_figure()
    else:
        obj_in = obj
    for lib in libraries:
        _module = sys.modules.get(lib['name'],None)
        if _module:
            _obj = getattr(_module,lib['obj'],None)
            if isinstance(obj_in, _obj):
                _func = getattr(obj_in,lib['func'],None)
                if _func:
                    return True, _func(*lib['args'],**lib['kwargs'])
                else: # Handle Matplotlib, bokeh etc here by making handling functions
                    try:
                        return True, lib['func'](obj_in)
                    except:
                        pass
    # If Nothing found
    return False, NotImplementedError(f"{obj}'s html representation is not implemented yet!")       
    



            