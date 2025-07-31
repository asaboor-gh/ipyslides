r"""
Extended Markdown

You can use the following syntax:

# Normal Markdown
```multicol
A
+++
This \%{var_name} (or legacy \`{var_name}\`) can be substituted with `fmt` function or from notebook if whole slide is built with markdown.
```
::: note-warning
    Nested blocks are not supported.

::: note-info  
    - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
    - Use `Slides.extender` or `ipyslides.xmd.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
"""
import textwrap, re, sys, string, builtins, inspect
from itertools import islice
from contextlib import contextmanager
from html import escape # Builtin library
from io import StringIO
from html.parser import HTMLParser

from markdown import Markdown
from IPython.display import display
from IPython.utils.capture import capture_output
from ipywidgets import DOMWidget

from .formatters import XTML, altformatter, _highlight, htmlize, get_slides_instance, _inline_style

_md_extensions = [
    "tables",
    "footnotes",
    "attr_list",
    "md_in_html",
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
    "line": "length in units of em, [color, width and style]",
    "alert": "text",
    "color": "text",
    "sub": "text, or use _ in place of sub",
    "sup": "text, or use ^ in place of sup",
    "hl": "inline code highlight. Accepts langauge as keywoard.",
    "today": "format_spec like %b-%d-%Y",
    "textbox": "text",  # Anything above this can be enclosed in a textbox
    "image": "path/src or clip:filename",
    "raw": "text, or use ::: raw block",
    "svg": "path/src",
    "iframe": "src",
    "details": "text or use ::: details block",
    "styled": "style objects with CSS classes and inline styles or use block ::: with css classes and props inline",
    "zoomable": "zoom a block of html when hovered or used ::: zoomable block",
    "center": r"text or \%{variable} or use ::: center, ::: align-center blocks", # should after most of the functions
    "stack": r"text separated by ||, like stack[(1,2,1),**css_props]\\`C1 || C2 || C3\\`, preferably use ::: columns block",
}

def error(name, msg):
    "Add error without breaking execution."
    return XTML(f"<pre class='Error'><b style='color:crimson;'>{name}</b><span>: {msg}</span></pre>")

def raw(text, css_class=None): # css_class is required here to make compatible with utils
    "Keep shape of text as it is (but apply dedent), preserving whitespaces as well. "
    _class = css_class if css_class else ''
    escaped_text = escape(textwrap.dedent(text).strip('\n')) # dedent and strip newlines on top and bottom
    return XTML(f"<div class='raw-text {_class}'>{escaped_text}</div>")

def get_unique_css_class():
    "Get slides unique css class if available."
    slides = get_slides_instance()
    return f".{slides.uid}" if slides else ""

def get_main_ns():
    "Top level namespace"
    return getattr(sys.modules.get('__main__',None),'__dict__',{})

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
    
    # @key! for inline citations even in footnote mode, do before others
    text_chunk = re.sub(r"@(?:[A-Za-z_]\w*)!", lambda m: slide_instance._nocite(m.group()[1:-1]), text_chunk)
    
    # @key -> cite`key` before other stuff
    at_key_pattern = re.compile(r'''
        (?<!\\) # negative lookbehind: don't match if there's a backslash
        (?<!\w) # Don't match if a word before so example@google.com is safe
        (?<!\`) # Don't match keys inside backticks
        @(?:[A-Za-z_]\w*)(?:\s*,\s*@(?:[A-Za-z_]\w*))*   # @key, @key4 (citation) or single @key
    ''', re.VERBOSE)
    for match in at_key_pattern.findall(text_chunk):
        tocite = f"cite`{match.replace('@','')}`"
        text_chunk = text_chunk.replace(match, tocite, 1)

    # cite`key`
    all_matches = re.findall(r"cite\`(.*?)\`", text_chunk, flags=re.DOTALL)
    for match in all_matches:
        if match.endswith('!'):
            xmd_key = ''.join(slide_instance._nocite(key) for key in match[:-1].strip().split(','))  # remove ! at end
        else:
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

    # Footnotes at place user likes
    all_matches = re.findall(r"refs\`([\d+]?)\`", text_chunk) # match digit or empty
    for match in all_matches:
        slide_instance.refs(match or int(match)) # match is empty or digit
        text_chunk = text_chunk.replace(f"refs`{match}`", "", 1)
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
            key = key.strip()  # remove leading and trailing spaces, no idea where it causes issues
            if not key.isidentifier():
                return error('NameError', f'name {key!r} is not a valid variable name').value
            return error('NameError', f'name {key!r} is not defined').value
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

