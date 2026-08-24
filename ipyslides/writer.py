"""
Main write functions to add content to slides
"""

__all__ = ['write', 'group']

from collections import UserList
from collections.abc import Iterable
from itertools import chain
from contextlib import contextmanager
from IPython.display import display as display
from IPython.utils.capture import CapturedIO
from dashlab.utils import _build_css

from .formatters import ipw, XTML, RichOutput, _Output, serializer, htmlize, _inline_style, toc_from_meta, _delim
from .xmd import BoundXMD, xmd, capture_content, get_slides_instance


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
    
    if isinstance(output, XTML):
        return output.value
    
    if hasattr(output, 'fmt_html'): # direct return, may be column
        return output.fmt_html()
    
    if isinstance(output, CapturedIO):
        return '\n'.join(serializer._export_other_reprs(out) for out in output.outputs)
    
    return serializer._export_other_reprs(output)

def _style_for_widget(widget, **css_props):
    "Not all widgets support all CSS properties, so we build style from user specified props."
    if not css_props or not isinstance(widget, ipw.DOMWidget):
        return
    uklass = f"wuid-{id(widget)}"
    widget.add_class(uklass) # unique class for this writer
    klass = '.' + '.'.join(widget._dom_classes)  # pick all classes to pass vriables at local scope
    return f'<style>\n{_build_css((klass,), css_props)}\n</style>'

def _is_pause_delim(output):
    "Check if output is a PAUSE delimiter."
    meta = getattr(output, 'metadata', {})
    return isinstance(meta, dict) and meta.get('DELIM', '') == 'PAUSE'

class group(UserList):
    def __init__(self, initlist=(), **kwargs):
        raise RuntimeError("group is deprecated, use `slides.steps` for step-wise behavior instead")

class Writer(ipw.HBox):
    _in_write = False
    def __init__(self, *objs, widths = None, css_class = None, paused=False, **css_props):
        self._frags = () # to store frames positions
        if self.__class__._in_write and len(objs) > 1: # Like from delayed lambda function
            raise RuntimeError("Trying to write inside a writer!")
        
        super().__init__() 
        self.add_class('columns').add_class('writer') # to differentiate from other columns
        self.layout.display = css_props.get('display', 'flex') # html export as well as user specified should be honored
        
        if isinstance(css_class, str): # additional classes
            [self.add_class(c) for c in css_class.split()]

        try:
            self.__class__._in_write = True
            self._cols = self._capture_objs(*objs, widths = widths, css_props=css_props, paused=paused) # run after getting slides instance
        finally:
            self.__class__._in_write = False

        single_col = len(self._cols) == 1
        single_meta = self._cols[0] if single_col else {}
        can_flatten_single = single_col and not any([
            isinstance(css_class, str),
            css_props,
        ])

        if can_flatten_single:
            # css_class/css_props still need to make all items in single block, without it just flatten display
            display(*self._cols[0]['outputs']) # auto handle last PAUSE deleimeter
        elif len(objs) >= 1: # avoid empty write
            self.children = [
                _Output(layout = ipw.Layout(flex = c['flex'],min_width='0',position='relative')) # make position relative explicitly
                for c in self._cols
            ]  
            display(self, metadata=self.metadata) # Just display it with ID
            self.update_display() # show content on widgets

    
    @property
    def data(self): return self._repr_mimebundle_() # Required to mimic RichOutput
    
    @property
    def metadata(self): return {"COLUMNS": self._model_id, "FRAGS": self._frags} # Required to update both display and frames

    def __repr__(self):
        return f'<{self.__module__}.Writer at {hex(id(self))}>'

    def _capture_objs(self, *objs, widths = None, css_props=None, paused=False):
        if widths is None: # len(objs) check is done in write
            widths = [100/len(objs) for _ in objs]
        else:
            if len(objs) != len(widths):
                raise ValueError(f'Number of columns ({len(objs)}) and widths ({len(widths)}) do not match')
        
            for w in widths:
                if not isinstance(w,(int, float)):
                    raise TypeError(f'widths must be numbers, got {w}')
            widths = [w/(sum(widths) or 1) for w in widths]
        
        cols = []
        for i, (w, obj) in enumerate(zip(widths, objs)):
            outputs = obj if isinstance(obj, (list, tuple)) else [obj] # flatten to list of outputs
            cols.append({'flex': f'{w:.3f} {w:.3f} {w*100:.3f}%', 'outputs': outputs})

        frags = []
        for i, col in enumerate(cols):
            col_outputs = list(col['outputs'])

            def _row_items(obj):
                if isinstance(obj, (list, tuple)): # nested rows as single group
                    yield from obj
                else:  # each object as single row
                    yield obj
                # Add PAUSE only if paused mode is enabled, otherwise all rows are visible at once
                if paused:
                    yield _delim("PAUSE")

            rows = chain.from_iterable(_row_items(obj) for obj in col_outputs)

            with capture_content() as cap:
                if i == 0 and css_props: # display CSS in first column only
                    XTML(_style_for_widget(self, **css_props)).display() 
                    
                for c in rows:
                    if isinstance(c,(RichOutput, ipw.DOMWidget)):
                        display(c)
                    elif isinstance(c, CapturedIO):
                        c.show() # Display captured outputs, all of them
                    elif isinstance(c,str):
                        xmd(c, returns = False)
                    elif isinstance(c, BoundXMD):
                        c.parse(returns = False) # parse and display extended markdown bounded object
                    elif isinstance(c, hold):
                        c() # If c is hold, call it and it will dispatch whatever is inside, ignore return value
                    elif hasattr(c, '_ipython_display_') and callable(c._ipython_display_):
                        c._ipython_display_() # IPython display protocol takes precedence, but we need some cases handled before it
                    else:
                        display(XTML(htmlize(c)))
            
            if cap.stderr:
                raise RuntimeError(f'Error in column {i+1}:\n{cap.stderr}')

            # can have last row delimiter, useful for single column automatically dropping last separator
            base_outputs = list(cap.outputs) 
            
            cols[i]['outputs'] = base_outputs

            if paused:
                for r, out in enumerate(cols[i]['outputs']):
                    if _is_pause_delim(out):
                        frags.append({"col": i, "row": r}) # mark row positions including last one
        
        self._frags = tuple(frags) # make it immutable
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

        def _fmt_rows(outputs):
            rows = []
            for output in outputs:
                html = _fmt_html(output)
                if not html:
                    continue

                rows.append(html)
            return rows

        for i, col in enumerate(self._cols):
            flex = f'flex:{col["flex"]};min-width:0;position:relative;'
            if i > col_idx: # Entire column is hidden
                content = '\n'.join(_fmt_rows(col['outputs']))
                cols.append(f'<div style="{flex};visibility:hidden">{content}</div>')
            elif i < col_idx: # Entire column is visible (or previous in focus mode)
                content = '\n'.join(_fmt_rows(col['outputs']))
                cols.append(f'<div style="{flex};">{content}</div>')
            else: # Current column, check rows
                rows = []
                row_idx = (visible_upto or {}).get("row", float('inf'))
                for r, output in enumerate(col['outputs']):
                    if r <= row_idx:
                        rows.append(_fmt_html(output))
                    else:
                        rows.append(f'<div style="visibility:hidden;">{_fmt_html(output)}</div>') # hold space
                
                cols.append(f'<div style="{flex};">{chr(10).join(rows)}</div>')
                
        css_class = ' '.join(self._dom_classes)
        return f'<div class="{css_class}" {_inline_style(self)}>{chr(10).join(cols)}</div>'


