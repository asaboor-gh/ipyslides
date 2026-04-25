"""
Main write functions to add content to slides
"""

__all__ = ['write', 'snapshots']

from collections import UserList
from collections.abc import Iterable
from itertools import chain
from contextlib import contextmanager
from IPython.display import display as display
from IPython.utils.capture import CapturedIO
from dashlab.utils import _build_css

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
    
    if isinstance(output, XTML):
        return output.value
    
    if hasattr(output, 'fmt_html'): # direct return, may be column
        return output.fmt_html()
    
    return serializer._export_other_reprs(output)

def _style_for_widget(widget, **css_props):
    "Not all widgets support all CSS properties, so we build style from user specified props."
    if not css_props or not isinstance(widget, ipw.DOMWidget):
        return
    uklass = f"wuid-{id(widget)}"
    widget.add_class(uklass) # unique class for this writer
    klass = '.' + '.'.join(widget._dom_classes)  # pick all classes to pass vriables at local scope
    return f'<style>\n{_build_css((klass,), css_props)}\n</style>'

def _snapshots_merge_style(selectors):
    "Hide rows from selector boundary onward when merge mode class is active."
    if not selectors:
        return ''

    if isinstance(selectors, str):
        selectors = (selectors,)

    return f'<style>\n{_build_css(tuple(selectors), {"display": "none !important"})}\n</style>'

class snapshots(UserList):
    """Column-content wrapper to reveal items one-by-one during frame navigation.

    You can append displayable items directly, or use `capture()` to collect multiple
    outputs as one snapshot step, especially when content is generated in a loop or from a function that doesn't return all content at once.
    """
    @contextmanager
    def capture(self):
        """Capture multiple outputs as one snapshot item.

        This is a convenient when a single snapshot step should contain multiple displayed objects.
        """
        with capture_content() as cap:
            yield
        self.append(cap) # Append captured content as a single item to maintain row grouping in `write`

