"""
write/ iwrite main functions to add content to slides
"""

__all__ = ['write','iwrite']

import ipywidgets as ipw
from collections import namedtuple
from IPython.display import display

from .formatter import _HTML, _HTML_Widget, stringify
from .extended_md import ExetendedMarkdown          

def _fix_repr(obj):
    "should return a string"
    if isinstance(obj,str):
        return ExetendedMarkdown().parse(obj, display_inline= False)
    else:
        return stringify(obj)
    
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
    
    if len(columns) == 1:
        return _cols.replace('<div', f'<div class = "{_class}"',1) if _class else _cols
    
    return f'''<div class="columns {_class}">{_cols}</div>''' if _class else f'''<div class="columns">{_cols}</div>'''
        
def write(*columns,width_percents=None,className=None): 
    '''Writes markdown strings or IPython object with method `_repr_<html,svg,png,...>_` in each column of same with. If width_percents is given, column width is adjusted.
    Each column should be a valid object (text/markdown/html/ have _repr_<format>_ or to_<format> method) or list/tuple of objects to form rows or explictly call `rows`. 
    
    - Pass int,float,dict,function etc. Pass list/tuple in a wrapped list for correct print as they used for rows writing too.
    - Give a code object from `ipyslides.get_cell_code()` to it, syntax highlight is enabled.
    - Give a matplotlib `figure/Axes` to it or use `ipyslides.objs_formatter.plt2html()`.
    - Give an interactive plotly figure.
    - Give a pandas dataframe `df` or `df.to_html()`.
    - Give any object which has `to_html` method like Altair chart. (Note that chart will not remain interactive, use display(chart) if need interactivity like brushing etc.)
    - Give an IPython object which has `_repr_<repr>_` method where <repr> is one of ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    - Give a function/class/module (without calling) and it will be displayed as a pretty printed code block.
    
    If an object is not in above listed things, `obj.__repr__()` will be printed. If you need to show other than __repr__, use `display(obj)` outside `write` command or use
    methods specific to that library to show in jupyter notebook.
    
    If you give a className, add CSS of it using `format_css` function and provide it to `write` function.
    Get a list of already available classes using `slides.css_styles`. For these you dont need to provide CSS.
    
    Note: Use `keep_format` method to bypass markdown parser, for example `keep_format(altair_chart.to_html())`.
    Note: You can give your own type of data provided that it is converted to an HTML string.
    Note: `_repr_<format>_` takes precedence to `to_<format>` methods. So in case you need specific output, use `object.to_<format>`.
    
    ''' 
    return display(_HTML(_fmt_write(*columns,width_percents=width_percents,className=className)))


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
                    tmp.value,  = _HTML_Widget(f'Error displaying object, cannot update object {item!r} as it needs Javascript. Use `write` or `display` commands')

                tmp._grid_location = {'row':i,'column':j}
                row = [*row,tmp]
                
        fixed_cols.append(row)

    children = [ipw.VBox(children = _c, layout = ipw.Layout(width=f'{_w}')) for _c, _w in zip(fixed_cols,widths)]
    # Format things as given in input
    out_cols = tuple(tuple(row) if len(row) > 1 else row[0] for row in fixed_cols) 
    out_cols = tuple(out_cols) if len(out_cols) > 1 else out_cols[0]
    return ipw.HBox(children = children).add_class('columns'), out_cols #Return display widget and list of objects for later use

class _WidgetsWriter:
    def __init__(self, *columns, width_percents=None, className=None):
        self._grid, self._cols = _fmt_iwrite(*columns,width_percents=width_percents)
        if isinstance(className, str):
            self._grid.add_class(className)
        self._grid.add_class('columns')
    
    def update(self, old_obj, new_obj):
        "Updates `old_obj`  with `new_obj`. Returns reference to created/given widget, which can be updated by it's own methods."
        row, col = old_obj._grid_location['row'], old_obj._grid_location['column']
        widgets_row = list(self._grid.children[col].children)
        try: 
            ipw.Box([new_obj]) # Check for widget first 
            tmp = new_obj
        except:
            tmp = _HTML_Widget(value = _fix_repr(new_obj))
            if '<script>' in tmp.value:
                tmp.value, = _HTML_Widget(f'Error displaying object, cannot update object {new_obj!r} as it needs Javascript. Use `write` or `display` commands')
                return # Don't update
        
        tmp._grid_location = old_obj._grid_location # Keep location
        widgets_row[row] = tmp
        self._grid.children[col].children = widgets_row
        return tmp
    
def iwrite(*columns,width_percents = None,className=None):
    """Each obj in columns could be an IPython widget like `ipywidgets`,`bqplots` etc 
    or list/tuple (or wrapped in `rows` function) of widgets to display as rows in a column. 
    Other objects (those in `write` command) will be converted to HTML widgets if possible. 
    Object containing javascript code may not work, use `write` command for that.
    
    If you give a className, add CSS of it using `format_css` function and provide it to `iwrite` function. 
    Get a list of already available classes using `slides.css_styles`. For these you dont need to provide CSS.
    
    **Returns**: writer, columns as reference to use later and update. rows are packed in columns.
    
    **Examples**:
    ```python
    writer, x = iwrite('X')
    writer, (x,y) = iwrite('X','Y')
    writer, (x,y) = iwrite(['X','Y'])
    writer, [(x,y),z] = iwrite(['X','Y'],'Z')
    #We unpacked such a way that we can replace objects with new one using `grid.update`
    new_obj = writer.update(x, 'First column, first row with new data') #You can update same `new_obj` with it's own widget methods. 
    ```
    """
    wr = _WidgetsWriter(*columns,width_percents=width_percents,className=className)
        
    display(wr._grid) # Actually display the widget
    
    return namedtuple('LiveGrid',['writer','columns'])(wr, wr._cols)
