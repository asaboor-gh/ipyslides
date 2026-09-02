_attrs = ['AnimationSlider', 'JupyTimer', 'ListWidget', 'alt', 'alert', 'as_html', 'as_widget', 'bullets', 'color', 'error', 'table', 'suppress_output','suppress_stdout','capture_content',
    'details', 'set_dir', 'textbox', 'code', 'fa', 'gap', 'link', 'center', 'icon', 'image', 'svg','iframe','frozen', 'raw', 'warn', 'bg',
    'focus','html', 'sig','stack', 'styled', 'steps', 'doc', 'transition', 'today','get_child_dir','get_notebook_dir','is_jupyter_session','inside_jupyter_notebook','yoffset','css','pin']

__all__ = sorted(_attrs)

import os, re, json, textwrap
import base64
import datetime
import inspect
import traceback

from itertools import chain, accumulate
from collections.abc import Iterable
from types import MethodType
from pathlib import Path
from io import BytesIO # For PIL image
from contextlib import contextmanager, suppress
from PIL import Image as pilImage, ImageGrab

from IPython import get_ipython
from IPython.display import SVG, IFrame
from IPython.display import Image, display
from dashlab.widgets import AnimationSlider, JupyTimer, ListWidget, StepSlider # For export
from dashlab.utils import _build_css, _fix_init_sig # This is very light weight and too important dependency

from ._base.icons import Icon as icon # for export and overrides in fa function
from .formatters import ipw, XTML, IMG, frozen, get_slides_instance, fix_ipy_image, _inline_style, htmlize, _fig_caption, slidebound, slidesready
from .xmd import xmd, get_unique_css_class, capture_content, raw, error, warn, _internal_xmd_call
from .source import code
from .writer import write, _style_for_widget, _fmt_html
from ._base.styles import animations, view_nodes


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

def _resolve_img(src, width):
    if src is None: return ''
    if isinstance(src, Path):
        src = str(src)  # important for svg checking below
    
    if isinstance(src, str):
        if not src.strip(): return '' # empty string
        if "<svg" in src and "</svg>" in src:
            return src.replace('<svg', f'<svg style="width:{width};height:auto" ') # extra space at end
        else:
            if src.startswith("clip:"):
                src = get_clips_dir() / src[5:] # don't strip it
            try:
                return fix_ipy_image(Image(src, width=width), width=width).value
            except:
                return _resolve_img(SVG(src)._repr_svg_(), width=width)
    return ''

_internal_xmd_call('code')(code) # Register code class for xmd usage

@_internal_xmd_call('details')
def details(obj,summary='Click to show content', name=None, opened=False, **css_props):
    "Show/Hide Content in collapsed html. Multiple details with same name in a container open exclusively to make an accordion."
    css_props = {'max-height':'100%','overflow':'auto', **css_props}
    nodeattr = f'name="{name}"' if name else ''
    isopen = 'open' if opened else ''
    return XTML(f"""<details {nodeattr} {_inline_style(css_props)} {isopen}><summary>{summary}</summary>{htmlize(obj)}</details>""")

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

@_internal_xmd_call('image')    
def image(data=None,width='95%',caption=None, crop = None, css_props={}, css_class=None, **kwargs):
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

    - [code! IMG.to_pil() /] returns [code! PIL.Image /] or None.
    - [code! IMG.to_numpy() /] returns image data as numpy array for use in plotting libraries or None.
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
    
    if css_class is None: css_class = ''
    _data = _check_pil_image(data) #Check if data is a PIL Image or return data
    data, metadata = Image(data = _data,**kwargs)._repr_mimebundle_()
    metadata['width'] = width
    metadata['caption'] = _fig_caption(caption)
    metadata['attrs'] = f'class="focus-child fig-{id(data)} {css_class}" style="{_fig_style_inline}"'

    _verify_css_props(css_props)
    if css_props:
        metadata["style"] = _styled_css({f'.fig-{id(data)}': css_props}).value
    return IMG({k:v for k,v in data.items() if k.startswith('image')}, metadata)

@_internal_xmd_call('bg', slidebound=True)
@slidebound
def bg(src=None, opacity=1, filter=None, contain=False):
    """Set background image for the current slide.

    Markdown usage: `[bg! "test.png", opacity=0.4,contain=True /]`
    """
    if isinstance(src, str) and src.strip().lower() in ('none', 'null'):
        src = None

    if not isinstance(contain, bool):
        raise TypeError(f"contain expects bool (True/False), got {type(contain).__name__}: {contain!r}")

    get_slides_instance().this._set_bg_ikws(
        src=src, opacity=opacity, filter=filter,contain=contain
    )

