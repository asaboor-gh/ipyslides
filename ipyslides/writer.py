"""
Main write functions to add content to slides
"""

__all__ = ['write', 'iwrite']

import ipywidgets as ipw
from IPython.display import display as display
from IPython.utils.capture import capture_output

from .formatters import _HTML, stringify, serializer, alt_html
from .xmd import parse, get_slides_instance

class CustomDisplay:
    def _ipython_display_(self):
        return self.display()
    
    def display(self):
        raise NotImplementedError("display method must be implemented in subclass")

class Writer:
    _in_write = False # To prevent write from being called inside write
    def __init__(self,*objs,widths = None):
        if self.__class__._in_write and len(objs) > 1:
            # This will only be intercepted if lambda function contains write with multiple columns, becuase they can't be nested
            raise RuntimeError('write(*objs) for len(objs) > 1 inside a previous call of write is not allowed!')
        
        self._box = ipw.HBox().add_class('columns') # Box to hold columns
        self._slides = get_slides_instance()
        
        try:
            self.__class__._in_write = True # To prevent write from being called inside write, specially by lambda function
            self._cols = self._capture_objs(*objs, widths = widths) # run after getting slides instance
        finally:
            self.__class__._in_write = False
            
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
                    elif isinstance(c, CustomDisplay):
                        c.display() # Handles all custom display classes like alt, goto_button etc.
                    elif callable(c) and c.__name__ == '<lambda>':
                        _ = c() # If c is a lambda function, call it and it will dispatch whatever is inside, ignore output
                    elif isinstance(c, ipw.DOMWidget): # Should be a displayable widget, not just Widget
                        if self._slides and self._slides.running:
                            if type(c) in [it['obj'] for it in serializer.types]: # Do not check instance here, need specific
                                for typ in serializer.types:
                                    if type(c) == typ['obj']:
                                        self._slides.alt(c, typ['func']).display() # Alternative representation will be available on export
                                        break # No need to further check
                            elif isinstance(c, ipw.HTML):
                                self._slides.alt(c, alt_html).display() # Display HTML widget and add it to alt
                                # NOTE: This is enough, Do not go too deep like in boxes to search for HTML, because then we will lose the column structure
                            else:
                                display(c, metadata = {'DOMWidget': '---'}) # Display only widget
                        else:
                            display(c, metadata = {'DOMWidget': '---'}) # Display only widget outside slide buuilder
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
                if hasattr(out, 'metadata') and 'ExpWidget' in out.metadata:
                    epx = self._slide._exportables[out.metadata['ExpWidget']]
                    content += ('\n' + epx.fmt_html() + '\n') # rows should be on their own line
                elif hasattr(out, 'metadata') and 'DYNAMIC' in out.metadata: # Buried in column
                    dpx = self._slide._dproxies[out.metadata['DYNAMIC']] # _slide is for sure there if dynamic proxy is there
                    content += ('\n' + dpx.fmt_html(allow_non_html_repr = allow_non_html_repr))
                elif 'Proxy' in out.metadata:
                    px = self._slide._proxies[out.metadata['Proxy']]
                    content += ('\n' + px.fmt_html(allow_non_html_repr = allow_non_html_repr))
                elif 'text/html' in out.data:
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
    - Use `Slides.alt(widget, func)` function to display widget on slides and alternative content in exported slides/report, function should return possible HTML representation of widget.
    - `ipywidgets.HTML` and its subclasses will be displayed as `Slides.alt(widget, lambda w: w.value)` where w is given widget. The value of exported HTML will be most recent.
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
        - You can add mini columns inside a column by markdown syntax or `Slides.cols`, but content type is limited in that case.
    """
    wr = Writer(*objs,widths = widths)
    if not any([(wr._slides and wr._slides.running), wr._in_proxy]):
        return wr.update_display() # Update in usual cell to have widgets working

# Keep long enough to raise deprecation warning
def iwrite(*objs,widths = None):
    raise DeprecationWarning('`iwrite` command is deprecated. Use `write` command instead.')
    