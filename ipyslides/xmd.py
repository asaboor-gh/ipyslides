r"""
Extended Markdown

You can use the following syntax:

```python run var_name
import numpy as np
```
# Normal Markdown
```multicol
A
+++
This \`{var_name}\` is a code from above and will be substituted with the value of var_name as:
`{var_name}`
```
::: note-warning
    Nested blocks are not supported.

::: note-info  
    - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
    - Use `Slides.extender` or `ipyslides.xmd.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
"""
import inspect
import textwrap, re, sys, string, builtins
from contextlib import contextmanager
from html import escape # Builtin library
from io import StringIO
from html.parser import HTMLParser
from ast import literal_eval

from markdown import Markdown
from IPython.core.display import display
from IPython import get_ipython
from IPython.utils.capture import capture_output
from ipywidgets import DOMWidget

from .formatters import XTML, highlight, htmlize, get_slides_instance
from .source import _str2code

_md_extensions = [
    "tables",
    "footnotes",
    "attr_list",
    "md_in_html",
    "customblocks",
    "def_list",
]  # For Markdown Parser
_md_extension_configs = {}


class PyMarkdown_Extender:
    def __init__(self):
        "Adds extensions to the Markdown parser. See [Website of Python-Markdown](https://python-markdown.github.io/extensions/)"
        self._exts = []
        self._configs = {}

    def __repr__(self) -> str:
        return (
            "Extensions:\n" + repr(self._all) + "\nConfigs:\n" + repr(self._all_configs)
        )

    @property
    def _all(self):
        return list(set([*self._exts, *_md_extensions]))

    @property
    def _all_configs(self):
        return {**self._configs, **_md_extension_configs}

    def extend(self, extensions_list):
        "Add list of extensions to the Markdown parser."
        self._exts = list(set([*self._exts, *extensions_list]))

    def config(self, configs_dict):
        "Add configurations to the Markdown extensions. configs_dict is a dictionary like {'extension_name': config_dict}"
        self._configs = {**self._configs, **configs_dict}

    def clear(self):
        "Clear all extensions and their configurations added by user."
        self._exts = []
        self._configs = {}

    @property
    def active(self):
        "List of active extensions."
        return {"extensions": self._all, "configs": self._all_configs}


extender = PyMarkdown_Extender()
del PyMarkdown_Extender

_special_funcs = {
    "vspace": "number in units of em",
    "hspace": "number in units of em",
    "alert": "text",
    "color": "text",
    "sub": "text",
    "sup": "text",
    "hl": "inline code highlight. Accepts langauge as keywoard.",
    "today": "fmt like %b-%d-%Y",
    "textbox": "text",  # Anything above this can be enclosed in a textbox
    "clip": "filename. Paste clipboard image",
    "image": "path/src or clip:filename",
    "raw": "text",
    "svg": "path/src",
    "iframe": "src",
    "details": "text",
    "styled": "style objects with CSS classes and inline styles",
    "zoomable": "zoom a block of html when hovered",
    "center": r"text or \`{variable}\`", # should be last
}
def _try_eval(str_value):
    try:
        return literal_eval(str_value)
    except:
        return str_value

def error(name, msg):
    "Add error without breaking execution."
    return XTML(f"<pre><b style='color:crimson;'>{name}</b><span>: {msg}</span></pre>")

def raw(text, css_class=None): # css_class is required here to make compatible with utils
    "Keep shape of text as it is (but apply dedent), preserving whitespaces as well. "
    _class = css_class if css_class else ''
    escaped_text = escape(textwrap.dedent(text).strip('\n')) # dedent and strip newlines on top and bottom
    return XTML(f"<div class='raw-text {_class}'>{escaped_text}</div>")

def get_unique_css_class():
    "Get slides unique css class if available."
    slides = get_slides_instance()
    return f".{slides.uid}" if slides else ""