def _rselove_targets(applyto):
    slides = get_slides_instance()
    if applyto is None and not slides.this:
        raise ValueError("applyto cannot be None when not under a slide builder, as there is no current slide to apply to!")
    
    if applyto is None:
        return slides.this, [slides.this._specs]
    elif isinstance(applyto, str) and applyto.lower() == 'all':
        return slides._current or slides[0], [type(s._specs) for s in slides[:1]] # gloabal setup
    else:
        if isinstance(applyto, int):
            applyto = [applyto]
        selected = slides[applyto] # by indexer they created with
        if not selected:
            raise ValueError(f"No slides selected with applyto={applyto!r}")
        return selected[0], [s._specs for s  in selected] 

@_internal_xmd_call('transition')
@slidesready
def transition(name:str, applyto=None):
    """Set transition animation for the current slide or slides selected by `applyto`. 
    Under a slide builder (including markdown), if `applyto` is None, it applies to current slide, 
    if 'all', it applies to all slides, otherwise it should be index or list of indices of slides to apply animation to.
    """
    if name and not name in animations:
        raise ValueError(f"Transition {name!r} is not defined, available transitions are: {list(animations.keys())}")
    slide, spec_targets = _rselove_targets(applyto)
    for spec in spec_targets:
        spec.anim = name
    slide._view_transition()

@_internal_xmd_call('yoffset')    
@slidesready
def yoffset(value:int, applyto=None):
    """Set vertical offset for the current slide or slides selected by `applyto`. 
    Value should be an integer between 0 and 100, representing percentage of slide height.
    
    Under a slide builder (including markdown), if `applyto` is None, it applies to current slide, 
    if 'all', it applies to all slides, otherwise it should be index or list of indices of slides.
    """
    if isinstance(value, str): # from markdown
        if value.strip().isdigit(): 
            value = int(value.strip())
        else:
            value = None # gracefully handle non-integers
    
    if value and value not in range(101): # handle None itself
        raise ValueError("yoffset value should be integer in units of percent betweem [0,100]!")
        
    slide, spec_targets = _rselove_targets(applyto)
    for spec in spec_targets:
        spec.yoffset = value
    slide._mount_user_css()

@_internal_xmd_call('css')
@slidesready
def css(props: dict=None, applyto=None, **css_vars):
    """
    Set CSS on current slide being built or slides selected by `applyto`. 
    Reset by empty props and variables on slides slected by `applyto`.
    
    Under a slide builder (including markdown), if `applyto` is None, it applies to current slide, 
    if 'all', it applies to all slides, otherwise it should be index or list of indices of slides.

    ::: note-tip
        - See [code! Slides.css_syntax /] for information on how to write CSS dictionary.
        - Underscores in CSS property and variable names are replaced with dashes, so `font_size` becomes `font-size` and `my_var` becomes `--my-var`.
        - You can define global/slide level CSS animation variables like `--time`, `--delay` etc. See `Slides.css_animations` for details of various animations usage.
        - You can define custom `@keyframes` in CSS and use them with `anim-kf` class by setting `--kf-name` and optional `--kf-*` controls.
        - An empty selector `''` is allowed to directly inject CSS string, useful to read a local CSS file while files from web must be downloaded first.
          Advanced CSS concepts like `@import`, `@layer` may not work as expected due to CSS scoping inside slides. Large files should be added to `overall` CSS only for performance reasons.
        - You can set theme colors per slide. Accepted color keys are `fg1`, `fg2`, `fg3`, `bg1`, `bg2`, `bg3`, `accent` and `pointer`. These apply to current selected theme.
        - Avoid gradient colors for other than `bg1`, as it will be ignored in most places and may lead to bad styling.
    """
    if props is None: props = {} # for resetting css or independent css variables, we want to allow None as well
    if isinstance(props, str) and props.strip(): # allow empty string for no props, but not other types of empty values
        props = {'': props} # from markdown or direct css string
    
    if props and not isinstance(props, dict):
        raise TypeError(f"style props should be a dict of CSS selectors and properties or css string, got {type(props)}") 
    
    for k,v in props.items():
        sels = k.split(',') # can be multiple selectors
        for s in sels:
            if not s.strip() and len(sels) > 1: # single empty selector is allowed to directly inject CSS
                raise KeyError(f"Empty CSS selector found in a compound selector {k!r}, perhaps due to extra comma?")
            if '<' in s: # avoid extreme selector
                raise KeyError(f"Trying to access top level with selector {s!r} in {k!r} is restricted!")
    
    _colors = ['fg1', 'fg2', 'fg3', 'bg1', 'bg2', 'bg3', 'accent', 'pointer'] 
    _vars = {}      
    for k,v in css_vars.items():
        if not isinstance(v, str):
            raise TypeError(f"CSS variable values should be strings, got {type(v)} for variable {k!r}")
        key = (f'--{k}-color' if k in _colors else k).replace('_','-')
        key = f'--{key}' if not key.startswith('--') else key # allow users to pass with or without --
        _vars[key] = v
    
    slide, spec_targets = _rselove_targets(applyto)
    for spec in spec_targets:
        spec.cssprops = props
        spec.cssvars  = _vars
    
    slide._mount_user_css()
    
            
