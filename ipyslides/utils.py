_attrs = ['AnimationSlider', 'alt', 'alert', 'as_html', 'block', 'bullets', 'clip', 'color', 'cols', 'error', 'table', 'suppress_output','suppress_stdout','capture_content',
    'details', 'set_dir', 'textbox', 'hspace', 'vspace', 'center', 'image', 'svg','iframe','frozen', 'raw', 'rows', 
    'zoomable','html', 'sig','styled', 'doc','today','get_child_dir','get_notebook_dir','is_jupyter_session','inside_jupyter_notebook']

_attrs.extend([f'block_{c}' for c in 'red green blue cyan magenta yellow'.split()])
__all__ = sorted(_attrs)

import os, re, json
import datetime
import inspect
import traceback

from types import MethodType
from pathlib import Path
from io import BytesIO # For PIL image
from contextlib import contextmanager, suppress
from PIL import Image as pilImage, ImageGrab

from IPython import get_ipython
from IPython.display import SVG, IFrame
from IPython.core.display import Image, display

from ._base._widgets import AnimationSlider # For export
from .formatters import ipw, XTML, IMG, frozen, get_slides_instance, htmlize, highlight, _inline_style
from .xmd import _fig_caption, get_unique_css_class, capture_content, parse, raw, error # raw error for export from here
from .writer import Writer, CustomDisplay, _Output

def is_jupyter_session():
     "Return True if code is executed inside jupyter session even while being imported."
     shell = get_ipython()
     if shell.__class__.__name__ in ("ZMQInteractiveShell","Shell"):
         return True # Verify Jupyter and Colab
     else:
         return False
     
def inside_jupyter_notebook(func):
    "Returns True only if a func is called inside notebook."
    shell = get_ipython()
    current_code = getattr(shell,'get_parent', lambda: {})().get('content',{}).get('code','')
    if getattr(func,'__name__') in current_code:
        return is_jupyter_session()
    return False

def get_notebook_dir():
    if is_jupyter_session() and (shell := get_ipython()):
        return Path(shell.starting_dir).absolute()
    else:
        raise RuntimeError("Not in a Notebook!")
    

def get_child_dir(name, *names, create = False):
    "Returns a child directory inside notebook directory with given name and names in order, if not exist, create one if create=True"
    notebook_dir = get_notebook_dir()
    _dir = notebook_dir.joinpath(name, *names)
    if not _dir.exists():
        if create:
            os.makedirs(_dir)
        else:
            raise FileNotFoundError(f"Directory: {_dir!r} does not exists. Use create = True to make it.")
    return _dir

def get_clips_dir():
    "Returns directory where clips are saved."
    return get_child_dir(".ipyslides-assets", "clips", create = True)

def _fmt_cols(*objs,widths = None):
    if not widths and len(objs) >= 1:
        widths = [100/len(objs) for _ in objs]
    else:
        if len(objs) != len(widths):
            raise ValueError(f'Number of columns ({len(objs)}) and widths ({len(widths)}) do not match')
        
        for w in widths:
            if not isinstance(w,(int, float)):
                raise TypeError(f'widths must be numbers, got {w}')
        widths = [w/sum(widths)*100 for w in widths]
    
    _cols = [_c if isinstance(_c,(list,tuple)) else [_c] for _c in objs] 
    _cols = ' '.join([f"""<div style='width:{w:.3f}%;overflow-x:auto;height:auto'>
                     {' '.join([htmlize(row) for row in _col])}
                     </div>""" for _col,w in zip(_cols,widths)])
    
    if len(objs) == 1:
        return _cols
    
    return f'''<div class="columns">{_cols}</div>'''

def hl(code, language="python"): # No need to have in __all__, just for markdown
    try: 
        return '<code class="highlight inline"' + re.findall(
            r'\<\s*code(.*?\<\s*\/\s*code\s*\>)', highlight(code, language).value
            )[0] # Avoid multilines, just first match in code
    except:
        return f'<code>{code}</code>' # Fallback , no need to raise errors

_example_props = {
    '.A': { # .A is repeated nowhere! But in CSS it is a lot
        'z-index': '2',
        '.B': {
            'font-size': ('24px','2em'), # fallbacks given as tuple
            '^:hover': {'opacity': '1'}, # Attach pseudo class to parent by prepending ^, or .B:hover works too
        },
        '> div': { # Direct nesting by >
            'padding': '0',
            '@media screen and (min-width: 650px)' : { # This will take above selectors inside and move itself out
                'padding': '2em',
            },
        },
        '.C p': {'font-size': '14px'},
    },
    '.D': {
        'transform': 'translate(-2px,1px)',
        '^, h1': { # caret ^ in start of key joins to parent without space
            'background': 'red',
            'span, i': { # Heavy nesting
                'color':'whitemoke',
                '@keyframes animation-name': { # This will not stay inside nesting
                    'from': {'opacity':0},
                    'to': {'opacity':1}
                },
            },
        },  
    },
}

