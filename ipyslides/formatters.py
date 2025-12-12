"""Format objects like different charting libraries and IPython display object to HTML representation.

"""
import sys
import textwrap
import inspect, re, base64

from pprint import PrettyPrinter
from io import BytesIO
from contextlib import contextmanager
from PIL import Image as PImage
import pygments
import ipywidgets as ipw

from IPython.display import display, HTML, Audio, Video, Image as IPyImage
from IPython.display import __dict__ as _all
from IPython.utils.capture import RichOutput, capture_output
from IPython import get_ipython
from dashlab.utils import _inline_style

__reprs = [rep.replace('display_','') for rep in _all if rep.startswith('display_')] # Can display these in write command

supported_reprs = tuple(__reprs) # don't let user change it

def widget_from_data(obj):
    "_model_id or dict of widget data."
    if isinstance(obj, str):
        out = ipw.widget_serialization['from_json']('IPY_MODEL_' + obj, None)
        if isinstance(out, ipw.DOMWidget): # It returns anything, make sure widget
            return out
    
    if isinstance(obj, dict):
        model_id = obj.get('application/vnd.jupyter.widget-view+json',{}).get('model_id','')
        return widget_from_data(model_id)
    
def toc_from_meta(metadata):
    if not isinstance(metadata, dict):
        return 
    number = metadata.get("DataTOC", None)
    if isinstance(number, int) and (slides := get_slides_instance()):
        return slides[number,]._reset_toc()


class _Output(ipw.Output):
    "Should only be used internally"
    _ipyshell = get_ipython()
    _hooks = (sys.displayhook, _ipyshell.display_pub if _ipyshell else None) # store once in start

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

    def __enter__(self):
        if self._ipyshell:
            self._chooks = (sys.displayhook, self._ipyshell.display_pub) # current hooks in top capture
            sys.displayhook, self._ipyshell.display_pub = self._hooks
        
        super().__enter__()

    def __exit__(self, etype, evalue, tb):
        if self._ipyshell:
            sys.displayhook, self._ipyshell.display_pub = self._chooks

        super().__exit__(etype, evalue, tb)

    def update_display(self):
        "Widgets output sometimes disappear on when Output is removed and displayed again. Fix that with this function."
        old_outputs = self.outputs
        self.outputs = () # Reset
        pending_displays = [] # Need to handle nested Output widgets to refresh as well

        for i, out in enumerate(old_outputs): # Update TOC if in column
            meta, data = out.get("metadata",{}), out.get("data",{})
            if (toc := toc_from_meta(meta)):
                old_outputs[i]['data'] = toc.data
            elif (widget := widget_from_data(data)):
                if isinstance(widget, type(self)):
                    pending_displays.append(widget)
                elif isinstance(widget, ipw.Box): # handles columns too
                    pending_displays.extend([child for child in widget.children if isinstance(child, type(self))])   

        self.outputs = old_outputs
        del old_outputs
        for widget in pending_displays:
            widget.update_display()


class XTML(HTML):
    "This HTML will be diplayable, printable and formatable. Use `self.as_widget()` to get a widget with same content."
    def __init__(self, *args,**kwargs):
        "Initialize with HTML string or other arguments that can be passed to `IPython.display.HTML` class."
        super().__init__(*args,**kwargs)
        
    def __format__(self, spec):
        return f'{self._repr_html_():{spec}}'
    
    def __repr__(self): # format handles string interpolation, need this short
        return f'<{self.__module__}.XTML at {hex(id(self))}>'
    
    def __str__(self):
        return str(self._repr_html_())
    
    def __call__(self):
        "Display this HTML object."
        return self.display()
    
    def display(self, metadata=None):
        "Display this HTML object with optionally passing metadata."
        display(self, metadata=metadata)
    
    @property
    def value(self):
        "Returns HTML string."
        return self._repr_html_()
    
    def as_widget(self):
        "Returns ipywidgets.HTML with same data."
        return ipw.HTML(self.value)

def _delim(_type):
    "Internal use to create delimiter for rows, parts and pages."
    return RichOutput(
        data={'text/plain': '', 'text/html': f'<!-- {_type} -->'},
        metadata={"DELIM": _type, "skip-export":"no need in export"}
    )  # to avoid unwanted output in Jupyter, just leave a comment

