_attrs = ['AnimationSlider', 'JupyTimer', 'ListWidget', 'alt', 'alert', 'as_html', 'as_html_widget', 'bullets', 'color', 'error', 'table', 'suppress_output','suppress_stdout','capture_content',
    'details', 'set_dir', 'textbox', 'code', 'hspace', 'vspace', 'center', 'image', 'svg','iframe','frozen', 'raw', 
    'zoomable','html', 'sig','stack', 'styled', 'doc','today','get_child_dir','get_notebook_dir','is_jupyter_session','inside_jupyter_notebook']

__all__ = sorted(_attrs)

import os, re, json, textwrap
import datetime
import inspect
import traceback

from collections.abc import Iterable
from types import MethodType
from pathlib import Path
from io import BytesIO # For PIL image
from contextlib import contextmanager, suppress
from PIL import Image as pilImage, ImageGrab

from IPython import get_ipython
from IPython.display import SVG, IFrame
from IPython.display import Image, display
from dashlab.widgets import AnimationSlider, JupyTimer, ListWidget # For export
from dashlab.utils import _build_css # This is very light weight and too important dependency

from .formatters import ipw, XTML, IMG, frozen, get_slides_instance, _inline_style, htmlize, _fig_caption
from .xmd import get_unique_css_class, capture_content, raw, error 
from .source import code

def is_jupyter_session():
     "Return True if code is executed inside jupyter session even while being imported."
     shell = get_ipython()
     if shell and hasattr(shell,'kernel'): # kernel is not there in ipython terminal
         return True # Verifies Jupyter, Pyodide, etc.
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