def _filter_prints(outputs):
    new_outputs, new_prints = [], []
    for out in outputs:
        if 'text/html'in out.data and re.findall(r'class(.*)InlinePrint',out.data['text/html'], flags=re.DOTALL):
            new_prints.append(out)
        else:
            new_outputs.append(out)
    return new_outputs, new_prints

@contextmanager
def suppress_output(stdout = True):
    "Suppress output of a block of code. If `stdout` is False, only display data is suppressed."
    with capture_content() as captured:
        yield # Do not yield handle
    
    if not stdout:
        outputs = captured.outputs
        _, new_prints = _filter_prints(outputs)
        if new_prints:
            return display(*new_prints) # under slides
        elif captured.stdout:
            return print(captured.stdout) # outside slides


@contextmanager
def suppress_stdout():
    "Suppress stdout in a block of code, especially unwanted print from functions in other modules."
    with capture_content() as captured:
        yield # do not yield, we want to suppress under and outside slides
    
    outputs = captured.outputs
    new_outputs, _ = _filter_prints(outputs)
    return display(*new_outputs)

    
@contextmanager
def set_dir(path):
    "Context manager to set working directory to given path and return to previous working directory when done."
    current = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(current)

def _validate_key(key):
    "Validate key for CSS,allow only string or tuple of strings. commas are allowed only in :is(.A,#B),:has(.A,#B) etc."
    if not isinstance(key,str):
        raise TypeError(f'key should be string, got {key!r}')

    if ',' in key:
        all_matches = re.findall(r'\((.*?)\)',key,flags=re.DOTALL)
        for match in all_matches:
            key = key.replace(f'{match}',match.replace(',','$'),1)  # Make safe from splitting with comma
    return key

def _build_css(selector, data):
    "selector is tuple of string(s), data contains nested dictionaries of selectors, attributes etc."
    content = '\n' # Start with new line so style tag is above it
    children = []
    attributes = []
    
    for key, value in data.items():
        key = _validate_key(key) # Just validate key
        if isinstance(value, dict):
            children.append( (key, value) )
        elif isinstance(value, (list, tuple)): # Fallbacks
            for item in value:
                attributes.append( (key, item) )
        else: # str, int, float etc. No need to check. User is responsible for it
            attributes.append( (key, value) )
    if attributes:
        content += re.sub(r'\s+\^','', (' '.join(selector) + " {\n").lstrip()) # Join nested tags to parent if it starts with ^
        content += '\n'.join(f"\t{key} : {value};"  for key, value in attributes)  
        content += "\n}\n"

    for key, value in children:
        if key.startswith('<'): # Make it root level
            content += _build_css((key.lstrip('<'),), value)
        elif key.startswith('@media') or key.startswith('@container'): # Media query can be inside a selector and will go outside
            content += f"{key} {{\n\t"
            content += _build_css(selector, value).replace('\n','\n\t').rstrip('\t') # last tab is bad
            content += "}\n"
        elif key.startswith('@'): # Page, @keyframes etc.
            content += f"{key} {{\n\t"
            content += _build_css((), value).replace('\n','\n\t').rstrip('\t')
            content += "}\n"
        elif  key.startswith(':root'): # This is fine
            content+= _build_css((key,), value)
        else:
            old_sels = re.sub(r'\s+', ' ',' '.join(selector)).replace('\n','').split(',') # clean up whitespace
            sels = ',\n'.join([f"{s} {k}".strip() for s in old_sels for k in key.split(',')]) # Handles all kind of nested selectors
            content += _build_css((sels,), value)

    
    content = re.sub(r'\$', ',', content) # Replace $ with ,
    content = re.sub(r'\n\s+\n|\n\n','\n', content) # Remove empty lines after tab is replaced above
    content = re.sub(r'\t', '    ', content) # 4 space instead of tab is bettter option
    content = re.sub(r'\^',' ', content) # Remove left over ^ from start of main selector
        
    return content

def _styled_css(props : dict):
    if not isinstance(props, dict):
        raise TypeError("props should be a dictionay of CSS selectors and properties.")
    
    if (root_attrs:={k:v for k,v in props.items() if not isinstance(v,dict)}):
        raise ValueError(f'CSS selectors should be at top level, found properties instead! \n{root_attrs}')
    
    klass = f'{get_unique_css_class()} .SlideArea'
    if (slide := getattr(get_slides_instance(), 'this', None)):
        klass += f'.n{slide.number}' # Under slide, avoids overall CSS
    
    props = {k:v for k,v in props.items() if (isinstance(v,dict) or k.lstrip(' ^<'))} # Remove root attrs and top level access
    return XTML(f"<style>{_build_css((f'{klass}',),props)}</style>")

