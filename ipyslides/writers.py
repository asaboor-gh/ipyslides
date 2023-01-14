"""
write/ iwrite main functions to add content to slides
"""

__all__ = ['write','iwrite']

import textwrap
import ipywidgets as ipw
from IPython import get_ipython
from IPython.display import display as display
from IPython.utils.capture import capture_output

from .formatters import _HTML, _HTML_Widget, stringify
from .xmd import parse 

class _Writer:
    def __init__(self,*columns,widths = None):
        self.columns = columns
        self._box = ipw.HBox().add_class('columns') # Box to hold columns
             
        self._cols = self._capture_objs(*columns, widths = widths)
        self._slides = get_ipython().user_ns.get('get_slides_instance',lambda:None)()
        self._slide = self._slides.running if self._slides else None
        self._in_proxy = getattr(self._slides, '_in_proxy', None)
        
        if len(columns) == 1:
            display(*self._cols[0]['outputs']) # If only one column, display it directly
        else:
            current_slide = self._slide if self._slide else self._in_proxy._slide if self._in_proxy else None
            if current_slide:
                idx = f'{"p" if self._in_proxy else ""}{len(current_slide._columns)}'
                current_slide._columns[idx] = self
                display(self._box, metadata={'COLUMNS': idx}) # Just placeholder to update in main display
            else:
                display(self._box) # Just display it
                
    def _capture_objs(self, *columns, widths = None):
        if widths is None: # len(columns) check is done in write
            widths = [100/len(columns) for _ in columns]
        
        assert len(columns) == len(widths)
        for w in widths:
            assert isinstance(w,int) or isinstance(w,float)
        
        widths = [f'{int(w)}%' for w in widths]
        cols = [{'width':w,'outputs':_c if isinstance(_c,(list,tuple)) else [_c]} for w,_c in zip(widths,columns)]
        for i, col in enumerate(cols):
            with capture_output() as cap:
                for c in col['outputs']:
                    try:
                        ipw.Box([c]) # Check if c is a widget by trying to put it in a box
                        display(c) # If yes, display it
                    except:
                        if isinstance(c,str):
                            parse(c, display_inline = True, rich_outputs = False)
                        elif callable(c) and c.__name__ == '<lambda>':
                            _out = c() # If c is a lambda function, call it and it will dispatch whatever is inside
                            if isinstance(_out, str):
                                display(_HTML(_out)) # Do not parse lambda function output, it should be something like third party library output
                        else:
                            display(_HTML(stringify(c)))
            
            if cap.stderr:
                raise RuntimeError(f'Error in column {i+1}:\n{cap.stderr}')
            
            cols[i]['outputs'] = cap.outputs
            
        return cols
    
    def update_display(self):
        self._box.children = [ipw.Output(layout = ipw.Layout(width = c['width'],overflow='auto',height='auto')) for c in self._cols]
        for c, out_w in zip(self._cols, self._box.children):
            with out_w:
                for out in c['outputs']: # Don't worry as _slide won't be None if DProxy/Proxy is present
                    if 'DProxy' in out.metadata:
                        display(*self._slide._dproxies[out.metadata['DProxy']].outputs) # Unpack DProxy as it can have many outputs
                    elif 'Proxy' in out.metadata:
                        display(*self._slide._proxies[out.metadata['Proxy']].outputs) # replace Proxy with its outputs/or new updated slide information
                    else:
                        display(out)
    
    def fmt_html(self, allow_non_html_repr = True):
        "Make HTML representation of columns that is required for exporting slides to other formats."
        cols = []
        for col in self._cols:
            content = ''
            for out in col['outputs']:
                if 'text/html' in out.data:
                    content += ('\n' + out.data['text/html']) # rows should be on their own line
                elif allow_non_html_repr:
                    content += ('\n' + out.data['text/plain'])
        
            cols.append(f'<div style="width:{col["width"]};overflow:auto;height:auto">{content}</div>')
        return f'<div class="columns">{"".join(cols)}</div>'
    
def _write(*columns,widths = None):
    """
    Write content to slides in columns. To create rows in a column, wrap the contents in a list or tuple.
    
    """
    wr = _Writer(*columns,widths = widths)
    if wr._slides and not any([wr._slides.running, getattr(wr._slides, '_in_proxy', None)]):
        return wr.update_display() # Update in usual cell

def _fix_repr(obj):
    "should return a string"
    if isinstance(obj,str):
        return parse(obj, display_inline= False, rich_outputs=False)
    else:
        return stringify(obj)        
    
    
def _fmt_write(*columns,width_percents=None,className=None):
    if not width_percents and len(columns) >= 1:
        widths = [f'{int(100/len(columns))}%' for _ in columns]
    else:
        widths = [f'{w}%' for w in width_percents]
    _class = className if isinstance(className,str) else ''
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in columns] 
    _cols = ' '.join([f"""<div style='width:{w};overflow-x:auto;height:auto'>
                     {' '.join([_fix_repr(row) for row in _col])}
                     </div>""" for _col,w in zip(_cols,widths)])
    
    if len(columns) == 1:
        return _cols.replace('<div', f'<div class = "{_class}"',1) if _class else _cols
    
    return f'''<div class="columns {_class}">{_cols}</div>''' if _class else f'''<div class="columns">{_cols}</div>'''
        


