# This package exports xmd at top level.

import textwrap, sys, string, builtins, inspect, ast
import re, secrets # secrets for unique keys
from itertools import islice
from functools import partial
from contextlib import contextmanager
from html import escape # Builtin library
from io import StringIO
from html.parser import HTMLParser
from typing import Optional, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from markdown import Markdown
from IPython.display import display
from IPython.utils.capture import capture_output, CapturedIO
from ipywidgets import DOMWidget

from .formatters import (XTML, altformatter, htmlize, get_slides_instance, 
    frozen, widget_from_data, _highlight, _inline_style, _delim)
from .source import SourceCode

_md_extensions = [
    "tables",
    "footnotes",
    "attr_list",
    "md_in_html",
    "def_list",
]  # For Markdown Parser
_md_extension_configs = {}

class Extensions:
    """Adds extensions to the Markdown parser. See [Website of Python-Markdown](https://python-markdown.github.io/extensions/)
    and [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/) for available extensions."""
    def __init__(self):
        self._exts = []
        self._configs = {}

    def __repr__(self) -> str:
        return "Extensions: {}\nConfigs: {}".format(*self.active.values())

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
        return {
            "extensions": list(set([*self._exts, *_md_extensions])), 
            "extension_configs": {**self._configs, **_md_extension_configs}
        }
        
# NEVER allow random functions, only xmd.register is gateway for security,
# as well as scope, like a function inside python script is not in notebook user namespace to access here
_XMD_FUNCS = {} # will be populated by decorated functions

def _internal_xmd_call(fname, slidebound=False):
    "Decorator to register a function as an internal xmd function."
    def decorator(func):
        nonlocal fname, slidebound
        _XMD_FUNCS[fname] = (func, "slide" if slidebound else "module") # store function and whether it is slidebound
        return func
    return decorator

def error(name, msg):
    "Add error without breaking execution."
    return XTML(f"<pre class='Error'><b style='color:crimson;'>{name}</b><span>: {msg}</span></pre>")

def warn(msg, name="UserWarning"):
    "Show warning message in slides but not in fullscreen mode."
    return XTML(f"<pre class='Error Warn jupyter-only'><b style='color:orange;'>{name}</b><span>: {msg}</span></pre>")

@_internal_xmd_call('raw')
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
        
def _resolve_citations(parser, content):
    "Resolve citations and other minimal stuff that can't nest other functions."
    slides = get_slides_instance()
    if not slides or not slides.this: # under building slide
        return content # no need to resolve anything

    AT_KEYS = re.compile(r'''
        (?<!\\) # negative lookbehind: don't match if there's a backslash
        (?<!\w) # Don't match if a word before so example@google.com is safe
        (?<!\`) # Don't match keys inside backticks
        @(?:[A-Za-z_]\w*!?)(?:\s*,\s*@(?:[A-Za-z_]\w*!?))*   # @key, @key2!, @key3 (single or comma-separated)
    ''', re.VERBOSE)
    
    def sub_cite(match):
        keys = [k.strip().lstrip('@') for k in match.group().split(',')] # split by comma and remove leading @
        # group keys types, superscript citations first, then inline
        sup_keys = ",".join(k for k in keys if not k.endswith('!'))
        inline_keys = [k for k in keys if k.endswith('!')]
        
        # First handle superscript citations in a group
        res = parser._handle_var(slides._cite(sup_keys)) if sup_keys else ""
        # Then handle inline citations
        for key in inline_keys:
            res += slides._nocite(key[:-1]) # remove ! at end for inline citations
        return res
    
    # replace @key, @key2! etc with citation output
    content = AT_KEYS.sub(sub_cite, content)  
    return content


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

class char_esc:
    r"""Utility class for escaping and restoring special characters using backslash in text."""
    _chars = r"`@%|/<>:;!.,+-" # Characters to escape

    @classmethod
    def escape(cls, text):
        """Escape characters by replacing with tokens."""
        for ch in cls._chars:
            text = text.replace(rf"\{ch}", f"ESC-{ord(ch):03}-CHR")
        return text

    @classmethod
    def restore(cls, text, ascii_backtick=False):
        """Restore escaped tokens back to original characters. ` -> &#96; if ascii_backtick is False (default)."""
        for ch in cls._chars:
            repl = r"&#96;" if ch == '`' and not ascii_backtick else ch
            text = text.replace(f"ESC-{ord(ch):03}-CHR", repl)
        return text
    
class esc:
    r"""Lazy escape of variables in markdown using python formatted strings, to be resolved later and safe from markdown parsing.
    Use as [code! xmd(f"This is an escaped variable: {esc(var or expression)}") /]
    or [code! xmd("This is an escaped variable: {}".format(esc(var or expression))) /].
    This is in par with \%{var} syntax, but more flexible as it can take any expression. 
    You are advised to use formatting strings rarely, instead use `xmd.gather` class to provide variable (also, automatically pick from local scope)
    and avoid clashes with $ \LaTeX $ syntax.
    """
    _store = {} # stores escaped varaibles here from formatting.
    
    def __init__(self, obj, display=False):
        self._key = f'ESC_VAR_{id(self)}{"DISPLAY" if display else ""}' # unique key
        self.__class__._store[self._key] = obj # store it
        
    def __format__(self, format_spec):
        return f"%{{{self._key}:{format_spec}}}" # return placeholder for later formatting
    
@_internal_xmd_call('load')
def load(filepath : str, start:int=None, end=None):
    "Load markdown file content in place. Use `start` and `end` to specify line numbers range."
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()[slice(start,end)]
            if lines:
                lines = [f'<!-- begin: {filepath} -->\n', *lines, f'<!-- end: {filepath} -->\n']
            return filepath, "".join(lines)
    except Exception as e:
        return filepath, error('Exception', f'Could not load content from file {filepath!r}:\n{e}').value

_extensions = Extensions() # Global instance of Extensions, don't delete class Extensions still

# Internal cache to avoid re-compiling regex for every slide/fragment
_PATTERN_CACHE = {}