def _crop_svg(node, bbox):
    _verify_bbox(bbox) # left, top, right, bottom in 0-1 range

    def crop_viewbox(m):
        vb, *_ = m.groups() # viewbox value
        x,y,w,h = [float(v) for v in vb.split()]

        X, Y = bbox[0]*w + x, bbox[1]*h + y # offset by original viewbox
        W, H = (bbox[2] - bbox[0])*w, (bbox[3] - bbox[1])*h
        return m.group().replace(vb, f'{X} {Y} {W} {H}') # Replace viewbox with new values
    
    return re.sub(r'viewBox\=[\"\'](.*?)[\"\']', crop_viewbox, node ,1, flags=re.DOTALL)
    
@_internal_xmd_call('svg')
def svg(data=None,width = None,caption=None, crop=None, css_props={}, css_class=None, **kwargs):
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
        css_props['img'] = {**css_props.get('img',{}), 'height':'auto', 'width':w}
    css_props['img'] = {'max-width': '100%', **css_props.get('img',{})}  # prevent overflow in HTML export, user can override

    svg = svg.replace(node, rnode)
    if css_class is None: css_class = ''
    
    # We encapsulate svg in img tag to avoid issues with rendering and clipping of texts plus ids conflicts
    svg_b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    svg = f'<img src="data:image/svg+xml;base64,{svg_b64}" alt="SVG Image"/>'
    fig = html('figure', svg + _fig_caption(caption), css_class=f'focus-child fig-{id(svg)} {css_class}', style=_fig_style_inline).value
    
    if css_props:
        fig += _styled_css({f'.fig-{id(svg)}': css_props}).value
    return XTML(fig) 

@_internal_xmd_call('iframe')
def iframe(src, width='100%',height='auto',**kwargs):
    "Display `src` in an iframe. `kwrags` are passed to IPython.display.IFrame"
    f = IFrame(src,width,height, **kwargs)
    return XTML(f._repr_html_())

_patch_display = lambda obj: setattr(obj, 'display', MethodType(XTML.display, obj)) # to be consistent with output displayable

@_internal_xmd_call('styled')
def styled(obj, css_class=None, **css_props):
    """Add a class to a given object, whether a widget or html/IPYthon object.
    CSS inline style properties should be given with names including '-' replaced with '_' but values should not.
    A widget will be wrapped in a Box to apply class and styles which otherwise may not work properly for some widgets.
    If you need a styled, yet not a block level widget, use `display="inline-grid"` in `css_props`.

    ::: note-tip
        Objects other than widgets will be wrapped in a 'div' tag. Use `html` function if you need more flexibility.
    """
    klass = css_class if isinstance(css_class, str) else ''

    if isinstance(obj,ipw.DOMWidget):
        if not any([css_class, css_props]): 
            _patch_display(obj) # user expects this function might has display
            return obj # nothing to do
        # We need a box to properly handle class and props
        # Some AyWidget-based widgets struggle with class and style directly
        # While others like plotly FigureWidget has different meaning of layout
        out = ipw.Box([obj])
        if klass: [out.add_class(k) for k in klass.split()] # needs each class separately
        _patch_display(out)
        
        # Attach few inline properties, inline-grid is better for most widgets
        out.layout.padding = str(css_props.get('padding', 0)) 
        out.layout.margin = str(css_props.get('margin', 0)) 
        
        if not css_props: 
            return out
        
        style = ipw.HTML(_style_for_widget(out, **css_props))
        style.layout.position = 'absolute' # to avoid taking space
        out.children = [style, obj] # style before obj to apply first
        return out
    else:
        # Same properties in div
        css_props = {"padding": 0, "margin": 0, **css_props}
        return XTML(f'<div class="{klass}" {_inline_style(css_props)}>{htmlize(obj)}</div>')

