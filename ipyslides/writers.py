"""
write/ iwrite main functions to add content to slides
"""

__all__ = ['write','iwrite']

from IPython.core.display import display, HTML, __all__ as __all
import ipywidgets as ipw
from markdown import markdown

from .objs_formatter import format_object, syntax_css, _fix_code
from .shared_vars import _md_extensions


__reprs__ = [rep.replace('display_','') for rep in __all if rep.startswith('display_')] # Can display these in write command

class _HTML_Widget(ipw.HTML):
    "Class for HTML widgets based on ipywidgets.HTML, but with `_repr_html_` method."
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
    def _repr_html_(self):
        "Make it available in `write` command as well."
        return self.value

def _fix_repr(obj):
    if isinstance(obj,str):
        _obj = obj.strip().replace('\n','  \n') #Markdown doesn't like newlines without spaces
        _html = markdown(_obj,extensions=_md_extensions) 
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
    - Give a matplotlib `figure/Axes` to it or use `ipyslides.objs_formatter.plt2html()`.
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
                    tmp.value,  = _HTML_Widget(f'Error displaying object, cannot update object {item!r} as it needs Javascript. Use `write` or `display` commands')

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
                tmp.value, = _HTML_Widget(f'Error displaying object, cannot update object {new_obj!r} as it needs Javascript. Use `write` or `display` commands')
                return # Don't update
        
        tmp._grid_location = old_obj._grid_location # Keep location
        widgets_row[row] = tmp
        self.children[col].children = widgets_row
        return tmp
    
    _grid.update = update.__get__(_grid,type(_grid)) #attach update method to grid
    return _grid, _objects