_css_docstring = parse("""
CSS is formatted using a `props` nested dictionary to simplify the process. 
There are few special rules in `props`:

- All nested selectors are joined with space, so hl`'.A': {'.B': ... }` becomes hl['css']`.A .B {...}` in CSS.
- A '^' in start of a selector joins to parent selector without space, so hl`'.A': {'^:hover': ...}` becomes hl['css']`.A:hover {...}` in CSS. You can also use hl`'.A:hover'` directly but it will restrict other nested keys to hover only.
- A list/tuple of values for a key in dict generates CSS fallback, so hl`'.A': {'font-size': ('20px','2em')}` becomes hl['css']`.A {font-size: 20px; font-size: 2em;}` in CSS.

Read about specificity of CSS selectors [here](https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity).
""" + f"""                      
```python
props = {json.dumps(_example_props, indent=2)}
```
Output of hl`html('style',props)`, hl`set_css(props)` etc. functions. Top selector would be different based on where it is called.
{highlight(_styled_css(_example_props).value, "css","CSS")}
""", returns=True)

def _alt_for_widget(func, widget):
    if not isinstance(widget, ipw.DOMWidget):
        raise TypeError(f'widget should be a widget, got {widget!r}')
    if not callable(func):
        raise TypeError(f'func should be a callable, got {func!r}')
    
    if (slides := get_slides_instance()):
        with slides._hold_running(): # To prevent dynamic content from being added to alt
            with capture_content() as cap:
                if not isinstance((out := func(widget)), str):
                    raise TypeError(f'Function {func.__name__!r} should return a string, got {type(out)}')
            
            if cap.stderr:
                raise RuntimeError(f'Function {func.__name__!r} raised an error: {cap.stderr}')

            if cap.outputs: # This also makes sure no dynamic content is inside alt, as nested contnet cannot be refreshed
                raise RuntimeError(f'Function {func.__name__!r} should not display or print anything in its body, it should return a string.') 
        
        _patch_display(widget)  # for completeness of display method
        setattr(widget, 'fmt_html', MethodType(func, widget)) # for export
    
    return widget 


def alt(exportable_data, obj, /, **kwargs):
    """Display `obj` for slides and output of `exportable_data` will be and displayed only in exported formats as HTML.
    `kwargs` are passed to ` clip ` when `exportable_data` is an image filename such as 'clip:test.png' to save clipboard image.
    
    - `exportable_data` should be an html str or an image file name prefixed with 'clip' e.g. 'clip:filename.png' or a callable to receive `obj` as its only argument.
        - A callable will give the latest representation of widget in exported slides and runtime representation of any other `obj`.
        - An html str, it will export the runtime representation of obj.
        - A 'clip:filename.png', will allow to take screenshot on slides for export, this may be most flexible use case.
    
    ```python
    import ipywidgets as ipw
    slides.alt(lambda w: f'<input type="range" min="{w.min}" max="{w.max}" value="{w.value}">', ipw.IntSlider()).display()
    ```

    ::: note-tip
        - hl`Slides.alt('clip:test.png', None)` is same as hl`Slides.clip('test.png', export_only=True)`.
    
    ::: note-info
        - If you happen to be using `alt` many times for same type, you can use `Slides.serializer.register` and then pass that type of widget without `alt`.
        - `ipywidgets`'s `HTML`, `Box` and `Output` widgets and their subclasses directly give html representation if used inside `write` command.
    """
    if not any([callable(exportable_data), isinstance(exportable_data, str)]):
        raise TypeError(f"first arguemnt of alt should be a func (func(obj) -> html str) or html str or an image filename prefixed with 'clip:', got {type(exportable_data)}")
    
    if isinstance(obj, ipw.DOMWidget) and callable(exportable_data):
        return _alt_for_widget(exportable_data, obj)
    
    text_html = exportable_data # default
    if callable(exportable_data):
        text_html = exportable_data(obj)
        if not isinstance(text_html, str):
            raise TypeError(f'First argument, if a function, should return a str, got {type(text_html)}')
    
    if text_html.startswith('clip:'):
        c = clip(text_html[5:], export_only=True,**kwargs)
        c._display_only_obj = obj 
        return c

    return frozen(obj, metadata={'skip-export':'', 'text/html': text_html}) # skip original obj

def _test_ext_and_parent(filename):
    p = Path(filename)
    if str(p.parent) != '.':
        raise ValueError('filename should not have parents. It will be stored in `Slides.clips_dir`.')
    if not p.suffix.lower() in ('.png','.jpeg','.jpg'):
        raise ValueError(f'filename should have an image extension .png, .jpg or .jpeg, got {p.suffix!r}')