@_internal_xmd_call('pin')
def pin(obj, x=None, y=None, width=None, height=None, center=False, zorder=0, rotate=0, blur=0, css_class=None, **css_props):
    """Pin an object at a specific position on the slide. Position is given in percentage of slide dimensions if int/float, otherwise any valid CSS unit.
    `center` will align the center of object to given coordinates instead of top left corner. `zorder` controls layering 
    of pinned objects, higher zorder means on top. `rotate` and `blur` applies CSS transform and filter to object. 
    
    `css_class` and `css_props` are applied to pinned object for further customizations.
    
    ::: note-warning
        - Beaware that pinning is contained relative to columns and containers with animation classes, use outside of any of those context to align to whole slide.
        - Use animation classes inside the pinned content, otherwise it will conflict with pin's CSS properties and may not work as expected.
    """
    # Clean up Path/Asset handling
    if isinstance(obj, (str, Path)):
        try:
            obj = _resolve_img(obj, width="100%") # Try to resolve as image first
        except:
            pass # does nothing, let object be handled below

    # Type validation with friendly messages (allowing floats for rotation/blur!)
    for name, prop in [("zorder", zorder), ("blur", blur), ("rotate", rotate)]:
        if prop and not isinstance(prop, (int, float)):
            raise TypeError(f"Parameter '{name}' must be a number, got {type(prop).__name__}")
            
    # Layering & Filter mapping
    if zorder: 
        css_props["z-index"] = int(zorder)
    if blur: 
        css_props["filter"] = f"blur({blur}px) {css_props.get('filter', '')}".strip()
    
    # Handle Transform Layering Safely
    transforms = []
    if center:
        transforms.append("translate(-50%, -50%)")
    if rotate:
        transforms.append(f"rotate({rotate}deg)")
    if transforms:
        css_props["transform"] = f"{' '.join(transforms)} {css_props.get('transform', '')}".strip()

    coords = {"left": x, "top": y, "width": width, "height": height}
    for prop, value in coords.items():
        if value is not None:
            if isinstance(value, (int, float)): 
                value = f"{value}%"
            css_props[prop] = value

    css_props["position"] = "absolute" # this is what makes it pinned
    css_class = f'ips-pinned-item {css_class}' if css_class else 'ips-pinned-item' # need some stuff
    return styled(obj, css_class=css_class, **css_props)    

@_internal_xmd_call('focus')
def focus(obj):
    "Wraps a given obj in a parent with 'focus-child' class or add 'focus-self' to widget, whether a widget or html/IPYthon object, to focus/exit on double click."
    if isinstance(obj,ipw.DOMWidget):
        _patch_display(obj)
        return obj.add_class('focus-self')
    else:
        return styled(obj, 'focus-child')

@_internal_xmd_call('center')
def center(obj):
    "Align a given object at center horizontally, whether a widget or html/IPYthon object"
    if isinstance(obj,ipw.DOMWidget):
        out = ipw.Box([obj]).add_class('align-center') # needs to wrap in another for cenering
        _patch_display(out)
        return out
    else:
        return XTML(f'<div class="align-center">{htmlize(obj)}</div>')
    
@_internal_xmd_call('link')
def link(target_uid:str, text:str="Jump to Linked Slide", icon:str=None, uid:str=None):
    r"""Create a link to jump to another slide with a unique `target_uid` either set by `[#target_uid/]` in markdown.
    
    - `uid` parameter allows you to make this link a target for other links. 
    - A pair of links with flipped `target_uid` and `uid` can be used to jump back and forth between two slides.
    - `icon` parameter allows you to add a font-awesome icon to the link.
    - This works in markdown as well. In python, you need to display (or pass to write) the output to make it work.
    """
    target_uid = target_uid.lstrip('#') # remove any leading # if present
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', target_uid):
        raise ValueError(f"target_uid should be a valid slide uid (alphanumeric, underscore, hyphen), got {target_uid!r}")
    
    kwargs = {"href": f"#{target_uid}", "css_class": "slide-link"}
    
    if uid is not None:
        uid = uid.lstrip('#') # remove any leading # if present
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', uid):
            raise ValueError(f"uid should be a valid slide uid (alphanumeric, underscore, hyphen), got {uid!r}")
        kwargs["id"] = f"{uid}"
    text = (f' <i class="fa fa-{icon}"></i>' if icon else '') + f"{text}"   
    return html('a',text,**kwargs)

_VOID_TAGS = ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr') # self closing tags
    