_example_props = {
    '.A': { # .A is repeated nowhere! But in CSS it is a lot
        'z-index': '2',
        '.B': {
            'font-size': ('24px','2em'), # fallbacks given as tuple
            '^:hover': {'opacity': '1'}, # Attach pseudo class to parent by prepending ^, or .B:hover works too
        },
        '> h1': { # Direct nesting by >
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

_css_docstring = htmlize(textwrap.dedent(_build_css.__doc__) + f"""                      
```python
props = {json.dumps(_example_props, indent=2)}
```
Output of code`html('style',props)`, code`set_css(props)` etc. functions. Top selector would be different based on where it is called.
""") + code(_styled_css(_example_props).value, "css","CSS").value

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


def alt(exportable_data, obj):
    """Display `obj` for slides and output of `exportable_data` will be and displayed only in exported formats as HTML.
    
    - `exportable_data` should be an html str or a callable to receive `obj` as its only argument.
        - A callable will give the latest representation of widget in exported slides and runtime representation of any other `obj`.
        - An html str, it will export the runtime representation of obj.

    ```python
    import ipywidgets as ipw
    slides.alt(lambda w: f'<input type="range" min="{w.min}" max="{w.max}" value="{w.value}">', ipw.IntSlider()).display()
    ```

    ::: note-info
        - If you happen to be using `alt` many times for same type, you can use `Slides.serializer.register` and then pass that type of widget without `alt`.
        - `ipywidgets`'s `HTML`, `Box` and `Output` widgets and their subclasses directly give html representation if used inside `write` command.
    """
    if not any([callable(exportable_data), isinstance(exportable_data, str)]):
        raise TypeError(f"first arguemnt of alt should be a func (func(obj) → html str) or html str, got {type(exportable_data)}")
    
    if isinstance(obj, ipw.DOMWidget) and callable(exportable_data):
        return _alt_for_widget(exportable_data, obj)
    
    text_html = exportable_data # default
    if callable(exportable_data):
        text_html = exportable_data(obj)
        if not isinstance(text_html, str):
            raise TypeError(f'First argument, if a function, should return a str, got {type(text_html)}')

    return frozen(obj, metadata={'skip-export':'', 'text/html': text_html}) # skip original obj

def _test_ext_and_parent(filename):
    p = Path(filename)
    if str(p.parent) != '.':
        raise ValueError('filename should not have parents. It will be stored in `Slides.clips_dir`.')
    if not p.suffix.lower() in ('.png','.jpeg','.jpg'):
        raise ValueError(f'filename should have an image extension .png, .jpg or .jpeg, got {p.suffix!r}')


def _clipbox_children():
    """Returns widgets for saving clipboard images as a list of children widgets."""
    fname = ipw.Text(description="File")
    paste = ipw.Button(icon="paste", description="Paste", layout={"width": "max-content"})
    owp = ipw.Button(icon="download", description="Overwrite", layout={"width": "max-content"}, button_style='danger')
    upload = ipw.Button(icon="upload", description="Preview Saved Image", layout={"width": "max-content", "margin": "0 0 0 var(--jp-widgets-inline-label-width)"})

    rep = html("span", 
        "For best fit, ensure that visual width of screenshot is same as width of area/column on slides where image will be displayed."
        "<br>On Linux, you need xclip or wl-paste installed"
    ).as_widget()
    rep.layout = {"height": "calc(100% - 80px)", "overflow": "auto","border_top":"1px solid #8988","padding":"8px 0"}

    def paste_clip(btn):
        try:
            if btn is paste:
                if (get_clips_dir() / fname.value).is_file():
                    raise FileExistsError(f"File {fname.value!r} already exists! Click Overwrite button to update image file, can't be undone!")
                else:
                    _save_clipboard_image(fname.value, overwrite=False)
            elif btn is owp:
                _save_clipboard_image(fname.value, overwrite=True)
            # In all cases, finally update
            rep.value = image(f"clip:{fname.value}", width="100%").value
        except:
            ename = 'FileUploadError' if btn is upload else 'ClipboardPasteError'
            e, text = traceback.format_exc(limit=0).split(':', 1)
            rep.value = f"{error(ename, 'something went wrong')}\n{error(e, text)}"

    for btn in [paste, owp, upload]:
        btn.on_click(paste_clip)
    fname.on_submit(lambda change: paste_clip(paste))

    def match_glob(change):
        rep.value = "Matching files in <code>Slides.clips_dir</code>:<br>" + html('code', ', '.join(
                map(lambda path: f"{path.parts[-1]!r}", get_clips_dir().glob(f"{fname.value}*"))
            )).value
    fname.observe(match_glob, names='value')

    children = [
        ipw.HTML('<b>Save Image from Clipboard</b>'),
        fname,
        ipw.HBox([paste, owp],
            layout=ipw.Layout(margin="0 0 0 var(--jp-widgets-inline-label-width)", min_height="28px",)
        ),
        upload,
        rep
    ]
    return children

def details(obj,summary='Click to show content'):
    "Show/Hide Content in collapsed html."
    return XTML(f"""<details style='max-height:100%;overflow:auto;'><summary>{summary}</summary>{htmlize(obj)}</details>""")

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
    - A str like "clip:image.png" will load an image saved in clips directory. 
    - A filename like "image.png" will look for the file in current directory and then in `Slides.clips_dir` if not found.
        Use 'clip:image.png' to pick image from `Slides.clips_dir` directly if another file 'image.png' also exists in current directory.

    **Returns** an `IMG` object which can be exported to other formats (if possible):

    - code`IMG.to_pil()` returns code` PIL.Image ` or None.
    - code`IMG.to_numpy()` returns image data as numpy array for use in plotting libraries or None.
    """
    if crop:
        try:
            im = _crop_image(image(data).to_pil(), crop) # Don't use Image.open here, this works for embeded data too
            return image(im, width=width, caption=caption,crop=None, css_props=css_props, **kwargs)
        except Exception as e:
            raise ValueError(f"Error in cropping image: {e}")

    if isinstance(width,int):
        width = f'{width}px'
    
    if isinstance(data, (str,Path)):
        fname = str(data) # Convert Path to str
        if fname.startswith("clip:"):
            data = get_clips_dir() / fname[5:] # strip clip by index, don't strip other characters
            if not data.exists():
                raise FileNotFoundError(f"File: {data!r} does not exist!")
        else:
            cwd_file = Path(fname) # Assumes data is a file path
            if not cwd_file.exists() and len(cwd_file.parts) == 1:
                # If file is not found in current directory, check if it exists in clips dir
                cwd_file = get_clips_dir() / cwd_file
                if cwd_file.exists():
                    data = cwd_file # Use file from clips dir if exists
    
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
    `tag` can be any valid html tag name. A `tag` that ends with ` / ` will be self closing e.g. ` hr/ ` will be `<hr/>`.  Empty tag gives unwrapped children.
    `children` expects:
    
    - If None, returns node such as code`html('image',alt='Image')` → code['html']`<img alt='Image'></img>` and code`html('image/',alt='Image')` → code['html']`<img alt='Image' />`
    - str: A string to be added as node's text content.
    - list/tuple of [objects]: A list of objects that will be parsed and added as child nodes. Widgets are not supported.
    - dict if tag is 'style', this will only be exported to HTML if called under slide builder, use code`slides[number,].set_css` otherwise. See `Slides.css_syntax` to learn about requirements of styles in dict.
    
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

def as_html_widget(obj=''): # should be useable empty
    "Convert supported (almost any) obj to html format and return widget."
    return XTML(htmlize(obj)).as_widget()

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
    """Formats text in a box for writing e.g. inline refrences. `css_props` are applied to box and ` - ` should be ` _ ` like `font-size` → `font_size`. 
    `text` is not parsed to general markdown i.e. only bold italic etc. applied, so if need markdown, parse it to html before. You can have common CSS for all textboxes using class `text-box`."""
    css_props = {'display':'inline','white-space': 'pre-wrap', **css_props} # very important to apply text styles in order
    return XTML(f'<span class="text-box" {_inline_style(css_props)}>{text}</span>')  # markdown="span" will avoid inner parsing

def alert(text):
    "Alerts text!"
    return XTML(f"<span style='color:#DC143C;'>{text}</span>")
    
def color(text,fg='var(--accent-color, blue)',bg=None):
    "Colors text, `fg` and `bg` should be valid CSS colors"
    return XTML(f"<span style='background:{bg};color:{fg};padding: 0.1em;border-radius:0.1em;'>{text}</span>")

def stack(objs, sizes=None, vertical=False, css_class=None, **css_props):
    """Stacks given objects in a column or row with given sizes. 
    
    - objs: list/tuple of objects or a markdown string with '||' as separator.
    - sizes: list/tuple of sizes(int, float) for each object, if not given, all objects will have equal size.
    - vertical: bool, to stack objects vertically or horizontally, default is horizontal.
    - css_class: str, to add a class to the container div.
    - css_props: dict, applied to the container div, so you can control top layout.
    """
    if isinstance(objs, str):
        objs = [v.strip() for v in objs.replace(r'\|','COL-SEP-PIPE').split('||')] # Split by pipes if given a string
    
    if not isinstance(objs, (list, tuple)):
        raise TypeError(f'objs should be a markdown string, list or tuple of objects, got {type(objs)}')
    
    kwargs = {
        'gap': '0.25em', 
        **css_props, # do not allow to override display and flex-direction, so come later
        'display': 'flex', 'flex-direction': 'column' if vertical else 'row', 
    } 
    if sizes is not None:
        if not isinstance(sizes, (list, tuple)):
            raise TypeError(f'sizes should be a list or tuple of sizes, got {type(sizes)}')
        if len(sizes) != len(objs):
            raise ValueError(f'sizes should have same length as objs, got {len(sizes)} and {len(objs)}')
        for size in sizes:
            if not isinstance(size, (int, float)):
                raise TypeError(f'size should be an int or float, got {type(size)}')
        sizes = [{'flex': f'{size} 1','min-width':0} for size in sizes] # Convert to flex style dicts
    else:
        sizes = [{'flex': '1 1','min-width':0}] * len(objs) # default sizes if not given
    
    return html('div', [
        html('div', htmlize(obj).replace('COL-SEP-PIPE','|'), style=size) 
        for obj, size in zip(objs, sizes)
    ], style = kwargs, css_class=(f'{css_class or ""} {"" if vertical else "columns"}').strip()) 
    

def table(data, headers = None, widths=None):
    """Creates a table of given data like DataFrame, but with rich elements. 
    `data` should be a 2D matrix-like. `headers` is a list of column names. `widths` is a list of widths for each column.
    
    Example:
    ```python
    import pandas as pd
    df = pd.DataFrame({'A': [1,2,3], 'B': [4,5,6]})
    slides.table(df.values, headers=df.columns, widths=[1,2])

    slides.table([[1,2,3],[4,5,6]], headers=['A','B','C'], widths=[1,2,3])
    ```
    """
    klass = 'grid-table' if headers is None else 'grid-table header'

    try:
        [col for row in data for col in row] # Check if data is iterable and 2D

        if headers is not None:
            if not isinstance(headers, Iterable):
                raise TypeError(f'headers should be an iterable of colum headers or None, got {type(headers)}')
            
            data = [headers, *data] # Add headers to data

    except TypeError:
        raise TypeError("data should be 2D matrix-like")
    
    return html('div', [stack(d, sizes=widths) for d in data],css_class=klass + ' zoom-self')

def sig(callable,prepend_str = None):
    "Returns signature of a callable. You can prepend a class/module name."
    try:
        _sig = f'<b>{callable.__name__}</b>'
        if prepend_str: 
            _sig = f'{prepend_str}.{_sig}' 
        _sig = f'<span class="sig">{_sig}</span>' + code(str(inspect.signature(callable))).inline.value
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

def bullets(iterable, ordered = False,marker = None, css_class = None):
    """A powerful bullet list. `iterable` could be list of anything that you can pass to `write` command.    
    `marker` could be a unicode charcter or string, only effects unordered list.
    """
    _bullets = []
    for it in iterable:
        start = f'<li style="list-style-type:\'{marker} \';">' if (marker and not ordered) else '<li>'
        _bullets.append(f'{start}{htmlize(it)}</li>')
    return html('div',children=[html('ol' if ordered else 'ul',_bullets, style='')],css_class = css_class) # Don't use style, it will remove effect of css_class

def _save_clipboard_image(filename, quality = 95, overwrite = False):
    # quality is for jpeg only, png is lossless
    _test_ext_and_parent(filename)
    path = get_clips_dir() / filename
    if overwrite or (not path.is_file()):
        im = ImageGrab.grabclipboard()
        if isinstance(im,pilImage.Image):
            im.save(path, format= im.format,quality = quality)
            im.close() # Close image to save mememory
        else:
            raise ValueError('No image on clipboard/file or not supported format.')