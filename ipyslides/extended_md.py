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
"""


import textwrap, re
from markdown import Markdown
from IPython.core.display import display
from IPython import get_ipython
from IPython.utils.capture import capture_output

from .formatter import _HTML, highlight, stringify
from .source import _str2code

_md_extensions = ['tables','footnotes','attr_list'] # For MArkdown Parser

    
class _ExtendedMarkdown(Markdown):
    "New in 1.4.5"
    def __init__(self):
        self.extensions = _md_extensions
        super().__init__(extensions = self.extensions)
        self._display_inline = False
        self._run_code = False
    
    def _extract_class(self, header):
        out = header.split('.')
        if len(out) == 1:
            return out[0].strip(), ''
        return out[0].strip(), out[1].strip()
        
    def parse(self, xmd, display_inline = False, rich_outputs = False):
        """Return a string after fixing markdown and code/multicol blocks if display_inline is False
        Else displays objects and execute python code from '```python run source_var_name' block.
        Precedence of content return/display is:
        rich_outputs = True > display_inline = True > parsed_html_string
        
        New in 1.4.5
        """
        self._display_inline = display_inline # Must change here
        if xmd[:3] == '```': # Could be a block just in start of file or string
            xmd = '\n' + xmd
            
        new_strs = xmd.split('\n```') # This avoids nested blocks and it should be
        outputs =[]
        if len(new_strs) > 1:
            for i, section in enumerate(new_strs):
                if i % 2 == 0:
                    out = self._sub_vars(self.convert(section))
                    outputs.append(_HTML(out))
                else:
                    outputs.extend(self._parse_block(section)) # vars are substituted already inside
        else:
            out = self._sub_vars(self.convert(new_strs[0]))
            outputs.append(_HTML(out))
        
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
    
    def _parse_block(self, block):
        "Returns list of parsed block or columns or code, input is without ``` but includes langauge name."
        header, data = block.split('\n',1)
        line, _class = self._extract_class(header)
        if 'multicol' in line:
            return [_HTML(self._sub_vars(self._parse_multicol(data, line, _class))),]
        elif 'python' in line:
            return self._parse_python(data, line, _class) # itself list
        else:
            language = line.strip() if line.strip() else 'text' # If no language, assume
            name = ' ' if language == 'text' else None # If no language or text, don't show name
            return [highlight(data,language = language, name = name, className = _class),] # no need to highlight with className separately     
        
    def _parse_multicol(self, data, header, _class):
        "Returns parsed block or columns or code, input is without \`\`\` but includes langauge name."
        cols = data.split('+++') # Split by columns
        cols = [self.convert(col) for col in cols] 
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
        shell = get_ipython()
        if len(header.split()) > 3:
            raise ValueError(f'Too many arguments in {header!r}, expects 3 or less as ```python run source_var_name')
        dedent_data = textwrap.dedent(data)
        if self._display_inline == False or header.lower() == 'python': # no run given
            return [highlight(dedent_data,language = 'python', className = _class),]
        elif 'run' in header and self._display_inline: 
            source = header.split('run')[1].strip() # Afte run it be source variable
            _source_out = _str2code(dedent_data,language='python',className = _class)
            
            if source:
                shell.user_ns[source] = _source_out 
            # Run Code now
            with capture_output() as captured:
                shell.run_cell(dedent_data) # Run after assigning it to variable, so can be accessed inside code too
            return captured.outputs
    
    def _sub_vars(self, html_output):
        "Substitute variables in html_output given as {{var}}, and two inline columns as ||C1||C2||"
    
        # Replace variables first 
        all_matches = re.findall(r'\{\{(.*?)\}\}', html_output)
        # only have python vars here, security is an issue for expressions
        for match in all_matches:
            try:
                var = get_ipython().user_ns[match.strip()]
                if isinstance(var, str):
                    html_output = html_output.replace('{{' + match + '}}', var, 1)
                else:
                    html_output = html_output.replace('{{' + match + '}}', stringify(var), 1)
            except Exception as e:
                raise e
        
        # Replace columns after vars, so not to format their brackets
        all_cols = re.findall(r'\|\|(.*?)\|\|(.*?)\|\|', html_output, flags = re.DOTALL) # Matches new line as well, useful for inline plots and big objects
        for cols in all_cols:
            _cols = ''.join(f'<div style="width:50%;">{self.convert(c)}</div>' for c in cols)
            _out = f'<div class="columns">{_cols}</div>'
            html_output = html_output.replace(f'||{cols[0]}||{cols[1]}||', _out, 1)
        
        return html_output # return in main scope
            

def parse_xmd(extended_markdown, display_inline = True, rich_outputs = False):
    """Parse extended markdown and display immediately. 
    If you need output html, use display_inline = False but that won't execute python code blocks.
    Precedence of content return/display is:
        rich_outputs = True > display_inline = True > parsed_html_string
        
    You can use the following syntax:

        ```python run var_name
        # If no var_name, code will be executed without assigning it to any variable
        import numpy as np
        ```
        # Normal Markdown {.report-only}
        ```multicol 40 60
        # First column is 40% width
        If 40 60 was not given, all columns will be of equal width
        +++
        # Second column is 60% wide
        This \{\{var_name\}\} is code from above and will be substituted with the value of var_name
        ```

        ```python
        # This will not be executed, only shown
        ```
        || Inline-column A || Inline-column B ||

    Each block can have a class name (in 1.4.7+) after all other options such as `python .friendly` or `multicol .Sucess`.
    For example, `python .friendly` will be highlighted with friendly theme from pygments.
    Pygments themes, however, are not supported with `multicol`.
    Aynthing with class name 'report-only' will not be displayed on slides, but appears in document when `LiveSlides.display_html` is called.
    
    Note: Nested blocks are not supported.
    New in 1.4.6
    """
    return _ExtendedMarkdown().parse(extended_markdown, display_inline = display_inline, rich_outputs = rich_outputs)  
    
    