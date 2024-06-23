"""
Display source code from files/context managers.
"""
import ast, re, os
import sys, linecache
import textwrap
import inspect
import pygments

from contextlib import contextmanager, suppress
from IPython.display import display

from .formatters import highlight, XTML
    

# Do not use this in main work, just inside a function
class SourceCode(XTML):
    "Returns the source code of the object as HTML."
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._raw = ''
    
    @property
    def raw(self):
        "Return raw source code."
        return self._raw
    
    @raw.setter
    def raw(self, value):
        "Set raw source code."
        self._raw = value
    
    def display(self,collapsed = False):
        "Display source object in IPython notebook."
        if collapsed:
            return XTML(f"""<details style='max-height:100%;overflow:auto;'>
                <summary>Show Code</summary>
                {self.value}
                </details>""").display()
        else:
            return display(self) # Without collapsed

    def show_lines(self, lines):
        "Return source object with selected lines from list/tuple/range of lines."
        if not isinstance(lines,(list,tuple,range)):
            raise TypeError(f'lines must be list, tuple or range, not {type(lines)}')
        
        start, *middle = self.value.split('<code>')
        middle[-1], end = middle[-1].split('</code>')
        middle[-1] += '</code>'
        max_index = len(middle) - 1
        lines = sorted([idx for idx in lines if idx <= max_index]) # don't throw error, just skip out of bound indices
        
        new_lines = [start]
        picks = [-1,*lines]
        for a, b in zip(picks[:-1],picks[1:]):
            if b - a > 1: # Not consecutive lines
                new_lines.append(f'<code class="code-no-focus"> + {b - a - 1} more lines ... </code>')
            new_lines.append('<code>' + middle[b])
        
        if lines and lines[-1] < max_index:
            new_lines.append(f'<code class="code-no-focus"> + {max_index - lines[-1]} more lines ... </code>')
        
        return self.__class__(''.join([*new_lines, end]))     
    
    def focus_lines(self, lines):
        "Return source object with focus on given list/tuple/range of lines."
        if not isinstance(lines,(list,tuple,range)):
            raise TypeError(f'lines must be list, tuple or range, not {type(lines)}')
        
        _lines = []
        for i, line in enumerate(self.value.split('<code>'), start = -1):
            if i == -1:
                _lines.append(line) # start things
            elif i not in lines:
                _lines.append('<code class="code-no-focus">' + line)
            else:
                _lines.append('<code class="code-focus">' + line)
        
        return self.__class__(''.join(_lines))

def _file2code(filename,language='python',name=None,**kwargs):
    "Only reads plain text or StringIO, return source object with `show_lines` and `focus_lines` methods."
    try:
        text = filename.read() # if stringIO
    except:
        with open(filename,'r',encoding='utf-8') as f: # emoji support
            text = f.read()
    
    return _str2code(text,language=language,name=name,**kwargs)


def _str2code(text,language='python',name=None,**kwargs):
    "Only reads plain text source code, return source object with `show_lines` and `focus_lines` methods."
    out = SourceCode(highlight(text,language = language, name = name, **kwargs).value)
    out.raw = text
    return out

class Code:
    def __init__(self,*args,**kwargs):
        raise Exception("""This class is not meant to be instantiated.
        Use cls.context() to get a context manager for source.
        Use cls.cast(obj) to get a source code from text, file or callable. Or explicitly:
            - cls.from_file(filename) to get a source object from a file.
            - cls.from_string(string) to get a source object from a string.
            - cls.from_callable(callable) to get a source object from a callable.
        """)
    
    @classmethod
    def cast(cls, obj, language='python',name=None, **kwargs):
        "Create source code object from file, text or callable. `kwargs` are passed to `ipyslides.formatter.highlight`."
        if isinstance(obj, str):
            try:
                return cls.from_file(obj,language=language,name=name, **kwargs)
            except:
                return cls.from_string(obj, language=language,name=name, **kwargs)
        else:
            return cls.from_callable(obj, **kwargs)
    
    @classmethod
    def from_string(cls,text,language='python',name=None,**kwargs):
        "Creates source object from string. `name` is alternate used name for language. `kwargs` are passed to `ipyslides.formatter.highlight`."
        return _str2code(text,language=language,name=name,**kwargs)
    
    @classmethod
    def from_file(cls, filename,language = None,name = None,**kwargs):
        """Returns source object with `show_lines` and `focus_lines` methods. `name` is alternate used name for language.  
        `kwargs` are passed to `ipyslides.formatter.highlight`.     
        
        It tries to auto detect lanaguage from filename extension, if `language` is not given.
        """
        _title = name or filename
        _lang = language or os.path.splitext(filename)[-1].replace('.','')
        
        if language is None:
            lexer = None
            with suppress(BaseException):
                lexer = pygments.lexers.get_lexer_by_name(_lang)
                
            if lexer is None:
                raise Exception(f'Failed to detect language from file {filename!r}. Use language argument!')
            
        return _file2code(filename,language = _lang,name = _title,**kwargs)
    
    @classmethod       
    def from_callable(cls, callable,**kwargs):
        "Returns source object from a given callable [class,function,module,method etc.] with `show_lines` and `focus_lines` methods. `kwargs` are passed to `ipyslides.formatter.highlight`"
        for _type in ['class','function','module','method','builtin','generator']:
            if getattr(inspect,f'is{_type}')(callable):
                source = inspect.getsource(callable)
                return _str2code(source,language='python',name=None)
            
        # If things above do not work, raise error
        raise TypeError(f"Object {callable} is not callable!")
    
    @classmethod
    @contextmanager 
    def context(cls, returns = False, **kwargs): 
        """Execute and displays source code in the context manager. `kwargs` are passed to `ipyslides.formatter.highlight` function.
        Useful when source is written inside context manager itself.
        If `returns` is False (by default), then source is displayed before the output of code. Otherwise you can assign the source to a variable and display it later anywhere.
        
        **Usage**:
        ```python
        with source.context(returns = True) as s: 
            do_something()
            write(s) # or s.display(), write(s)
            
        #s.raw, s.value are accesible attributes.
        #s.focus_lines, s.show_lines are methods that are used to show selective lines.
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
        
        while (len(lines) > n1 - offset >= 0) and re.match('^\t?^\s+', lines[n1 - offset]): 
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
        source_html = SourceCode(highlight(source,language = 'python', **kwargs).value)
        source_html.raw = source # raw source code
        
        if not returns:
            source_html.display()
        
        yield source_html
        