def html(tag, children = None,css_class = None, style=None, void_attrs=None,**node_attrs):
    """Returns html node with given children and node attributes like style, id etc. If an ttribute needs '-' in its name, replace it with '_'.     
    `tag` can be any valid html tag name. A self closing tag must not have children e.g. ` hr ` will be `<hr/>`.  Empty tag gives unwrapped children.
    
    `children` expects:
    
    - If None, returns node for self closing tags such as [code! html('image',alt='Image') /] → [code!! 'html' .. <img alt='Image'></img> /].
    - str: A string to be added as node's text content.
    - list/tuple of [objects]: A list of objects that will be parsed and added as child nodes. Widgets are not supported.
    - dict if tag is 'style', this will only be exported to HTML if called under slide builder, use [code! slides.css /] otherwise. See [code! Slides.css_syntax /] to learn about requirements of styles in dict.
    
    `void_attrs` are value-less attributes, such as `disabled`, `checked`, `open` etc. Must be a string of space separated attributes names.
    
    Example:
    ```python
    html('img',src='ir_uv.jpg') #Returns IPython.display.HTML("<img src='ir_uv.jpg'></img>") and displays image if last line in notebook's cell.
    ```
    
    ::: note-tip 
        To keep an image persistently embeded, use `ipyslides.utils.imge` function instead of just an html tag.
    """
    if not isinstance(tag, str):
        raise TypeError('tag should be a string of html tags or empty string!')
    
    tag = tag.strip() # clean up
    
    if tag in ['hr', 'hr/']: 
        return XTML(f'<hr/>') # Special case for hr
    
    if void_attrs:
        if not isinstance(void_attrs, str):
            raise TypeError(f'void_attrs should be a string of space separated attributes, got {type(void_attrs)}')
    else:
        void_attrs = ''
    
    if tag == 'style':
        if isinstance(children, dict):
            return _styled_css(children)
        elif isinstance(children, str): # This is need internally, no need to tell in docs/error
            return XTML(f"<style>\n{children}\n</style>")
        else:
            raise TypeError(f"'style' tag requires dict with CSS, got {type(children)}")
    
    node_attrs = {k.replace('_','-'):v for k,v in node_attrs.items()}
    attrs = ' '.join(f'{k}="{v}"' for k,v in node_attrs.items()) 
    
    if style is not None:
        if not isinstance(style, (str, dict)):
            raise TypeError(f"'style' attribute should be a string or dict of inline css properties, got {type(style)}")
        attrs += f' {_inline_style(style)}' if isinstance(style, dict) else f' style="{style}"'
    
    attrs += (f' {void_attrs}' if void_attrs else '') # these usually come at end
    if css_class:
        attrs = f'class="{css_class}" {attrs}'
    
    if tag in _VOID_TAGS: # Self closing tag
        if children:
            raise RuntimeError(f'Parametr `children` should be None for self closing tag {tag!r}')
        return XTML(f'<{tag} {attrs} />' if attrs else f'<{tag}/>')
    
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

def as_widget(obj=''): # should be useable empty
    "Convert supported (almost any) obj to html format and return `ipywidgets.HTML` instance. If obj is a widget, it will be returned as is."
    if isinstance(obj, ipw.DOMWidget):
        return obj
    return as_html(obj).as_widget()

# This is only intended to use for general tags in markdown, do not use in python
@_internal_xmd_call('anyTag')
def anyTag(tag, content = "", css_class = None, void_attrs=None, node_attrs=None, **css_props):
    """Picks up html tag from markdown function calls and returns html node with given text and node attributes 
    like style, id etc. If an attribute needs '-' in its name, replace it with '_'.
    
    `void_attrs` are value-less attributes, such as `disabled`, `checked`, `open` etc. Must be a string of space separated attributes names.
    
    `node_attrs` are other html node attributes like `id`, `data-*` etc. with ('_' → '-' in keys) Must be a dict of attribute name and value pairs excluding `style` which is handled separately by `css_props`. If an attribute needs '-' in its name, replace it with '_'.
    
    The markdown call syntax for registered python functions and html tags is same, see `slides.xmd.funcs` for details.
    
    If `tag` is self closing tag and content is not empty. e.g. `[img\! src="test.png" \.. test content \/]` will throw error.
    
    ```markdown   
    [details!! summary = "Open Me" ..
        This is a test content with multiple lines
        It must maintain its own indentation and line breaks
    /]
    ```
    
    You can override a registered function by pure html tag by appending ` _ ` to the tag. For example,
    ` svg_ ` will be html tag that overrides the `svg` function."""
    if not isinstance(content, str):
        raise TypeError(f"'content' should be a string, got {type(content)}. Use html() for non-string content.")
    if tag in _VOID_TAGS and content:
        raise RuntimeError(f'Parametr `content` should be empty for self closing tag {tag!r}')
    
    if node_attrs is not None:
        if not isinstance(node_attrs, dict):
            raise TypeError(f"'node_attrs' should be a dict of html node attributes or None, got {type(node_attrs)}")
        
        if 'style' in node_attrs:
            node_attrs.pop('style',None) # remove style from node_attrs if present, as it will be handled separately
            raise KeyError("'style' attribute is built from **css_props, must not be in 'node_attrs'.")
    
    # strips outer <p> tags to avoid double wrapping in <p> when used inside other tags
    return html(tag, xmd(content, True, ""), css_class=css_class, style=css_props, void_attrs=void_attrs, **(node_attrs or {}))

