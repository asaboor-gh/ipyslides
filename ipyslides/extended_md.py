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
This {{var_name}} is a code from above and will be substituted with the value of var_name
```

Note: Nested blocks are not supported.

**New in 1.7.2**    
Find special syntax to be used in markdown by `Slides.xmd_syntax`.

**New in 1.7.5**
Use `Slides.extender` or `ipyslides.extended_md.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
"""

import textwrap, re
from markdown import Markdown
from IPython.core.display import display
from IPython import get_ipython
from IPython.utils.capture import capture_output

from .formatters import _HTML, highlight, stringify
from .source import _str2code

_md_extensions = ['tables','footnotes','attr_list','md_in_html', 'customblocks'] # For Markdown Parser
_md_extension_configs = {}

class PyMarkdown_Extender:
    def __init__(self):
        "Adds extensions to the Markdown parser. See [Website of Python-Markdown](https://python-markdown.github.io/extensions/)"
        self._exts = []
        self._configs = {}
    
    def __repr__(self) -> str:
        return "Extensions:\n" + repr(self._all) + "\nConfigs:\n" + repr(self._all_configs)
        
    @property
    def _all(self):
        return list(set([*self._exts, *_md_extensions]))
    
    @property
    def _all_configs(self):
        return {**self._configs, **_md_extension_configs}
    
    def extend(self,extensions_list):
        "Add list of extensions to the Markdown parser."
        self._exts = list(set([*self._exts, *extensions_list]))
    
    def config(self,configs_dict):
        "Add configurations to the Markdown extensions. configs_dict is a dictionary like {'extension_name': config_dict}"
        self._configs = {**self._configs, **configs_dict}
    
    def clear(self):
        "Clear all extensions and their configurations added by user."
        self._exts = []
        self._configs = {}
    
    @property
    def active(self):
        "List of active extensions."
        return {'extensions': self._all, 'configs': self._all_configs}
  
extender = PyMarkdown_Extender()
del PyMarkdown_Extender

_special_funcs = {
    'alert':'text',
    'image':'path/src',
    'raw':'text',
    'svg':'path/src', 
    'iframe':'src',
    'sub': 'text',
    'sup': 'text',
    'today': 'fmt like %b-%d-%Y',
    'textbox':'text', # Anything above this can be enclosed in a textbox
    'center':'text or \{\{variable\}\}',} # align-center should be at end of all


def resolve_objs_on_slide(slide_instance,text_chunk):
    "Resolve objects in text_chunk corrsponding to slide such as cite, notes, etc."
    # notes`This is a note for current slide`
    all_matches = re.findall(r'notes\`(.*?)\`', text_chunk, flags = re.DOTALL | re.MULTILINE)
    for match in all_matches:
        slide_instance.notes.insert(match)
        text_chunk = text_chunk.replace(f'notes`{match}`', '', 1)
    
    # cite`key` should be after citations`key`, so that available for writing there if any
    all_matches = re.findall(r'cite\`(.*?)\`', text_chunk, flags = re.DOTALL)
    for match in all_matches:
        key = match.strip()
        text_chunk = text_chunk.replace(f'cite`{match}`', slide_instance.cite(key), 1)
    
    # citations`This is citations title` after setting citations and cite
    all_matches = re.findall(r'citations\`(.*?)\`', text_chunk, flags = re.DOTALL | re.MULTILINE)
    for match in all_matches:
        repr_html = slide_instance.format_html([match, *slide_instance.citations]).value
        text_chunk = text_chunk.replace(f'citations`{match}`', repr_html, 1)
        
    # section`This is section title`
    all_matches = re.findall(r'section\`(.*?)\`', text_chunk, flags = re.DOTALL | re.MULTILINE)
    for match in all_matches:
        slide_instance.section(match) # This will be attached to the running slide
        text_chunk = text_chunk.replace(f'section`{match}`', '', 1)
        
    # toc`This is toc title`
    all_matches = re.findall(r'toc\`(.*?)\`', text_chunk, flags = re.DOTALL | re.MULTILINE)
    for match in all_matches:
        bullets = '\n'.join([f'{idx}. {text}' for idx,text in enumerate(slide_instance.toc, start = 1)])
        repr_html = slide_instance.format_html([match or '<h3>Table of Contents</h3><hr/>', bullets]).value
        text_chunk = text_chunk.replace(f'toc`{match}`', repr_html, 1)
    
    return text_chunk

class _ExtendedMarkdown(Markdown):
    "New in 1.4.5"
    def __init__(self):
        super().__init__(extensions = extender._all, extension_configs=extender._all_configs)
        self._display_inline = False
        self._shell = get_ipython()
        self._slides = self._shell.user_ns.get('get_slides_instance',lambda: None)() # It is callable, do not get it in global namespace,need only single reference outside
    
    def _extract_class(self, header):
        out = header.split('.',1) # Can have many classes there
        if len(out) == 1:
            return out[0].strip(), ''
        return out[0].strip(), out[1].replace('.', ' ').strip()
        
    def parse(self, xmd, display_inline = False, rich_outputs = False):
        """Return a string after fixing markdown and code/multicol blocks if display_inline is False
        Else displays objects and execute python code from '```python run source_var_name' block.
        Precedence of content return/display is:
        rich_outputs = True > display_inline = True > parsed_html_string
        
        New in 1.4.5
        """
        self._display_inline = display_inline # Must change here
        xmd = textwrap.dedent(xmd) # Remove leading spaces from each line, better for writing under indented blocks
        xmd = re.sub('\\\`', '&#96;', xmd) # Escape backticks
        xmd = self._resolve_nested(xmd) # Resolve nested objects in form func`?text?` to func`html_repr`
        
        if self._slides and self._slides.running: 
            xmd = resolve_objs_on_slide(self._slides,xmd) # Resolve objects in xmd related to current slide
        
        if xmd[:3] == '```': # Could be a block just in start of file or string
            xmd = '\n' + xmd
        
        new_strs = xmd.split('\n```') # This avoids nested blocks and it should be
        outputs =[]
        for i, section in enumerate(new_strs):
            if i % 2 == 0:
                out = self.convert(self._sub_vars(section))
                outputs.append(_HTML(out))
            else:
                section = textwrap.dedent(section) # Remove indentation in code block, useuful to write examples inside markdown block
                outputs.extend(self._parse_block(section)) # vars are substituted already inside
        
        if rich_outputs:
            return outputs
        elif display_inline:
            display(*outputs)
        else:
            content = ''
            for out in outputs:
                try:
                    content += out.value # _HTML, _Source
                except:
                    content += out.data['text/html'] # Rich content from python execution
            return content
        
    def _resolve_nested(self,text_chunk):
        old_display_inline = self._display_inline
        try:
            # match func`?text?` to parse text and return func`html_repr`
            all_matches = re.findall(r'\`\?(.*?)\?\`', text_chunk, flags = re.DOTALL | re.MULTILINE)
            for match in all_matches:
                repr_html = self.parse(match, display_inline = False, rich_outputs = False)
                repr_html = re.sub('</p>$','',re.sub('^<p>', '', repr_html)) # Remove <p> and </p> tags at start and end
                text_chunk = text_chunk.replace(f'`?{match}?`', f'`{repr_html}`', 1)
        finally:
            self._display_inline = old_display_inline
            
        return text_chunk
    
    def _parse_block(self, block):
        "Returns list of parsed block or columns or code, input is without ``` but includes langauge name."
        header, data = block.split('\n',1)
        line, _class = self._extract_class(header)
        if 'multicol' in line:
            return [_HTML(self._parse_multicol(data, line, _class)),]
        elif 'python' in line:
            return self._parse_python(data, line, _class) # itself list
        else:
            language = line.strip() if line.strip() else 'text' # If no language, assume
            name = ' ' if language == 'text' else None # If no language or text, don't show name
            return [highlight(data,language = language, name = name, className = _class),] # no need to highlight with className separately     
        
    def _parse_multicol(self, data, header, _class):
        "Returns parsed block or columns or code, input is without \`\`\` but includes langauge name."
        cols = data.split('+++') # Split by columns
        cols = [self.convert(self._sub_vars(col)) for col in cols] 
        if len(cols) == 1:
            return f'<div class={_class}">{cols[0]}</div>' if _class else cols[0]
        
        if header.strip() == 'multicol':
            widths = [f'{int(100/len(cols))}%' for _ in cols]
        else:
            widths = header.split('multicol')[1].split()
            if len(widths) != len(cols):
                raise ValueError(f'Number of columns {len(cols)} does not match with given widths in {header!r}')
            for w in widths:
                if not w.strip().isdigit():
                    raise TypeError(f'{w} is not an integer')
                
            widths = [f'{w}%' for w in widths]
            
        cols =''.join([f"""
        <div style='width:{w};overflow-x:auto;height:auto'>
            {col}
        </div>""" for col,w in zip(cols,widths)])
        
        return f'<div class="columns {_class}">{cols}\n</div>'
    
    def _parse_python(self, data, header, _class):
        # if inside some writing command, do not run code at all
        if len(header.split()) > 3:
            raise ValueError(f'Too many arguments in {header!r}, expects 3 or less as ```python run source_var_name')
        dedent_data = textwrap.dedent(data)
        if (self._display_inline == False) or ('run' not in header): # no run given
            return [highlight(dedent_data,language = 'python', className = _class),]
        elif 'run' in header and self._display_inline: 
            source = header.split('run')[1].strip() # Afte run it be source variable
            if source:
                self._shell.user_ns[source] = _str2code(dedent_data,language='python',className = _class) 
            
            # Run Code now 
            with capture_output() as captured:
                (self._slides or self._shell).run_cell(dedent_data)

            outputs = captured.outputs
            return outputs
        
    def _sub_vars(self, html_output):
        "Substitute variables in html_output given as {{var}} and two inline columns as ||C1||C2||"
            
        # Replace variables first 
        user_ns = get_ipython().user_ns
        all_matches = re.findall(r'\{\{(.*?)\}\}', html_output, flags = re.DOTALL)
        for match in all_matches:
            output = match # If below fails, it will be the same as input line
            _match = match.strip()
            if _match in user_ns:
                output = user_ns[_match]
            else:
                raise ValueError(('{{'+ match + '}}' + ' could not be resolved. ' 
                'Only variables are allowed in double curly braces or see Slides.xmd_syntax as well'))
                
            _out = (stringify(output) if output is not None else '') if not isinstance(output, str) else output # Avoid None
            html_output = html_output.replace('{{' + match + '}}', _out, 1)
        
        # Replace inline one argumnet functions
        from . import utils # Inside function to avoid circular import
        for func in _special_funcs.keys():
            all_matches = re.findall(fr'{func}\`(.*?)\`', html_output, flags = re.DOTALL | re.MULTILINE)
            for match in all_matches:
                _func = getattr(utils,func)
                _out = _func(match).value if match else _func().value # If no argument, use default
                html_output = html_output.replace(f'{func}`{match}`', _out, 1)
        
        # Replace columns after vars, so not to format their brackets
        all_cols = re.findall(r'\|\|(.*?)\|\|(.*?)\|\|', html_output, flags = re.DOTALL | re.MULTILINE) # Matches new line as well, useful for inline plots and big objects
        for cols in all_cols:
            _cols = ''.join(f'<div style="width:50%;">{self.convert(c)}</div>' for c in cols)
            _out = f'<div class="columns">{_cols}</div>'
            html_output = html_output.replace(f'||{cols[0]}||{cols[1]}||', _out, 1)
              
        # Replace colored text
        all_matches = re.findall(r'color\[(.*?)\]\`(.*?)\`', html_output, flags = re.DOTALL | re.MULTILINE)
        for match in all_matches:
            kws = {'fg':None,'bg':None}
            if '_' in match[0]:
                kws['fg'], kws['bg'] = [c.strip() for c in match[0].split('_',1)]
            else:
                kws['fg'] = match[0].strip()
            html_output = html_output.replace(f'color[{match[0]}]`{match[1]}`', utils.colored(match[1],**kws).value, 1)
        
        # Run an included file
        all_matches = re.findall(r'include\`(.*?)\`', html_output, flags = re.DOTALL)
        for match in all_matches:
            with open(match,'r') as f:
                repr_html = self.parse(f.read(),display_inline=False,rich_outputs=False)
            html_output = html_output.replace(f'include`{match}`', repr_html, 1)
        
        return html_output # return in main scope
            

def parse_xmd(extended_markdown, display_inline = True, rich_outputs = False):
    """Parse extended markdown and display immediately. 
    If you need output html, use `display_inline = False` but that won't execute python code blocks.
    Precedence of content return/display is `rich_outputs = True > display_inline = True > parsed_html_string`.

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
     This {{var_name}} is code from above and will be substituted with the value of var_name
     ```

     ```python
     # This will not be executed, only shown
     ```
     || Inline-column A || Inline-column B ||
    ```

    Each block can have class names (speparated with space or .) (in 1.4.7+) after all other options such as `python .friendly` or `multicol .Sucess.info`.
    For example, `python .friendly` will be highlighted with friendly theme from pygments.
    Pygments themes, however, are not supported with `multicol`. You need to write and display CSS for a custom class.
    Aynthing with class name 'report-only' will not be displayed on slides, but appears in document when `Slides.export.<export_function>` is called.

    Note: Nested blocks are not supported.
    
    This function was added  in 1.4.6
    
    **New in 1.7.2**    
    Find special syntax to be used in markdown by `Slides.xmd_syntax`.
    
    **New in 1.7.5**
    Use `Slides.extender` or `ipyslides.extended_md.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
    """
    return _ExtendedMarkdown().parse(extended_markdown, display_inline = display_inline, rich_outputs = rich_outputs)  
    
    