def _fig_caption(text): # need here to use in many modules
    return f'<figcaption class="no-focus">{htmlize(text)}</figcaption>' if text else ''

def plt2html(plt_fig = None,transparent=True,width = None, caption=None, crop=None):
    """Write matplotib figure as HTML string to use in `ipyslide.utils.write`.
    **Parameters**
    
    - plt_fig    : Matplotlib's figure instance, auto picks as well.
    - transparent: True of False for fig background.
    - width      : CSS style width. Default is figsize.
    - caption    : Caption for figure.
    - crop       : Crop SVG to given box in fraction 0-1 as tuple of (left, top, right, bottom).
    """
    # First line is to remove depedency on matplotlib if not used
    if not (plt := sys.modules.get('matplotlib.pyplot', None)):
        return None
    
    _fig = plt_fig or plt.gcf()
    plot_bytes = BytesIO()
    _fig.savefig(plot_bytes,format='svg',transparent = transparent)
    plt.close(_fig) #AVoids throwing text outside figure
    if width is None:
        width = f'{_fig.get_size_inches()[0]}in'
    width = (f'width:{width}px' if isinstance(width,int) else f'width:{width}') + ';max-width:100%;' # important to avoid overflow
    svg = f'<svg style="{width};height:auto;"' + plot_bytes.getvalue().decode('utf-8').split('<svg')[1]

    from .utils import svg as USVG # Avoid circular import
    return XTML(re.sub(r'fig\-(\d+)', r'fig-\1 mpl', USVG(svg, width=width,crop=crop,caption=caption).value))
    
def plt2image(plt_fig=None, transparent=True, width=None, caption=None, format='png', dpi=300):
    """Convert matplotlib figure to image with base64 encoding.
    
    **Parameters**
    
    - plt_fig     : Matplotlib's figure instance, auto picks as well.
    - transparent : True or False for fig background.
    - width       : CSS style width. Default is calculated from figsize and dpi.
    - caption     : Caption for figure.
    - format      : Image format ('png', 'jpg', 'jpeg'). Default is 'png'.
    - dpi         : Resolution for raster image. Default is 300.
    """
    # First line is to remove dependency on matplotlib if not used
    if not (plt := sys.modules.get('matplotlib.pyplot', None)):
        return None
    
    _fig = plt_fig or plt.gcf()
    
    # Determine format
    fmt = format.lower()
    if fmt in ('jpg', 'jpeg'):
        fmt = 'jpeg'
        transparent = False  # JPEG doesn't support transparency
    elif fmt == 'png':
        fmt = 'png'
    
    plot_bytes = BytesIO()
    _fig.savefig(plot_bytes, format=fmt, transparent=transparent, dpi=dpi, bbox_inches='tight')
    plt.close(_fig)  # Close after saving
    
    # Seek to beginning before reading
    plot_bytes.seek(0)
    
    # Encode to base64
    img_base64 = base64.b64encode(plot_bytes.getvalue()).decode('utf-8')
    
    # Create metadata with proper width handling
    width_str = f'{width}%' if isinstance(width, int) else width
    
    metadata = {
        'width': width_str,
        'caption': _fig_caption(caption) if caption else '',
        'attrs': 'class="focus-child mpl"',
    }
    return IMG({f'image/{fmt}': img_base64}, metadata)

def bokeh2html(bokeh_fig,title=""):
    """Write bokeh figure as HTML string to use in `ipyslide.utils.write`.
    **Parameters**
    
    - bokeh_fig : Bokeh figure instance.
    - title     : Title for figure.
    """
    if (bokeh := sys.modules.get('bokeh', None)):
        return XTML(f'''<div class="focus-child">
            {bokeh.embed.file_html(bokeh_fig, bokeh.resources.CDN, title)}
        </div>''')

def _altair2htmlstr(chart): return _focus_on(chart._repr_mimebundle_().get('text/html',''))

