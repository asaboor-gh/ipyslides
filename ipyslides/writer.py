"""
Main write functions to add content to slides
"""

__all__ = ['write']

from IPython.display import display as display
from IPython.utils.capture import CapturedIO

from .formatters import ipw, XTML, RichOutput, _Output, serializer, htmlize, _inline_style, toc_from_meta
from .xmd import fmt, parse, capture_content


class hold:
    "Hold the display of a callable (return value is discarded) until the instance is called. Use this to delay display of a function until it is captured in a column of `Slides.write`"
    def __init__(self, f, *args, **kwargs):
        if not callable(f):
            raise TypeError(f'Expected first argument a callable, got {type(f)}')
        
        self._callable = f
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        "Call the held callable with stored arguments. Returns None. `Slides.write` will auto call it."
        self._callable(*self._args, **self._kwargs)

    def display(self):
        self.__call__()

class CustomDisplay:
    "Use this to create custom display types for object."
    def _ipython_display_(self):
        self.display()
    
    def display(self):
        raise NotImplementedError("display method must be implemented in subclass")
    

def _fmt_html(output):
    "Format captured rich output and others to html if possible. Used in other modules too."
    if isinstance(output, str):
        return output
    
    if hasattr(output, 'fmt_html'): # direct return, may be column
        return output.fmt_html()
    
    return serializer._export_other_reprs(output)


class Writer(ipw.HBox):
    _in_write = False
    def __init__(self, *objs, widths = None):
        if self.__class__._in_write: # Like from delayed lambda function
            raise RuntimeError("Trying to write inside a writer!")
        
        super().__init__() 
        self.add_class('columns').add_class('writer') # to differentiate from other columns

        try:
            self.__class__._in_write = True
            self._cols = self._capture_objs(*objs, widths = widths) # run after getting slides instance
        finally:
            self.__class__._in_write = False

        if len(objs) == 1:
            display(*self._cols[0]['outputs']) # If only one column, display it directly without Box
        elif len(objs) > 1:
            self.children = [_Output(layout = ipw.Layout(width = c['width'],overflow='auto',height='auto')) for c in self._cols]
            display(self, metadata=self.metadata) # Just display it with ID
            self.update_display() # show content on widgets

    
    @property
    def data(self): return self._repr_mimebundle_() # Required to mimic RichOutput
    
    @property
    def metadata(self): return {'UPDATE': self._model_id,"COLUMNS": ""} # Required to update both display and frames

    def __repr__(self):
        return f'<{self.__module__}.Writer at {hex(id(self))}>'

    def _capture_objs(self, *objs, widths = None):
        if widths is None: # len(objs) check is done in write
            widths = [100/len(objs) for _ in objs]
        else:
            if len(objs) != len(widths):
                raise ValueError(f'Number of columns ({len(objs)}) and widths ({len(widths)}) do not match')
        
            for w in widths:
                if not isinstance(w,(int, float)):
                    raise TypeError(f'widths must be numbers, got {w}')
            widths = [w/sum(widths)*100 for w in widths]
        
        
        widths = [f'{w:.3f}%' for w in widths]
        cols = [{'width':w,'outputs':_c if isinstance(_c,(list,tuple)) else [_c]} for w,_c in zip(widths,objs)]
        for i, col in enumerate(cols):
            with capture_content() as cap:
                for c in col['outputs']:
                    if isinstance(c,(fmt, RichOutput, CustomDisplay, ipw.DOMWidget)):
                        display(c)
                    elif isinstance(c, CapturedIO):
                        c.show() # Display captured outputs, all of them
                    elif isinstance(c,str):
                        parse(c, returns = False)
                    elif isinstance(c, hold):
                        _ = c() # If c is hold, call it and it will dispatch whatever is inside, ignore return value
                    else:
                        display(XTML(htmlize(c)))
            
            if cap.stderr:
                raise RuntimeError(f'Error in column {i+1}:\n{cap.stderr}')
            
            cols[i]['outputs'] = cap.outputs
            
        return cols
    
    def update_display(self):
        for col, out in zip(self._cols, self.children):
            if not out.outputs:
                out.clear_output(wait=True)
                with out:
                    display(*[toc_from_meta(o.metadata) or o for o in col['outputs']])
            else:
                out.update_display()
    
    def fmt_html(self, _pad_from=None):
        "Make HTML representation of columns that is required for exporting slides to other formats."
        cols = []
        for i, col in enumerate(self._cols):
            content = ''
            if (_pad_from is None) or (isinstance(_pad_from, int) and (i < _pad_from)): # to make frames
                content += '\n'.join(map(_fmt_html, col['outputs']))
                
            cols.append(f'<div style="width:{col["width"]};overflow:auto;height:auto">{content}</div>')
        
        css_class = ' '.join(self._dom_classes) # handle custom classes in blocks as well
        return f'<div class="{css_class}" {_inline_style(self)}>{"".join(cols)}</div>'
    
    
def write(*objs,widths = None, css_class=None):
    """
    Write `objs` to slides in columns. To create rows in a column, wrap objects in a list or tuple.      
    You can optionally specify `widths` as a list of percentages for each column. 
    `css_class` can have multiple classes separated by space, works only for multiple columns.
         
    Write any object that can be displayed in a cell with some additional features:
    
    - Strings will be parsed as as extended markdown that can have citations/python code blocks/Javascript etc.
    - Display another function to capture its output in order using hl`Slides.hold(func,...)`. Only body of the function will be displayed/printed. Return value will be ignored.
    - Dispaly IPython widgets such as `ipywidgets` or `ipyvolume` by passing them directly.
    - Display Axes/Figure form libraries such as `matplotlib`, `plotly` `altair`, `bokeh` etc. by passing them directly.
    - Display source code of functions/classes/modules or other languages by passing them directly or using `Slides.code` API.
    - Use `Slides.alt` function to display obj/widget on slides and alternative content/screenshot of widgets in exported slides.
    - hl`ipywidgets.[HTML, Output, Box]` and their subclasses will be displayed as hl`Slides.alt(html_converter_func, widget)`. The value of exported HTML will be most recent.
    - Other options include but not limited to:
        - Output of functions in `ipyslides.utils` module that are also linked to `Slides` object.
        - PIL images, SVGs etc.
        - IPython display objects such as Image, SVG, HTML, Audio, Video, YouTubeVideo, IFrame, Latex, Markdown, JSON, Javascript, etc.
        - Any object that has a `_repr_html_` method, you can create one for your own objects/third party objects by:
            - `Slides.serializer` API. IPython's `display` automatically takes care of such objects on export to html.
            - `IPython.core.formatters` API for third party libraries.
            
    ::: note
        - Use `Slides.frozen` to avoid display formatting and markdown parsing over objects in `write` and for some kind of objects in `display` too.
        - `write` is a robust command that can handle most of the cases. If nothing works, hl`repr(obj)` will be displayed.
        - You can avoid hl`repr(obj)` by hl`Slides.hold(func, ...)` e.g. hl`Slides.hold(plt.show)`. This can also be used to delay display until it is captured in a column.
        - You can use hl`display(obj, metadata = {'text/html': 'html repr by user'})` for any object to display object as it is and export its HTML representation in metadata.
        - A single string passed to `write` is equivalent to `parse` command.
        - You can add mini columns inside a column by markdown syntax or `Slides.cols`, but content type is limited in that case.
    """
    w = Writer(*objs,widths = widths) # Display itself
    if isinstance(css_class, str):
        [w.add_class(c) for c in css_class.split()]