class clip(CustomDisplay):
    """Save image from clipboard to file with a given quality when you paste in given area on slides.
    Pasting UI is automatically enabled and can be disabled in settings panel.
    On next run, it loads from saved file under `Slides.clips_dir`. 

    If `obj` is given (any object), that is directly shown on slides without any parsing and pasted image is exported.
    If no `obj` is passed, both slides and exported HTML shares same image view.

    On each paste, existing image is overwritten and stays persistent for later use. You can use these clips
    in other places with hl`Slides.image("clip:filename")` as well.

    ::: note-tip
        hl`Slides.alt('clip:test.png', obj)` is same as hl`display(obj);Slides.clip('test.png', export_only=True)`.

    ::: not-info
        If you have an HTML serialization function for a widget, pass it directly to `write` or use hl`alt(func, widget)` instead. 
        That will save you the hassel of copy pasting screenshots. `ipywidgets`'s `HTML`, `Box` and `Output` widgets and their subclasses directly give
        html representation if used inside `write` command.
    
    **kwargs are passed to ` Slides.image ` function.

    On Linux, you need alert` xclip ` or alert`wl-paste` installed.
    """
    def __init__(self, filename, export_only = False, quality =95, **kwargs):
        if isinstance(filename, Path):
            filename = str(filename)

        _test_ext_and_parent(filename)
        self._fname = filename
        self._quality = quality
        self._kws = {"width": "100%", **kwargs} # fit full by default
        self._paste = ipw.Button(icon="paste", description="Paste clipboard image", layout={"width":"max-content"})
        self._owp = ipw.Button(icon="download", description="Overwrite", layout={"width":"max-content"}).add_class("danger")
        self._upload = ipw.Button(icon="upload", description="Upload existing image", layout={"width":"max-content"})
        
        for btn in [self._paste, self._owp, self._upload]:
            btn.on_click(self._paste_clip)
        
        self._rep = html("div", 
            alert(f"{filename!r} in `Slides.clips_dir` will receive a clipboard image. Image's visual width on screen equal to width of this box would fit best.").value, 
        ).as_widget().add_class("clipboard-image").add_class("export-only" if export_only else "")
        
        with suppress(FileNotFoundError):
            self._rep.value = image(f"clip:{self._fname}", **self._kws).value # previous data to be persistent

    def display(self):
        if getattr(self, '_display_only_obj', None) is not None: # Will be added from alt
            display(self._display_only_obj, metadata = {"skip-export":"This was abondoned by alt function to export!"})
        display(ipw.VBox([ipw.GridBox([self._paste, self._owp, self._upload]).add_class('paste-btns'), self._rep]).add_class("paste-box"))

    def _paste_clip(self, btn):
        try:
            if btn is self._paste:
                if (get_clips_dir() / self._fname).is_file():
                    raise FileExistsError(f"File {self._fname!r} already exists! Click Overwrite button to update image file, can't be undone!")
                else:
                    _save_clipboard_image(self._fname, quality= self._quality, overwrite=False)
            elif btn is self._owp:
                _save_clipboard_image(self._fname, quality= self._quality, overwrite=True)
            # In all cases, finally update
            self._rep.value = image(f"clip:{self._fname}", **self._kws).value
        except:
            ename = 'FileUploadError' if btn is self._upload else 'ClipboardPasteError'
            e, text = traceback.format_exc(limit=0).split(':',1) # only get last error for notification
            self._rep.value = f"{error(ename,'something went wrong')}<br/><br/>{error(e,text)}"
    
    def to_pil(self): return pilImage.open(get_clips_dir() / self._fname)
    def to_numpy(self): return IMG.to_numpy(self)

        
def details(str_html,summary='Click to show content'):
    "Show/Hide Content in collapsed html."
    return XTML(f"""<details style='max-height:100%;overflow:auto;'><summary>{summary}</summary>{str_html}</details>""")

def _check_pil_image(data):
    "Check if data is a PIL Image or numpy array"
    if data.__repr__().startswith('<PIL'):
        im_bytes = BytesIO()
        data.save(im_bytes,data.format if data.format else 'PNG',quality=95) #Save image to BytesIO in format of given image
        return im_bytes.getvalue()
    return data # if not return back data

_fig_style_inline = "margin-block:0.25em;margin-inline:0.25em" # its 40px by defualt, ruins space, not working in CSS outside

def _verify_css_props(css_props):
    if not isinstance(css_props, dict):
        raise TypeError(f'css_props should be a dictionary of CSS properties, got {type(css_props)}')

def _verify_bbox(bbox):
    if not isinstance(bbox, (tuple, list)):
        raise TypeError(f"Bounding box should be a tuple or list, got {type(bbox)}")
    if len(bbox) != 4:
        raise ValueError(f"Bounding box should have 4 values [left, top, right, bottom], got {len(bbox)}")
    for b in bbox:
        if not isinstance(b,(int,float)) or b < 0 or b > 1:
            raise ValueError(f"Bounding box values should be between 0 and 1, got {b}")