@_internal_xmd_call('gap')
def gap(h=1, v=1, unit = 'em'):
    r"""Returns html span node with given horizontal and vertical gap in `unit` (px, em, rem, % etc.). 
    Useful for creating space between elements in a layout. `h` is horizontal gap and `v` is vertical gap.
    Markdown usage: `[gap\! v=0.5 \/]`, `[gap\! 2, 0.5, unit="px" \/]` etc.
    """
    return html('span',style=f'width:{h}{unit};height:{v}{unit};display:inline-block;') # span with inline display can be used inside <p>

@_internal_xmd_call('line')
def line(length=5, color='var(--fg1-color)',width=1,style='solid'):
    """Returns a horizontal line with given length in em and color. `width` is the thickness of line."""
    return f"<span style='display:inline-block;border-bottom:{width}px {style} {color};width:{length}em;max-width:100%;'></span>"

@_internal_xmd_call('sup')
def sup(text, **css_props):
    "Returns superscript text with given css properties."
    return XTML(f"<sup {_inline_style(css_props)}>{xmd(text, True,'')}</sup>")

@_internal_xmd_call('sub')
def sub(text, **css_props):
    "Returns subscript text with given css properties."
    return XTML(f"<sub {_inline_style(css_props)}>{xmd(text, True,'')}</sub>")

@_internal_xmd_call('textbox')
def textbox(text, **css_props):
    """Formats text in a box for writing e.g. inline refrences. `css_props` are applied to box and ` - ` should be ` _ ` like `font-size` → `font_size`. 
    `text` is not parsed to general markdown i.e. only bold italic etc. applied, so if need markdown, parse it to html before. You can have common CSS for all textboxes using class `text-box`."""
    css_props = {'display':'inline','white-space': 'pre-wrap', **css_props} # very important to apply text styles in order
    return XTML(f'<span class="text-box" {_inline_style(css_props)}>{text}</span>')  # markdown="span" will avoid inner parsing

@_internal_xmd_call('alert')
def alert(text, css_class=None, bold=False, italic=False, **css_props):
    "Alerts text in red color. `css_props` are applied to span element."
    kws = {'color':'#DC143C', 'font-weight': 'bold' if bold else 'normal', 'font-style': 'italic' if italic else 'normal', **css_props}
    klass = f"class='{css_class}'" if css_class and isinstance(css_class, str) else ''
    return XTML(f"<span {klass} {_inline_style(kws)}>{xmd(text, True,'')}</span>")

@_internal_xmd_call('color')    
def color(text,fg='var(--accent-color, blue)',bg=None, **css_props):
    "Colors text, `fg` and `bg` should be valid CSS colors. `css_props` are applied to span element."
    style_kws = {'color': fg, 'background': bg, 'padding': '0.1em', 'border-radius':'0.1em', **css_props}
    return XTML(f"<span {_inline_style(style_kws)}>{xmd(text, True,'')}</span>")

@_internal_xmd_call('fa')
def fa(name: str, color:str = 'currentColor', size:str = '1em',rotation:int = 0, **css_props):
    """Returns FontAwesome icon as html. `name` is the icon name without 'fa-' prefix. 
    You can control `color`, `size` (like '2em', '24px'), `rotation` (0, 90, 180, 270) and other `css_props` applied to icon.
    If an icon is available through ipyslides, it takes precedence over online fontawesome icons, use `fa-` prefix in that case to avoid conflict.
    """
    if name in icon.available:
        return XTML(icon(name, color=color, size=size, rotation=rotation).value)  # use built-in icon but return same type
    
    if not name.startswith('fa-'):
        name = f'fa-{name}' # use online fontawesome icon
    style_kws = {'color': color, 'font-size': size, 'transform': f'rotate({rotation}deg)' if rotation else '', **css_props}
    return XTML(f'<i class="fa {name}" {_inline_style(style_kws)}></i>')

# Do not add this in markdown which has ::: columns.inline equivalent
def stack(objs, sizes=None, vertical=False, css_class=None, **css_props):
    """Stacks given objects in a column or row with given sizes. Markdown equivalent to `stack(..., vertical=False)` is `::: columns.inline` block.
    
    - objs: list/tuple of objects. Markdown strings in list will be parsed to html in non-display mode. 
    - sizes: list/tuple of sizes(int, float) for each object, if not given, all objects will have equal size.
    - vertical: bool, to stack objects vertically or horizontally, default is horizontal.
    - css_class: str, to add a class to the container div.
    - css_props: dict, applied to the container div, so you can control top layout.
    """
    if not isinstance(objs, (list, tuple)):
        raise TypeError(f'objs should be list or tuple of objects, got {type(objs)}')
    
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
    
