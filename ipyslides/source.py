"""
Display source code from files/context managers.
"""
import ast, re
import sys, linecache
import textwrap
import inspect
from contextlib import contextmanager

from .formatter import highlight, _HTML
    

# Do not use this in main work, just inside a function
class _Source(_HTML):
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

    def show_lines(self, lines):
        "Return source object with selected lines from list/tuple/range of lines."
        if not isinstance(lines,(list,tuple,range)):
            raise TypeError(f'lines must be list, tuple or range, not {type(lines)}')
        
        start, *middle = self.value.split('<code>')
        middle[-1], end = middle[-1].split('</code>')
        middle[-1] += '</code>'
        _max_index = len(middle) - 1
        
        new_lines = [start]
        picks = [-1,*sorted(lines)]
        for a, b in zip(picks[:-1],picks[1:]):
            if b - a > 1: # Not consecutive lines
                new_lines.append(f'<code class="code-no-focus"> + {b - a - 1} more lines ... </code>')
            new_lines.append('<code>' + middle[b])
        
        if lines and lines[-1] < _max_index:
            new_lines.append(f'<code class="code-no-focus"> + {_max_index - lines[-1]} more lines ... </code>')
        
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
        with open(filename,'r') as f:
            text = f.read()
    
    return _str2code(text,language=language,name=name,**kwargs)


def _str2code(text,language='python',name=None,**kwargs):
    "Only reads plain text source code, return source object with `show_lines` and `focus_lines` methods."
    out = _Source(highlight(text,language = language, name = name, **kwargs).value)
    out.raw = text
    return out

class Source:
    current = None
    def __init__(self):
        raise Exception("""This class is not meant to be instantiated.
        Use Source.context() to get a context manager for source.
        Use Source.current to get the current source object.
        Use Source.from_file(filename) to get a source object from a file.
        Use Source.from_string(string) to get a source object from a string.
        Use Source.from_callable(callable) to get a source object from a callable.
        """)
    @classmethod
    def from_string(cls,text,language='python',name=None,**kwargs):
        "Creates source object from string. `name` is alternate used name for language. `kwargs` are passed to `ipyslides.formatter.highlight`."
        cls.current = _str2code(text,language=language,name=name,**kwargs)
        return cls.current
    
    @classmethod
    def from_file(cls, filename,language='python',name=None,**kwargs):
        "Returns source object with `show_lines` and `focus_lines` methods. `name` is alternate used name for language.`kwargs` are passed to `ipyslides.formatter.highlight`"
        _title = filename if name is None else name
        cls.current = _file2code(filename,language=language,name=_title,**kwargs)
        return cls.current
    
    @classmethod       
    def from_callable(cls, callable,**kwargs):
        "Returns source object from a given callable [class,function,module,method etc.] with `show_lines` and `focus_lines` methods. `kwargs` are passed to `ipyslides.formatter.highlight`"
        for _type in ['class','function','module','method','builtin','generator']:
            if getattr(inspect,f'is{_type}')(callable):
                source = inspect.getsource(callable)
                cls.current = _str2code(source,language='python',name=None)
                return cls.current
    
    @classmethod
    @contextmanager 
    def context(cls, **kwargs): 
        """Excute and displays source code in the context manager. kwargs are passed to `ipyslides.formatter.highlight` function.
        Useful when source is written inside context manager itself.
        **Usage**:
        ```python
        with source.context() as s: #if not used as `s`, still it is stored `source.current` attribute.`
            do_something()
            write(s)
            
        #s.raw, s.value are accesible attributes.
        #s.focus_lines, s.show_lines are methods that are used to show selective lines.
        ```
        """  
        frame = sys._getframe().f_back.f_back # go two steps back
        lines, n1 = linecache.getlines(frame.f_code.co_filename), frame.f_lineno
        offset = 0 # going back to zero indent level
        while re.match('^\t?^\s+', lines[n1 - offset]): 
             offset = offset + 1
             
        _source = ''.join(lines[n1 - offset:])
        tree = ast.parse(_source)
        with_node = tree.body[0] # Could be itself at top level
        
        for node in ast.walk(tree):
            if isinstance(node, ast.With) and node.lineno == offset: # that much gone up, so back same
                with_node = node
                break

        if (sys.version_info.major >= 3) and (sys.version_info.minor >= 8):
            n2 = with_node.body[-1].end_lineno #can include multiline expression
        else: # if no next sibling node, pick by brute force for < 3.8
            n2 = with_node.body[-1].lineno # multiline expressions can't be handled, just first line picked
        
        source = textwrap.dedent(''.join(lines[n1:][:n2 - offset]))
        source_html = _Source(highlight(source,language = 'python', **kwargs).value)
        source_html.raw = source # raw source code
        cls.current = source_html
        
        yield source_html
        # No need to try as it is not possible to get here if not in context manager