def _crop_image(image, bbox):
    _verify_bbox(bbox)
    w,h = image.size
    bbox = [int(round(b*x,0)) for b,x in zip(bbox, [w,h,w,h])] # Convert to pixel values to nearest integer
    return image.crop(bbox)

    
def image(data=None,width='95%',caption=None, crop = None, css_props={}, **kwargs):
    """Displays PNG/JPEG files or image data etc, `kwrags` are passed to IPython.display.Image. 
    `crop` is a tuple of (left, top, right, bottom) in percentage of image size to crop the image.
    `css_props` are applied to `figure` element, so you can control top layout and nested img tag.
    You can provide following to `data` parameter:
        
    - An opened PIL image. Useful for image operations and then direct writing to slides. 
    - A file path to image file.
    - A url to image file.
    - A str/bytes object containing image data.  
    - A str like "clip:image.png" will load an image saved using `Slides.clip('image.png')`. 

    **Returns** an `IMG` object which can be exported to other formats (if possible):

    - hl`IMG.to_pil()` returns hl` PIL.Image ` or None.
    - hl`IMG.to_numpy()` returns image data as numpy array for use in plotting libraries or None.
    """
    if crop:
        try:
            im = _crop_image(image(data).to_pil(), crop) # Don't use Image.open here, this works for embeded data too
            return image(im, width=width, caption=caption,crop=None, css_props=css_props, **kwargs)
        except Exception as e:
            raise ValueError(f"Error in cropping image: {e}")

    if isinstance(width,int):
        width = f'{width}px'
    
    if isinstance(data, str) and data.startswith("clip:"):
        data = get_clips_dir() / data[5:] # strip clip by index, don't strip other characters
        if not data.exists():
            raise FileNotFoundError(f"File: {data!r} does not exist!")
    
    _data = _check_pil_image(data) #Check if data is a PIL Image or return data
    data, metadata = Image(data = _data,**kwargs)._repr_mimebundle_()
    metadata['width'] = width
    metadata['caption'] = _fig_caption(caption)
    metadata['attrs'] = f'class="zoom-child fig-{id(data)}" style="{_fig_style_inline}"'

    _verify_css_props(css_props)
    if css_props:
        metadata["style"] = _styled_css({f'.fig-{id(data)}': css_props}).value
    return IMG({k:v for k,v in data.items() if k.startswith('image')}, metadata)

def _crop_svg(node, bbox):
    _verify_bbox(bbox) # left, top, right, bottom in 0-1 range

    def crop_viewbox(m):
        vb, *_ = m.groups() # viewbox value
        x,y,w,h = [float(v) for v in vb.split()]

        X, Y = bbox[0]*w + x, bbox[1]*h + y # offset by original viewbox
        W, H = (bbox[2] - bbox[0])*w, (bbox[3] - bbox[1])*h
        return m.group().replace(vb, f'{X} {Y} {W} {H}') # Replace viewbox with new values
    
    return re.sub(r'viewBox\=[\"\'](.*?)[\"\']', crop_viewbox, node ,1, flags=re.DOTALL)
    

def svg(data=None,width = None,caption=None, crop=None, css_props={}, **kwargs):
    """Display svg file or svg string/bytes with additional customizations. 
    `crop` is a tuple of (left, top, right, bottom) in percentage of image size to crop the image.
    `css_props` are applied to `figure` element, so you can control top layout and nested svg tag.
    `kwrags` are passed to IPython.display.SVG. You can provide url/string/bytes/filepath for svg.
    """
    svg = SVG(data=data, **kwargs)._repr_svg_()
    node = rnode = re.search(r'\<svg.*?\>', svg, flags=re.DOTALL).group() #  rnode will be overwritten
    
    if width is None: # Infer width from svg or use default width
        width, *_ = re.findall(r'\s+width\=[\"\'](.*?)[\"\']', node, flags=re.DOTALL) or ['95%'] 

    w = f'{width}px' if isinstance(width,(int,float)) else width
    
    if node:
        _height = ' height="auto"' if re.search(r'\s+width\=[\"\'].*?[\"\']', node) else f' height="auto" width="{w}"' # if no width given add that too
        rnode = re.sub(r'\s+height\=[\"\'](.*?)[\"\']', _height, node,1,flags=re.DOTALL) 
        _width = f' width="{w}"' if re.search(r'\s+height\=[\"\'].*?[\"\']', node) else f' width="{w}" height="auto"' # if no height given add that too
        rnode = re.sub(r'\s+width\=[\"\'](.*?)[\"\']', _width, rnode,1,flags=re.DOTALL) # Replace width with given width

    if crop and node:
        try:
            rnode = _crop_svg(rnode, crop)
        except Exception as e:
            raise ValueError(f"Error in cropping svg: {e}")

    _verify_css_props(css_props)
    if re.search(r'\s+width\=[\"\'].*?[\"\']|\s+height\=[\"\'].*?[\"\']', node): # Add height and width to svg tag if none present inline
        css_props['svg'] = {**css_props.get('svg',{}), 'height':'auto', 'width':w} 
    
    svg = svg.replace(node, rnode) # Replace node with rnode
    fig = html('figure', svg + _fig_caption(caption), css_class=f'zoom-child fig-{id(svg)}', style=_fig_style_inline).value
    
    if css_props:
        fig += _styled_css({f'.fig-{id(svg)}': css_props}).value
    return XTML(fig) 


