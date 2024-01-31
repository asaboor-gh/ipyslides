"""
Extended Markdown

You can use the following syntax:

```python run var_name
import numpy as np
```
# Normal Markdown
```multicol
A
+++
This ~`var_name` is a code from above and will be substituted with the value of var_name
```
::: note-warning
    Nested blocks are not supported.

::: note-info  
    - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
    - Use `Slides.extender` or `ipyslides.xmd.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
"""

import textwrap, re, ast, sys, json
from markdown import Markdown
from IPython.core.display import display
from IPython import get_ipython
from IPython.utils.capture import capture_output

from .formatters import XTML, highlight, htmlize
from .source import _str2code

_md_extensions = [
    "tables",
    "footnotes",
    "attr_list",
    "md_in_html",
    "customblocks",
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
    "alert": "text",
    "color": "text",
    "image": "path/src or clip:filename",
    "raw": "text",
    "svg": "path/src",
    "iframe": "src",
    "sub": "text",
    "sup": "text",
    "today": "fmt like %b-%d-%Y",
    "textbox": "text",  # Anything above this can be enclosed in a textbox
    "details": "text",
    "center": "text or ~\`variable\`",
}  # align-center should be at end of all

_code_ = """
```python run
{app} = get_slides_instance()
{block}
```
"""


def fmt_code(code, instance_name="slides"):
    "Format given code block to be runable under markdown. instance_name is the name of the slides instance as used in current code."
    return _code_.format(app=instance_name, block=textwrap.dedent(code).strip())

def get_slides_instance():
    "Get the slides instance from the current namespace."
    if (isd:= sys.modules.get('ipyslides',None)):
        if (slides := getattr(isd, "Slides",None)): # Avoid partial initialization
            return slides.instance()


def get_unique_css_class():
    "Get slides unique css class if available."
    slides = get_slides_instance()
    return f".{slides.uid}" if slides else ""


def is_var(name):
    try:
        ast.parse(f"{name} = None") # if not valid variable name, it will fail
        return True
    except:
        return False
    
def get_var(match, user_ns):
    parts = match.split('.')
    if parts[0] not in user_ns:
        return f"<pre>alert`NameError`: name {match!r} is not defined</pre>"
    
    var = user_ns[parts[0]]
    for part in parts[1:]:
        if not hasattr(var, part):
            return f"<pre>alert`AttributeError`: {var!r} object has no attribute {part!r}</pre>"
        var = getattr(var, part)
    
    return var 

    
def get_user_ns():
    "Top level user namespace"
    main = sys.modules.get('__main__',None) # __main__ is current top module
    return main.__dict__ if main else {}