# This shoul be outside, as needed in other modules
def resolve_included_files(text_chunk):
    "Markdown files added by include`file.md[start:end]` should be inserted as plain."
    all_matches = re.findall(r"^(\s*)include\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE)
    for indent, match in all_matches:
        # Parse match into file path and range
        range_match = re.search(r'\[(.*?)\]$', match)
        if range_match:
            filepath = match[:range_match.start()].strip()
            range_str = range_match.group(1).strip()
            
            start, end = None, None
            try:
                if ':' in range_str:
                    start_str, end_str = range_str.split(':', 1)
                    start = int(start_str.strip()) - 1 if start_str.strip() else None
                    end = int(end_str.strip()) if end_str.strip() else None
                elif range_str: # single line number
                    start = int(range_str) - 1
                    end = start + 1
            except (ValueError, IndexError):
                # Invalid range, treat whole match as filename
                filepath = match
                start, end = None, None
        else:
            filepath = match
            start, end = None, None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()[slice(start,end)]
                text = textwrap.indent("\n" + "".join(lines) + "\n", indent) # need inside ::: blocks
                text_chunk = text_chunk.replace(f"include`{match}`", text, 1)
        except Exception as e:
            err_msg = error('Exception', f'Could not include file {filepath!r}:\n{e}').value
            text_chunk = text_chunk.replace(f"include`{match}`", err_msg, 1)

    return text_chunk

class XMarkdown(Markdown):
    def __init__(self):
        super().__init__(
            extensions=extender._all, extension_configs=extender._all_configs
        )
        self._vars = {}
        self._fmt_ns = {} # provided by fmt
        self._returns = True
        self._slides = get_slides_instance()
        self._nested = False # checks if using _parse in nested manner
    
    @property
    def _wr(self):
        if not hasattr(self, '_wr_imported'):
            from . import writer # avoid cyclic, but import once
            self._wr_imported = writer
        return self._wr_imported
    
    def user_ns(self):
        "Top level namespace or set by user inside `Slides.fmt`."
        if self._fmt_ns: 
            return self._fmt_ns # always preferred
        elif self._slides and self._slides.this:
            return { 
                **self._slides._md_vars, # by Notebook variable update, last
                **self._slides.this._md_vars, # by Slide.rebuild after fmt
            } or get_main_ns() # not yet in _md_vars
        return get_main_ns()  # top scope at end

    def _parse(self, xmd, returns = True): # not intended to be used directly
        """Return a string after fixing markdown and code/multicol blocks returns = True
        otherwise displays objects given as vraibales may not give their proper representation.
        """
        self._returns = returns  # Must change here
        if isinstance(xmd, fmt): # scoped variables picked here
            xmd, self._fmt_ns = fmt._astuple(xmd)

        if xmd[:3] == "```":  # Could be a block just in start but we need newline to split blocks
            xmd = "\n" + xmd

        if len(re.findall(r'^```', xmd, flags = re.MULTILINE)) % 2:
            issue = error("ValueError",f"Some blocks started with ```, but never closed, in markdown:\n{xmd}")
            return issue.value if returns else display(issue) # return value or display
        
        blocks = []
        for i, text in enumerate(textwrap.dedent(xmd).split("\n```")): # \n``` only split top level, nested handleed later
            if i % 2 == 0:
                blocks.extend(self._split_blocks_with_dedent(text))  # split by :::
            elif len(parts := text.split('\n', 1)) == 2 and parts[1].strip():
                blocks.append(("block", parts))  # ``` blocks, avoid empty blocks

        outputs = []
        for typ, obj in blocks:
            if typ == "block":
                outputs.extend(self._parse_block(*obj))  # vars are substituted already inside, obj = (header, data)
            elif content := obj.strip():  # raw text but avoid empty stuff
                out = self.convert(content) 
                if isinstance(out, list):
                    outputs.extend(out)
                elif out: # Some syntax like section on its own line can leave empty block later
                    outputs.append(XTML(out))
        
        if not self._nested: # we need to keep these if nested parsing
            self._vars = {} # reset at end to release references
            self._fmt_ns = {} # reset back at end

        if returns:
            content = ""
            for out in outputs:
                if isinstance(out, XTML):
                    content += out.value 
                else:
                    content += self._wr._fmt_html(out) # Rich content from python execution and Writer 
            return content
        else:
            return display(*outputs)
        
    def _parse_params(self, param_string):
        """Parse parameter string with simple regex."""
        RE_PARAM = re.compile(
            r'(?:([\w\-]+)=)?'
            r'("([^"]*)"|\'([^\']*)\'|([\S]+))'
        )
        numbers, args, kwargs, node_attrs = [], [], {}, {}
        post_slash = False # *widths *classes **props / **attrs
        for match in RE_PARAM.finditer(param_string.lstrip(': ')): # remove leading : and space
            # The value is captured in one of three groups
            value = match.group(3) or match.group(4) or match.group(5)
            if value == "/": 
                post_slash = True
                continue # skip slashed, it is not a value
            if key := match.group(1):
                if key.startswith(('fg', 'bg')) and key[2:].isdigit():
                    key = f'--{key}-color' # if key in fg1,....3, bg1,....3, then it is a css property
                if post_slash: # node attributes
                    node_attrs[key] = value
                else:
                    kwargs[key] = value
            else:
                if value.isdigit() or re.match(r'^\d+(\.\d+)?$', value):
                    numbers.append(float(value) if '.' in value else int(value))
                else:
                    args.append(value.replace('.',' ').strip()) # remove . from classes
        sizes = numbers if numbers else None # making None is important for multicol and stack 
        # flatten node_attrs to a string, but not css properties
        node_attrs = ' '.join(f'{k}="{v}"' for k, v in node_attrs.items())
        if args:
            return args[0], sizes, ' '.join(args[1:]), kwargs, node_attrs # block type, sizes, className, css_props, node_attrs
        return '', sizes, '', kwargs, node_attrs

    
    def _split_blocks_with_dedent(self, text):
        """Split ::: blocks, ending them when dedentation occurs. 
        DON'T TRY TO BE OVERSMART WITH COMPLAEX REGEX AS THIS CODE
        IS MORE EFFICENT THAN REGEX AND CLEAR. I TRIED THAT BEFORE WITH FAILURES.
        """
        if not re.search(r'^:::', text, flags=re.MULTILINE):
            return [("raw", text)] if text.strip() else [] # but keep text as it is
        
        blocks = []
        parts = re.split(r'^:::',text, flags=re.MULTILINE)
        # parts[0] is raw text, parts[1:] are blocks
        if parts and parts[0].strip():
            blocks.append(("raw", parts[0]))
            
        for part in parts[1:]:
            lines = part.splitlines(keepends=True)
            header = '::: ' + lines[0].strip() # first line is always header
            block_body, text_chunk = '', ''
            still_header = True # still header, until non-indented line
            for line in islice(lines, 1, None): # skip first line
                if still_header and line.startswith(':'): # indented line, part of block header
                    header += line.replace(':',' ',1).rstrip()
                else:
                    still_header = False # no more header
                    if re.search(r'^\s+', line): # indented line with one or more spaces
                        block_body += line # indented block body
                    else:
                        text_chunk += line # text chunk, not part of block
                        
            if block_body.strip(): # block comes first, only if not empty
                blocks.append(("block", (header, block_body)))
            if text_chunk.strip(): # text chunk comes after block
                blocks.append(("raw", text_chunk)) # keep text as it is
        return blocks       
    
    def _parse_nested(self, xmd, returns=True):
        old_returns = self._returns
        self._nested = True
        try:
            out = self._parse(textwrap.dedent(xmd), returns=returns) # allows nesting via indent
        finally:
            self._returns = old_returns
            self._nested = False
        return out

    def _resolve_nested(self, text_chunk):
        def repl(m: re.Match): # Remove <p> and </p> tags at start and end, also keep backtick
            return f'`{re.sub("^<p>|</p>$", "", self._parse_nested(m.group(1), returns = True))}`' 

        # match legacy func`?text?` to parse text and return func`html_repr`
        text_chunk = re.sub(r"\`\?(.*?)\?\`", repl, text_chunk, flags=re.DOTALL | re.MULTILINE)
        # Now match neseted `// //` upto many levels
        for depth in range(4,1,-1): # `////, `///, `// at least two slashes
            op, cl = '/'*depth, '/'*depth
            text_chunk = re.sub(rf"\`{op}(.*?){cl}\`", repl, text_chunk, flags=re.DOTALL | re.MULTILINE)
        return text_chunk

    def _parse_block(self, header, data):
        "Returns list of parsed block or columns or code, input is without ``` but includes langauge name."
        data = resolve_included_files(textwrap.dedent(data)) # clean up data  before processing 
        typ, widths, _class, css_props, attrs = self._parse_params(header)
        
        if typ == "citations" or header.lstrip(' :').startswith("citations"): # both kind of blocks
            pre = '```' if typ == "citations" else '' # correct error message
            return [error("ValueError", 
                f"citations block is only parsed inside synced markdown file! "
                f"Use `Slides.set_citations` otherwise.\n{pre}{header}\n{data}"
            )]
        elif typ in ("multicol","columns") and re.search(r'^\+\+\+\s*$', data, flags=re.MULTILINE): # handle columns and multicol with display mode
            return self._parse_multicol(data, widths, _class) # simple columns will be handled inline 
        elif "md-" in typ:
            return self._parse_md_src(data, header)
        elif typ == "table":
            return self._parse_table(data, widths, _class, css_props, attrs)
        elif header.strip().startswith(":::") or typ in ("columns","multicol"): # simple flex ```columns without +++ or ::: block
            return self._parse_colon_block(header, data)
        else:
            out = XTML() # empty placeholder
            try:
                name = " " if typ.lower() == "text" else None
                out.data = _highlight(data, language=typ, name=name, css_class=_class) # intercept code highlight
            except:
                out.data = super().convert(f'```{header}\n{data}\n```') # Let other extensions parse block
            
            return [out,] # list 
        
    def _parse_colon_block(self, header, data):
        STRICT_TAGS = ("code","pre","raw")
        CAPTURED_TAGS = ("p","details","summary","center","blockquote","ul","ol","nav", *STRICT_TAGS) # tags that are captured by this parser
        
        tag, widths, _class, css_props, attrs = self._parse_params(header)
        
        if tag in CAPTURED_TAGS:
            if tag in STRICT_TAGS: # keep as is from further processing
                if tag == "code":
                    return self._parse_code(data, _class, css_props, attrs)
                return [XTML(f"<pre class='{_class} raw-text' {_inline_style(css_props)} {attrs}>\n{data}\n</pre>")]
            
            # These tags should strip outer p tags for being properly structured as intended by user
            out = self._parse_nested(data, returns=True)
            if re.search(r'^<ul|^<ol|^<p|<nav', out): # these tags are difficult ones to style
                # remove these in case of ul, ol, p in single regex 
                out = re.sub(r'^<(p|ol|ul|nav)[^>]*>|</(p|ol|ul|nav)>$', '', out, count=1)
            return [XTML(f"<{tag} class='{_class}' {_inline_style(css_props)} {attrs}>{out}</{tag}>")]
        
        style = "" # style for columns if widths are given
        if tag in ("multicol","columns")  and widths: # columns with inline mode
            klass = f"c-{id(widths)}" # unique class for columns
            _class = f"{_class} {klass}" if _class else klass # add klass
            style = '\n'.join(f".{klass} > :nth-child({i+1}) {{flex: {w} 1;}}" for i, w in enumerate(widths)) # nth-child selectors
            style = f"<style>.{klass} > p:empty {{display:none;}}\n{style}</style>" # empty p tags should not be treated as columns
            
        # treat tag as class if not given at end
        _class = " ".join([tag, _class, "columns" if tag == "multicol" else ""]) # add columns class if multicol
        return [XTML(f"<div class='{_class}' {_inline_style(css_props)} {attrs}>{self._parse_nested(data, returns=True)}</div>{style}")]
    
    def _parse_code(self, data, _class, props, attrs):
        params = inspect.signature(_highlight).parameters.keys()
        kwargs = {k: eval(v) if v in "TrueFalseNone" else v for k, v in props.items() if k in params} # only pass known params
        out = _highlight(data, css_class=_class, **kwargs)
        leftover = {k: v for k, v in props.items() if k not in params} # left over attributes
        if leftover:
            out = re.sub(r"^<div([^>]*)>", rf"<div\1 {_inline_style(leftover)} {attrs}>",out, count=1)
        return [XTML(out)]
                
    def _parse_table(self, data, widths, _class, props, attrs):
        out = self._parse_nested(data, returns=True) # let table extension handle it
        props["caption-side"] = props.get("caption-side", "top") # default caption side
        repl = f"<table class='{_class}' {_inline_style(props)} {attrs}>\n"
    
        def _caption_repl(m: re.Match):
            if m.group(1): # return first group
                nonlocal repl
                repl += f"<caption>{m.group(1)}</caption>"
            return ""
        # subsutute <p> </p> tags with caption tag
        out = re.sub(r'<p>(.*?)</p>', _caption_repl, out, count=1, flags=re.DOTALL) # only single caption
        if widths: # widths are given, add them
            repl += ('<colgroup>' + ''.join(f"<col style='width:{w}%;'>" for w in widths) + '</colgroup>')
        out = re.sub(r'<table[^>]*>', repl, out, count=1, flags=re.DOTALL)
        return [XTML(out)] # return table as is, it will be parsed by table extension
        
    def _parse_md_src(self, data, header):
        pos, *collapse = header.strip(' :')[3:].split() # if ::: md-[suffix] [-c], clean :::
        _class = ' '.join(collapse[1:] if collapse and collapse[0] == "-c" else collapse)
        _req_pos = "before,after,left,right"
        if pos not in _req_pos:
            return [error("ValueError",f"The suffix after md- should be {_req_pos}, got {pos}")]
        if collapse and collapse[0] not in ("","-c"):
            return [error("ValueError",f"Only swicth -c expected if given to collapse code after md-[suffix] other than CSS class, got {collapse[0]}")]
        src = XTML(_highlight(data, "markdown", name=False if collapse else None, css_class=f"md-src {_class}"))
        if collapse:
            src = XTML(f"<details><summary>Show Markdown Source</summary>\n{src}\n</details>")
        
        if self._returns: # display context
            outs = [XTML(self._parse_nested(data, returns=True))]
        else:
            with capture_content() as cap:
                self._parse_nested(data, returns=False)
            outs = cap.outputs
        
        if pos in ("before","after"):
            return [src, *outs] if pos == "before" else [*outs, src]
        
        if self._returns: 
            objs = (src, outs[0]) if pos == "left" else (outs[0], src) # return mode, len(outs) == 1
            output = "\n".join(f"<div style='width:50%;overflow-x:auto;height:auto;position:relative;'>{v}</div>" for v in objs)
            return [XTML(f'<div class="columns md-block" style="display:flex;">\n{output}\n</div>')] # display for notebook
        
        with capture_content() as cap:
            self._wr.write(*((src, outs) if pos == "left" else (outs, src)), css_class="md-block")
        return cap.outputs


    def _parse_multicol(self, data, widths, _class):
        "Returns parsed block or columns or code, input is without ``` but includes langauge name."
        cols = re.split(r"^\+\+\+\s*$", data, flags=re.MULTILINE)  # Split by columns, allow nesetd blocks by indents
        if not widths:
            widths = [100/len(cols) for _ in cols]
        else:
            if len(widths) > len(cols): # This allows merging column notation with frames
                for _ in range(len(cols), len(widths)):
                    cols.append("")

            if len(widths) < len(cols):
                return [error('ValueError',
                    f"Number of columns '{len(cols)}' should be <= given widths {widths}"
                )]

            widths = [float(w) for w in widths]
            widths = [100*w/sum(widths) for w in widths] # allow relative column widths
        
        # Under any display context
        if not self._returns:
            cap_cols = []
            for col in cols:
                with capture_content() as cap:
                    self._parse_nested(col,returns=False)
                cap_cols.append(cap)

            with capture_content() as cap:
                self._wr.write(*cap_cols, widths=widths, css_class=_class)
            
            return cap.outputs
        
        cols = [self._parse_nested(col,returns=True) for col in cols]
        if len(cols) == 1: # do not return before checking widths and adding extra cols if needed
            return [XTML(f'<div class={_class}">{cols[0]}</div>' if _class else cols[0])]

        cols = "".join(
            [f"""<div style='width:{w}%;overflow-x:auto;height:auto;position:relative;'>{col}</div>"""
                for col, w in zip(cols, widths)])

        return [XTML(f'<div class="columns {_class}" style="display:flex;">{cols}\n</div>')] # display for notebook
    
    def convert(self, text):
        """Replaces variables with placeholder after conversion to respect all other extensions.
        Returns str or list of outputs based on context. To ensure str, use `parse(..., returns=True)`.
        """
        text = resolve_included_files(text)
        text = re.sub(r"\\\`", "&#96;", text)  # Escape backticks after files added
        text = re.sub(r"\\%\{", r"&#37;{", text) # Escap \%{, before below latest addition of variables %{var}

        # Now let's convert old `{var}` to new  %{var} for backward compatibility
        text = re.sub(r"\`\{([^{]*?)\}\`", r"%{\1}", text, flags=re.DOTALL)

        text = self._resolve_nested(text)  # Resolve nested objects in form func`?text?` to func`html_repr`
        if self._slides and self._slides.this: # under building slide
            text = re.sub("ESCAPED_AT_SYMBOL","@", resolve_objs_on_slide(
                self, self._slides, re.sub(r"\\@","ESCAPED_AT_SYMBOL", text) # escape \@cite_key before resolving objects on slides
            ))  # Resolve objects in xmd related to current slide
        text = re.sub(r"\\@","@", text) # same stuff when goes off slides, should be correct
        
        # Resolve <link:label:origin text> and <link:label:target text?>
        text = re.sub(r"<link:([\w\d-]+):origin\s*(.*?)>", r"<a href='#target-\1' id='origin-\1' class='slide-link'>\2</a>", text)
        text = re.sub(r"<link:([\w\d-]+):target\s*(.*?)>", r"<a href='#origin-\1' id='target-\1' class='slide-link'>\2</a>", text)

        # Replace fa`name` with <i class="fa fa-name"></i>
        text = re.sub(r"fa\`([^\`]+?)\`", lambda m: f"<i class='fa fa-{m.group(1).strip()}'></i>", text)
        
        # _resolve_vars internally replace escaped \` and `%{ back to ` and %{ 
        return self._resolve_vars( # reolve vars after conversion
            super().convert(
                self._sub_vars(text) # sub vars before conversion
            ))
    
    def _var_info(self, match_str):
        try: 
            obj = self._vars[match_str]
            ctx = self._vars.get(f"{match_str}_ctx", '')
            return f"The object {type(obj).__name__!r}" + (f" (returned by {ctx!r})" if ctx else "")
        except: 
            return self._vars.get(f"{match_str}_ctx", match_str) # fallback to match ctx/group
    
    def _resolve_vars(self, text):
        "Substitute saved variables"
        if re.findall(r'DISPLAYVAR(\d+)DISPLAYVAR', text):
            if self._returns:
                text = re.sub(
                    r'DISPLAYVAR(\d+)DISPLAYVAR', 
                    lambda m: error(
                        'DisplayError',
                        f'{self._var_info(m.group())} cannot be displayed in current context '
                        'because markdown parser was requested to return a string by the caller. '
                        'You may use a display context such as write function or columns block in '
                        'display mode (+++ separtor used in multicol/columns) to show object properly.'
                    ).value,
                    text
                )
                self._resolve_vars(text)
            else:
                objs = []
                for i, block in enumerate(re.split('DISPLAYVAR', text), start=1):
                    content = block.strip() # Avoid empty objects
                    if i % 2 == 0:
                        key = f"DISPLAYVAR{content}DISPLAYVAR"
                        objs.append(self._vars.get(key, error('KeyError',f'Variable {self._var_info(key)!r} is not accessible')))
                    elif (content := tagfixer.fix_html(content)):
                        objs.append(XTML(self._resolve_vars(content)))
                return objs

        out = re.sub(r"PrivateXmdVar(\d+)X", lambda m: self._vars.get(m.group(), m.group()), text)
        # replacing backtick and %{, sometimes it leads to &amp;, need to cover it
        return re.sub(r"&(?:amp;)?#(?:96;|37;\{)", lambda m: "`" if "96" in m.group() else "%{", out)
    
    def _handle_var(self, value, ctx=None): # Put a temporary variable that will be replaced at end of other conversions.
        if isinstance(value, (str, XTML)): 
            key = f"PrivateXmdVar{len(self._vars)}X" # end X to make sure separate it 
            # Handle nested like center`alert`text`` things before saving next varibale
            self._vars[key] = self._resolve_vars(value if isinstance(value, str) else value.value) 
        else: # Handles TOC, DOMWidget and Others rich displays
            key = f"DISPLAYVAR{len(self._vars)}DISPLAYVAR"
            self._vars[key] = value # Direct value stored
        
        if ctx: # for better error message
            self._vars[key + '_ctx'] = ctx
        return key
    
    def _sub_vars(self, html_output):
        "Substitute variables in html_output given as %{var}."   
        user_ns = self.user_ns() # get once, will be called multiple time
        # Replace variables first to have small data
        def handle_match(match):
            key,*_ = _matched_vars(match.group()) 
            if key not in user_ns: # top level var without ., indexing not found
                err = error('NameError', f'name {key!r} is not defined')
                return self._handle_var(error('Exception', f'Could not resolve {match.group()!r}:\n{err}'))

            cmatch = match.group()[2:-1].strip().split('!')[0] # conversion split
            key, *fmt_spec = cmatch.rsplit(':',1) # split from right, could be slicing
           
            if ('[' in key) and (not ']' in key): # There was no spec, just a slicing splitted, but don't need to throw error here based on that
                key = ''.join([key,':',*fmt_spec])
                fmt_spec = ()
            try:
                value, _ = hfmtr.get_field(key, (), user_ns)
            except Exception as e:
                return self._handle_var(error('Exception', f'Could not resolve {match.group()!r}:\n{e}'))
            
            if isinstance(value, DOMWidget) or 'nb' in fmt_spec: # Anything with :nb or widget
                return self._handle_var(value,ctx = match.group()) 
            return self._handle_var(hfmtr.vformat(match.group()[1:], (), user_ns))
        
        html_output = re.sub(r"%\{([^{]*?)\}", handle_match, html_output, flags=re.DOTALL)

        # Replace inline  functions
        from . import utils  # Inside function to avoid circular import

        for func in _special_funcs.keys():
            all_matches = re.findall(
                rf"(?<!\`){func}(\[.*?\])?\`(.*?)\`", html_output, flags=re.DOTALL | re.MULTILINE
            ) # returns two matches always, don't match like `image` or and keep trying forward for no reason
            for m1, m2 in all_matches:
                _func = getattr(utils, func)
                arg0 = m2.strip() # avoid spaces in this

                if not m1:
                    try:
                        _out = (_func(arg0) if arg0 else _func()) # If no argument, use default
                    except Exception as e:
                        _out = error('Exception', f"Could not parse '{func}`{m2}`': \n{e}")
                    html_output = html_output.replace(f"{func}`{m2}`", self._handle_var(_out), 1)
                else: # func with arguments
                    try:
                        _out = eval(f"utils.{func}({arg0!r},{m1[1:-1]})" if arg0 else f"utils.{func}({m1[1:-1]})") # evaluate
                    except Exception as e:
                        _out = error('Exception',
                            f"Could not parse '{func}{m1}`{m2}`': \n{e}\nArguments in [] should be proper Python code that does not rely on a scope "
                            f" and are passed to {func}{inspect.signature(_func)} except first argument which is the text to be processed."
                        )
                    html_output = html_output.replace(f"{func}{m1}`{m2}`", self._handle_var(_out), 1)
        
        html_output = re.sub(r'\^\`([^\^]+?)\`',r'<sup>\1</sup>', html_output) # superscript
        html_output = re.sub(r'\_\`([^\_]+?)\`',r'<sub>\1</sub>', html_output) # subscript
        return re.sub(r"&(?:amp;)?#96;","`", html_output)  # return in main scope


def parse(xmd, returns = False):
    r"""Parse extended markdown and display immediately.
    If you need output html, use `returns = True` but that won't display variables.

    **Example**
    ```markdown
     # Normal Markdown
     ```multicol 40 60
     # First column is 40% width
     If 40 60 was not given, all columns will be of equal width, this paragraph will be inside info block due to class at bottom
     {.info}
     +++
     # Second column is 60% wide
     This \%{var_name} (or legacy \`{var_name}\`) can be substituted with `fmt` function or from notebook if whole slide is built with markdown.
     ```

     ```python
     # This will not be executed, only shown
     ```
     stack`Inline-column A || Inline-column B`
    ```

    ::: note-info
        - Each block can have class names (speparated with space or .) after all other options such as `python .friendly` or `multicol .Sucess.info`.
            - For example, `python .friendly` will be highlighted with friendly theme from pygments.
            - Pygments themes, however, are not supported with `multicol`.
            - You need to write and display CSS for a custom class.
        - The block with `::: class_type` syntax accepts extra classes in quotes, for example `::: multicol "Success" "info"`.
        - There are special CSS classes `jupyter-only` and `export-only` that control appearance of content in different modes.

    ::: note-warning
        Nested blocks are supported via indentation in `md-[before,after,left,right]` and `multicol`, but may be broken in display contexts.

    ::: note-info
        - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        - Use `Slides.extender` or `ipyslides.xmd.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
    """
    return XMarkdown()._parse(xmd, returns = returns)

def _matched_vars(text):
    matches = [var 
        for slash, var, _ in re.findall(
            r"([\\]*?)%\{\s*([a-zA-Z_][\w\d_]*)(.*?)\s*\}", # avoid \%{ escape, [\w\d_]* means zero or more word, to allow single letter
            re.sub(r"\`\{([^{]*?)\}\`", r"%{\1}", text, flags=re.DOTALL), # backward `{var}` compatibility
            flags = re.DOTALL,
        ) if not slash
    ]
    return tuple(matches) 
    
def _fig_caption(text): # need here to use in many modules
    return f'<figcaption class="no-zoom">{parse(text,True)}</figcaption>' if text else ''


class fmt:
    """Markdown string wrapper that will be parsed with given kwargs lazily. 
    If markdown contains variables not in kwargs, it will try to resolve them 
    from local/global namespace and raise error if name is nowhere. Use inside
    python scripts when creating slides. In notebook, variables are automatically 
    resolved, although you can still use it there.
    
    Being as last expression of notebook cell or using self.parse() will parse markdown content.
    """
    def __init__(*args, **kwargs):
        if len(args) != 2:
            raise ValueError("fmt expects a markdown str as positional argument!")
        
        self, xmd = args  # this enables user passing self and xmd into kwargs
        if not isinstance(xmd, str):
            raise TypeError(f"xmd expects a string got {type(xmd)}")
        
        self._xmd = xmd
        req_vars = _matched_vars(xmd)
        self._kws = {k:v for k,v in kwargs.items() if k in req_vars} # remove extras

        missing_keys = set(req_vars) - kwargs.keys()

        # We will fetch missing variables from caller's scope if possible
        if missing_keys:
            frame = inspect.currentframe()
            try:
                c_locals = frame.f_back.f_locals
                c_globals = frame.f_back.f_globals
                # Merge kwargs with any missing values from caller
                for key in missing_keys:
                    if key in c_locals:
                        self._kws[key] = c_locals[key]
                    elif key in c_globals:
                        self._kws[key] = c_globals[key]
                    else:
                        raise NameError(f"name {key!r} is not defined")
            finally:
                del frame  # Prevent reference cycles
    
    def __str__(self):
        _kws = ',\n'.join([f"{k} = \'<{getattr(type(v),'__name__','object')} at {hex(id(v))}>\'" for k,v in self._kws.items()])  
        _kws = f',\n{_kws}\n)' if _kws else ")"    
        return f'fmt("""\n{self._xmd}\n"""{_kws}'

    def parse(self,returns=False):
        "Parse the associated markdown string."
        return parse(self if self._kws else self._xmd, returns=returns) # handle empty kwargs silently

    @classmethod
    def _astuple(cls, target): # This is required to handle form_markdown
        "Return (markdown, kwargs) of supplied markdown and kwargs if target is of same type. If str, returns (target, {})"
        if isinstance(target, fmt):
            return (target._xmd, target._kws)
        elif isinstance(target, str):
            return (target, {})
        else:
            raise TypeError(f"_astuple expects str or fmt, got {type(target)}")

    def _ipython_display_(self): # to be correctly captured in write etc. commands
        with altformatter.reset(): # don't let it be caught in html conversion
            self.parse(returns = False)
        
    def _repr_html_(self): # for functions to consume as html and for export
        return parse(self if self._kws else self._xmd, returns=True)

    