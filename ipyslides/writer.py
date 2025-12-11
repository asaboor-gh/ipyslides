"""
Main write functions to add content to slides
"""

__all__ = ['write']

from collections.abc import Iterable
from itertools import chain
from IPython.display import display as display
from IPython.utils.capture import CapturedIO

from .formatters import ipw, XTML, RichOutput, _Output, serializer, htmlize, _inline_style, toc_from_meta, _delim
from .xmd import fmt, xmd, capture_content, get_slides_instance


class hold:
    """Hold the display of a callable (return value is discarded) until the instance is called. 
    Use this to delay display of a function until it is captured in a column of `Slides.write`.
    
    Alternatively, you can use `capture_content` context manager to capture multiple outputs together and pass that to `Slides.write`.
    """
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
        

def _fmt_html(output):
    "Format captured rich output and others to html if possible. Used in other modules too."
    if isinstance(output, str):
        return output
    
    if hasattr(output, 'fmt_html'): # direct return, may be column
        return output.fmt_html()
    
    return serializer._export_other_reprs(output)


class Writer(ipw.HBox):
    _in_write = False
    def __init__(self, *objs, widths = None, css_class = None):
        self._parts = () # to store part positions
        if self.__class__._in_write and len(objs) > 1: # Like from delayed lambda function
            raise RuntimeError("Trying to write inside a writer!")
        
        super().__init__() 
        self.add_class('columns').add_class('writer') # to differentiate from other columns
        
        if isinstance(css_class, str): # additional classes
            [self.add_class(c) for c in css_class.split()]

        try:
            self.__class__._in_write = True
            self._cols = self._capture_objs(*objs, widths = widths) # run after getting slides instance
        finally:
            self.__class__._in_write = False

        if len(objs) == 1 and not isinstance(css_class, str):
            # css_class still need to make all items in single block, without it just flatten display
            rows = self._cols[0]['outputs']
            if len(rows) == 1:
                display(*rows) # Just display single output directly
            elif len(rows) > 1:
                display(rows[0], metadata={"FLATCOL": len(rows)})  # First output with FLATCOL metadata to indicate for frames
                display(*rows[1:]) # Just display rest of rows directly
        elif len(objs) >= 1: # avoid empty write
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
        parts, rowsep = [], _delim("ROW")  # row delimiter
        for i, col in enumerate(cols):
            rows = chain(*(
                (*obj, rowsep) if isinstance(obj, (list, tuple)) # nested rows as single group
                else (obj, rowsep)  # each object as single row
                for obj in col['outputs']
            ))
            with capture_content() as cap:
                for c in rows:
                    if isinstance(c,(fmt, RichOutput, ipw.DOMWidget)):
                        display(c)
                    elif isinstance(c, CapturedIO):
                        c.show() # Display captured outputs, all of them
                    elif isinstance(c,str):
                        xmd(c, returns = False)
                    elif isinstance(c, hold):
                        c() # If c is hold, call it and it will dispatch whatever is inside, ignore return value
                    elif hasattr(c, '_ipython_display_') and callable(c._ipython_display_):
                        c._ipython_display_() # IPython display protocol takes precedence, but we need some cases handled before it
                    else:
                        display(XTML(htmlize(c)))
            
            if cap.stderr:
                raise RuntimeError(f'Error in column {i+1}:\n{cap.stderr}')
            
            cols[i]['outputs'] = cap.outputs[:-1]  # remove last rowsep output
            
            for r, out in enumerate(cols[i]['outputs']):
                meta = getattr(out, 'metadata', {})
                if isinstance(meta, dict) and meta.get('DELIM','') == 'ROW':
                    parts.append({"col": i, "row": r}) # mark row positions
            parts.append({"col": i}) # only columns incremented after rows done inside
        
        self._parts = tuple(parts) # make it immutable
        return cols
    
    def update_display(self):
        for col, out in zip(self._cols, self.children):
            if not out.outputs: # first time update
                out.clear_output(wait=True)
                with out:
                    display(*[toc_from_meta(o.metadata) or o for o in col['outputs']])
            else:
                out.update_display()
    
    def fmt_html(self, visible_upto=None):
        "Make HTML representation of columns for exporting slides to other formats."
        cols = []
        col_idx = (visible_upto or {}).get("col", float('inf')) 
        for i, col in enumerate(self._cols):
            if i > col_idx: # Entire column is hidden
                content = '\n'.join(map(_fmt_html, col['outputs']))
                cols.append(f'<div style="width:{col["width"]};overflow:auto;height:auto;visibility:hidden">{content}</div>')
            elif i < col_idx: # Entire column is visible
                content = '\n'.join(map(_fmt_html, col['outputs']))
                cols.append(f'<div style="width:{col["width"]};overflow:auto;height:auto">{content}</div>')
            else: # Current column, check rows
                rows = []
                row_idx = (visible_upto or {}).get("row", float('inf'))
                for r, output in enumerate(col['outputs']):
                    if r <= row_idx:
                        rows.append(_fmt_html(output))
                    else:
                        rows.append(f'<div style="visibility:hidden;">{_fmt_html(output)}</div>')
                
                cols.append(f'<div style="width:{col["width"]};overflow:auto;height:auto">{"".join(rows)}</div>')
                
        css_class = ' '.join(self._dom_classes)
        return f'<div class="{css_class}" {_inline_style(self)}>{"".join(cols)}</div>'