class Writer(ipw.HBox):
    _in_write = False
    def __init__(self, *objs, widths = None, css_class = None, **css_props):
        self._parts = () # to store part positions
        self._snapshots_cols = {} # map {col: last_row_delim_idx} for per-column snapshots
        self._snapshots_first_rows = {} # map {col: first_row_delim_idx} for merge-first-row CSS cutoff
        if self.__class__._in_write and len(objs) > 1: # Like from delayed lambda function
            raise RuntimeError("Trying to write inside a writer!")
        
        super().__init__() 
        self.add_class('columns').add_class('writer') # to differentiate from other columns
        self.layout.display = css_props.get('display', 'flex') # html export as well as user specified should be honored
        
        if isinstance(css_class, str): # additional classes
            [self.add_class(c) for c in css_class.split()]

        try:
            self.__class__._in_write = True
            self._cols = self._capture_objs(*objs, widths = widths, css_props=css_props) # run after getting slides instance
        finally:
            self.__class__._in_write = False

        single_col = len(self._cols) == 1
        single_meta = self._cols[0] if single_col else {}
        can_flatten_single = single_col and not any([
            isinstance(css_class, str),
            css_props,
            single_meta.get('snapshots', False),
        ])

        if can_flatten_single:
            # css_class/css_props still need to make all items in single block, without it just flatten display
            rows = self._cols[0]['outputs']
            if len(rows) == 1:
                display(*rows) # Just display single output directly
            elif len(rows) > 1:
                display(rows[0], metadata={"FLATCOL": len(rows)})  # First output with FLATCOL metadata to indicate for frames
                display(*rows[1:]) # Just display rest of rows directly
        elif len(objs) >= 1: # avoid empty write
            self.children = [
                _Output(layout = ipw.Layout(flex = c['flex'],min_width='0',height='auto'))
                for c in self._cols
            ]
            for i, (col, out) in enumerate(zip(self._cols, self.children)):
                if col.get('uclass'):
                    out.add_class(col['uclass'])
                if col.get('snapshots'):
                    out.add_class('snapshots-rows')
            display(self, metadata=self.metadata) # Just display it with ID
            self.update_display() # show content on widgets

    
    @property
    def data(self): return self._repr_mimebundle_() # Required to mimic RichOutput
    
    @property
    def metadata(self): return {'_MODEL_ID': self._model_id,"COLUMNS": ""} # Required to update both display and frames

    def __repr__(self):
        return f'<{self.__module__}.Writer at {hex(id(self))}>'

    def _capture_objs(self, *objs, widths = None, css_props=None):
        raw_cols = list(objs)

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
        for i, (w, raw) in enumerate(zip(widths, raw_cols)):
            is_snapshots = isinstance(raw, snapshots)
            content = list(raw) if is_snapshots else raw
            cols.append({
                'flex': f'{w:.3f} {w:.3f} {w*100:.3f}%',
                'outputs': content if isinstance(content, (list, tuple)) else [content],
                'snapshots': is_snapshots,
                'uclass': f'coluid-{id(self)}-{i}',
            })

        parts, rowsep = [], _delim("ROW")  # row delimiter
        snapshots_cols = {}
        snapshots_first_rows = {}
        for i, col in enumerate(cols):
            col_outputs = list(col['outputs'])
            if i > 0: # for i == 0, we want to preserve empty start for paused columns, handled in _split_parts
                while col_outputs and col_outputs[0] == "":
                    col_outputs.pop(0)

            rows = chain(*(
                (*obj, rowsep) if isinstance(obj, (list, tuple)) # nested rows as single group
                else (obj, rowsep)  # each object as single row
                for obj in col_outputs
            ))
            with capture_content() as cap:
                if i == 0 and css_props: # display CSS in first column only
                    XTML(_style_for_widget(self, **css_props)).display() 
                    
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

            base_outputs = cap.outputs[:-1]  # remove last rowsep output
            if col.get('snapshots'):
                first_row_idx = next((
                    r for r, out in enumerate(base_outputs)
                    if isinstance(getattr(out, 'metadata', {}), dict)
                    and getattr(out, 'metadata', {}).get('DELIM', '') == 'ROW'
                ), None)
                if isinstance(first_row_idx, int):
                    live_start_n = first_row_idx + 3 # +1 for prepended style, +2 for nth-child cutoff in widget DOM
                    merge_live_sel = (
                        f'.SlidesWrapper.SlidesMerged '
                        f'.{col["uclass"]}.snapshots-rows > .jp-OutputArea > .jp-OutputArea-child:nth-child(n + {live_start_n})'
                    )
                    cols[i]['outputs'] = [XTML(_snapshots_merge_style(merge_live_sel)), *base_outputs]
                else:
                    cols[i]['outputs'] = base_outputs
            else:
                cols[i]['outputs'] = base_outputs

            for r, out in enumerate(cols[i]['outputs']):
                meta = getattr(out, 'metadata', {})
                if isinstance(meta, dict) and meta.get('DELIM','') == 'ROW':
                    parts.append({"col": i, "row": r}) # mark row positions
                    if col.get('snapshots'):
                        if i not in snapshots_first_rows:
                            snapshots_first_rows[i] = r
                        snapshots_cols[i] = r

            parts.append({"col": i}) # only columns incremented after rows done inside
        
        self._parts = tuple(parts) # make it immutable
        self._snapshots_cols = snapshots_cols
        self._snapshots_first_rows = snapshots_first_rows
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
        snapshots_last_rows = (visible_upto or {}).get("_snapshots_last_rows", {})
        merge_hide_class = 'snapshots-merge-hide'

        def _fmt_rows(outputs, hide_after=None):
            rows = []
            for r, output in enumerate(outputs):
                html = _fmt_html(output)
                if not html:
                    continue
                if isinstance(hide_after, int) and r > hide_after:
                    rows.append(f'<div class="{merge_hide_class}">{html}</div>')
                else:
                    rows.append(html)
            return rows

        for i, col in enumerate(self._cols):
            flex = f'flex:{col["flex"]};height:auto;min-width:0'
            col_class = ' '.join(x for x in (col.get('uclass', ''), 'snapshots-rows' if col.get('snapshots') else '') if x)
            class_attr = f' class="{col_class}"' if col_class else ''
            merge_hide_after = self._snapshots_first_rows.get(i) if col.get('snapshots') else None
            if i > col_idx: # Entire column is hidden
                content = '\n'.join(_fmt_rows(col['outputs'], hide_after=merge_hide_after))
                cols.append(f'<div{class_attr} style="{flex};visibility:hidden">{content}</div>')
            elif i < col_idx: # Entire column is visible (or previous in focus mode)
                if i in snapshots_last_rows:
                    # snapshots mode: previous column shows only last row, skip others entirely
                    last_r = snapshots_last_rows[i]
                    rows = [_fmt_html(output) for r, output in enumerate(col['outputs']) if r > last_r]
                    cols.append(f'<div{class_attr} style="{flex};">{chr(10).join(rows)}</div>')
                else:
                    content = '\n'.join(_fmt_rows(col['outputs'], hide_after=merge_hide_after))
                    cols.append(f'<div{class_attr} style="{flex};">{content}</div>')
            else: # Current column, check rows
                rows = []
                row_idx = (visible_upto or {}).get("row", float('inf'))
                prev_row_idx = (visible_upto or {}).get("prev_row", -1) if i in snapshots_last_rows else -1
                # snapshots mode on current column when fully visible (no row key)
                if row_idx == float('inf') and i in snapshots_last_rows:
                    last_r = snapshots_last_rows[i]
                    rows = [_fmt_html(output) for r, output in enumerate(col['outputs']) if r > last_r]
                else:
                    for r, output in enumerate(col['outputs']):
                        if row_idx != float('inf') and i in snapshots_last_rows:
                            # snapshots mode: only include current row content, skip others
                            if prev_row_idx < r < row_idx:
                                rows.append(_fmt_html(output))
                        else:
                            if r <= row_idx:
                                rows.append(_fmt_html(output))
                            else:
                                rows.append(f'<div style="visibility:hidden;">{_fmt_html(output)}</div>')
                
                cols.append(f'<div{class_attr} style="{flex};">{chr(10).join(rows)}</div>')
                
        css_class = ' '.join(self._dom_classes)
        return f'<div class="{css_class}" {_inline_style(self)}>{chr(10).join(cols)}</div>'