class IMG(XTML):
    "IMG object with embeded data from any possible source. Use `self.to_pil` and `self.to_numpy` to export to other formats."
    def __init__(self, data, metadata):
        self._data = (data, metadata)
        super().__init__(self._make_fig())
    
    def _make_fig(self):
        _, metadata = self._data
        return f"<figure {metadata['attrs']}>{self.clean()}{metadata['caption']}</figure>" + metadata.get('style', '') # optional style

    def clean(self):
        "Get clean img tag XTML without figure wrapping. Caption will be lost."
        data, metadata = self._data
        src, *_ = [f'data:{k};base64, {v}' for k,v in data.items()]
        width = metadata['width']
        return XTML(f"<img src='{src}' width='{width}' height='auto'/>")
    
    def to_pil(self):
        "Return PIL image or None."
        for value in self._data[0].values():
            buf = BytesIO(base64.b64decode(value))
            return PImage.open(buf)
    
    def to_numpy(self):
        "Return numpy array data of image or None. Useful for plotting."
        from numpy import asarray # Do not import at top, as it is not a dependency
        return asarray(self.to_pil() or [])
    

def fix_ipy_image(image,width='100%'): # Do not add focs class here, it's done in util as well as below
    img = image._repr_mimebundle_() # Picks PNG/JPEG/etc
    _src, *_ = [f'data:{k};base64, {v}' for k,v in img[0].items()]
    return XTML(f"<img src='{_src}' width='{width}' height='auto'/>") # width is important, height auto fixed

def _focus_on(html_str, self=True): # Focus for auto output, self or child
    klass = 'self' if self else 'child'
    return f'<div class="focus-{klass}">{html_str}</div>'


def code_css(style='default',color = None, background = None, hover_color = 'var(--bg3-color)', css_class = None, lineno = True):
    """Style code block with given style from pygments module. ` color ` and ` background ` are optional and will be overriden if pygments style provides them.
    """
    _class = '.highlight' if css_class is None else f'.highlight.{css_class}'
    if lineno:
        _class += '.numbered'
    
    if style not in pygments.styles.get_all_styles():
        raise KeyError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
    _style = pygments.formatters.HtmlFormatter(style = style).get_style_defs(_class)
    if style == 'default':
        _bg_fg = {'background': 'var(--bg2-color)', 'color': 'var(--fg1-color)'} # Should match inherit theme
    else: # Override color and background if provided by theme
        _bg_fg = {} 
        items = [b.strip().split() for b in ''.join(re.findall(rf'{_class}\s+?{{(.*?)}}',_style)).replace(':',' ').rstrip(';').split(';')]
        for item in items:
            if len(item) == 2 and item[0] in ('background','color'):
                _bg_fg[item[0]] = item[1]      
    
    # keep user preferences               
    bg = background if background else _bg_fg.get('background','var(--bg2-color)')
    fg = color if color else _bg_fg.get('color','var(--fg1-color)')
     
    return f"""<style>\n{_style}
    {_class} {{ 
        background: {bg}; 
        color: {fg}; 
        border-left: 0.2em solid {hover_color};
        border-radius: 0.2em;
    }}
    span.err {{border: none !important;}}
    {_class} code:hover, {_class} code:hover::before {{
        background: {hover_color} !important; /* Important to override default hover */
    }}
    {_class} pre {{
        padding :4px 8px 4px {0 if lineno else 8}px !important; 
    }}
    {_class} pre, {_class} code {{
        background: transparent !important; /* in notebook directly */
    }}
    {_class} code::before {{
        width: {'1.2em' if lineno else '0'};
        color: {fg};
        font-size: 80% !important;
        background: {bg} !important;
        display:{'inline-block' if lineno else 'none'} !important;
    }}\n</style>"""

def _highlight(code, language='python', name = None, css_class = None, style='default', color = None, background = None, hover_color = 'var(--bg3-color)', lineno = True, height='400px'):
    if style not in pygments.styles.get_all_styles():
        raise KeyError(f"Style {style!r} not found in {list(pygments.styles.get_all_styles())}")
    if css_class in pygments.styles.get_all_styles():
        style = css_class
    
    if not isinstance(code, str):
        code = _source_code(code)
        
    formatter = pygments.formatters.HtmlFormatter(style = style)
    _style = code_css(style=style, color = color, background = background, hover_color = hover_color,css_class=css_class, lineno = lineno) if css_class else ''
    _code = pygments.highlight(textwrap.dedent(code).strip('\n'), # dedent make sure code blocks at any level are picked as well
            pygments.lexers.get_lexer_by_name(language), formatter)
    
    start, mid_end = _code.split('<pre>')
    middle, end = mid_end.split('</pre>')
    lines = middle.strip().replace('<span></span>','').splitlines()
    code_ = '\n' + '\n'.join([f'<code>{line}</code>' for line in lines]) # start with newline is important
    _title = '' if name is False else name if name else language.title()
    
    _class = (css_class if isinstance(css_class, str) else '') + (' numbered' if lineno else '')
    start = start.replace('class="highlight"',f'class="highlight {_class}"')
    
    return f'''<div><span class="lang-name">{_title}</span>
        <div class="highlight-wrapper" style="height:auto;max-height:{height};overflow:auto;position:relative;">
        {_style}\n{start}
        <pre>{code_}
        </pre>\n{end}</div></div>'''
    