def iframe(src, width='100%',height='auto',**kwargs):
    "Display `src` in an iframe. `kwrags` are passed to IPython.display.IFrame"
    f = IFrame(src,width,height, **kwargs)
    return XTML(f._repr_html_())

_patch_display = lambda obj: setattr(obj, 'display', MethodType(XTML.display, obj)) # to be consistent with output displayable

def styled(obj, css_class=None, **css_props):
    """Add a class to a given object, whether a widget or html/IPYthon object.
    CSS inline style properties should be given with names including '-' replaced with '_' but values should not.
    Only a subset of inline properties take effect if obj is a widget.

    ::: note-tip
        Objects other than widgets will be wrapped in a 'div' tag. Use `html` function if you need more flexibility.
    """
    klass = css_class if isinstance(css_class, str) else ''

    if isinstance(obj,ipw.DOMWidget):
        if hasattr(obj, 'layout'):
            kwargs = {k.replace('_','-'):v for k,v in css_props.items()}
            for k,v in kwargs.items():
                setattr(obj.layout, k, v)
        _patch_display(obj)
        return obj.add_class(klass)
    elif isinstance(obj, (str, bytes)):
        return XTML(f'<div class="{klass}" {_inline_style(css_props)}>{parse(obj, True)}</div>')
    else:
        return XTML(f'<div class="{klass}" {_inline_style(css_props)}>{htmlize(obj)}</div>')
    
def zoomable(obj):
    "Wraps a given obj in a parent with 'zoom-child' class or add 'zoom-self' to widget, whether a widget or html/IPYthon object"
    if isinstance(obj,ipw.DOMWidget):
        _patch_display(obj)
        return obj.add_class('zoom-self')
    else:
        return styled(obj, 'zoom-child')

def center(obj):
    "Align a given object at center horizontally, whether a widget or html/IPYthon object"
    if isinstance(obj,ipw.DOMWidget):
        out = ipw.Box([obj]).add_class('align-center') # needs to wrap in another for cenering
        _patch_display(out)
        return out
    else:
        return XTML(f'<div class="align-center">{htmlize(obj)}</div>')
    
def html(tag, children = None,css_class = None,**node_attrs):
    """Returns html node with given children and node attributes like style, id etc. If an ttribute needs '-' in its name, replace it with '_'.     
    `tag` can be any valid html tag name. A `tag` that ends with `/` will be self closing e.g. `hr/` will be `<hr/>`.  Empty tag gives unwrapped children.
    `children` expects:
    
    - If None, returns node such as 'image' -> <img alt='Image'></img> and 'image/' -> <img alt='Image' />
    - str: A string to be added as node's text content.
    - list/tuple of [objects]: A list of objects that will be parsed and added as child nodes. Widgets are not supported.
    - dict if tag is 'style', this will only be exported to HTML if called under slide builder, use hl`slides[number,].set_css` otherwise. See `Slides.css_syntax` to learn about requirements of styles in dict.
    
    Example:
    ```python
    html('img',src='ir_uv.jpg') #Returns IPython.display.HTML("<img src='ir_uv.jpg'></img>") and displas image if last line in notebook's cell.
    ```
    
    ::: note-tip 
        To keep an image persistently embeded, use `ipyslides.utils.imge` function instead of just an html tag.
    """
    if not isinstance(tag, str):
        raise TypeError('tag should be a string of html tags or empty string!')
    
    tag = tag.strip() # clean up
    
    if tag in ['hr', 'hr/']: 
        return XTML(f'<hr/>') # Special case for hr
    
    if children and tag.endswith('/'):
        raise RuntimeError(f'Parametr `children` should be None for self closing tag {tag!r}')
    
    if tag == 'style':
        if isinstance(children, dict):
            return _styled_css(children)
        elif isinstance(children, str): # This is need internally, no need to tell in docs/error
            return XTML(f"<style>{children}</style>")
        else:
            raise TypeError(f"'style' tag requires dict with CSS, got {type(children)}")
    
    node_attrs = {k.replace('_','-'):v for k,v in node_attrs.items()}
    attrs = ' '.join(_inline_style(v) if ('style' in k and isinstance(v, dict)) else f'{k}="{v}"' for k,v in node_attrs.items()) # Join with space is must
    if css_class:
        attrs = f'class="{css_class}" {attrs}'
    
    if tag.endswith('/'): # Self closing tag
        return XTML(f'<{tag[:-1]} {attrs} />' if attrs else f'<{tag[:-1]}/>')
    
    if children is None:
        content = ''
    elif isinstance(children,str):
        content = children
    elif isinstance(children,(list,tuple)):
        content = '\n'.join(htmlize(child) for child in children) # Convert to html nodes in sequence of rows
    else:
        raise TypeError(f'Children should be a list/tuple (or dict for style tag) of objects or str, not {type(children)}')
    
    if not tag: # empty tag.
        return XTML(content) # don't wrap in any node
        
    tag_in =  f'<{tag} {attrs}>' if attrs else f'<{tag}>' # space is must after tag, strip attrs spaces
    return XTML(f'{tag_in}{content}</{tag}>')