@contextmanager
def capture_content(stdout: bool = True, stderr: bool = True, display: bool = True):
    """Works like IPython's capture_output contextmanager but keep output of print in given order by converting it to rich output display.
    """
    def rprint(*args, **kwargs):
        if "file" in kwargs and kwargs["file"] != sys.stdout:  # User should be able to redirect print to file
            return bprint(*args, **kwargs)
        
        if stdout: 
            kwargs['file'] = StringIO()
            bprint(*args, **kwargs)
            return raw(kwargs['file'].getvalue(), css_class="InlinePrint").display() # InlinePrint  is important for filterning in utils
        else:
            return bprint(*args, **kwargs)
    
    try:
        bprint = builtins.print # should be here, not on global level
        builtins.print = rprint # replace temporarily
        with capture_output(stdout=stdout, stderr=stderr,display=display) as cap:
            yield cap # pass capturedIO at top
    finally: # only need finally, errors are automatically thrown
        builtins.print = bprint


def resolve_objs_on_slide(xmd_instance, slide_instance, text_chunk):
    "Resolve objects in text_chunk corrsponding to slide such as cite, notes, etc."
    # notes`This is a note for current slide`
    all_matches = re.findall(
        r"notes\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE
    )
    for match in all_matches:
        slide_instance.notes.insert(match)
        text_chunk = text_chunk.replace(f"notes`{match}`", "", 1)

    # yoffset`interger in pixels`
    all_matches = re.findall(r"yoffset\`(\d+)\`", text_chunk, flags= re.MULTILINE)
    for i, match in enumerate(all_matches, start=1):
        text_chunk = text_chunk.replace(f"yoffset`{match}`", "", 1)
        
        if i == len(all_matches): # only last one to take effect
            slide_instance.this.yoffset(int(match))

    # cite`key` should be after citations`key`, so that available for writing there if any
    all_matches = re.findall(r"cite\`(.*?)\`", text_chunk, flags=re.DOTALL)
    for match in all_matches:
        xmd_key = xmd_instance._handle_var(slide_instance._cite(match.strip()))
        text_chunk = text_chunk.replace(f"cite`{match}`", xmd_key, 1)
    
    # section`This is section title`
    all_matches = re.findall(
        r"section\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE
    )
    for match in all_matches:
        slide_instance.section(match)  # This will be attached to the running slide
        text_chunk = text_chunk.replace(f"section`{match}`", "", 1)


    # toc[highlight]`This is toc title`, should be after block
    all_matches = re.findall(r"toc(\[.*?\])?\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE)
    for hl, title in all_matches:
        slide_instance.this._toc_args = (title, True if hl.strip('[]').strip() else False) # should be fully clear
        text_chunk = text_chunk.replace(f"toc{hl}`{title}`", xmd_instance._handle_var(slide_instance.this._reset_toc()), 1)

    all_matches = re.findall( # will be removed in future
        r"proxy\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE
    )
    for match in all_matches:
        text_chunk = text_chunk.replace(f"proxy`{match}`", xmd_instance._handle_var(slide_instance.proxy(match)), 1) 
    
    # Footnotes at place user likes
    all_matches = re.findall(r"refs\`([\d+]?)\`", text_chunk) # match digit or empty
    for match in all_matches:
        slide_instance.this._set_refs = False # already added here
        _cits = ''.join(v.value for v in sorted(slide_instance.this._citations.values(), key=lambda x: x._id))
        out = f"<div class='Citations' style='column-count: {match} !important;'>{_cits}</div>"
        text_chunk = text_chunk.replace(f"refs`{match}`", out, 1)

    return text_chunk

class HtmlFormatter(string.Formatter):
    def format_field(self, value, format_spec):
        if not format_spec:
            if not isinstance(value, str): # keep str as it is
                return htmlize(value) if value is not None else "" # Avoid None
            else:
                return value # Just return string

        return super().format_field(value, format_spec)
        
    def get_value(self, key, args, kwargs):
        if isinstance(key, int):
            return error('RuntimeError','Positional arguments are not supported in custom formatting!').value
        elif isinstance(key, str) and key not in kwargs:
            return error('KeyError', f'{key!r} not found in given namespace. You may need to enclose input text in Slides.fmt function!').value
        return super().get_value(key, args, kwargs)
    

hfmtr = HtmlFormatter() # custom format
del HtmlFormatter

class TagFixer(HTMLParser):
    "Use self.fix_html function."
    def handle_starttag(self, tag, attrs): 
        self._objs.append(f'{tag}')

    def handle_endtag(self, tag):
        if self._objs and self._objs[-1] == tag:
            self._objs.pop() # tag properly closed
        else:
            self._objs.append(f'/{tag}')

    def _fix_tags(self, content):
        tags = self._objs[::-1]  # Reverse order is important
        end_tags = [f"</{tag}>" for tag in tags if not tag.startswith('/')]
        start_tags = [f"<{tag.lstrip('/')}>" for tag in tags if tag.startswith('/')]
        return ''.join(start_tags) + content + ''.join(end_tags)
    
    def _remove_empty_tags(self, content, depth=5):
        empty_tags = re.compile(r'\<\s*(.*?)\s*\>\s*\<\s*\/\s*(\1)\s*\>') # keeps tags with attributes
        i = 0
        while empty_tags.findall(content) and i <= depth: 
            content = empty_tags.sub('', content).strip() 
            i += 1
        return content

    def fix_html(self, content, clean_depth=5):
        "Fixes unopened/unclosed tags and clear empty tags upto `clean_depth` nesting levels."
        self._objs = []
        self.feed(content)
        self.close()

        if self._objs: # Otherwise its already correct
            content = self._fix_tags(content)
        return self._remove_empty_tags(content, clean_depth) 
        

tagfixer = TagFixer()
del TagFixer

class xtr(str):
    """String that will be parsed with given namespace lazily. Python's default str will be parsed in top level namespace only!
    If you apply some str operations on it, make sure to use 'copy_ns' method on every generated string to bring it's type back, otherwise it will discard given namespace.
    This is not intended to do string operations, just to hold namespace for extended markdown.
    
    Being as last expression of notebook cell or using self.parse() will parse markdown content.
    """
    def with_ns(self, ns): # cannot add ns in __init__
        if not isinstance(ns, dict):
            raise TypeError(f"ns should be a dictionary, got {type(ns)}")
        self._ns = ns
        return self
    
    @property
    def data(self):
        return super().__str__()
    
    @property
    def ns(self):
        return self._ns
    
    def format(self, *args, **kwargs):
        raise RuntimeError("xtr does not support explicit formatting, use .parse instaed!")
    
    def format_map(self, mapping):
        raise RuntimeError("xtr does not support explicit formatting, use .parse instaed!")
    
    def __format__(self, spec):
        raise RuntimeError("xtr is not allowed inside a string formatting!")
    
    def __add__(self, other):
        raise RuntimeError("xtr does not support addition!")
    
    def __mul__(self, other):
        raise RuntimeError("xtr does not support multiplication!")
    
    def __rmul__(self, other):
        raise RuntimeError("xtr does not support multiplication!")
    
    def __repr__(self):
        return f"xtr(data = {self.data!r}, ns = {self.ns})" 
    
    def copy_ns(source, target): # This works with xtr as source as well as str and others when called from class
        "Add ns of source to target str and return target wrapped in source type if source is a 'xtr', otherwise return target."
        if type(source) == xtr:  # do not check instances here
            if not hasattr(source, '_ns'):
                raise AttributeError("The method 'with_ns' was never used on source!")
            if type(target) == str:
                return xtr(target).with_ns(source._ns)
        return target
    
    def parse(self, returns = False):
        "Parse markdown content of itself and returns parsed html or display."
        return parse(self, returns = returns) # parse from top level
    
    def _ipython_display_(self):
        return self.parse(returns = False)

class XMarkdown(Markdown):
    def __init__(self):
        super().__init__(
            extensions=extender._all, extension_configs=extender._all_configs
        )
        self._vars = {}
        self._ns = {} # provided by fmt and xtr
        self._returns = True
        self._shell = get_ipython()
        self._slides = get_slides_instance()

    def _extract_class(self, header):
        out = header.split(".", 1)  # Can have many classes there
        if len(out) == 1:
            return out[0].strip(), ""
        return out[0].strip(), out[1].replace(".", " ").strip()
    
    def user_ns(self):
        "Top level namespace or set by user inside `Slides.fmt`."
        if self._ns:
            return self._ns
        # Otherwise get top level namespace only
        return self.main_ns() 

    def main_ns(self): # This is required to set variables
        main = sys.modules.get('__main__',None) # __main__ is current top module
        return main.__dict__ if main else {}

    def _parse(self, xmd, returns = True): # not intended to be used directly
        """Return a string after fixing markdown and code/multicol blocks returns = True
        otherwise displays objects and execute python code from '```python run source_var_name' block.
        """
        self._returns = returns  # Must change here
        if isinstance(xmd, xtr):
            self._ns = xmd._ns

        if xmd[:3] == "```":  # Could be a block just in start but we need newline to split blocks
            xmd = "\n" + xmd

        if len(re.findall(r'^```', xmd, flags = re.MULTILINE)) % 2:
            raise ValueError("Some blocks started with ```, but never closed!")

        # xmd can have code blocks which may not be passed from suitable context
        if (r"\n```python run" in xmd) and self._returns: # Do not match nested blocks, r"" is important
            raise RuntimeError(
                "Cannot execute code in current context, use Slides.parse(..., returns = False) for complete parsing!"
            )

        new_strs = textwrap.dedent(xmd).split("\n```")  # \n``` avoids nested blocks and it should be, dedent is important
        outputs = []
        for i, section in enumerate(new_strs, start=1):
            content = section.strip() # Don't add empty object, they don't let increment columns
            if content and i % 2 == 0:
                content = textwrap.dedent(content)  # Remove indentation in code block, useuful to write examples inside markdown block
                outputs.extend(self._parse_block(content))  # vars are substituted already inside
            elif content: 
                out = self.convert(content)
                if isinstance(out, list):
                    outputs.extend(out)
                elif out: # Some syntax like section on its own line can leave empty block later
                    outputs.append(XTML(out))

        self._vars = {} # reset at end to release references
        self._ns = {} # reset back at end

        if returns:
            content = ""
            for out in outputs:
                if isinstance(out, XTML):
                    content += out.value 
                else:
                    from .writer import _fmt_html
                    content += _fmt_html(out) # Rich content from python execution and Writer 
            return content
        else:
            return display(*outputs)
    
    def _resolve_files(self, text_chunk):
        "Markdown files added by include`file.md` should be inserted a plain."
        all_matches = re.findall(r"include\`(.*?)\`", text_chunk, flags=re.DOTALL)
        for match in all_matches:
            with open(match, "r", encoding="utf-8") as f:
                text = "\n" + f.read() + "\n" 
                text_chunk = text_chunk.replace(f"include`{match}`", text, 1)
        return text_chunk

    def _resolve_nested(self, text_chunk):
        old_returns = self._returns
        try:
            # match func`?text?` to parse text and return func`html_repr`
            all_matches = re.findall(
                r"\`\?(.*?)\?\`", text_chunk, flags=re.DOTALL | re.MULTILINE
            )
            for match in all_matches:
                repr_html = self._parse(match, returns = True)
                repr_html = re.sub(
                    "</p>$", "", re.sub("^<p>", "", repr_html)
                )  # Remove <p> and </p> tags at start and end
                text_chunk = text_chunk.replace(f"`?{match}?`", f"`{repr_html}`", 1)
        finally:
            self._returns = old_returns

        return text_chunk

    def _parse_block(self, block):
        "Returns list of parsed block or columns or code, input is without ``` but includes langauge name."
        header, data = block.split("\n", 1)
        line, _class = self._extract_class(header)
        if "multicol" in line:
            out = self._parse_multicol(data, line, _class)
            return [XTML(out)] if isinstance(out, str) else out # Writer under frames
        elif "python" in line:
            return self._parse_python(data, line, _class)  # itself list
        else:
            out = XTML() # empty placeholder
            try:
                name = " " if line.strip().lower() == "text" else None
                out.data = highlight(data, language=line.strip(), name=name, css_class=_class).value # intercept code highlight
            except:
                out.data = super().convert(f'```{block}\n```') # Let other extensions parse block
            
            return [out,] # list 

    def _parse_multicol(self, data, header, _class):
        "Returns parsed block or columns or code, input is without ``` but includes langauge name."
        cols = data.split("+++")  # Split by columns
        if header.strip() == "multicol":
            widths = [int(100/len(cols)) for _ in cols]
        else:
            widths = header.split("multicol")[1].split()
            if len(widths) > len(cols): # This allows merging column notation with frames
                for _ in range(len(cols), len(widths)):
                    cols.append("")

            if len(widths) < len(cols):
                raise ValueError(
                    f"Number of columns {len(cols)} should be <= given widths in {header!r}"
                )
            for w in widths:
                if not w.strip().isdigit():
                    raise TypeError(f"{w} is not an integer")

            widths = [int(w) for w in widths]
        
        # Under slides and any display context, multicol should return Writer 
        if self._slides and not self._returns:
            with capture_content() as cap:
                self._slides.write(*[self.convert(col) for col in cols], widths=widths, css_class=_class)
            
            return cap.outputs
        
        cols = [self.convert2str(col) for col in cols]
        if len(cols) == 1: # do not return before checking widths and adding extra cols if needed
            return f'<div class={_class}">{cols[0]}</div>' if _class else cols[0]

        cols = "".join(
            [f"""<div style='width:{w}%;overflow-x:auto;height:auto'>{col}</div>"""
                for col, w in zip(cols, widths)])

        return f'<div class="columns {_class}">{cols}\n</div>'

    def _parse_python(self, data, header, _class):
        # if inside some writing command, do not run code at all
        if len(header.split()) > 3:
            raise ValueError(
                f"Too many arguments in {header!r}, expects 3 or less as ```python run source_var_name"
            )
        dedent_data = textwrap.dedent(data)

        if "run" not in header:  # no run given
            return [highlight(dedent_data, language="python", css_class=_class),]
        
        if "run" in header:
            if self._returns:
                raise RuntimeError("Cannot execute code in this context!")
            
            source = header.split("run")[1].strip()  # Afte run it be source variable
            main_ns = self.main_ns() # get once
            if source:
                main_ns[source] = _str2code(dedent_data, language="python", css_class=_class)

            # Run Code now
            with capture_content() as captured:
                if current_shell := self._slides or self._shell:
                    try: # Need slides to be  accessible in namespace
                        main_ns['get_slides_instance'] = get_slides_instance
                        current_shell.run_cell(dedent_data)
                    finally:
                        main_ns.pop('get_slides_instance') # don't keep

                else:
                    raise RuntimeError("Cannot execute this outside IPython!")

            outputs = captured.outputs
            return outputs
    
    def convert(self, text):
        """Replaces variables with placeholder after conversion to respect all other extensions.
        Returns str or list of outputs based on context. To ensure str, use `self.convert2str`.
        """
        text = self._resolve_files(text)
        text = re.sub(r"\\\`", "&#96;", text)  # Escape backticks after files added

        text = self._resolve_nested(text)  # Resolve nested objects in form func`?text?` to func`html_repr`
        if self._slides and self._slides.this: # under building slide
            text = resolve_objs_on_slide(
                self, self._slides, text
            )  # Resolve objects in xmd related to current slide
        output = super().convert(self._sub_vars(text)) # sub vars before conversion
        return self._resolve_vars(re.sub("&#96;", "`", output))  # Reverse backticks
    
    def convert2str(self, text):
        "Ensures that output will be a str."
        outputs = self.convert(text)
        if isinstance(outputs, list): # From Variables
            new_outputs = []
            for out in outputs:
                if isinstance(out, DOMWidget):
                    new_outputs.append(error("RuntimeError", f"{out!r} cannot be displayed in this context!"))
                else:
                    new_outputs.append(out)
            return ''.join([f"{out}" for out in new_outputs]) # formats handled automatically
        return outputs
    
    def _resolve_vars(self, text):
        "Substitute saved variables"
        if re.findall(r'DISPLAYVAR(\d+)DISPLAYVAR', text):
            if self._returns:
                text = re.sub(
                    r'DISPLAYVAR(\d+)DISPLAYVAR', 
                    lambda m: error('RuntimeError',f'{self._vars.get(m.group(), m.group())!r} cannot be displayed in this context!').value,
                    text
                )
                self._resolve_vars(text)
            else:
                objs = []
                for i, block in enumerate(re.split('DISPLAYVAR', text), start=1):
                    content = block.strip() # Avoid empty objects
                    if i % 2 == 0:
                        key = f"DISPLAYVAR{content}DISPLAYVAR"
                        objs.append(self._vars.get(key, error('KeyError','Variable not accessible')))
                    elif (content := tagfixer.fix_html(content)):
                        objs.append(XTML(self._resolve_vars(content)))
                return objs

        return re.sub(r"PrivateXmdVar(\d+)X", lambda m: self._vars.get(m.group(), m.group()), text)
    
    def _handle_var(self, value): # Put a temporary variable that will be replaced at end of other conversions.
        if isinstance(value, (str, XTML)): 
            key = f"PrivateXmdVar{len(self._vars)}X" # end X to make sure separate it 
            self._vars[key] = self._resolve_vars(value if isinstance(value, str) else value.value) # Handle nested like center`alert`text`` things before saving next varibale
        else: # Handles TOC, DOMWidget and Others rich displays
            key = f"DISPLAYVAR{len(self._vars)}DISPLAYVAR"
            self._vars[key] = value # Direct value stored
        return key
    
    def _sub_vars(self, html_output):
        "Substitute variables in html_output given as `{var}` and two inline columns as ||C1||C2||"
        user_ns = self.user_ns() # get once, will be called multiple time
        # Replace variables first to have small data
        def handle_match(match):
            key, *fmt_spec = match.group()[2:-2].strip().split('!')[0].split(':')
            value, _ = hfmtr.get_field(key, (), user_ns)
            if isinstance(value, DOMWidget) or 'nb' in fmt_spec: # Anything with :nb or widget
                return self._handle_var(value) 
            return self._handle_var(hfmtr.vformat(match.group()[1:-1], (), user_ns))
        
        html_output = re.sub(r"\`\{(.*?)\}\`", handle_match, html_output, flags=re.DOTALL)

        # Replace inline  functions
        from . import utils  # Inside function to avoid circular import

        for func in _special_funcs.keys():
            all_matches = re.findall(
                rf"{func}(\[.*?\])?\`(.*?)\`", html_output, flags=re.DOTALL | re.MULTILINE
            ) # returns two matches always
            for m1, m2 in all_matches:
                _func = getattr(utils, func)
                arg0 = m2.strip() # avoid spaces in this

                if not m1:
                    _out = (_func(arg0) if arg0 else _func()) # If no argument, use default
                    html_output = html_output.replace(f"{func}`{m2}`", self._handle_var(_out), 1)
                else: # func with arguments
                    args = [
                        v.replace("__COM__", ",")
                        for v in m1.strip('[]') # [] will be there
                        .replace(r"\=", "__EQ__")
                        .replace(r"\,", "__COM__")
                        .split(",")
                    ]  # respect escaped = and ,
                    kws = {
                        k.strip().replace("__EQ__", "="): _try_eval(v.strip().replace("__EQ__", "="))
                        for k, v in [a.split("=") for a in args if "=" in a]
                    }
                    args = [_try_eval(a.strip().replace("__EQ__", "=")) for a in args if "=" not in a]
        
                    try:
                        _out = (_func(arg0, *args, **kws) if arg0 else _func(*args, **kws)) # If no argument, use default 
                        html_output = html_output.replace(f"{func}{m1}`{m2}`", self._handle_var(_out), 1)
                    except Exception as e:
                        raise Exception(rf"Error in {func}{m1}`{m2}`: {e}.\nYou may need to escape , and = with \, and \= if you need to keep them inside {m1}")

        # Replace columns at end because they will convert HTML
        all_cols = re.findall(
            r"\|\|(\s*\d*\s*)(.*?)\|\|(.*?)\|\|", html_output, flags=re.DOTALL | re.MULTILINE
        )  # Matches new line as well, useful for inline plots and big objects
        for width, *cols in all_cols:
            digit = int(width.strip()) if width.strip() else 50 # could be tabs, new lines etc
            if not (digit in range(1,100)): # 1-99, why zero width
                raise ValueError(f'column width after first || should be 0-99, got {digit}')
            
            _cols = "\n".join(
                f'<div style="width:{w}%;">{self.convert2str(c.strip())}</div>' for w, c in zip([digit, 100 - digit], cols)
            )
            _out = f'<div class="columns">{_cols}</div>'  # Replace new line with 4 spaces to keep indentation if block ::: is used
            html_output = html_output.replace(f"||{width}{cols[0]}||{cols[1]}||", self._handle_var(_out), 1)

        return html_output  # return in main scope


def parse(xmd, returns = False):
    r"""Parse extended markdown and display immediately.
    If you need output html, use `returns = True` but that won't execute python code blocks.

    **Example**
    ```markdown
     ```python run var_name
     #If no var_name, code will be executed without assigning it to any variable
     import numpy as np
     ```
     # Normal Markdown
     ```multicol 40 60
     # First column is 40% width
     If 40 60 was not given, all columns will be of equal width, this paragraph will be inside info block due to class at bottom
     {.info}
     +++
     # Second column is 60% wide
     This \`{var_name}\` is code from above and will be substituted with the value of var_name
     ```

     ```python
     # This will not be executed, only shown
     ```
     || Inline-column A || Inline-column B ||
    ```

    ::: note-info
        - Each block can have class names (speparated with space or .) after all other options such as `python .friendly` or `multicol .Sucess.info`.
            - For example, `python .friendly` will be highlighted with friendly theme from pygments.
            - Pygments themes, however, are not supported with `multicol`.
            - You need to write and display CSS for a custom class.
        - The block with `::: class_type` syntax accepts extra classes in quotes, for example `::: multicol "Success" "info"`.
        - There are special CSS classes `jupyter-only` and `export-only` that control appearance of content in different modes.

    ::: note-warning
        Nested blocks are not supported.

    ::: note-info
        - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        - Use `Slides.extender` or `ipyslides.xmd.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
    """
    return XMarkdown()._parse(xmd, returns = returns)

def _get_ns(text, depth, **kwargs): # kwargs are preferred
    fr = inspect.currentframe()
    for _ in range(depth):
        fr = fr.f_back

    ls, gs = fr.f_locals, fr.f_globals
    matches = [match.strip() for match in re.findall(
        r"[^\\]\`\{(.*?)[\.\[\:\!\s+].*?\}\`", # should not start with \`
        text.replace('}`', ' }`'), # needs a space if only variable
        flags = re.DOTALL) if not re.search(r"\{|\}", match)]
    
    ns = {} 
    for m in matches:
        if m in kwargs: # prefers user given, but only keep matching
            ns[m] = kwargs[m]
        elif m in ls: # then prefers locals
            ns[m] = ls[m]
        elif m in gs:
            ns[m] = gs[m]
        # Will be a soft error on formatting time, no need to add it here
 
    del fr, ls, gs, kwargs
    return ns

def fmt(text, **kwargs):
    """Stores refrences to variables used in syntax `{var}` from current namespace until markdown parsed by function it is passed to. 
    You need this if not in top level scope of Notebook. kwargs can be used to add extra vairables without clutering user namespace.
    If you do some str operations on output of this function, use hl`output.copy_ns(target)` to attch namespace to new string.

    Output is not intended to do string operations, just to hold namespace for extended markdown.

    Returns an xtr object which delays formatting until it is intercepted by markdown parser.
    """
    if isinstance(text, str): # depth belowshoul be 2 to go where fmt will run
        return xtr(text).with_ns(_get_ns(text, 2, **kwargs)) # should return as string to be parsed
    else: # should not allow anything else because it will cause issues in Makrdown formatting
        return TypeError(f"fmt expects a str, got {type(text)}!")
    
def _fig_caption(text): # need here to use in many modules
    return f'<figcaption class="no-zoom">{parse(text,True)}</figcaption>' if text else ''