class Serializer:
    def __init__(self):
        """HTML serializer for an object to use inside `Slides.write` or `display`.
        ipywidgets's `HTML`, `Box`, `Output` and their subclasses are already serialized.
        """
        self._libs = []
    
    def register(self, obj_type, verbose = True):
        """Decorator to register html serializer for an object type.
        
        - Decoracted function accepts one argument that will take `obj_type` and should return HTML string.
        - This definition will take precedence over any other in the module.
        - All regeisted serializers only exist for the lifetime of the module in a namespace.
        - Only a single serializer can be registered for an object type.
        
        **Usage**
        ```python
        class MyObject:
            def __repr__(self):
                return 'My object is awesome'
        
        slides = ipyslides.Slides()
        @slides.serializer.register(MyObject)
        def make_h1(obj):
            return f'<h1>{obj!r}</h1>'
            
        my_object = MyObject()
        slides.write(my_object) #This will write "My object is awesome" as main heading
        make_h1(my_object) #This will return "<h1>My object is awesome</h1>"
        
        #This is equivalent to above for custom objects(builtin objects can't be modified)
        class MyObject:
            def _repr_html_(self):
                return '<h1>My object is awesome</h1>'
                
        my_object = MyObject()
        slides.write(my_object)
        ```
        ::: note
            - Serializer function should return html string. It is not validated for correct code on registration time.       
            - Serializer is useful for buitin types mostly, for custom objects, you can always define a ` _repr_html_ ` method which works as expected.
            - Serialzers for widgets are equivalent to `Slides.alt(func, widget)` inside `write` command for export purpose. Other commands such as `Slides.[cols,rows,...]` will pick oldest value only.
            - IPython's `display` function automatically take care of serialized objects.
        """
        def _register(func):
            if obj_type is str:
                raise TypeError("Cannot register serializer for string type! Use custom class to encapsulate string the way you want.")
            
            if isinstance(obj_type, RichOutput):
                raise TypeError("Cannot serialize a RichOutput instance!")
            
            if getattr(func, '__name__','').startswith('_alt_'):
                raise ValueError(f"func names starting with _alt_ are reserved!")

            item = {'obj': obj_type, 'func': func}
            already = False
            for i, _lib in enumerate(self._libs):
                if item['obj'] is _lib['obj']:
                    self._libs[i] = item
                    if verbose:
                        print(f'Updated: {item["obj"]} → {item["func"].__name__}({item["obj"]})')
                    already = True
                    break
                    
            if not already:
                self._libs.append(item)
                if verbose:
                    print(f'Registered: {item["obj"]} → {item["func"].__name__}({item["obj"]})')
                
            return func
        return _register
    
    @property
    def available(self):
        "Tuple of all registered types."
        return tuple(self._libs)
    
    @property
    def types(self):
        "Tuple of all registered types."
        return tuple(item['obj'] for item in self._libs)

    def get_func(self, obj_type):
        "Get serializer function for a type. Returns None if not found."
        if isinstance(obj_type, RichOutput): # like frozen and already computed
            return None
        
        if isinstance(obj_type, ipw.DOMWidget) and hasattr(obj_type, 'fmt_html'):
            return lambda obj: obj.fmt_html() # From alt, fmt_html is method, so need one arguemnt be there
        
        if type(obj_type) in serializer.types: # Do not check instance here, need specific information
            for item in serializer.available:
                if type(obj_type) == item['obj']:
                    return item['func']
        # Check instance for ipywidgets.HTML/Output after user defined types
        if isinstance(obj_type, ipw.Box):
            return self._alt_box
        elif isinstance(obj_type, _Output):
            return self._alt_output
        elif isinstance(obj_type, (ipw.HTML, ipw.HTMLMath)): # Instance here is fine to include subclasses as they will behave same
            return self._alt_html
        elif isinstance(obj_type, (ipw.Audio, ipw.Video, ipw.Image)):
            return self._alt_media
        return _exportable_func(obj_type)
    
    def get_metadata(self, obj_type):
        """Get metadata for a type to use in `display(obj, metadata)` for export purpose. This take precedence over object's own html representation. Returns {} if not found.
        """
        if (func := self.get_func(obj_type)):
            return {'text/html': func(obj_type)}
        return {}
    
    def get_html(self, obj_type):
        "Get html str of a registerd obj_type."
        if (func := self.get_func(obj_type)):
            return func(obj_type)
        elif isinstance(obj_type, ipw.DOMWidget): # Empty div for widgets, needed to keep layout in export
            css_class = ' '.join(obj_type._dom_classes)
            kwargs = {k:v for k,v in obj_type.layout.get_state().items() if v and k[0]!='_'}
            return f'<div class="{css_class}" {_inline_style(kwargs)}></div>' 
        return ''
    
    def _alt_box(self, box_widget):
        if not isinstance(box_widget, ipw.Box):
            raise TypeError(f"Expects ipywidget's Box and subclasses, got {type(box_widget)}")
        
        kwargs = dict(width='100%', gap="0.2em") # avoid collapse in export, defult layouts are None there
        if isinstance(box_widget,ipw.HBox):
            kwargs.update(dict(display="flex",flex_flow="row nowrap"))
        elif isinstance(box_widget,ipw.VBox):
            kwargs.update(dict(display="flex",flex_flow="column nowrap"))
        
        kwargs.update({k:v for k,v in box_widget.layout.get_state().items() if v and k[0]!='_'}) # only those if not None
        css_class = ' '.join(box_widget._dom_classes) # To keep style of HTML widget, latest as well
        content = '\n'.join(self.get_html(child) for child in box_widget.children)
        return f'<div class="{css_class}" {_inline_style(kwargs)}>{content}</div>'
    
    def _alt_html(self, html_widget):
        """Convert ipywidgets.HTML object to HTML string."""
        if not isinstance(html_widget,(ipw.HTML,ipw.HTMLMath)):
            raise TypeError(f"Expects instance of ipywidgets.(HTML/HTMLMath), got {type(html_widget)}")

        css_class = ' '.join(html_widget._dom_classes) # To keep style of HTML widget, latest as well
        return f'<div class="{css_class}" {_inline_style(html_widget)}>{html_widget.value}</div>' 
    
    def _alt_media(self, media_widget):
        if isinstance(media_widget, ipw.Image):
            return fix_ipy_image(IPyImage(media_widget.value)).value
        elif isinstance(media_widget, ipw.Audio):
            return Audio(media_widget.value.tobytes(),embed=True)._repr_html_()
        elif isinstance(media_widget, ipw.Video):
            return Video(media_widget.value.tobytes(),embed=True, mimetype=f'video/{media_widget.format}')._repr_html_()
        raise TypeError(f"Expects ipywidgets.(Audio/Video/Image), got {type(media_widget)}")
    
    def _alt_output(self, output_widget):
        "Convert objects in ipywidgets.Output to HTML string."
        if not isinstance(output_widget, _Output):
            raise TypeError(f"Expects Output widget instnace, got {type(output_widget)}")
        
        from .xmd import raw # avoid circular import
        
        css_class = ' '.join(output_widget._dom_classes) # To keep style of Output widget, latest as well
        content = ''
        for d in output_widget.outputs:
            if 'text' in d: # streams takes prefersnces
                content += raw(d['text']).value
            else:
                content += self._export_other_reprs(d)
        return f'<div class="{css_class}" {_inline_style(output_widget)}>{content}</div>' 
    
    def _export_other_reprs(self, d):
        "Everything future can be added at end of this. d should be dict or RichOutput"
        # Metadata text/html Should take precedence over data if given
        if isinstance(d, RichOutput):
            data, metadata = d.data or {}, d.metadata or {}
        elif isinstance(d, dict):
            data, metadata = d.get('data',{}), d.get('metadata',{})
        else:
            raise TypeError(f"expect dict or RichOutput, got {type(d)}")
        
        if metadata and isinstance(metadata, dict):
            if "text/html" in metadata: # wants to export text/html even skip there for main obj
                return metadata['text/html']
            elif "skip-export" in metadata: # only skip
                return ''
            elif (toc := toc_from_meta(metadata)): # TOC in columns
                return toc.data["text/html"] # get latest title
        
        # Widgets after metadata
        if (widget := widget_from_data(data)):
            if hasattr(widget, 'fmt_html'):
                return widget.fmt_html() # May be some deep nested columns, alt etc
            return self.get_html(widget)
        
        # Next data itself NEED TO INCLUDE ALL REPRS LIKE OUTPUT
        if (reps := [rep for rep in supported_reprs if data.get(f'text/{rep}','')]):
            return data[f'text/{reps[0]}'] # first that works

        # Image data, handles plt.show as well
        if (keys := [key for key in data if key.startswith('image')]):
            key, value, alt = keys[0], data[keys[0]], data['text/plain']
            return value if 'svg' in key else f'<img src="data:{key};base64, {value}" alt="{alt}" />' # first that works
        
        return ''  

    def unregister(self, obj_type):
        "Unregister all serializer handlers for a type."
        for item in self._libs:
            if obj_type is item['obj']:
                self._libs.remove(item)
    
    def unregisterall(self):
        "Unregister all serializer handlers."
        self._libs = []
    
    def __repr__(self):
        return 'Serializer(\n\t' + '\n\t'.join(f'{item["obj"]} → {item["func"].__name__}({item["obj"]})' for item in self._libs) + '\n)'