class cmnt_esc:
    "Important to escape HTML comment to avoid parsing syntax inside it"
    _store = {} # stores escaped comments here from formatting.
    _COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL | re.MULTILINE)
    _TOKEN_RE = re.compile(r"<!-- ESC-[0-9a-f]{16}-CMT -->") # 16 hex digits key
    
    @classmethod
    def _ukey(cls):
        while True: # avoid collision, though very unlikely
            key = f'<!-- ESC-{secrets.token_hex(8)}-CMT -->' # keep as comment to avoid issues if can't be replaced
            if key not in cls._store:
                return key
            
    @classmethod
    def escape(cls, text):
        def _mask(m):
            key = cls._ukey()
            cls._store[key] = m.group(0)
            return key
        
        return cls._COMMENT_RE.sub(_mask, text)
    
    @classmethod
    def restore(cls, text):
        def _unmask(m):
            key = m.group(0)
            if cls._store.get(key, None) is None:
                return key  # leave unknown token unchanged
            return cls._store.pop(key)  # Remove used key from the store to free memory

        return cls._TOKEN_RE.sub(_unmask, text)
    

PLUS_RE = re.compile(r'^\+\+(?:\[(?P<opt>[^\]\n]+)\])?(?:\s*$|\s)', re.MULTILINE) # This is used to split by ++ on its own line,
DOTS_RE = re.compile(r'(?<!\S)\.\.(?!\S)') # Count only standalone ".." tokens (surrounded by whitespace or string boundaries)
VARS_RE = re.compile(r"%\{([^{]*?)\}", flags=re.DOTALL)
FUNC_RE = re.compile(
    r"(?<![\\\`])"            # not preceded by backslash or backtick
    r"\[([a-zA-Z_]\w*)(!{1,2})(?![!])\s*"         # [name! / [name!! but not more !, with optional spaces, must not start with a digit
    r"((?:(?!\[[a-zA-Z_]\w*!)[\s\S])*?)"  # body; stop before a nested macro opener
    r"\s*/\]",            # closing /] must stay free so sub/sup before text can stay closer
    flags = re.DOTALL | re.MULTILINE
)

def strip_ptags(content):
    "Strip <p> and </p> tags from the start and end of the content, if present."
    return re.sub(r"^<p>\s*|\s*</p>$", "", content) # clean up internal spaces as well, but no stripping outside if no p tags