def write(*columns,width_percents=None,className=None): 
    '''Writes markdown strings or IPython object with method `_repr_<html,svg,png,...>_` in each column of same with. If width_percents is given, column width is adjusted.
    Each column should be a valid object (text/markdown/html/ have _repr_<format>_ or to_<format> method) or list/tuple of objects to form rows or explictly call `rows`. 
    
    - Pass int,float,dict,function etc. Pass list/tuple in a wrapped list for correct print as they used for rows writing too.
    - Give a code object from `Slides.source.context[from_...]` to it, syntax highlight is enabled.
    - Give a matplotlib `figure/Axes` to it or use `ipyslides.formatters.plt2html()`.
    - Give an interactive plotly figure.
    - Give a pandas dataframe `df` or `df.to_html()`.
    - Give any object which has `to_html` method like Altair chart. (Note that chart will not remain interactive, use display(chart) if need interactivity like brushing etc.)
    - Give an IPython object which has `_repr_<repr>_` method where <repr> is one of ('html','markdown','svg','png','jpeg','javascript','pdf','pretty','json','latex').
    - Give a function/class/module (without calling) and it will be displayed as a pretty printed code block.
    - Give a registered object using `@Slides.serializer.registor` decorator.
    
    If an object is not in above listed things, `obj.__repr__()` will be printed. If you need to show other than __repr__, use `display(obj)` outside `write` command or use
    methods specific to that library to show in jupyter notebook.
    
    If you give a className, add CSS of it using `format_css` function and provide it to `write` function.
    Get a list of already available classes using `slides.css_styles`. For these you dont need to provide CSS.
    ::: note
        - Use `keep_format` method to bypass markdown parser, for example `keep_format(altair_chart.to_html())`.
        - You can give your own type of data provided that it is converted to an HTML string.
        - `_repr_<format>_` takes precedence to `to_<format>` methods. So in case you need specific output, use `object.to_<format>`.
        - If you pass a single string, it will be passed to `ipyslides.xmd.parse` function to execute available code.
    ''' 
    if len(columns) == 1 and isinstance(columns[0],str):
        if className:
            return parse(f'''
                ::: {className}
                {textwrap.indent(columns[0],"    ")}    
                ''', display_inline = True, rich_outputs = False)
        else:
            return parse(columns[0], display_inline = True, rich_outputs = False)
            
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
                if '</script>' in tmp.value:
                    tmp.value = f'Error displaying object, cannot update object {item!r} as it needs Javascript. Use `write` or `display` commands or `ipywidgets.Outpt()` to display it.'

                tmp._grid_location = {'row':i,'column':j}
                row = [*row,tmp]
        
        fixed_cols.append(row)

    children = [ipw.VBox(children = _c, layout = ipw.Layout(width=f'{_w}')) for _c, _w in zip(fixed_cols,widths)]
    # Format things as given in input
    out_cols = tuple(tuple(row) if len(row) > 1 else row[0] for row in fixed_cols) # If single element in row, unwrap it
    out_cols = tuple(out_cols) # Each column is a tuple of rows even if it has only one row
    return ipw.HBox(children = children).add_class('columns'), out_cols #Return display widget and list of objects for later use

class _WidgetsWriter:
    def __init__(self, *columns, width_percents=None, className=None):
        self._grid, self._cols = _fmt_iwrite(*columns,width_percents=width_percents)
        if isinstance(className, str):
            self._grid.add_class(className)
        self._grid.add_class('columns')
        
    def _ipython_display_(self):
        return display(self._grid)
        
    def __getitem__(self, index): # For unpacking like write, *columns
        if index == 0:
            return self
        elif isinstance(index, int) and index != 0: # != 0 for accessing from -1, -2 as well
            idx = index - 1 if index > 0 else index
            return self._cols[idx]
        else:
            raise TypeError(f'Index should be integer, got {index!r}')
    @property
    def cols(self):
        "Access columns of the grid. Each column is a list of widgets or single widget if only one row."
        return self._cols
    
    def update(self, old_obj, new_obj):
        "Updates `old_obj`  with `new_obj`. Returns reference to created/given widget, which can be updated by it's own methods."
        row, col = old_obj._grid_location['row'], old_obj._grid_location['column']
        widgets_row = list(self._grid.children[col].children)
        try: 
            ipw.Box([new_obj]) # Check for widget first 
            tmp = new_obj
        except:
            tmp = _HTML_Widget(value = _fix_repr(new_obj))
            if '</script>' in tmp.value:
                tmp.value = f'Error displaying object, cannot update object {new_obj!r} as it needs Javascript. Use `write` or `display` commands or `ipywidgets.Outpt()` to display it.'
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
    writer, x = iwrite('X')  # writer = iwrite('X'); x = writer.cols[0] # gives same result
    writer, (x,y) = iwrite('X','Y')
    writer, (x,y) = iwrite(['X','Y']) # One column with two rows
    writer, (x,y),z = iwrite(['X','Y'],'Z')
    #We unpacked such a way that we can replace objects with new one using `grid.update`
    new_obj = writer.update(x, 'First column, first row with new data') #You can update same `new_obj` with it's own widget methods. 
    ```
    """
    wr = _WidgetsWriter(*columns,width_percents=width_percents,className=className)
    display(wr._grid) # Display it must to show it there
    return wr # Return it to use later as writer, columns unpacked