serializer = Serializer()
del Serializer # Make sure this is not used by user

def frozen(obj, metadata=None):
    """Display object as it it and export metadata if not str. 
    A frozen object may not appear in exported html if metadata is not given.
    
    Returned object has a display method, or can be directly passed to display/write commands.
    """
    if isinstance(obj, str):
        return RichOutput(data={'text/plain':'', 'text/html': obj}) # no metadta required

    with altformatter.reset(), capture_output() as cap:
        metadata= serializer.get_metadata(obj) if metadata is None else metadata
        display(obj, metadata=metadata)
    
    if len(cap.outputs) == 1:
        return cap.outputs[0] # single object
    
    cap.display = cap.show # for completenes with other returns
    cap._ipython_display_ = cap.show # This is important to not being caught by altformatter
    return cap
    

def get_slides_instance():
    "Get the slides instance from the current namespace."
    if (isd:= sys.modules.get('ipyslides',None)):
        if (slides := getattr(isd, "Slides",None)): # Avoid partial initialization
            return slides.instance()


class AltDispalyFormatter:
    "Used to display widgets correctly. Use self.reset() contextmanager to disable for your desired display."
    _ip = get_ipython()
    _ipy_format = _ip.display_formatter.format if _ip else None

    def __init__(self):
        if self._ip:
            self._ip.display_formatter.format = self.format
        
    def format(self, obj, *args, **kwargs):
        "Handles Slides.serializer objects inside display command."
        with self.reset():
            if not isinstance(obj, ipw.DOMWidget) and (html := serializer.get_html(obj)):
                slides = get_slides_instance()
                if getattr(slides, 'this', None) or getattr(slides, '_in_output', False):
                    display(XTML(html)) # User defined serializers in display as well
                    return {}, {} # Need empty there
                
        # Display should only handle above, it is counter intuitive otherwise for user
        return self._ipy_format(obj, *args, **kwargs)

    @contextmanager
    def reset(self):
        "Contextmanager to reset temporarily to default display formatter."
        try:
            if self._ip:
                self._ip.display_formatter.format = self._ipy_format
            yield
        finally:
            if self._ip:
                self._ip.display_formatter.format = self.format
        