def write(*objs,widths = None, css_class=None, **css_props):
    """
    Write `objs` to slides in columns. To create rows in a column, wrap objects in a list or tuple.   
    You can optionally specify `widths` as a list of percentages for each column. 
    `css_class` can have multiple classes separated by space, use this to do animations with classes. See `Slides.css_animations` for details.
    `**css_props` are additional CSS properties applied to the writer block node, CSS variables names like `--origin` should be passed as `__origin`.
         
    Write any object that can be displayed in a cell with some additional features:
    
    - Strings will be parsed as as extended markdown that can have citations/python code blocks/Javascript etc.
    - Wrap a column content list using code`snapshots([...])` to reveal items one-by-one during frame navigation.
        You can also build it with code`s = snapshots(); with s.capture(): ...` and pass `s` as a column.
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
        - In markdown `columns` block syntax is similar to `write` command if `+++` separartor is used there.
        - In markdown `::: columns` with `+++`, put `[snapshots]` inside a specific column to enable code`snapshots([...])` behavior for that column.
    
    ::: tip
        To make a group of rows as single item visually for incremental display purpose, wrap them in a nested list/tuple.
        A single column is flattened up to 2 levels, so `[[obj1], row2, [item1, item2]]` will be displayed as 3 rows.
        
        Use code`snapshots([...])` to reveal rows in isolation for a specific column.
        
        **Incremental display** is triggered only when you place `Slides.pause()` delimiter **before** the `write` command:
        
        ```python
        slides.pause()  # Trigger incremental display, equivalent to ++ before `columns` in markdown
        slides.write([row1, [item1, item2], row3], column2)  # Shows rows one by one (item1 and item2 together), then column2
        slides.pause()  # Another trigger for next write
        slides.write([row1, row2]) # Shows both rows incrementally , no additional columns here
        slides.write(1,2,3,4, css_class='anim-group anim-slide-up', __distance='400px',display='grid',grid_template_columns='1fr 1fr') # animated group of columns
        ``` 
    """
    Writer(*objs,widths = widths, css_class=css_class, **css_props) # Displays itself
