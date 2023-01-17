"""
write/ iwrite main functions to add content to slides
"""

__all__ = ['write','iwrite']

import ipywidgets as ipw
from IPython import get_ipython
from IPython.display import display as display
from IPython.utils.capture import capture_output

from .formatters import _HTML, _HTML_Widget, stringify, _fix_repr
from .xmd import parse 

class Writer:
    def __init__(self,*objs,widths = None):
        self._box = ipw.HBox().add_class('columns') # Box to hold columns
        self._slides = get_ipython().user_ns.get('get_slides_instance',lambda:None)()
        self._cols = self._capture_objs(*objs, widths = widths) # run after getting slides instance
        self._slide = self._slides.running if self._slides else None
        self._in_proxy = getattr(self._slides, '_in_proxy', None)
        self._in_dproxy = getattr(self._slides, '_in_dproxy', None)
        
        if len(objs) == 1:
            display(*self._cols[0]['outputs']) # If only one column, display it directly
        else:
            context = (self._in_dproxy if self._in_dproxy else self._slide) or self._in_proxy # order strictly matters
            if context:
                idx = f'{len(context._columns)}' 
                context._columns[idx] = self
                display(self._box, metadata={'COLUMNS': idx}) # Just placeholder to update in main display
            else:
                display(self._box) # Just display it
                
    def _capture_objs(self, *objs, widths = None):
        if widths is None: # len(objs) check is done in write
            widths = [100/len(objs) for _ in objs]
        
        if len(objs) != len(widths):
            raise ValueError(f'Number of columns ({len(objs)}) and widths ({len(widths)}) do not match')
        for w in widths:
            if not isinstance(w,(int, float)):
                raise TypeError(f'widths must be numbers, got {w}')
        
        widths = [f'{int(w)}%' for w in widths]
        cols = [{'width':w,'outputs':_c if isinstance(_c,(list,tuple)) else [_c]} for w,_c in zip(widths,objs)]
        for i, col in enumerate(cols):
            with capture_output() as cap:
                for c in col['outputs']:
                    if isinstance(c,str):
                        parse(c, display_inline = True, rich_outputs = False)
                    elif callable(c) and c.__name__ == '<lambda>':
                        if self._slides:
                            self._slides._in_cols = True # Need to restrict things in lambda
                            try:
                                _ = c() # If c is a lambda function, call it and it will dispatch whatever is inside, ignore output
                            finally:
                                self._slides._in_cols = False
                        else:
                            _ = c() # If c is a lambda function, call it and it will dispatch whatever is inside, ignore output
                    elif isinstance(c, ipw.DOMWidget): # Should be a displayable widget, not just Widget
                        if self._slides and isinstance(c, ipw.HTML):
                            self._slides.alt(c, c.value).display() # Display HTML widget as slide and its value as hidden HTML
                            # NOTE: This is enough, Do not go too deep like in boxes to search for HTML, because then we will lose the column structure
                        else:
                            display(c, metadata = {'DOMWidget': '---'}) # Display widget
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
                for out in c['outputs']: # Don't worry as _slide won't be None if Proxy is present
                    if 'Proxy' in out.metadata:
                        display(*self._slide._proxies[out.metadata['Proxy']].outputs) # replace Proxy with its outputs/or new updated slide information
                    else: # No need to check for DYNAMIC as it is not allowed in cloumns
                        display(out)
    
    def _ipython_display_(self): # Called when displayed automtically, this is important
        display(self._box)
        self.update_display()
        
    @property
    def data(self): return getattr(self._box, '_repr_mimebundle_', lambda: {'application':'HBox'})() # Required for check in slide display of there are widgets
    
    @property
    def metadata(self): return {} # Required for check in slide display of there are widgets
    
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
    