def as_html(obj):
    "Convert supported (almost any) obj to html format."
    return XTML(htmlize(obj))

def vspace(em = 1):
    "Returns html node with given height in `em`."
    return html('span',style=f'height:{em}em;display:inline-block;') # span with inline display can be used inside <p>

def hspace(em = 1):
    "Returns html node with given height in `em`."
    return html('span',style=f'width:{em}em;display:inline-block;') # span with inline display can be used inside <p>

def line(length=5, color='var(--fg1-color)',width=1,style='solid'):
    """Returns a horizontal line with given length in em and color. `width` is the thickness of line."""
    return f"<span style='display:inline-block;border-bottom:{width}px {style} {color};width:{length}em;max-width:100%;'></span>"

def textbox(text, **css_props):
    """Formats text in a box for writing e.g. inline refrences. `css_props` are applied to box and `-` should be `_` like `font-size` -> `font_size`. 
    `text` is not parsed to general markdown i.e. only bold italic etc. applied, so if need markdown, parse it to html before. You can have common CSS for all textboxes using class `text-box`."""
    css_props = {'display':'inline-block','white-space': 'pre', **css_props} # very important to apply text styles in order
    return XTML(f'<span class="text-box" {_inline_style(css_props)}>{text}</span>')  # markdown="span" will avoid inner parsing

def alert(text):
    "Alerts text!"
    return XTML(f"<span style='color:#DC143C;'>{text}</span>")
    
def color(text,fg='blue',bg=None):
    "Colors text, `fg` and `bg` should be valid CSS colors"
    return XTML(f"<span style='background:{bg};color:{fg};padding: 0.1em;border-radius:0.1em;'>{text}</span>")

def rows(*objs):
    "Creates single compact object instead of publishing multiple display data. Create grid using `cols` as children."
    return XTML(_fmt_cols(objs))

def cols(*objs,widths=None):
    "Returns HTML containing multiple columns of given widths. This alongwith `rows` can create grid."
    return XTML(_fmt_cols(*objs,widths=widths))

def table(data, widths=None):
    "Creates a table of given data like DataFrame, but with rich elements. `data` should be a list of lists or tuples."
    return html('div', [cols(*d, widths=widths) for d in data],css_class='grid-table')

def _block(*objs, widths = None, suffix = ''): # suffix is for block-{suffix} class
    if len(objs) == 0:
        return # Nothing
    
    if suffix and suffix not in 'red green blue yellow cyan magenta gray'.split():
        raise ValueError(f'Invalid suffix {suffix!r}, should be one of [red, green, blue, yellow, cyan, magenta, gray]')
    
    if len(objs) == 1:
        out = _Output().add_class('block' + (f'-{suffix}' if suffix else '')) # _Output for adding cite etc.
        with out:
            Writer(*objs)
        display(out, metadata = {'UPDATE', out._model_id}) # For auto refresh
    else:
        Writer(*objs,widths = widths).add_class('block' + (f'-{suffix}' if suffix else '')) # Displayed

    
def block(*objs, widths = None): 
    """
    Format a block like in LATEX beamer with `objs` in columns and immediately display it. Format rows by given an obj as list of objects.   
    ::: block
        - Block is automatically displayed and returns nothing.
        - Available functions include: `block_<red,green,blue,yellow,cyan,magenta,gray>`.
        - You can create blocks just by CSS classes in markdown as {.block}, {.block-red}, {.block-green}, etc.
        - See documentation of `write` command for details of `objs` and `widths`.
    """
    return _block(*objs, widths = widths)  

def block_red(*objs, widths = None): return _block(*objs, widths = widths, suffix = 'red')
def block_blue(*objs, widths = None): return _block(*objs, widths = widths, suffix = 'blue')
def block_green(*objs, widths = None): return _block(*objs, widths = widths, suffix = 'green')
def block_yellow(*objs, widths = None): return _block(*objs, widths = widths, suffix = 'yellow')
def block_cyan(*objs, widths = None): return _block(*objs, widths = widths, suffix = 'cyan')
def block_magenta(*objs, widths = None): return _block(*objs, widths = widths, suffix = 'magenta')