altformatter = AltDispalyFormatter() # keep reference for being live
del AltDispalyFormatter # Only one


pprinter = PrettyPrinter(indent=2,depth=5,compact=True)

def _format_object(obj):
    "Returns string of HTML for given object."
    if (func := serializer.get_func(obj)):
        return True, func(obj)
    
    # just prettry format some builtin types, others can be handled at end of htmlize
    if isinstance(obj, (int, float, complex, bool)):
        return True, str(obj) # should have same fonts as text

    if isinstance(obj, (set,list,tuple,dict,range)):
        return True, f"<code style='color:var(--fg1-color) !important;'>{pprinter.pformat(obj)}</code>"
    
    # If Code object given
    for _type in ['class','function','module','method','builtin','generator']:
        if getattr(inspect,f'is{_type}')(obj):
            source = _highlight(_source_code(obj), language='python',style='default',css_class=None)
            return (True, source)
    
    # If Nothing found
    return False, NotImplementedError(f"{obj}'s html representation is not implemented yet!")  

def _source_code(obj):
    try:
        source = textwrap.dedent(inspect.getsource(obj)).strip('\n') # dedent is must
        source = re.sub(r'^#\s+','#',source) # Avoid Headings in source
    except:
        source = f'Can not get source code of:\n{obj}'
    return source