def resolve_objs_on_slide(slide_instance, text_chunk):
    "Resolve objects in text_chunk corrsponding to slide such as cite, notes, etc."
    # notes`This is a note for current slide`
    all_matches = re.findall(
        r"notes\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE
    )
    for match in all_matches:
        slide_instance.notes.insert(match)
        text_chunk = text_chunk.replace(f"notes`{match}`", "", 1)

    # cite`key` should be after citations`key`, so that available for writing there if any
    all_matches = re.findall(r"cite\`(.*?)\`", text_chunk, flags=re.DOTALL)
    for match in all_matches:
        key = match.strip()
        text_chunk = text_chunk.replace(f"cite`{match}`", slide_instance._cite(key), 1)
    
    # section`This is section title`
    all_matches = re.findall(
        r"section\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE
    )
    for match in all_matches:
        slide_instance._section(match)  # This will be attached to the running slide
        text_chunk = text_chunk.replace(f"section`{match}`", "", 1)

    # toc`This is toc title`
    all_matches = re.findall(r"toc\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE)
    for match in all_matches:
        block = fmt_code(
            f"""
            kwargs = dict(title = {match!r}) if {match!r} else {{}} # auto
            slide_instance._toc(**kwargs)
            """, instance_name="slide_instance",
        )

        text_chunk = text_chunk.replace(f"toc`{match}`", block, 1)
    
    # ```toc title\n text\n``` as block start with new line 
    all_matches = re.findall(r"\n\`\`\`toc(.*?)\n\`\`\`", text_chunk, flags=re.DOTALL | re.MULTILINE)
    for match in all_matches:
        title, extra = [v.strip() for v in (match + '\n').split('\n', 1)] # Make sure a new line is there and then strip
        jstr = json.dumps({"title": title, "extra" : extra.strip()}) # qoutes fail otherwise
        block = fmt_code(
            f"""
            import json
            slide_instance._toc(**json.loads({jstr!r}))
            """, instance_name="slide_instance",
        )

        text_chunk = text_chunk.replace(f"\n```toc{match}\n```", block, 1)

    # proxy`This is prxoy's placeholder text`
    all_matches = re.findall(
        r"proxy\`(.*?)\`", text_chunk, flags=re.DOTALL | re.MULTILINE
    )
    for match in all_matches:
        block = fmt_code(
            f"pr = slide_instance.proxy({match!r})", instance_name="slide_instance"
        )  # assign to avoid __repr__ output in markdown
        text_chunk = text_chunk.replace(f"proxy`{match}`", block, 1)

    return text_chunk


class XMarkdown(Markdown):
    def __init__(self):
        super().__init__(
            extensions=extender._all, extension_configs=extender._all_configs
        )
        self._display_inline = False
        self._shell = get_ipython()
        self._slides = get_slides_instance()

    def _extract_class(self, header):
        out = header.split(".", 1)  # Can have many classes there
        if len(out) == 1:
            return out[0].strip(), ""
        return out[0].strip(), out[1].replace(".", " ").strip()

    def parse(self, xmd, display_inline=False):
        """Return a string after fixing markdown and code/multicol blocks if display_inline is False
        otherwise displays objects and execute python code from '```python run source_var_name' block.
        """
        self._display_inline = display_inline  # Must change here
        if xmd[:3] == "```":  # Could be a block just in start but we need newline to split blocks
            xmd = "\n" + xmd

        # included file before other parsing
        xmd = self._resolve_files(xmd)

        xmd = textwrap.dedent(
            xmd 
        )  # Remove leading spaces from each line, better for writing under indented blocks
        xmd = re.sub("\\\`", "&#96;", xmd)  # Escape backticks
        xmd = self._resolve_nested(
            xmd
        )  # Resolve nested objects in form func`?text?` to func`html_repr`

        if self._slides and self._slides.running:
            xmd = resolve_objs_on_slide(
                self._slides, xmd
            )  # Resolve objects in xmd related to current slide


        # After resolve_objs_on_slide, xmd can have code blocks which may not be passed from suitable context
        if (r"\n```python run" in xmd) and not self._display_inline: # Do not match nested blocks, r"" is important
            raise RuntimeError(
                "Cannot execute code in current context, use Slides.parse(..., display_inline = True) for complete parsing!"
            )

        new_strs = xmd.split("\n```")  # This avoids nested blocks and it should be
        outputs = []
        for i, section in enumerate(new_strs):
            if i % 2 == 0:
                outputs.append(XTML(self.convert(self._sub_vars(section))))
            else:
                section = textwrap.dedent(section)  # Remove indentation in code block, useuful to write examples inside markdown block
                outputs.extend(
                    self._parse_block(section)
                )  # vars are substituted already inside

        if display_inline:
            return display(*outputs)
        else:
            content = ""
            for out in outputs:
                try:
                    content += out.value  # XTML, SourceCode
                except:
                    content += out.data[
                        "text/html"
                    ]  # Rich content from python execution
            return content
    
    def _resolve_files(self, text_chunk):
        "Markdown files added by include`file.md` should be inserted a plain."
        all_matches = re.findall(r"include\`(.*?)\`", text_chunk, flags=re.DOTALL)
        for match in all_matches:
            with open(match, "r", encoding="utf-8") as f:
                text = "\n" + f.read() + "\n"
                text_chunk = text_chunk.replace(f"include`{match}`", text, 1)
        return text_chunk

    def _resolve_nested(self, text_chunk):
        old_display_inline = self._display_inline
        try:
            # match func`?text?` to parse text and return func`html_repr`
            all_matches = re.findall(
                r"\`\?(.*?)\?\`", text_chunk, flags=re.DOTALL | re.MULTILINE
            )
            for match in all_matches:
                repr_html = self.parse(match, display_inline=False)
                repr_html = re.sub(
                    "</p>$", "", re.sub("^<p>", "", repr_html)
                )  # Remove <p> and </p> tags at start and end
                text_chunk = text_chunk.replace(f"`?{match}?`", f"`{repr_html}`", 1)
        finally:
            self._display_inline = old_display_inline

        return text_chunk

    def _parse_block(self, block):
        "Returns list of parsed block or columns or code, input is without ``` but includes langauge name."
        header, data = block.split("\n", 1)
        line, _class = self._extract_class(header)
        if "multicol" in line:
            return [XTML(self._parse_multicol(data, line, _class)),]
        elif "python" in line:
            return self._parse_python(data, line, _class)  # itself list
        elif "toc" in line:
            raise RuntimeError("Some blocks with may not be properly formatted. Check each block is closed with three backticks!")
        else:
            language = (
                line.strip() if line.strip() else "text"
            )  # If no language, assume
            name = (
                " " if language == "text" else None
            )  # If no language or text, don't show name
            return [
                highlight(data, language=language, name=name, className=_class),
            ]  # no need to highlight with className separately

    def _parse_multicol(self, data, header, _class):
        "Returns parsed block or columns or code, input is without \`\`\` but includes langauge name."
        cols = data.split("+++")  # Split by columns
        cols = [self.convert(self._sub_vars(col)) for col in cols]

        if header.strip() == "multicol":
            widths = [f"{int(100/len(cols))}%" for _ in cols]
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

            widths = [f"{w}%" for w in widths]
        
        if len(cols) == 1: # do not return before checking widths and adding extra cols if needed
            return f'<div class={_class}">{cols[0]}</div>' if _class else cols[0]

        cols = "".join(
            [f"""<div style='width:{w};overflow-x:auto;height:auto'>{col}</div>"""
                for col, w in zip(cols, widths)])

        return f'<div class="columns {_class}">{cols}\n</div>'

    def _parse_python(self, data, header, _class):
        # if inside some writing command, do not run code at all
        if len(header.split()) > 3:
            raise ValueError(
                f"Too many arguments in {header!r}, expects 3 or less as ```python run source_var_name"
            )
        dedent_data = textwrap.dedent(data)
        if (self._display_inline == False) or ("run" not in header):  # no run given
            return [
                highlight(dedent_data, language="python", className=_class),
            ]
        elif "run" in header and self._display_inline:
            source = header.split("run")[1].strip()  # Afte run it be source variable
            if source:
                get_user_ns()[source] = _str2code(
                    dedent_data, language="python", className=_class
                )

            # Run Code now
            with capture_output() as captured:
                if current_shell := self._slides or self._shell:
                    try: # Need slides to be  accessible in namespace
                        get_user_ns()['get_slides_instance'] = get_slides_instance
                        current_shell.run_cell(dedent_data)
                    finally:
                        get_user_ns().pop('get_slides_instance') # don't keep

                else:
                    raise RuntimeError("Cannot execute this outside IPython!")

            outputs = captured.outputs
            return outputs

    def _sub_vars(self, html_output):
        "Substitute variables in html_output given as ~`var` and two inline columns as ||C1||C2||"
        # Check maximum level of indentation if under custom blocks
        matches = [
            4 + len(match)
            for match in re.findall(
                r"^(\s*):::", html_output.replace("\t", "    "), flags=re.MULTILINE
            )
        ]  # 4 is default
        sub_nl = "\n" + (
            " " * max(matches) if matches else ""
        )  # If no :::, no indentation is needed

        # Replace variables first
        all_matches = re.findall(r"\~\`(.*?)\`", html_output, flags=re.DOTALL)
        for match in all_matches:
            output = match  # If below fails, it will be the same as input line
            _match = match.strip()
            if not is_var(_match):
                raise ValueError(f"Only variables/var.attr are allowed inside ~`variable` syntax, got {_match!r}. Use string formatting for arbitrary expressions.")
            
            output = get_var(_match, get_user_ns())
            _out = (
                (htmlize(output) if output is not None else "")
                if not isinstance(output, str)
                else output
            )  # Avoid None
            html_output = html_output.replace(
                "~`" + match + "`", _out.replace("\n", sub_nl), 1
            )  # Replace with htmlized output, replace new line with 4 spaces to keep indentation if block ::: is used

        # Replace inline one argumnet functions
        from . import utils  # Inside function to avoid circular import

        for func in _special_funcs.keys():
            all_matches = re.findall(
                rf"{func}\`(.*?)\`", html_output, flags=re.DOTALL | re.MULTILINE
            )
            for match in all_matches:
                _func = getattr(utils, func)
                _out = (_func(match) if match else _func()).value.replace(
                    "\n", sub_nl
                )  # If no argument, use default, replace new line with 4 spaces to keep indentation if block ::: is used
                html_output = html_output.replace(f"{func}`{match}`", _out, 1)

        # Replace functions with arguments
        for func in _special_funcs.keys():
            all_matches = re.findall(
                rf"{func}\[(.*?)\]\`(.*?)\`",
                html_output,
                flags=re.DOTALL | re.MULTILINE,
            )
            for match in all_matches:
                arg0 = match[1].strip()
                args = [
                    v.replace("__COM__", ",")
                    for v in match[0]
                    .replace("\=", "__EQ__")
                    .replace("\,", "__COM__")
                    .split(",")
                ]  # respect escaped = and ,
                kws = {
                    k.strip().replace("__EQ__", "="): v.strip().replace("__EQ__", "=")
                    for k, v in [a.split("=") for a in args if "=" in a]
                }
                args = [a.strip().replace("__EQ__", "=") for a in args if "=" not in a]
                _func = getattr(utils, func)
                try:
                    _out = (
                        _func(arg0, *args, **kws).value
                        if arg0
                        else _func(*args, **kws).value
                    )  # If no argument, use default
                    _out = _out.replace(
                        "\n", sub_nl
                    )  # Replace new line with 4 spaces to keep indentation if block ::: is used
                    html_output = html_output.replace(
                        f"{func}[{match[0]}]`{match[1]}`", _out, 1
                    )
                except Exception as e:
                    raise Exception(
                        f"Error in {func}[{match[0]}]`{match[1]}`: {e}.\nYou may need to escape , and = with \, and \= if you need to keep them inside [{match[0]}]"
                    )

        # Replace columns at end because they will convert HTML
        all_cols = re.findall(
            r"\|\|(.*?)\|\|(.*?)\|\|", html_output, flags=re.DOTALL | re.MULTILINE
        )  # Matches new line as well, useful for inline plots and big objects
        for cols in all_cols:
            _cols = "".join(
                f'<div style="width:50%;">{self.convert(c)}</div>' for c in cols
            )
            _out = f'<div class="columns">{_cols}</div>'.replace(
                "\n", sub_nl
            )  # Replace new line with 4 spaces to keep indentation if block ::: is used
            html_output = html_output.replace(f"||{cols[0]}||{cols[1]}||", _out, 1)


        return html_output  # return in main scope


def parse(xmd, display_inline=True):
    """Parse extended markdown and display immediately.
    If you need output html, use `display_inline = False` but that won't execute python code blocks.

    **Example**
    ```markdown
     ```python run var_name
     #If no var_name, code will be executed without assigning it to any variable
     import numpy as np
     ```
     # Normal Markdown {.report-only}
     ```multicol 40 60
     # First column is 40% width
     If 40 60 was not given, all columns will be of equal width, this paragraph will be inside info block due to class at bottom
     {.info}
     +++
     # Second column is 60% wide
     This ~\`var_name\` is code from above and will be substituted with the value of var_name
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
        - There are three special CSS classes `report-only`, `slides-only` and `export-only` that control appearance of content in different modes.

    ::: note-warning
        Nested blocks are not supported.

    ::: note-info
        - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
        - Use `Slides.extender` or `ipyslides.xmd.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
    """
    return XMarkdown().parse(xmd, display_inline=display_inline)