def sig(callable,prepend_str = None):
    "Returns signature of a callable. You can prepend a class/module name."
    try:
        _sig = f'<b>{callable.__name__}</b>'
        if prepend_str: 
            _sig = f'{prepend_str}.{_sig}' 
        _sig = f'<span class="sig">{_sig}</span>' + hl(str(inspect.signature(callable)))
        return XTML(_sig)
    except:
        raise TypeError(f'Object {callable} is not a callable')


def doc(obj,prepend_str = None, members = None, itself = True):
    "Returns documentation of an `obj`. You can prepend a class/module name. members is True/List of attributes to show doc of."
    if obj is None:
        return XTML('') # Must be XTML to work on memebers
    
    _doc, _sig, _full_doc = '', '', ''
    if itself == True:
        with suppress(BaseException): # if not __doc__, go forwards
            _doc += htmlize(inspect.getdoc(obj) or '')

        with suppress(BaseException): # This allows to get docs of module without signature
            _sig = sig(obj,prepend_str)
    
    # If above fails, try to get name of module/object
    _name = obj.__name__ if hasattr(obj,'__name__') else type(obj).__name__
    if _name == 'property':
        _name = obj.fget.__name__
        
    
    if _name.startswith('_'): # Remove private attributes
        return XTML('') # Must be XTML to work on memebers
        
    _pstr = f'{str(prepend_str) + "." if prepend_str else ""}{_name}'
    _name = ".".join([f"<b>{n}</b>" if i == 0 else n for i, n in enumerate(_pstr.split(".")[::-1])][::-1])
    _sig = _sig or f'<span class="sig">{_name}</span>' # Picks previous signature if exists
    _full_doc = f"<div class='docs'>{_sig}<br>{_doc}\n</div>" if itself == True else ''
    _pstr = (prepend_str or _pstr) if itself == False else _pstr # Prefer given string if itself is not to doc
    
    _mems = []
    if members == True:
        if hasattr(obj,'__all__'):
            _mems = [getattr(obj, a, None) for a in obj.__all__]
        else: # if no __all__, show all public members
            for attr in [getattr(obj, d) for d in dir(obj) if not d.startswith('_')]:
                if inspect.ismodule(obj): # Restrict imported items in docs
                    if hasattr(attr, '__module__')  and attr.__module__ == obj.__name__:
                        _mems.append(attr) 
                elif inspect.isclass(obj):
                    if inspect.ismethod(attr) or inspect.isfunction(attr) or type(attr).__name__ == 'property':
                        _mems.append(attr)
                else:
                    with suppress(BaseException):
                        if attr.__module__ == obj.__module__: # Most useful
                            _mems.append(attr)
                
    elif isinstance(members, (list, tuple, set)):
        for attr in members:
            if not hasattr(obj,attr):
                raise AttributeError(f'Object {obj} does not have attribute {attr!r}')
            else:
                _mems.append(getattr(obj,attr))
    
    # Collect docs of members
    for attr in _mems:
        with suppress(BaseException):
            _class_members = inspect.ismodule(obj) and (inspect.isclass(attr) and (attr.__module__ == obj.__name__)) # Restrict imported classes in docs
            _full_doc += doc(attr, prepend_str = _pstr, members = _class_members, itself = True).value
    
    return XTML(_full_doc)

def today(fmt = '%b %d, %Y',fg = 'inherit'): # Should be inherit color for markdown flow
    "Returns today's date in given format."
    return color(datetime.datetime.now().strftime(fmt),fg=fg, bg = None)

def sub(text):
    return html('sub',text,style="font-size:85%;color:inherit;")

def sup(text):
    return html('sup',text,style="font-size:85%;color:inherit;")

def bullets(iterable, ordered = False,marker = None, css_class = None):
    """A powerful bullet list. `iterable` could be list of anything that you can pass to `write` command.    
    `marker` could be a unicode charcter or string, only effects unordered list.
    """
    _bullets = []
    for it in iterable:
        start = f'<li style="list-style-type:\'{marker} \';">' if (marker and not ordered) else '<li>'
        _bullets.append(f'{start}{_fmt_cols(it)}</li>')
    return html('div',children=[html('ol' if ordered else 'ul',_bullets, style='')],css_class = css_class) # Don't use style, it will remove effect of css_class

def _save_clipboard_image(filename, quality = 95, overwrite = False):
    _test_ext_and_parent(filename)
    path = get_clips_dir() / filename
    if overwrite or (not path.is_file()):
        im = ImageGrab.grabclipboard()
        if isinstance(im,pilImage.Image):
            im.save(path, format= im.format,quality = quality)
            im.close() # Close image to save mememory
        else:
            raise ValueError('No image on clipboard/file or not supported format.')