def write(*objs,widths = None, css_class=None, paused=False, **css_props):
    """
    Write `objs` to slides in columns. To create rows in a column, wrap objects in a list or tuple.   
    You can optionally specify `widths` as a list of percentages for each column. 
    `css_class` can have multiple classes separated by space, use this to do animations with classes. See `Slides.css_animations` for details.
    `**css_props` are additional CSS properties applied to the writer block node, CSS variables names like `--origin` should be passed as `__origin`.
         
    Write any object that can be displayed in a cell with some additional features:
    
    - Strings will be parsed as as extended markdown that can have citations/python code blocks/Javascript etc. Variables are resolved from notebook scope.
    - The output of `xmd.gather` can be passed to parse and display content with user given and scoped variables.
    - Use `paused=True` with rows in columns to reveal content incrementally during frame navigation.
    - Use `slides.steps([...])` for slider-driven step transitions where content is swapped in place.
    - Display another function to capture its output in order using [code! Slides.hold(func,...) /]. Only body of the function will be displayed/printed. Return value will be ignored.
    - Dispaly IPython widgets such as `ipywidgets` or `ipyvolume` by passing them directly.
    - Display Axes/Figure form libraries such as `matplotlib`, `plotly` `altair`, `bokeh` etc. by passing them directly.
    - Display source code of functions/classes/modules or other languages by passing them directly or using `Slides.code` API.
    - Use `Slides.alt` function to display obj/widget on slides and alternative content/screenshot of widgets in exported slides.
    - [code! ipywidgets.[HTML, Output, Box] /] and their subclasses will be displayed as [code! Slides.alt(html_converter_func, widget) /]. The value of exported HTML will be most recent.
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
        - `write` is a robust command that can handle most of the cases. If nothing works, `repr(obj)` will be displayed.
        - You can avoid `repr(obj)` by `Slides.hold(func, ...)` e.g. `Slides.hold(plt.show)`. This can also be used to delay display until it is captured in a column.
        - You can use [code! display(obj, metadata = {'text/html': 'html repr by user'}) /] for any object to display object as it is and export its HTML representation in metadata.
        - You can add mini columns inside a column by markdown syntax or ` Slides.stack `, but content type is limited in that case.
        - In markdown, `::: columns` maps to static `write(..., paused=False)`, while `::: columns.paused` maps to incremental `write(..., paused=True)`.
        - `::: columns.inline` is inline display mode and ignores incremental framing.
        - Use `++` before `::: columns.paused` to isolate previous content from the first reveal step.
    
    ::: note-tip
        To make a group of rows as single item visually for incremental display purpose, wrap them in a nested list/tuple.
        A single column is flattened up to 2 levels, so `[[obj1], row2, [item1, item2]]` will be displayed as 3 rows.
        
        Use nested row lists together with `paused=True` to control incremental reveal grouping for a column.
        First row of first column is immediately visible alongwith previous content, to show it separately, use `pause()` before write, e.g.
        
        ```python
        slides.write("Title Text")
        slides.pause()  # shows first row after title text
        slides.write([row1, [item1, item2], row3], column2, paused=True)  # incremental reveal
        slides.pause()  # optional pause between writes if anyone is itself not paused
        slides.write([row1, row2], paused=True) # Next write(below) is single group shown after this
        slides.write(1,2,3,4, css_class='anim-group anim-slide-up', __distance='400px',display='grid',grid_template_columns='1fr 1fr') # animated group of columns
        ``` 
    """
    Writer(*objs,widths = widths, css_class=css_class, paused=paused, **css_props) # Displays itself
