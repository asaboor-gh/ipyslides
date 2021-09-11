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

def bokeh2html(bokeh_fig,title=""):
    from bokeh.resources import CDN
    from bokeh.embed import file_html
    return file_html(bokeh_fig, CDN, title)


# ONLY ADD LIBRARIEs who's required objects either do not have a _repr_html_ method or need ovverride

libraries = [
    {'name':'matplotlib.pyplot','obj':'Figure','func':plt2html,'args':(),'kwargs': {}},
    {'name':'altair','obj':'Chart','func': 'to_html','args':(),'kwargs': {}},
    {'name':'pygal','obj':'Graph','func':'render','args':{},'kwargs':{'is_unicode':True}},
    {'name':'pydeck','obj':'Deck','func':'to_html','args':(),'kwargs': {'as_string':True}},
    {'name':'pandas','obj':'DataFrame','func':'to_html','args':(),'kwargs': {}},
    {'name':'bokeh.plotting','obj':'Figure','func':bokeh2html,'args':(),'kwargs':{'title':''}}
    
]

def format_object(obj):
    try: # If matplotlib axes given
        _fig = obj.get_figure()
        return True,plt2html(_fig)
    except: pass
        
    try: module_name = obj.__module__
    except: module_name = '' #str, int etc don't have __module__
    
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
    



            