class XMarkdown(Markdown):
    def __init__(self):
        super().__init__(**_extensions.active)
        self._vars = {}
        self._returns = True
        self._nesting_depth = 0 # checks if using _parse in nested manner
    
    @property
    def _wr(self):
        if not hasattr(self, '_wr_imported'):
            from . import writer # avoid cyclic, but import once
            self._wr_imported = writer
        return self._wr_imported
    
    @property
    def _slides(self):
        return get_slides_instance() # always get the current slides instance, not cached
    
    @property
    def _running_md_slide(self): # checks if parsing under purely markdown slide
        return self._slides and self._slides.this and self._slides.this._markdown
    
    def user_ns(self):
        "Top level namespace or set by user from `xmd.gather`."
        if hasattr(BoundXMD, '_bound_vars'):
            return BoundXMD._bound_vars

        if self._running_md_slide:
            return { 
                **self._slides._nb_vars, # Top level notebook scope variables
                **self._slides.this._md_vars, # by Slide
                **self._slides.this._esc_vars, # escaped variables stored on slide
            } # slide specific variables based on scope
        return get_main_ns()  # top scope at end

    def _parse(self, xmd, returns = True, tag=None): # not intended to be used directly
        """Return a string after fixing markdown and code blocks returns = True
        otherwise displays objects given as vraibales may not give their proper representation.
        """
        self._returns = returns  # Must change here
        if not isinstance(xmd, str):
            issue = error("TypeError",f"Expected a string for markdown content, got {type(xmd)} instead.")
            return issue.value if returns else display(issue) # return value or display
        
        # resolve loading files first, before any processing
        _, xmd = _load_files(xmd)
        
        # Mask HTML comments before any splitting so their content (:::, ++, ```) is not treated as markers.
        # Python-Markdown passes <!--...--> through unchanged, so short placeholders survive convert().
        xmd = cmnt_esc.escape(char_esc.escape(xmd))  # Escape characters as well before processing

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
                outputs.extend(self._parse_block(*obj))  
                continue # vars are substituted already inside, obj = (header, data)

            for part in _split_parts(obj, delimited=True):
                if not isinstance(part, str):
                    outputs.append(part) # Delimiter
                    continue
                
                out = self.convert(part) 
                if isinstance(out, list):
                    outputs.extend(out)
                elif out: # Some syntax like section on its own line can leave empty block after conversion
                    outputs.append(XTML(out))

        if not self._nesting_depth: # we need to keep these if nested parsing
            self._vars = {} # reset at end to release references

        if returns:
            content = ""
            for out in outputs:
                if isinstance(out, XTML):
                    content += out.value
                else:
                    content += self._wr._fmt_html(out) # Rich content from python execution and Writer
            content = char_esc.restore(cmnt_esc.restore(content))
            
            if tag is not None:
                content = strip_ptags(content) # strip <p> tags if tag is specified, for inline content
                if name:= tag.strip(): # empty tag returns bare content
                    content = f'<{name}>\n{content}\n</{name}>'
            return content
        else:
            return display(*outputs)
            
    def _parse_params(self, param_string):
        """Parse parameter string with simple regex."""
        RE_PARAM = re.compile(
            r'(?:([\w\-.]+)=)?'
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
                if post_slash or key.strip().startswith('data-'): # node attributes
                    node_attrs[key] = value
                else:
                    kwargs[key] = value
            else:
                if value.isdigit() or re.match(r'^\d+(\.\d+)?$', value):
                    numbers.append(float(value) if '.' in value else int(value))
                else:
                    value = (value.replace('.',' ') if args else value).strip() # remove . from classes except from directive name
                    node_attrs.update({value: None}) if post_slash else args.append(value) # if after /, treat as non-value as void attributes such as open
                    
        sizes = numbers if numbers else None # making None is important for columns and stack 
        # flatten node_attrs to a string, but not css properties
        node_attrs = ' '.join(f'{k}="{v}"' if v is not None else k for k, v in node_attrs.items())
        
        if args:
            typ, mode = [v.strip() for v in args[0].split('.',1)] if '.' in args[0] else (args[0], '')
            if typ == "multicol": typ = "columns" # backward-compatible alias
            return typ, mode, sizes, ' '.join(args[1:]), kwargs, node_attrs # block type, mode, sizes, className, css_props, node_attrs
        return '', '', sizes, '', kwargs, node_attrs
    
    def _parse_args(self, param_str, content=None):
        "Parse inline function arguments and keyword arguments from a string using ast.literal_eval."
        # Must avoid using eval() for security reasons. ast.literal_eval is safe for literals.
        if not param_str or not param_str.strip():
            return () if content is None else (content,), {}

        call_node = ast.parse(f"dummy({param_str})").body[0].value
        args, kwargs = [], {}
        
        for arg in call_node.args:
            arg = ast.literal_eval(arg)
            if isinstance(arg, str):
                arg = self._resolve_vars(arg)  # Resolve variables in string arguments
            args.append(arg)
        
        for kw in call_node.keywords:
            karg = ast.literal_eval(kw.value)
            if isinstance(karg, str):
                karg = self._resolve_vars(karg)  # Resolve variables in string keyword arguments
            kwargs[kw.arg] = karg
        
        # We are not resolving vars in content yet here
        if content is not None:
            args = [content, *args] 
    
        return tuple(args), kwargs

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
            still_header, still_block = True, True # still header or block, until non-indented line
            for line in islice(lines, 1, None): # skip first line
                if still_header and line.startswith(':'): # indented line, part of block header
                    header += line.replace(':',' ',1).rstrip()
                else:
                    still_header = False # no more header
                    if still_block and re.search(r'^\s+', line): # indented line with one or more spaces
                        block_body += line # indented block body
                    else:
                        still_block = False # no more block body
                        text_chunk += line # text chunk, not part of block
            
            header = char_esc.escape(header)  # Escape characters in header before splitting
            if DOTS_RE.search(header): # if header has .. then it is a block with same line content
                header, rest_line = DOTS_RE.split(header, maxsplit=1) # split at first .., rest is block body
                if not block_body.strip(): # if block body is empty but header has pipe, then it is inline block
                    block_body = rest_line.strip() # treat rest of line as block body
            header = char_esc.restore(header)  # Restore characters in header after splitting
            
            if block_body.strip(): # block comes first, only if not empty
                blocks.append(("block", (header, block_body)))
            if text_chunk.strip(): # text chunk comes after block
                blocks.append(("raw", text_chunk)) # keep text as it is
        return blocks       
    
    def _parse_nested(self, xmd, returns=True, tag=None):
        old_returns = self._returns
        self._nesting_depth += 1 # increase nesting depth
        try:
            out = self._parse(textwrap.dedent(xmd), returns=returns, tag=tag) # allows nesting via indent
        finally:
            self._returns = old_returns
            self._nesting_depth -= 1 # decrease nesting depth
        return out

    def _handle_syntax_error(self, content):
        content = re.sub(r"<link:([\w\d-]+):(origin|target)\s*(.*?)>", error('SyntaxError', r'The `&lt;link: ...&gt;` syntax is deprecated. Use `link` function instead.').value, content)
        content = re.sub(r"(?<![\`\\])\<md-([\w]+)/\>", error('SyntaxError', r'The `&lt;md-var/&gt;` syntax is deprecated. Use `[md-var/]` instead.').value, content)
        content = re.sub(r'(?: )?[\^\_]\`([^\`]*?)\`',error('SyntaxError', r'Legacy syntax _\`...\`, ^\`...\` is deprecated. Use `sub/sup` functions instead.').value, content) 
        
        # legacy nesting with 2+ slashes
        if re.search(r"\`(?P<slashes>/{2,})(.*?)(?P=slashes)\`", content, flags=re.DOTALL | re.MULTILINE):
            content = self._handle_var(error("SyntaxError",
                "Nested `// //` syntax is deprecated. New format [func! ... /] automatically support nesting."
            )) + "\n" + content
        
        # legacy functions syntax
        legacy_funcs = rf"(?<![\`\.])\b({('|'.join(_XMD_FUNCS))})(\[.*?\])?\`([^\`]*)\`"
        if match := re.search(legacy_funcs, content, flags=re.DOTALL | re.MULTILINE):
            content = self._handle_var(error("SyntaxError",
                f'Legacy inline function syntax {match.group()} is deprecated. '
                f'Use [{match.group(1)}! ... /] format for flexible automatic nesting, see slides.xmd.funcs for details.'
            )) + "\n" + content
        
        # legacy citations
        content = re.sub(r"(?<![\`\.])\bcite\`(.*?)\`;?", 
            lambda m: self._handle_var(error('SyntaxError',f'Use @key, @key2!, @key3 etc. {m.group()} syntax is deprecated.')), 
            content, flags=re.DOTALL
        )
        return content

    def _parse_block(self, header, data):
        "Returns list of parsed block or columns or code, input is without ``` but includes langauge name."
        typ, mode, widths, _class, css_props, attrs = self._parse_params(header)
        
        if typ == "citations": # avoid using citations block
            return [error("ValueError", f"Use '--- citations ---' syntax at the end of the synced markdown file instead of a citations block.")]
        elif typ == "display":
            with self.active_parser(), capture_content() as cap:
                self._wr.write(data, css_class=_class, **css_props)
            return cap.outputs
        elif typ == "group":
            return [error("RuntimeError", "'group' markdown block is deprecated. Use 'columns.paused' or 'steps' instead.")]
        elif typ == "columns" and mode in ("", "paused"): # handle columns with display mode
            return self._parse_columns(data, widths, _class, css_props, mode=mode) # simple columns will be handled inline 
        elif "md-" in typ:
            return self._parse_md_src(data, header)
        elif typ == "table":
            return self._parse_table(data, widths, _class, css_props, attrs)
        elif typ == "code":
            return self._parse_code(data, mode, widths, _class, css_props, attrs)
        elif header.strip().startswith(":::") or typ == "columns": # simple columns.inline
            return self._parse_colon_block(header, data)
        else:
            out = XTML() # empty placeholder
            data = char_esc.restore(cmnt_esc.restore(data)) # restore comments before highlighting
            try:
                name = " " if typ.lower() == "text" else None
                out.data = _highlight(data, language=typ, name=name, css_class=_class) # intercept code highlight
            except:
                out.data = super().convert(f'```{header}\n{data}\n```') # Let other extensions parse block
            
            return [out,] # list is required
    
    def _ignore_incremental(self, data):
        # Just ignore, don't ask user change their content if they can switch mode to paused or inline
        return PLUS_RE.sub('', data) # remove ++ lines, but keep content
    
    def _handle_inline_cols(self, data):
        "Check if columns are on a single line and split them by | separator to make them multi-line for proper parsing."
        if (line := data.strip()) and re.fullmatch('^.*$', line): # single line columns
            data = re.sub(r'\s+\|\s+', '\n--\n', line) # ensure | is spaced
        return data
        
    def _parse_colon_block(self, header, data):
        STRICT_TAGS = ("pre","raw") # code is handled separately
        CAPTURED_TAGS = ("p","details","summary","center","blockquote","ul","ol", "li", "nav", *STRICT_TAGS) # tags that are captured by this parser
        
        tag, mode, widths, _class, css_props, attrs = self._parse_params(header)
        
        if tag == "columns":
            if mode != "inline": # columns with display mode were already handled
                return [error("ValueError", f"Invalid block type '{tag}' with mode '{mode}'. Supported modes are 'inline' and 'paused' only!")]
            
            css_props = {"display":"flex", **css_props} # add display flex for in notebook formatting
            data = self._handle_inline_cols(data) # handle single line columns with | separator, do before adding warnings
            data = self._ignore_incremental(self._fix_legacy_col_sep(data)) # handle legacy mode and ++ separator
            
            if re.search(r'^\-\-\s*$', data, flags=re.MULTILINE): # make columns by optional -- separator
                data = XTML('<div>' + '</div>\n<div>'.join(
                    [self._parse_nested(c, returns=True) for c in _stream_chunks(data, sep='--')]
                ) + '</div>') # wrapping in divs is important otherwise can be so many columns based on parsed content
        
        if tag in CAPTURED_TAGS:
            if tag in STRICT_TAGS: # keep as is from further processing
                return [XTML(f"<pre class='{_class} raw-text' {_inline_style(css_props)} {attrs}>\n{data}\n</pre>")]
            
            # These tags should strip outer p tags for being properly structured as intended by user
            out = self._parse_nested(data, returns=True)
            if re.search(r'^<ul|^<ol|^<p|<nav', out): # these tags are difficult ones to style
                # remove these in case of ul, ol, p in single regex 
                out = re.sub(r'^<(p|ol|ul|nav)[^>]*>|</(p|ol|ul|nav)>$', '', out)
            return [XTML(f"<{tag} class='{_class}' {_inline_style(css_props)} {attrs}>{out}</{tag}>")]
        
        style = "" # style for columns if widths are given
        if tag == "columns"  and widths: # columns with inline mode
            klass = f"c-{id(widths)}" # unique class for columns
            _class = f"{_class} {klass}" if _class else klass # add klass
            widths = [float(w) for w in widths]
            widths = [w/(sum(widths) or 1) for w in widths] # allow relative column widths
            style = '\n'.join(f".{klass} > :nth-child({i+1}) {{flex: {w:.3f} {w:.3f} {100*w:.3f}%}}" for i, w in enumerate(widths)) # nth-child selectors
            style += '\n' + f".{klass} > :nth-child({len(widths)}) ~ * {{flex: {min(widths):.3f} {min(widths):.3f} {100*min(widths):.3f}% !important;}}" # rest all columns get min width
            style = f"<style>.{klass} > p:empty {{display:none;}}\n{style}</style>" # empty p tags should not be treated as columns
            
        # treat tag as class if not given at end
        _class = " ".join([tag, _class])
        data = data.value if isinstance(data, XTML) else self._parse_nested(data, returns=True) # -- columns parsed already
        return [XTML(f"<div class='{_class}' {_inline_style(css_props)} {attrs}>{data}</div>{style}")]
    
    def _parse_code(self, data, mode, focus_lines, _class, props, attrs):
        params = inspect.signature(_highlight).parameters.keys()
        kwargs = {k: eval(v) if v in "TrueFalseNone" else v for k, v in props.items() if k in params} # only pass known params
        data = char_esc.restore(cmnt_esc.restore(data)) # restore escape/comments before highlighting
        out = _highlight(data, css_class=_class, **kwargs)
        leftover = {k: v for k, v in props.items() if k not in params} # left over css properties
        if leftover:
            out = re.sub(r"^<div([^>]*)>", rf"<div\1 {_inline_style(leftover)} {attrs}>",out, count=1)
        out = SourceCode(out)
        if focus_lines:
            lines = lines=[int(l) - 1 for l in focus_lines] # convert to 0-based index for python
            if min(lines) < 0:
                return [error('IndexError',f"Focus lines {focus_lines} in markdown code blocks are 1-based index unlike python!")]
            out = out.focus(lines) 
        out.raw = textwrap.dedent(data) # attach raw code as well to access
        
        if mode and getattr(out, mode, None):
            out = getattr(out, mode) # get property if available
            
        return [out]
    
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
        typ, mode, focus_lines, _class, kwargs, attrs = self._parse_params(header) 
        kwargs["language"] = "markdown" # force markdown language anyhow
        src, = self._parse_code(data, mode, focus_lines, _class, kwargs, attrs) # list of one item
        if typ not in ("md-before", "md-after"):  # normal md block
            esc._store[typ[3:]] = src # store variable excluding md- prefix to have available in processing below
        outputs = []
        if "before" in typ: outputs.append(src)
        if self._returns: # display context
            outputs.append(XTML(self._parse_nested(data, returns=True)))
        else:
            with capture_content() as cap:
                self._parse_nested(data, returns=False)
            outputs.extend(cap.outputs)
        if "after" in typ: outputs.append(src)
        return outputs
    
    def _fix_legacy_col_sep(self, data):
        if re.search(r"^\+\+\+\s*$", data, flags=re.MULTILINE):
            data = re.sub(r"^\+\+\+\s*$", "--", data, flags=re.MULTILINE)  # Change to -- for backward compatibility
            data = "\n".join([error('SyntaxError','Use -- instead of legacy +++ to separate columns.').value, data]) # Prepend error to the data once
        return data
    
    def _parse_columns(self, data, widths, _class, css_props, mode=None):
        data = self._handle_inline_cols(data)  # Handle single line columns with | separator before adding extra warnings
        data = self._fix_legacy_col_sep(data)  # Fix legacy +++ column separators
        cols = list(_stream_chunks(data, sep='--'))  # Split columns by -- separator

        if len(cols) == 1: # full width one column
            widths = [100]
        elif not widths:
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
        cap_cols = []
        for col in cols:
            rows = [] # list to make row-wise parts
            for row in _split_parts(col):
                with capture_content() as cap:
                    if self._returns: self._show_disply_error = True # to show error in display var resolution if top level returns
                    try:
                        self._parse_nested(row,returns=False)
                    finally:
                        if hasattr(self, '_show_disply_error'): del self._show_disply_error # cleanup
                        
                rows.append(cap.outputs)
            cap_cols.append(rows)
            
        with self.active_parser(), capture_content() as cap:
            kwargs = {"css_class": _class, "paused": mode == "paused", **css_props}
            self._wr.write(*cap_cols, widths=widths, **kwargs)
            
        return cap.outputs
    
    def convert(self, text):
        """Replaces variables with placeholder after conversion to respect all other extensions.
        Returns str or list of outputs based on context. To ensure str, use `parse(..., returns=True)`.
        """
        text = self._handle_syntax_error(text) 
        text = self._resolve_md_vars(text)  # Resolve [md-var/] variables stored during md-var blocks
        # Reolve link targets as invisible span with id
        text = re.sub(r"(?<![\`\\])\[\#([\w\-]+)/\](?!\S)", r"<span id='\1' class='slide-link-target'></span>", text)
        # Resolve citations before variable substitution to avoid conflicts with citation keys
        text = _resolve_citations(self, text)  
        
        # _resolve_vars internally replace escaped \` and `%{ back to ` and %{ 
        return self._resolve_vars( # reolve vars after conversion, resets escaped characters too
            super().convert(
                self._sub_vars(text) # sub vars before conversion
            ))
    
    def _resolve_md_vars(self, text):
        # Replace [md-var/] variables stored during md-var blocks, 
        # but reusing snippets expose internal state, AVOID THAT
        all_matches = re.findall(r"(?<![\`\\])\[md-([\w]+)/\](?!\S)", text) # avoid `\ and end must
        for match in all_matches:
            value = esc._store.pop(match, error('NameError', f'Markdown variable {match!r} is not defined or already used!'))
            text = text.replace(f"[md-{match}/]", self._handle_var(value, f'::: md-{match}'), 1)
        return text
    
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
            if self._returns or getattr(self, '_show_disply_error', False):
                text = re.sub(
                    r'DISPLAYVAR(\d+)DISPLAYVAR', 
                    lambda m: error(
                        'DisplayError',
                        f'{self._var_info(m.group())} cannot be displayed in current context or nesting level '
                        'because markdown parser was requested to return a string by the caller. '
                        'Display contexts such as write function or markdown columns block in '
                        '(not columns.inline) display objects properly when the parser is called in display context.'
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
        return char_esc.restore(cmnt_esc.restore(out)) # restore comments and escaped characters
  
    def _handle_var(self, value, ctx=None): # Put a temporary variable that will be replaced at end of other conversions.
        if value is None: # Avoid None values such as coming from refs
            return '' # empty string
        
        if isinstance(value, (str, XTML)): 
            key = f"PrivateXmdVar{len(self._vars)}X" # end X to make sure separate it 
            # Handle nested funcs output before saving next variable
            self._vars[key] = self._resolve_vars(value if isinstance(value, str) else value.value) 
        else: # Handles TOC, DOMWidget and Others rich displays
            values = value.outputs if isinstance(value, CapturedIO) else [value] # if captured, get outputs
            keys = []
            for val in values:
                key = f"DISPLAYVAR{len(self._vars)}DISPLAYVAR"
                self._vars[key] = val # Direct value stored
                keys.append(key) 
            key = '\n'.join(keys) # join all keys for multiple outputs
        
        if ctx: # for better error message
            self._vars[key + '_ctx'] = ctx
        return key
    
    def _sub_vars(self, html_output):
        "Substitute variables in html_output given as %{var} and inline functions."   
        # Check for variables first
        if VARS_RE.search(html_output):
            user_ns = self.user_ns() # get once, will be called multiple time
            def handle_match(match):
                key,*_ = _matched_vars(match.group()) 
                # First check if it is an escaped variable
                if key in esc._store: # escaped variable
                    value = esc._store.pop(key) # remove after using once
                    if isinstance(value, DOMWidget) or key.endswith('DISPLAY'): # Anything with display or widget
                        return self._handle_var(value, ctx = match.group())
                    return self._handle_var(hfmtr.vformat(f"{{{match.group()[2:-1].strip()}}}", (), {key: value})) # clear spaces around variable
                
                if key not in user_ns: # top level var without ., indexing not found
                    err = error('NameError', f'name {key!r} is not defined')
                    if self._running_md_slide: # under slide building purely from markdown
                        err = err.value + ("You can update this variable by `Slides[int,|list|slice].vars.update` "
                            "or by defining it in notebook if `Auto Rebuild` is enabled.")
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

                if isinstance(value, DOMWidget) or 'nb' in fmt_spec: # Anything with :nb or widget or from escaped display variable
                    return self._handle_var(value,ctx = match.group()) 
                return self._handle_var(hfmtr.vformat(f"{{{match.group()[2:-1].strip()}}}", (), user_ns)) # clear spaces around variable

            html_output = VARS_RE.sub(handle_match, html_output) # replace all variables in html_output

        # Replace macros after variable, keep it nested for accessing inner state, but limit depth to avoid infinite recursion
        with self.active_parser(): # set instance parser to pass variables
            depth = 0
            while FUNC_RE.search(html_output):
                depth += 1
                html_output = FUNC_RE.sub(self.repl_py_func, html_output)
                if depth > 16: # prevent infinite loop
                    return self._handle_var(error('RecursionError', f"Too many nested macros (> 16) in '{html_output}'"))
        return html_output 
    
    def repl_py_func(self, match):
        fname, bangs, body = match.groups()
        ParamsFirst = bangs == '!!' # single ! means content first, !! means params first
        
        # By default, content None and argvs is str, handle [tag! /] and [tag!! /] empty call autoamtically
        content, argvs = None, body.rstrip() if isinstance(body, str) else "" # avoid losing indenttation, use rstrip
        
        if argvs.strip() == '..': 
            content, argvs = "", "" # handles [tag! .. /]  and [tag!! .. /] -> tag("")
        else:
            nsep = len(DOTS_RE.findall(argvs))
            if nsep > 1:
                return self._handle_var(error('ValueError', f"Too many '..' separators in \n'{match.group(0)}'.\nOnly one is allowed. Escape .. with backslash if needed"))
            elif nsep == 1:
                content, argvs = DOTS_RE.split(argvs, maxsplit=1) # content .. params case
                if ParamsFirst:
                    argvs, content = content, argvs # swap for [tag!! params .. content /] case
            elif argvs.strip(): 
                content, argvs = (None, argvs) if ParamsFirst else (argvs, "") # if no .., its content unless params first (then no content passed)
        
        # Process the function content and arguments, and call the corresponding function
        if fname == "anyTag":
            return self._handle_var(error('Exception', f"anyTag function cannot be called directly, use valid html [tag! node content .. **node_attributes /] instead!"))
        
        # resolve variables in content for certain functions as they take content out of flow
        if content is not None:
            content = textwrap.dedent(content).rstrip() # dedent content for better formatting, but keep leading spaces
            if fname in ("section", "toc", "notes"):
                content = self._resolve_vars(content) # variables are not accesible outside
            elif fname == "code": # code needs corrected content
                content = char_esc.restore(cmnt_esc.restore(content), True)
        
        # Must to keep check on internal calls
        if not "anyTag" in _XMD_FUNCS:
            return self._handle_var(error('Exception', f"ipyslides is partially initialized. Cannot parse {match.group(0)!r}"))
        
        func, ctx = _XMD_FUNCS.get(fname, _XMD_FUNCS["anyTag"])
        if 'anyTag' in getattr(func, '__name__', ''): # __name__ is not available on all types of callables
            func = partial(func, fname.strip('_').lower()) # partial function for anyTag with tag name, svg_ goes to svg tag, not svg function
        
        if ctx == "slide" and not getattr(self._slides, 'this', None): # slide only functions
            return self._handle_var(error('Exception', f"Slide-only function '{match.group(0)}' cannot be used outside a slide context!"))
        
        # Give user a cleaned parsed content 
        if ctx == "user" and isinstance(content,str):
            content = self._resolve_vars(
                strip_ptags(super().convert(content))
            ) # resolve variables in user context functions otherwise they will lose scope
        
        try:
            args, kwargs = self._parse_args(argvs, content)
        except Exception as e:
            return self._handle_var(error('Exception', f"Error parsing arguments for '{match.group(0)}': \n{e}\n"))
        
        # make sure inline displays are captured in correct place like matplotlib plots
        with capture_content() as cap:
            try:
                res =  func(*args, **kwargs)
                res = res.inline if fname == "code" else res # code function returns SourceCode object, not inline
            except Exception as e:
                res = error('Exception', f"Could not parse '{match.group(0)}': \n{e}\n"
                    f"<div class='block-yellow'>⚠️ Function '{fname}' expects arguments <code>{inspect.signature(func)}</code>, "
                    f"got <code>{args}, {kwargs}</code></div>")
        
        if fname == "load":
            return res # load function needs to flatten the content
        
        if cap.outputs:
            return self._handle_var(cap) + self._handle_var(res)
        return self._handle_var(res)
    
    @contextmanager
    def active_parser(self):
        XMarkdown._active_parser = self._parse_nested # keep instance parser to pass variables
        try:
            yield
        finally:
            if hasattr(XMarkdown, '_active_parser'):
                del XMarkdown._active_parser
    

def _matched_vars(text):
    matches = [var 
        for slash, var, _ in re.findall(
            r"([\\]*?)%\{\s*([a-zA-Z_][\w\d_]*)(.*?)\s*\}", # avoid \%{ escape, [\w\d_]* means zero or more word, to allow single letter
            text, flags = re.DOTALL,
        ) if not slash
    ]
    return tuple(matches)  

@dataclass(frozen=True)
class BoundXMD:
    """Class to store markdown content and user variables (and from caller's scope) for later parsing.
    Use `parse` method to parse the content with given variables. This class is useful for picking variables
    without poluting the global namespace as well as inside python scripts where notebook's scope is not available.
    """
    content: str
    vars: Mapping[str, object] = field(default_factory=dict)
    _rel_depth: int = 0 # above stack of this class
    
    def __post_init__(self):
        req_vars = _matched_vars(self.content)
        scoped_vars = { # only pick needed vars if user pass smething like locals
            k:v for k,v in self.vars.items() if k in req_vars
        } if isinstance(self.vars, dict) else {}
        missing_keys = set(req_vars) - scoped_vars.keys() # check for missing keys
        if missing_keys:
            depth = self._rel_depth + 2 # 1 for __post_init__, 1 for __init__
            frame = sys._getframe(depth)
            try:
                for key in missing_keys:
                    if key in frame.f_locals:
                        scoped_vars[key] = frame.f_locals[key]
                    elif key in frame.f_globals:
                        scoped_vars[key] = frame.f_globals[key]
                    else:
                        raise NameError(f"name {key!r} is not defined")
            finally:
                del frame  # Prevent reference cycles
        # Reset final vars to be immutable MappingProxyType
        object.__setattr__(self, 'vars', MappingProxyType(scoped_vars)) 
    
    def parse(self, returns:bool=False, tag:str=None) -> Optional[str]:
        BoundXMD._bound_vars = self.vars # set bound vars for parsing
        try:
            return xmd(self.content, returns=returns, tag=tag)
        finally:
            if hasattr(BoundXMD, '_bound_vars'):
                del BoundXMD._bound_vars # cleanup after parsing
    
    def __format__(self, spec):
        return f'{self.parse(returns=True):{spec}}'
    
    def __repr__(self):
        keys = ', '.join(map(repr, self.vars.keys())) # only show keys for brevity
        return f"{self.__class__.__name__}(content={self.content!r}, vars=[{keys}])"

class fmt(BoundXMD):
    """Use xmd.gather instead of this class. This class is deprecated and will be removed in future releases."""
    def __init__(self, content: str, **vars):
        print("⚠️ Warning: `fmt` is deprecated and will be removed in future releases. Use `xmd.gather` instead.")
        super().__init__(content, vars=vars, _rel_depth=1) # _rel_depth=1 to account for this __init__ call

    def _ipython_display_(self): # to be correctly captured in write etc. commands
        with altformatter.reset(): # don't let it be caught in html conversion
            self.parse(returns = False)
        
    def _repr_html_(self): # for functions to consume as html and for export
        return self.parse(returns=True)

class _XMDMeta(type):
    @property
    def extensions(self) -> Extensions:
        "Entry point to extend and configure markdown extensions."
        return _extensions
    @property
    def syntax(self) -> XTML:
        "Extended markdown syntax information."
        from ._base._syntax import xmd_syntax # circular import
        return _parse_as_steps(xmd_syntax())
    
    @property
    def escaped_chars(self) -> tuple[str]:
        "List of characters that are escaped in extended markdown."
        return tuple(char_esc._chars)
    
    @property
    def funcs(self):
        "List of available inline functions for extended markdown."
        from .utils import html, doc, details, XTML
        
        info = html("", [r"""
        **Inline Python Functions**{.text-big}
        
        Call pattern for inline functions is shown in table below. `*args` and `**kwargs` are arguments given as Python literals.
        The content does not require quotes and must maintain its own indentation and line breaks.
        
        | Mode          | Markdown Call                              | Python Call                        |
        |:--------------|:-------------------------------------------|:-----------------------------------|
        | Empty Call    | `[func\! \/] / [func\!! /]`                | `func()`                           |
        | Empty Content | `[func\! \.. \/] / [func\!\! \.. \/]`      | `func("")`                         |
        | Content Only  | `[func\! Content \/]`                      | `func("Content")`                  |
        | Content First | `[func\! Content .. *args, **kwargs \/]`   | `func("Content", *args, **kwargs)` |
        | Params First  | `[func\!! *args, **kwargs \.. Content \/]` | `func("Content", *args, **kwargs)` |
        | Params Only   | `[func\!! *args, **kwargs \/]`             | `func(*args, **kwargs)`            |
    
        - You can override a registered function by pure html tag by appending ` _ ` to the tag. For example, ` svg_ ` will be html tag that overrides the ` svg ` function.
        - User can register their own functions using [code! xmd.register /] function, which will be listed here.
        - If you need a literal `..` in content, escape it with backslash like `\\..`. Similarly, to avoid parsing a function call, escape the first `!` as `\\!` and ending `/` as `\\/`. No need to escape `[` and `]`.
        """])
        
        dtls = html("div", "\n".join([
            details(doc(value[0]), 
                summary=f"{key}: <em style='font-size:0.75em;opacity:0.6;'>{value[1]}</em>", 
                name="funcs-accordian", # to open exclusively
                background="var(--bg2-color)",
                border_radius="0.25em",
            ).value
            for key, value in sorted(_XMD_FUNCS.items(), key=lambda x: x[0])
        ]) + html("style", ".funcs-grid > details[open] {grid-column: 1/-1;}").value,
        style="display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 0.5em;", 
        css_class="funcs-grid")
        
        return XTML(info.value + dtls.value)
    
    def __dir__(cls): # tab completion still sucks with meta programming!
        return sorted(list(super().__dir__()) + ["escaped_chars", "extensions", "funcs", "gather", "register", "syntax"])
    
    @staticmethod
    def gather(content:str, **vars): # export xmd in docs and demo to show this
        """Gather markdown content and variables for later parsing. This is useful for picking variables without 
        polluting the global namespace as well as inside python scripts where notebook's scope is not available.
        
        - content (str): The markdown content to gather.
        - vars (dict): The variables to be used in the markdown content.
        
        Returns a `BoundXMD` object that can be parsed later using the `parse` method or passed to `write` and utility functions.
        """
        
        return BoundXMD(content, vars=vars, _rel_depth=1) # +1 for this function call
    
    @staticmethod
    def register(name: str, func: callable=None):
        r"""Register a user-defined inline function for extended markdown.

        - name (str): The name of the function to register.
        - func (callable, optional): The function to register or use as a decorator if not provided.

        ```python
        from functools import wraps
        import matplotlib.pyplot as plt
        from ipyslides import xmd
        
        # Directly register a function with the same signature as plt.plot
        xmd.register("plot", plt.plot)
        
        # Adopt it for modified behavior, e.g., to convert to HTML for proper display in slides
        @xmd.register("plot") 
        @wraps(plt.plot) # signature will be adopted, note only *args and *kwargs to avoid conflicts
        def _(*args, **kwargs):
            caption = kwargs.pop("caption", None) # optional caption
            plt.plot(*args, **kwargs)
            # convert to html to display in proper place even in inline context
            # plt.show() will display in unexpected place if not in a display context
            return slides.plt2html(caption=caption) # convert to html for proper display in slides
        
        # Or decorate your own pure function 
        @xmd.register("myfunc")
        def myfunc(arg1, arg2, kwarg1=True):
            # Your function implementation here
            return f"Processed {arg1} and {arg2} with kwarg1={kwarg1}"
        ```
        
        ::: code language="markdown"   
            [plot!! [1,2,3], [4,5,6], caption="This is a plot from markdown!" /]
        
        ::: note
           - If your registered function does not accept content as first argument, skip `..` in the call and start with `!!`, e.g., `[myfunc\!! arg1, arg2, kwarg1=False \/]`.
           - Content is converted to html string and outer `<p>` tags are stripped before passing to the function, so you can wrap it in tags of your choice.
        """
        # MUST BE ONLY GATEWAY FOR USER-DEFINED FUNCTIONS FOR SECURITY and SCOPE REASONS.
        # SCOPE ISSUE: A function in python file is not visible in user namespace
        # although user may think it is, so register is the only way to make it visible in extended markdown.
        if not isinstance(name, str):
            raise TypeError(f"Expected a string for function name, got {type(name)}")
        
        if name in _XMD_FUNCS:
            _, ctx = _XMD_FUNCS[name]
            if ctx != "user":
                raise ValueError(f"Function name '{name}' is already registered by ipyslides. Please choose a different name.")
        
        def decorator(func):
            if not callable(func):
                raise TypeError(f"Expected a callable function, got {type(func)}")
            _XMD_FUNCS[name] = (func, "user")
            return func
        
        if func is not None:
            return decorator(func)
        return decorator
        
    
class xmd(metaclass=_XMDMeta):
    r"""
    Extended markdown parser for ipyslides. You can use %%xmd and %xmd cell and line magics in Jupyter Notebook as well.

    Besides the base [Python-Markdown](https://python-markdown.github.io/) syntax, 
    it supports additional syntax which you can read about by executing following code a notebook cell:

    ```python
    import ipyslides as isd
    display(isd.xmd.syntax)
    ```

    By default, the extensions `tables`, `footnotes`, `attr_list`, `md_in_html`, `def_list` are enabled.

    You can add extra markdown extensions using `Slides.xmd.extensions` or `ipyslides.xmd.extensions`.
    See [markdown extensions](https://python-markdown.github.io/extensions/) for details.
    
    If you want to return the stripped paragraph content without outer <p> tags, use `xmd(content, True, tag="")` or any valid html tag to enclose content.
    
    Use `xmd.gather(content, **vars)` to gather content and variables for later parsing. This is useful for picking variables 
    without polluting the global namespace as well as inside python scripts where notebook's scope is not available.
    
    **Returns**: A string with HTML content if `returns=True` (default), otherwise display rich output objects.
    """
    def __new__(cls, content:str, returns:bool=False, tag=None) -> Optional[str]:
        if hasattr(XMarkdown, '_active_parser'): # keeps variables in scope for nested calls
            return XMarkdown._active_parser(content, returns=returns, tag=tag)
        return XMarkdown()._parse(content, returns=returns, tag=tag)

def _parse_as_steps(markdown):
    "Parse markdown chunks splitted by -- and show alternate chunks through a steps widget. First chunk is treated as common header and shown always."
    if not isinstance(markdown, str):
        raise TypeError(f"markdown expects a string, got {markdown!r}")
    
    pages = list(_stream_chunks(markdown, sep='--'))
    with capture_content() as cap:
            xmd(pages[0], returns=False) # render common header part

            if len(pages) > 1:
                from .utils import steps  # circular import
                from .writer import write  # circular import
            
            stps = [XTML(xmd(page,True)) for page in pages[1:]] # parse each page and store as XTML
            write(steps(stps, dots_loc='right'))
    return frozen(cap) # return captured content as frozen to be automatically displayed in last line of cell


def _stream_chunks(text, sep='---'):
    "Used for slides and pages splitting, yields chunks. Use _split_parts for splitting by ++ more flexibly and yielding delimiter objects."
    s = sep.strip()
    if s.startswith('```'):
        raise ValueError(f"Invalid separator '{s}'. To split by backticks, use re.split instead!")

    if s not in _PATTERN_CACHE:
        # Group 1: Shield (3+ backticks) | Group 2: Cut (Separator)
        _PATTERN_CACHE[s] = re.compile(rf"(?m)(^`{{3}})|(^{re.escape(s)}\s*$)")

    if eof := re.search(r'^\s*EOF\s*$',text, flags = re.MULTILINE):
        text = text[:eof.start()]  # truncate at EOF

    text = textwrap.dedent(text)  # content coming from python functions is usually indented, fix for all cases, need sep at start

    # Mask HTML comments so sep inside them are not treated as separators.
    text = cmnt_esc.escape(text)

    pattern = _PATTERN_CACHE[s]
    last_pos = 0
    in_block = False

    for match in pattern.finditer(text):
        if match.group(1): # It's a backtick fence (toggle shielding)
            in_block = not in_block
        elif not in_block: # It's a separator and we're NOT inside a block
            if (chunk := text[last_pos:match.start()].rstrip()): # need to preseve leading indents, so only rstrip
                yield cmnt_esc.restore(chunk)
            last_pos = match.end()

    if final_chunk := text[last_pos:].rstrip():
        if in_block:
            final_chunk += '\n```'  # close unclosed code block in forgiven manner instead of raising error
        yield cmnt_esc.restore(final_chunk)
        

def _split_parts(content, delimited=False):
    "Split content at '++', optionally yielding delimiter objects. '++ ' inline is also supported unlinke strict '++' on a line by itself in _stream_chunks."
    def _part_delim():
        delim = _delim("PAUSE")
        if opt == 'isolate':
            error("SyntaxError", "The '[isolate]' option after ++ is deprecated. Use 'columns.paused' directive followed by a '++' instead.").display()
        return delim
    
    start = 0
    first = True

    content = textwrap.dedent(content)  # Dedent content before processing to make sure ++ is at start of line
    for m in PLUS_RE.finditer(content):
        opt = (m.group('opt') or '').strip().lower().replace('_', '-')
        chunk = content[start:m.start()].rstrip() # preserve leading indentation, clear trailing junk

        if chunk:
            yield chunk
            if delimited:
                yield _part_delim()
        elif first and delimited:
            yield _part_delim()

        first = False
        start = m.end()

    if tail := content[start:].rstrip():
        yield tail

# This shoul be outside, as needed in other modules
def _load_files(content):
    "Load files from [load! file_path /] macros in content. Returns list of loaded files and modified content."
    loader_func = XMarkdown().repl_py_func # needed instance method
    files, chunks, last_pos = [], [], 0
    for match in FUNC_RE.finditer(content):
        macro_name, *_ = match.groups()
        # only intercept load macros here
        if macro_name != "load":
            continue

        # Resolve the current line prefix so [load! ... /] can only appear after whitespace.
        line_start = content.rfind("\n", 0, match.start()) + 1
        line_prefix = content[line_start:match.start()]

        if line_prefix.strip():
            chunks.append(content[last_pos:match.start()])
            escaped_match = match.group(0).replace('!', r'\\!').replace('/', r'\\/')  # Escape ! and / for display as info
            chunks.append("\n" + error("SyntaxError",f"load macro must be on its own line with optional indentation only: '{line_prefix}{escaped_match}'").value)
            last_pos = match.end()
            continue

        chunks.append(content[last_pos:line_start])
        file, filecontent = loader_func(match)
        
        # Nested loading is not allowed
        nested_err = error("SyntaxError",f"Nested loading of files is not supported in a top loaded file: {file!r}").value
        filecontent = re.sub(r'(?<![\\\`])\[load!.*?/\]', nested_err, filecontent, flags=re.DOTALL)

        if line_prefix:
            filecontent = textwrap.indent(filecontent, line_prefix)

        chunks.append(filecontent)
        files.append(file)
        last_pos = match.end()

    if chunks:
        chunks.append(content[last_pos:])
        content = "".join(chunks)
    
    # This error must be hard (and at end to include loaded files) to avoid error content being passed to citations etc.
    if re.search(r"^(\s*)include\`(.*?)\`", content, flags=re.DOTALL | re.MULTILINE):
        raise SyntaxError("Legacy include`file` syntax is deprecated. Use [load! file /] instead.")
    return files, content    