def htmlize(obj):
    "Returns string of HTML representation for given object."
    # Brute force: Matplotlib figure get lost may be due to some race conditions 
    # if not handled here immediately and becomes bool at some point, ax work fine though
    if 'matplotlib.figure.Figure' in str(type(obj)):
        return plt2html(obj).value
    
    if isinstance(obj, RichOutput):
        from .xmd import error
        return error("TypeError","Received a non-serializable object. Use display or write directly or use %{obj:nb} syntax in markdown!").value
    
    if isinstance(obj,str):
        from .xmd import xmd # Avoid circular import
        return xmd(obj, returns = True) 
    elif isinstance(obj,XTML) or callable(getattr(obj, '_repr_html_',None)):
        return obj._repr_html_() #_repr_html_ is a method of XTML and it is quick   
    else:
        # Next prefer custom methods of objects as they are more frequently used
        is_true, _html = _format_object(obj)
        if is_true:
            return _html # it is a string
        
        # Ipython objects
        _reprs_ = [rep for rep in [getattr(obj,f'_repr_{r}_',None) for r in __reprs] if rep]   
        for _rep_ in _reprs_:
            _out_ = _rep_()
            if _out_: # If there is object in _repr_<>_, don't return None
                return _out_
        
        # Return __repr__
        return f"<code style='color:var(--fg1-color) !important;'>{obj.__repr__()}</code>"
    

def _exportable_func(obj):
    module = getattr(obj, '__module__','') or '' # can have None set as __modeule__, fix it
    mro_str = str(obj.__class__.__mro__)  
    
    # Instead of instance check, we can get mro, same effect without importing modules
    if re.search('matplotlib.*Figure', mro_str, flags=re.DOTALL):return lambda obj: plt2html(obj).value # intercept figure before axes
    if module.startswith('matplotlib') and hasattr(obj,'get_figure'): # any axes
        return lambda obj: plt2html(obj.get_figure()).value
    
    if re.search('altair.*JupyterChart', mro_str, flags=re.DOTALL): return lambda obj: _altair2htmlstr(obj.chart)
    
    if re.search('altair.*Chart', mro_str, flags=re.DOTALL): return lambda obj: _altair2htmlstr(obj)
    
    if re.search('plotly.*FigureWidget', mro_str, flags=re.DOTALL): return lambda obj: _focus_on(obj.to_html(full_html=False))
    
    if re.search('ipympl.*Canvas',mro_str, flags=re.DOTALL): return lambda obj: plt2html(obj.figure).value
    
    if re.search('pygal.*Graph', mro_str, flags=re.DOTALL): return lambda obj: _focus_on(obj.render(is_unicode=True))
    
    if re.search('pydeck.*Deck', mro_str, flags=re.DOTALL): return lambda obj: _focus_on(obj.to_html(as_string=True))
    
    if re.search('pandas.*DataFrame', mro_str, flags=re.DOTALL): return lambda obj: _focus_on(obj.to_html())# full instead of repr
    
    if re.search('pandas.*Series', mro_str, flags=re.DOTALL):
        return lambda obj: f"<code style='color:var(--fg1-color) !important;'>{pprinter.pformat(list(obj))}</code>"# full instead of repr
    
    if re.search('polars.*DataFrame', mro_str, flags=re.DOTALL):
        return lambda obj: _focus_on(obj.to_pandas().to_html())# full instead of repr
    
    if re.search('bokeh.*Figure', mro_str, flags=re.DOTALL): return lambda obj: bokeh2html(obj,title='').value
    
    if re.search('IPython.*Image', mro_str, flags=re.DOTALL): return lambda obj: _focus_on(fix_ipy_image(obj,width='100%'),False) 