# Don't try this in markdown, standard markdown table is better alongwith ::: table block
def table(data, headers = None, widths=None, css_class=None, **css_props):
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
    if isinstance(css_class, str):
        klass += f' {css_class}'

    try:
        [col for row in data for col in row] # Check if data is iterable and 2D

        if headers is not None:
            if not isinstance(headers, Iterable):
                raise TypeError(f'headers should be an iterable of colum headers or None, got {type(headers)}')
            
            data = [headers, *data] # Add headers to data

    except TypeError:
        raise TypeError("data should be 2D matrix-like")
    
    return html('div', [stack(d, sizes=widths) for d in data],css_class=klass + ' focus-self', style=css_props)

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

@_internal_xmd_call('today')
def today(fmt = '%b %d, %Y',fg = 'inherit'): # Should be inherit color for markdown flow
    "Returns today's date in given format."
    return color(datetime.datetime.now().strftime(fmt),fg=fg, bg = None)

def bullets(iterable, ordered = False, marker = None, css_class = None, **css_props):
    """A powerful bullet list. `iterable` could be list of anything that you can pass to `write` command. 
    Use `write(..., paused=True)` for frame-based incremental reveal, or `steps(...)` for slider-based step view.
    
    - If an item in iterable is a tuple/list of 2 elements and first element is a str, it will be used as per item marker.   
    - `ordered`: bool, to create ordered or unordered list.
    - `marker`: str, CSS list-style-marker property for overall list, e.g. '✅' or '🔴' etc.
    
    You can also use CSS `list-style` property in `css_props` for overall list, e.g. disc, circle, square, upper-roman etc. but it will be overridden by `marker` parameter if given.
    See [list-style](https://developer.mozilla.org/en-US/docs/Web/CSS/list-style) for marker types details.
    
    Markdown Equivalent:
    ```md-before
    ::: ul .hrules list-style="'✅'" 
        ::: li list-style="'❌'" .. First item
        ::: li data-marker=🔴 .. Second item 
        ::: li
            Third item takes default marker and is large, so made block
    ```
    """
    _bullets = []
    for it in iterable:
        start = '<li'
        if isinstance(it, (list, tuple)) and len(it) == 2 and isinstance(it[0], str):
            limkr, it = it # allow per item marker
            start += f" data-marker={limkr!r}"
        _bullets.append(f'{start}>{htmlize(it)}</li>')
    kwargs = dict(style = css_props)
    if marker is not None:
        kwargs['data-marker'] = marker
    
    return html('ol' if ordered else 'ul', children = _bullets, css_class = css_class, **kwargs) 

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

def update_class(widget, css_class:str, keep:bool):
    """Add or remove a class from a widget based on the `keep` flag. If `keep` is True, add the class(es), otherwise remove them.
    css_class should be a string with many classes separated by space.
    """
    if not isinstance(widget, ipw.DOMWidget):
        raise TypeError(f'widget should be an ipywidgets.DOMWidget, got {type(widget)}')
    if not isinstance(css_class, str):
        raise TypeError(f'css_class should be a string, got {type(css_class)}')
    
    action = widget.add_class if keep else widget.remove_class
    for cls in css_class.split():
        action(cls)

# for css_syntax
_css_info = (f"""
{textwrap.dedent(_build_css.__doc__)}

::: note-info
    In the output of [code! Slides.html('style',props) /], [code! Slides.css(props) /] etc. functions, top selector 
    would be different if it is called under slide context or not.

```columns.inline
{code('props = ' + json.dumps(_example_props, indent=2))}
--
{code(_styled_css(_example_props).value, 'css','CSS')}
```""").replace('@',r'\@') # @import etc keys to clean up for markdown


