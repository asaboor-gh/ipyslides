"""
Main write functions to add content to slides
"""

__all__ = ['write']

import ipywidgets as ipw
from IPython.display import display as display
from IPython.utils.capture import capture_output

from .formatters import XTML, htmlize, serializer
from .xmd import parse, get_slides_instance

class CustomDisplay:
    def _ipython_display_(self):
        return self.display()
    
    def display(self):
        raise NotImplementedError("display method must be implemented in subclass")
    
class GotoButton(CustomDisplay):
    "Should not be used directly, use `Slides.goto_button` instead."
    def __init__(self, button, app):
        self._button = button
        self._app = app
        self._button._TargetSlide = None # Will be set by set_target
        self._target_id = f't-{id(button)}'
    
    def __repr__(self) -> str:
        return '<GotoButton>'
    
    def display(self):
        alt_link = self._app.html('a',self._button.description, href=f'#{self._target_id}', 
            style='color:var(--accent-color);text-decoration:none;', 
            className='goto-button slides-only export-only'
        )
    
        display(self._button, metadata = {'DOMWidget': '---'})
        display(alt_link) # Hidden from slides
        
    def set_target(self, force = False):
        if not self._app.running:
            raise RuntimeError("GotoButton's target can be set only inside a slide constructor!")
        if self._button._TargetSlide and not force:
            raise RuntimeError("GotoButton's target can be set only once! Use `force=True` to link here and remove previous link.")
        
        if force:
            self._button._TargetSlide._target_id = None # Remove previous link
        
        self._button._TargetSlide = self._app.running
        self._button._TargetSlide._target_id = self._target_id # Set new link
    
class AltForWidget(CustomDisplay):
    def __init__(self, widget, func):
        if not isinstance(widget, ipw.DOMWidget):
            raise TypeError(f'widget should be a widget, got {widget!r}')
        if not callable(func):
            raise TypeError(f'func should be a callable, got {func!r}')
        self._widget = widget
        self._func = func
        
        slides = get_slides_instance()
        if slides: 
            with slides._hold_running(): # To prevent dynamic content from being added to alt
                with capture_output() as cap:
                    out = self._func(self._widget)
                    if not isinstance(out, str):
                        raise TypeError(f'Function {func.__name__!r} should return a string, got {type(out)}')
                if cap.stderr:
                    raise RuntimeError(f'Function {func.__name__!r} raised an error: {cap.stderr}')

                if cap.outputs: # This also makes sure no dynamic content is inside alt, as nested contnet cannot be refreshed
                    raise RuntimeError(f'Function {func.__name__!r} should not display or print anything in its body, it should return a string.')   
        
    def __repr__(self):
        return 'AltForWidget(widget, func)'
        
    def _ipython_display_(self):
        return self.display()
        
    def display(self):
        slides = get_slides_instance()
        if slides and (context := (slides.in_proxy or slides.running)):
            display(context._exp4widget(self._widget, self._func))
        else:
            display(self._widget, metadata = {'DOMWidget': '---'}) # Display widget under slides/notebook anywhere

def _fmt_html(output):
    "Format captured rich output and others to html if possible. Used in other modules too."
    if hasattr(output, 'fmt_html'): # Columns
        return output.fmt_html()
    # Metadat text.html Should take precedence over data if given
    elif hasattr(output, 'metadata') and isinstance(output.metadata, dict) and 'text/html' in output.metadata: 
        return output.metadata['text/html']
    elif 'text/html' in output.data:
        return output.data['text/html']  
    return ''

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
        self._in_proxy = getattr(self._slides, '_in_proxy', None) # slide itself can be Non, so get via getattr
        self._in_dproxy = getattr(self._slides, '_in_dproxy', None)
        self._context = (self._in_dproxy if self._in_dproxy else self._slide) or self._in_proxy # order strictly matters
        
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
            widths = [int(100/len(objs)) for _ in objs]
        else:
            if len(objs) != len(widths):
                raise ValueError(f'Number of columns ({len(objs)}) and widths ({len(widths)}) do not match')
        
            for w in widths:
                if not isinstance(w,(int, float)):
                    raise TypeError(f'widths must be numbers, got {w}')
            widths = [int(w/sum(widths)*100) for w in widths]
        
        
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
                            if (func := serializer.get_func(c)):
                                self._slides.alt(c, func).display() # Alternative representation will be available on export, specially for ipw.HTML
                            else:
                                display(c, metadata = {'DOMWidget': '---'}) # Display only widget
                        else:
                            display(c, metadata = {'DOMWidget': '---'}) # Display only widget outside slide buuilder
                    else:
                        display(XTML(htmlize(c)))
            
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
    
    def fmt_html(self):
        "Make HTML representation of columns that is required for exporting slides to other formats."
        cols = []
        for col in self._cols:
            content = ''
            for out in col['outputs']:
                if 'Exp4Widget' in out.metadata:
                    epx = self._context._exportables[out.metadata['Exp4Widget']]
                    content += ('\n' + epx.fmt_html() + '\n') # rows should be on their own line
                elif 'DYNAMIC' in out.metadata: # Buried in column
                    dpx = self._context._dproxies[out.metadata['DYNAMIC']] 
                    content += ('\n' + dpx.fmt_html())
                elif 'Proxy' in out.metadata:
                    px = self._context._proxies[out.metadata['Proxy']]
                    content += ('\n' + px.fmt_html())
                else:
                    content += ('\n' + _fmt_html(out))
                
            cols.append(f'<div style="width:{col["width"]};overflow:auto;height:auto">{content}</div>')
        
        className = ' '.join(self._box._dom_classes) # handle custom classes in blocks as well
        style = getattr(self._box, '_extra_style', '') # provided from blocks
        return f'<div class="{className}" {style}>{"".join(cols)}</div>'
    
    
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
    - `ipywidgets.HTML` and its subclasses will be displayed as `Slides.alt(widget, html_converter_func)`. The value of exported HTML will be most recent.
    - Other options include but not limited to:
        - Output of functions in `ipyslides.utils` module that are also linked to `Slides` object.
        - PIL images, SVGs etc.
        - IPython display objects such as Image, SVG, HTML, Audio, Video, YouTubeVideo, IFrame, Latex, Markdown, JSON, Javascript, etc.
        - Any object that has a `_repr_html_` method, you can create one for your own objects/third party objects by:
            - `Slides.serializer` API. Use its `.get_metadata` method to display object as it is and export its HTML representation from metadata when used as `display(obj, metadata = {'text/html': 'html repr by user or by serializer.get_metadata(obj)'})`.
            - `IPython.core.formatters` API for third party libraries.
            
    ::: note
        - `write` is a robust command that can handle most of the cases. If nothing works, `repr(obj)` will be displayed.
        - You can avoid `repr(obj)` by `lambda: func()` e.g. `lambda: plt.show()`.
        - You can use `display(obj, metadata = {'text/html': 'html repr by user'})` for any object to display object as it is and export its HTML representation in metadata.
        - A single string passed to `write` is equivalent to `parse` command.
        - You can add mini columns inside a column by markdown syntax or `Slides.cols`, but content type is limited in that case.
    """
    wr = Writer(*objs,widths = widths)
    if not any([(wr._slides and wr._slides.running), wr._in_proxy]):
        return wr.update_display() # Update in usual cell to have widgets working

