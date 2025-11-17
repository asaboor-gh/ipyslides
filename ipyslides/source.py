"""
Display source code from files/context managers.
"""
import ast, re, os
import sys, linecache
import textwrap
import inspect
import pygments

from pathlib import Path
from contextlib import contextmanager, suppress
from IPython.display import display

from .formatters import _highlight, XTML
    

# Do not use this in main work, just inside a function
class SourceCode(XTML):
    """Returns the source code of the object as HTML.
    Use `.show(lines)` to show only selected lines (list/tuple/range).
    Use `.focus(lines)` to focus on selected lines (list/tuple/range).
    Use `.inline` property to get inline code object.
    Use `.collapsed` property to get collapsed code object.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._raw = ''
    
    def __repr__(self): # short for view
        return f'<{self.__module__}.SourceCode at {hex(id(self))}>'
    
    @property
    def raw(self):
        "Return raw source code."
        return self._raw
    
    @raw.setter
    def raw(self, value):
        "Set raw source code."
        self._raw = value.strip() # avoid new lines
    
    def display(self,collapsed = False, summary = "Show Code"):
        "Display source object in IPython notebook, with optionally showing as collpased element."
        if collapsed:
            return XTML(f"""<details style='max-height:100%;overflow:auto;'>
                <summary>{summary}</summary>
                {self.value}
                </details>""").display()
        else:
            return display(self) # Without collapsed

    def show(self, lines):
        "Return source object with selected lines from list/tuple/range of lines. You can use list/slice indexes to show instead of this."
        if not isinstance(lines,(list,tuple,range)):
            raise TypeError(f'lines must be list, tuple or range, not {type(lines)}')
        
        start, *middle = self.value.split('<code>')
        middle[-1], end = middle[-1].split('</code>')
        middle[-1] += '</code>'
        max_index = len(middle) - 1
        lines = sorted([idx for idx in lines if idx <= max_index]) # don't throw error
        for line in lines:
            if not isinstance(line,int) or line < 0:
                raise ValueError(f'lines must be positive intergers, not {lines}!')
        
        new_lines = [start]
        picks = [-1,*lines]
        for a, b in zip(picks[:-1],picks[1:]):
            if b - a > 1: # Not consecutive lines
                new_lines.append(f'<code class="dim"> + {b - a - 1} more lines ... </code>')
            new_lines.append('<code>' + middle[b])
        
        if lines and lines[-1] < max_index:
            new_lines.append(f'<code class="dim"> + {max_index - lines[-1]} more lines ... </code>')
        
        return self.__class__(''.join([*new_lines, end]))     
    
    def focus(self, lines):
        "Return source object with focus on given list/tuple/range of lines. You can use tuple indexes to focus instead of this."
        if not isinstance(lines,(list,tuple,range)):
            raise TypeError(f'lines must be list, tuple or range, not {type(lines)}')
        lines = sorted([idx for idx in lines])
        for line in lines:
            if not isinstance(line,int) or line < 0:
                raise ValueError(f'lines must be positive integers, not {lines}!')
        
        _lines = []
        for i, line in enumerate(self.value.split('<code>'), start = -1):
            if i == -1:
                _lines.append(line) # start things
            elif i not in lines:
                _lines.append('<code class="dim">' + line)
            else:
                _lines.append('<code>' + line)
        
        return self.__class__(''.join(_lines))
    
    @property
    def inline(self): 
        "Return inline code object that can be embedded inside text."
        klass = lambda attr: 'highlight inline' + (' dim' if 'dim' in attr else '')
        return XTML( 
            '<br>'.join(f'<code class="{klass(attr)}" style="white-space:pre-wrap;">' + c 
                for attr, c in re.findall(r'\<\s*code(.*?)\>(.*?\<\s*\/\s*code\s*\>)', 
                    self.value, flags=re.DOTALL | re.MULTILINE
        ))) # intended to be one liner, but leave for flexibility
    
    @property
    def collapsed(self):
        "Return collapsed code object that can be expanded on click."
        return XTML(f"""<details style='max-height:400px;overflow:auto;'>
            <summary>Show Code</summary>
            {self.value}
            </details>""")


def _file2code(filename,language='python',name=None,**kwargs):
    "Only reads plain text or StringIO, return source object with `show` and `focus` methods."
    try:
        text = filename.read() # if stringIO
    except:
        with open(filename,'r',encoding='utf-8') as f: # emoji support
            text = f.read()
    
    return _str2code(text,language=language,name=name,**kwargs)


def _str2code(text,language='python',name=None,**kwargs):
    "Only reads plain text source code, return source object with `show` and `focus` methods."
    out = SourceCode(_highlight(text,language = language, name = name, **kwargs))
    out.raw = text
    return out

class code:
    """Create highlighted source code object from text, file or callable.
    
    Use code(obj) or code.cast(obj) to get source code from any object that has a source or str of code.
    
    Explicitly use:
    
    - code.from_file(filename) to get a source object from a file or file-like object.
    - code.from_string(string) to get a source object from a string.
    - code.from_source(obj) to get a source object from a python object (class, function, module, method etc.).
    
    **Returns**: `SourceCode` object with `show` and `focus` methods to show selective lines, as well as `.inline` and `.collapsed` properties.
    """
    def __new__(cls, obj, language='python',name=None, css_class = None, style='default', color = None, background = None, hover_color = 'var(--bg3-color)', lineno = True, height='400px'):
        """Highlight code (any python object that has a source or str of code) with given language and style. 

        - style only works if css_class is given.
        - If css_class is given and matches any of code`pygments.styles.get_all_styles()`, then style will be applied immediately.
        - color is used for text color as some themes dont provide text color. 
        - CSS properties like color and background are applied if css_class is provided.
        - height is max-height of code block, it does not expand more than code itself.
        - If `obj` is a file-like object, it's `read` method will be accessed to get source code.

        If you want plain inline syntax highlighting, use `Slides.code`.
        """
        kwargs = {k:v for k,v in locals().items() if k not in 'cls obj language name'}
        if isinstance(obj, (str,Path)) or (hasattr(obj,'read') and callable(obj.read)):
            try:
                return cls.from_file(obj,language=language,name=name, **kwargs)
            except:
                return cls.from_string(obj, language=language,name=name, **kwargs)
        else:
            return cls.from_source(obj, **kwargs)
    
    cast = classmethod(__new__)

    @classmethod
    def from_string(cls,text,language='python',name=None,**kwargs):
        "Creates source object from string. `name` is alternate used name for language. `kwargs` are passed to `Slides.code`."
        return _str2code(text,language=language,name=name,**kwargs)
    
    @classmethod
    def from_file(cls, file,language = None,name = None,**kwargs):
        """Returns source object with `show` and `focus` methods. `name` is alternate used name for language.  
        `kwargs` are passed to `Slides.code`.     
        
        It tries to auto detect lanaguage from filename extension, if `language` is not given.
        """
        _title = name or file
        _lang = language or os.path.splitext(str(file))[-1].replace('.','')
        
        if language is None:
            lexer = None
            with suppress(BaseException):
                lexer = pygments.lexers.get_lexer_by_name(_lang)
                
            if lexer is None:
                raise Exception(f'Failed to detect language from file {file!r}. Use language argument!')
            
        return _file2code(file,language = _lang,name = _title,**kwargs)
    
    @classmethod       
    def from_source(cls, obj,**kwargs):
        "Returns source code from a given obj [class,function,module,method etc.] with `show` and `focus` methods. `kwargs` are passed to `Slides.code`"
        for _type in ['class','function','module','method','builtin','generator']:
            if getattr(inspect,f'is{_type}')(obj):
                source = inspect.getsource(obj)
                return _str2code(source,**{**kwargs,'language':'python','name':None}) # avoid chnagings name here

        # If things above do not work, raise error
        raise TypeError(f"Cannot access source code of {obj}!")
    
    @classmethod
    @contextmanager 
    def context(cls, returns = False, **kwargs): 
        """Execute and displays source code in the context manager. `kwargs` are passed to `Slides.code` function.
        Useful when source is written inside context manager itself.
        If `returns` is False (by default), then source is displayed before the output of code. Otherwise you can assign the source to a variable and display it later anywhere.
        
        **Usage**:
        ```python
        with source.context(returns = True) as s: 
            do_something()
            write(s) # or s.display(), write(s)
            
        #s.raw, s.value are accesible attributes.
        #s.focus, s.show are methods that are used to focus/show selective lines.
        ```
        """ 
        frame = sys._getframe() 
        depth = 2 # default depth is 2 to catch under itself, others would be given from differnt context managers to get their source.
        if 'depth' in kwargs:
            depth = kwargs.pop('depth')
        
        for _ in range(depth):
            frame = frame.f_back # keep going back until required depth is reached.
              
        if kwargs.pop("start", False):
            yield (''.join(inspect.getframeinfo(frame).code_context)).strip() # other one is full code, this is where function called
            return # breaking it is must by return

        lines, n1 = linecache.getlines(frame.f_code.co_filename), frame.f_lineno
        offset = 0 # going back to zero indent level
        
        while (len(lines) > n1 - offset >= 0) and re.match(r'^\t?^\s+', lines[n1 - offset]): 
            offset = offset + 1
             
        _source = ''.join(lines[n1 - offset:])
        tree = ast.parse(_source or lines[0]) # empty source if it is just one line like with func(): pass
        with_node = tree.body[0] # Could be itself at top level
        
        for node in ast.walk(tree):
            if isinstance(node, ast.With) and node.lineno == offset: # that much gone up, so back same
                with_node = node
                break

        n2 = with_node.body[-1].end_lineno if hasattr(with_node, 'body') else with_node.end_lineno #can include multiline expressions in python 3.8+, could be an expression
        source = textwrap.dedent(''.join(lines[n1:][:n2 - offset])) # n2 is not from source, but current block as if n1 was zero, so sliced after n1 slice
        source_html = SourceCode(_highlight(source,language = 'python', **kwargs))
        source_html.raw = source # raw source code
        
        if not returns:
            source_html.display()
        
        yield source_html