def write(*objs,widths = None):
    """
    Write `objs` to slides in columns. To create rows in a column, wrap objects in a list or tuple.      
    You can optionally specify `widths` as a list of percentages for each column. 
         
    Write any object that can be displayed in a cell with some additional features:
    
    - Strings will be parsed as as extended markdown that can have citations/python code blocks/Javascript etc.
    - Display another function in order by passing it to a lambda function like `lambda: func()`. Only body of the function will be displayed/printed. Return value will be ignored.
    - Dispaly IPython widgets such as `ipywidgets` or `ipyvolume` by passing them directly.
    - Display Axes/Figure form libraries such as `matplotlib`, `plotly` `altair`, `bokeh`, `ipyvolume` ect. by passing them directly.
    - Display source code of functions/classes/modules or other languages by passing them directly or using `Slides.source` API.
    - Use `Slides.alt(widget, obj)` function to display widget on slides and alternative content in exported slides/report.
    - `ipywidgets.HTML` and its subclasses will be displayed as `Slides.alt(widget, value)`. The value of exported HTML will be oldest one.
    - Other options include but not limited to:
        - Output of functions in `ipyslides.utils` module that are also linked to `Slides` object.
        - PIL images, SVGs etc.
        - IPython display objects such as Image, SVG, HTML, Audio, Video, YouTubeVideo, IFrame, Latex, Markdown, JSON, Javascript, etc.
        - Any object that has a `_repr_html_` method, you can create one for your own objects/third party objects by:
            - `Slides.serializer` API.
            - `IPython.core.formatters` API for third party libraries.
            
    ::: note
        - `write` is a robust command that can handle most of the cases. If nothing works, `repr(obj)` will be displayed.
        - You can avoid `repr(obj)` by `lambda: func()` e.g. `lambda: plt.show()`.
        - A single string passed to `write` is equivalent to `parse` command.
    """
    wr = Writer(*objs,widths = widths)
    if not any([(wr._slides and wr._slides.running), wr._in_proxy]):
        return wr.update_display() # Update in usual cell to have widgets working
    

# We can just discourage the use of `iwrite` command in favor of the robust `write` command.        

def _fmt_iwrite(*objs,widths=None):
    if not widths:
        widths = [f'{int(100/len(objs))}%' for _ in objs]
    else:
        widths = [f'{w}%' for w in widths]
        
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in objs] #Make list if single element
    
    # Conver to other objects to HTML
    fixed_cols = []
    for j, _rows in enumerate(_cols):
        row = []
        for i, item in enumerate(_rows):
            if isinstance(item, ipw.DOMWidget):
                item._grid_location = {'row':i,'column':j}
                row.append(item)
            else:
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
    def __init__(self, *objs, widths=None):
        self._grid, self._cols = _fmt_iwrite(*objs,widths=widths)
        self._grid.add_class('columns')
        
    def _ipython_display_(self):
        return display(self._grid)
        
    def __getitem__(self, index): # For unpacking like write, *objs
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
        
        if isinstance(new_obj, ipw.DOMWidget):
            tmp = new_obj
        else:
            tmp = _HTML_Widget(value = _fix_repr(new_obj))
            if '</script>' in tmp.value:
                tmp.value = f'Error displaying object, cannot update object {new_obj!r} as it needs Javascript. Use `write` or `display` commands or `ipywidgets.Outpt()` to display it.'
                return # Don't update
        
        tmp._grid_location = old_obj._grid_location # Keep location
        widgets_row[row] = tmp
        self._grid.children[col].children = widgets_row
        return tmp
    
def iwrite(*objs,widths = None):
    """Each obj in objs could be an IPython widget like `ipywidgets`,`bqplots` etc 
    or list/tuple (or wrapped in `rows` function) of widgets to display as rows in a column. 
    Other objects (those in `write` command) will be converted to HTML widgets if possible. 
    Object containing javascript code may not work, use `write` command for that.
    
    Get a list of already available classes using `slides.css_styles`. For these you dont need to provide CSS.
    
    **Returns**: writer, objs as reference to use later and update. rows are packed in columns.
    
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
    wr = _WidgetsWriter(*objs,widths=widths)
    display(wr._grid, metadata = {'DOMWidget':'---'}) # Display it must to show it there with a metadata
    return wr # Return it to use later as writer, columns unpacked