import string
import textwrap, re
from markdown import Markdown
from IPython.core.display import display
from IPython import get_ipython

from .formatter import _HTML, highlight, stringify
from .source import _str2code

_md_extensions = ['tables','footnotes','attr_list'] # For MArkdown Parser
# Add fix_repr here for all objects other than string
# Add column divider firts
# after tha evalue python code blocks with display options
# at last evaluate expressions in {{exp}}
    
class ExetendedMarkdown(Markdown):
    "New in 1.4.5"
    def __init__(self):
        self.extensions = _md_extensions
        super().__init__(extensions = self.extensions)
        self._display_inline = False
        
    def parse(self, md_str, display_inline = False):
        """Return a string after fixing markdown and code/multicol blocks if display_inline is False
        Else displays objects and execute python code from '```python run source_var_name' block.
        
        New in 1.4.5
        """
        self._display_inline = display_inline # Must chnage here
        new_str = md_str.split('```') # Split by code blocks
        collect = ''
        if len(new_str) > 1:
            for i, section in enumerate(new_str):
                if i % 2 == 0:
                    out = self.convert(section)
                    if display_inline:
                        display(_HTML(out))
                    else:
                        collect += out
                else:
                    out = self._parse_block(section) 
                    if display_inline:
                        display(_HTML(out))
                    else:
                        collect += out
            return collect
        else:
            out = self.convert(new_str[0])
            if display_inline:
                display(_HTML(out))
            else:
                return out
    
    def _parse_block(self, block):
        "Returns parsed block or columns or code, input is without ``` but includes langauge name."
        line, data = block.split('\n',1)
        if 'multicol' in line:
            return self._parse_multicol(data, line.strip())
        elif 'python' in line:
            return self._parse_python(data, line.strip())
        else:
            language = line.strip() if line.strip() else 'text' # If no language, assume
            name = ' ' if language == 'text' else None # If no language or text, don't show name
            return highlight(data,language = language, name = name, className=None).value # no need to highlight with className separately     
        
    def _parse_multicol(self, data, header):
        "Returns parsed block or columns or code, input is without ``` but includes langauge name."
        cols = data.split('+++') # Split by columns
        cols = [self.convert(col) for col in cols] 
        if len(cols) == 1:
            return cols[0] # Single as is
        
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
        
        return f'<div class="columns">{cols}\n</div>'
    
    def _parse_python(self, data, header):
        # if inside some writing command, do not run code at all
        if len(header.split()) > 4:
            raise ValueError(f'Too many arguments in {header!r}, expects 4 or less as ```python run source_var_name above(below)')
        if self._display_inline == False or header.lower() == 'python': # no run given
            return highlight(data,language = 'python', className=None).value
        elif 'run' in header and self._display_inline: 
            dedent_data = textwrap.dedent(data)
            source = header.split('run')[1].strip() # Afte run it be source variable
            _source_out = _str2code(dedent_data,language='python',className=None)
            if source:
                get_ipython().user_ns[source] = _source_out
            if 'above' in header:
                display(_source_out)
            # Run Code now
            get_ipython().run_cell(dedent_data) # Run after assigning it to variable, so can be accessed inside code too
            
            if 'below' in header and not 'above' in header:
                display(_source_out)
    
    def eval_exp(self, html_output):
        all_matches = re.findall(r'\{\{(.*?)\}\}', html_output) # ['x','x + y'] in {{x}}, {{x + y}}
        # only have python vars here, and functions in scope of LiveSlides to eval
        # for match in all_matches:
        #     try:
        #         html_output = html_output.replace(f'{{{match}}}', string(eval(match)))
        #     except Exception as e:
        #         raise e
            
        
        
    
    