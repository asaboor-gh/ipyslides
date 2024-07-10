"""
Main write functions to add content to slides
"""

__all__ = ['write']

from IPython.display import display as display

from .formatters import ipw, XTML, RichOutput, _Output, serializer, htmlize, _inline_style, supported_reprs, widget_from_data, toc_from_meta
from .xmd import parse, capture_content, get_slides_instance

class CustomDisplay:
    "Use this to create custom display types for object."
    def _ipython_display_(self):
        return self.display()
    
    def display(self):
        raise NotImplementedError("display method must be implemented in subclass")
    

class GotoButton(ipw.Button):
    "Use `Slides.goto_button` function which returns this class."
    def __init__(self, app, on_click, *args, **kwargs):
        self._app = app 
        self._TargetSlide = None # Will be set by set_target
        self._target_id = f't-{id(self)}'
        super().__init__(*args,**kwargs)
        self.add_class("goto-button")
        self.on_click(on_click)
    
    def fmt_html(self):
        return self._app.html('a',self.description, href=f'#{self._target_id}', 
            style='color:var(--accent-color);text-decoration:none;', 
            css_class=f'goto-button export-only {self._app.icon.get_css_class(self.icon)}'
        ).value
    
    def display(self): display(self) # completeness

    def set_target(self):
        "Set target slide of goto button. Returns itself."
        self._app.verify_running("GotoButton's target can be set only inside a slide constructor!")
        
        if getattr(self, '_TargetSlide', None):
            self._TargetSlide._target_id = None # Remove previous link
        
        self._TargetSlide = self._app.this
        self._TargetSlide._target_id = self._target_id # Set new link
        return self 

def _fmt_html(output):
    "Format captured rich output and others to html if possible. Used in other modules too."
    if isinstance(output, str):
        return output
    
    if hasattr(output, 'fmt_html'): # direct return
        return output.fmt_html()
    
    # Metadata text/html Should take precedence over data if given
    data, metadata = getattr(output, 'data',{}),  getattr(output, 'metadata',{})
    if metadata and isinstance(metadata, dict):
        if "text/html" in metadata: # wants to export text/html even skip there for main obj
            return metadata['text/html']
        elif "skip-export" in metadata: # only skip
            return ''
        elif (toc := toc_from_meta(metadata)): # TOC in columns
            return toc.data["text/html"] # get latest title

    
    # Widgets after metadata
    if (widget := widget_from_data(data)):
        return serializer.get_html(widget) # handles fmt_html
    
    # Next data itself NEED TO INCLUDE ALL REPRS LIKE OUTPUT
    if (reps := [rep for rep in supported_reprs if data.get(f'text/{rep}','')]):
        return data[f'text/{reps[0]}'] # first that works
    
    return ''


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
            with capture_content() as cap:
                for c in col['outputs']:
                    if isinstance(c,(RichOutput, CustomDisplay, ipw.DOMWidget)):
                        display(c)
                    elif isinstance(c,str):
                        parse(c, returns = False)
                    elif callable(c) and c.__name__ == '<lambda>':
                        _ = c() # If c is a lambda function, call it and it will dispatch whatever is inside, ignore output
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
    
    
def write(*objs,widths = None):
    """
    Write `objs` to slides in columns. To create rows in a column, wrap objects in a list or tuple.      
    You can optionally specify `widths` as a list of percentages for each column. 
         
    Write any object that can be displayed in a cell with some additional features:
    
    - Strings will be parsed as as extended markdown that can have citations/python code blocks/Javascript etc.
    - Display another function in order by passing it to a lambda function like `lambda: func()`. Only body of the function will be displayed/printed. Return value will be ignored.
    - Dispaly IPython widgets such as `ipywidgets` or `ipyvolume` by passing them directly.
    - Display Axes/Figure form libraries such as `matplotlib`, `plotly` `altair`, `bokeh`, `ipyvolume` ect. by passing them directly.
    - Display source code of functions/classes/modules or other languages by passing them directly or using `Slides.code` API.
    - Use `Slides.alt` function to display obj/widget on slides and alternative content in exported slides.
    - Use `Slides.alt_clip` function to display anything (without parsing) on slides and paste its screenshot for export. Screenshots are persistent and taken on slides.
    - Use `Slides.image_clip` to add screenshots from clipboard while running the cell.
    - `ipywidgets.[HTML, Output, Box]` and their subclasses will be displayed as `Slides.alt(html_converter_func, widget)`. The value of exported HTML will be most recent.
    - Other options include but not limited to:
        - Output of functions in `ipyslides.utils` module that are also linked to `Slides` object.
        - PIL images, SVGs etc.
        - IPython display objects such as Image, SVG, HTML, Audio, Video, YouTubeVideo, IFrame, Latex, Markdown, JSON, Javascript, etc.
        - Any object that has a `_repr_html_` method, you can create one for your own objects/third party objects by:
            - `Slides.serializer` API. IPython's `display` automatically takes care of such objects on export to html.
            - `IPython.core.formatters` API for third party libraries.
            
    ::: note
        - Use `Slides.frozen` to avoid display formatting and markdown parsing over objects in `write` and for some kind of objects in `display` too.
        - `write` is a robust command that can handle most of the cases. If nothing works, `repr(obj)` will be displayed.
        - You can avoid `repr(obj)` by `lambda: func()` e.g. `lambda: plt.show()`. This can also be used to delay display until it is captured in a column.
        - You can use `display(obj, metadata = {'text/html': 'html repr by user'})` for any object to display object as it is and export its HTML representation in metadata.
        - A single string passed to `write` is equivalent to `parse` command.
        - You can add mini columns inside a column by markdown syntax or `Slides.cols`, but content type is limited in that case.
    """
    Writer(*objs,widths = widths) # Display itself