def write(*objs,widths = None, css_class=None):
    """
    Write `objs` to slides in columns. To create rows in a column, wrap objects in a list or tuple.   
    You can optionally specify `widths` as a list of percentages for each column. 
    `css_class` can have multiple classes separated by space, works only for multiple columns.
         
    Write any object that can be displayed in a cell with some additional features:
    
    - Strings will be parsed as as extended markdown that can have citations/python code blocks/Javascript etc.
    - Display another function to capture its output in order using code`Slides.hold(func,...)`. Only body of the function will be displayed/printed. Return value will be ignored.
    - Dispaly IPython widgets such as `ipywidgets` or `ipyvolume` by passing them directly.
    - Display Axes/Figure form libraries such as `matplotlib`, `plotly` `altair`, `bokeh` etc. by passing them directly.
    - Display source code of functions/classes/modules or other languages by passing them directly or using `Slides.code` API.
    - Use `Slides.alt` function to display obj/widget on slides and alternative content/screenshot of widgets in exported slides.
    - code`ipywidgets.[HTML, Output, Box]` and their subclasses will be displayed as code`Slides.alt(html_converter_func, widget)`. The value of exported HTML will be most recent.
    - Other options include but not limited to:
        - Output of functions in `ipyslides.utils` module that are also linked to `Slides` object.
        - PIL images, SVGs etc.
        - IPython display objects such as Image, SVG, HTML, Audio, Video, YouTubeVideo, IFrame, Latex, Markdown, JSON, Javascript, etc.
        - Any object that has a ` _repr_html_ ` method, you can create one for your own objects/third party objects by:
            - `Slides.serializer` API. IPython's `display` automatically takes care of such objects on export to html.
            - `IPython.core.formatters` API for third party libraries.
        - A whole column in `write` can be multiple captured outputs from a `capture_content` context manager, which can be used as alternative to `Slides.hold`.
            
    ::: note
        - Use `Slides.frozen` to avoid display formatting and markdown parsing over objects in `write` and for some kind of objects in `display` too.
        - `write` is a robust command that can handle most of the cases. If nothing works, code`repr(obj)` will be displayed.
        - You can avoid code`repr(obj)` by code`Slides.hold(func, ...)` e.g. code`Slides.hold(plt.show)`. This can also be used to delay display until it is captured in a column.
        - You can use code`display(obj, metadata = {'text/html': 'html repr by user'})` for any object to display object as it is and export its HTML representation in metadata.
        - You can add mini columns inside a column by markdown syntax or ` Slides.stack `, but content type is limited in that case.
        - In markdown `multicol/columns` block syntax is similar to `write` command if `+++` separartor is used there.
    
    ::: tip
        To make a group of rows as single item visually for incremental display purpose, wrap them in a nested list/tuple.
        A single column is flattened up to 2 levels, so `[[obj1], row2, [item1, item2]]` will be displayed as 3 rows.
        
        **Incremental display** is triggered only when you place `Slides.PART()` delimiter **before** the `write` command:
        
        ```python
        slides.PART()  # Trigger incremental display, equivalent to ++ before `multicol/columns` in markdown
        slides.write([row1, [item1, item2], row3], column2)  # Shows rows one by one (item1 and item2 together), then column2
        slides.PART()  # Another trigger for next write
        slides.write([row1, row2]) # Shows both rows incrementally , no additional columns here
        ``` 
    """
    Writer(*objs,widths = widths, css_class=css_class) # Displays itself