@_fix_init_sig
class steps(ipw.GridBox):
    """A stepper widget to step through given objects with a slider. `objs` should be a list/tuple of objects 
    to step through and can be any object that can be converted to a widget using `as_widget`. Multiple objects
    in a single step can be given as a nested list/tuple of objects. `dots_loc` controls 
    the location of step dots, which can be 'left', 'top', 'right' or 'bottom'. `interval` controls the time interval 
    in milliseconds for automatic stepping. `css_class` and `css_props` can be used to style the widget.
    `static_index` can be used to set a specific index to be displayed statically in PDF and HTML export, while the stepper will still function normally in the notebook.
    """
    def __init__(self, objs, dots_loc="left", interval=1500, css_class=None, static_index = -1, **css_props):
        if not isinstance(objs, (list, tuple)) or len(objs) < 2:
            raise ValueError("objs must be a list/tuple with at least two objects to step through!")
        if not dots_loc in ("left","top","right","bottom"):
            raise ValueError(f"dots_loc must be one of left, right, top, bottom, got {dots_loc!r}")
        
        self._uclass = f'output-{id(self)}' # unique class for this instance's output area
        klasses = ['ips-steps-wrapper', 'vertical'] if dots_loc in ("left","right") else ['ips-steps-wrapper']
        
        if isinstance(css_class, str):
            klasses.extend(css_class.split())
            
        key = 'grid_template_columns' if dots_loc in ("left","right") else 'grid_template_rows'
        value = '24px 1fr' if dots_loc in ("left","top") else '1fr 24px'
        super().__init__(layout={'display': 'grid', key: value}, _dom_classes=klasses)
        
        self._sidxs, outputs = self._process_objs(objs)
        
        if static_index < 0:
            static_index = len(self._sidxs) - 1 
        if static_index >= len(self._sidxs):
            raise ValueError(f"static_index must index {len(self._sidxs)} objects, got {static_index}")
        
        self._expidx = static_index
        self._viewstyle =  ipw.HTML().add_class('abs-style').add_class('jupyter-only') # will not export this style
        self._output = ipw.Output(layout={'min_width': '0'} # must have min-width in grid layout to avoid unexpected lengths
            ).add_class(self._uclass).add_class('ips-steps-output')
        self._output._exprng = self._sidxs[self._expidx] if self._sidxs else None # attach range for export
        
        with self._output:
            display(*outputs) # only clean outputs
            
        first, last = self._sidxs[self._expidx] if self._sidxs else [0, None]
        self._fixstyle = html('style', _build_css((), {
                f'.{self._uclass}': css_props, # apply user css to output
                '.ips-steps-wrapper > .abs-style': {'position': 'absolute', 'width': '0', 'height': '0', 'padding': '0'}, # take style widgets out of flow
                ':not(.SlideArea) .ips-steps-output': {'max-height': '400px', 'overflow': 'auto'},
            })).as_widget().add_class('abs-style')
        
        self._printstyle = html('style', _build_css(('@media print',), {
            **view_nodes(f'.{self._uclass} > div > .jp-OutputArea-child',first, last),
            '.ips-steps-wrapper .steps-widget': {'opacity': '0.2 !important'}, # dim it
        })).as_widget().add_class('abs-style').add_class('jupyter-only') # will not export this style to avoid conflicts
        
        self._stepper = StepSlider(vertical=True if dots_loc in ("left","right") else False, nsteps=len(self._sidxs), interval=interval)
        
        children = (self._stepper, self._output) if dots_loc in ("left","top") else (self._output, self._stepper)
        self.children = (self._fixstyle, self._viewstyle, self._printstyle, *children)
        self._stepper.observe(self._set_view, names="value")
        self._set_view(0) # set initial view
        
    def _process_objs(self, objs):
        # This is crucial to capture them here as they do not update directly in output widget in same synchronous call
        with capture_content() as cap:
            write(objs, paused=True)

        main = [[]]
        for c in cap.outputs:
            meta = c.metadata if isinstance(c.metadata, dict) else {}
            if meta.get('DELIM', None) == "PAUSE":
                if main[-1]:
                    main.append([])
            else:
                main[-1].append(c)

        if main and not main[-1]:
            main.pop()

        idxs = list(accumulate([0, *(len(m) for m in main)]))
        sidxs = tuple((i, j - 1) for i, j in zip(idxs[:-1], idxs[1:]))
        return sidxs, tuple(chain(*main))
    
    def _set_view(self, change):
        forward = True # default to forward jump even when value set
        if isinstance(change, int): # given interger index
            idxs = self._sidxs[change]
        else:
            num = change['new']
            idxs = self._sidxs[num - 1] # stepper is 1-indexed
            forward = change['old'] and num > change['old']
        
        if slides := get_slides_instance(): # must before changing view window to take effect
            # Allow animation on selection any time
            update_class(slides.widgets.slidebox, 'AnimPrev', not forward)
            slides._send_nav_msg(forward, parts=True, selector=f'.{self._uclass}')
        
        selector = f'.{self._uclass} > div > .jp-OutputArea-child'
        css = _build_css(('@media screen',), view_nodes(selector,*idxs)) # only screen mode to avoid print conflicts
        self._viewstyle.value = f"<style>\n{css}\n</style>"
        