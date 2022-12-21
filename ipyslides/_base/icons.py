import re
from textwrap import dedent as _dedent

from ..formatters import _HTML

_icons = {
    'chevron-left': '''
        <svg width="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
            <path d="M15 4L7 12L15 20" />
        </svg>''',
    'chevron-right': '''
        <svg width="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
            <path d="M9 4L17 12L9 20" />
        </svg>''',
    'chevron-up': '''
        <svg width="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
            <path d="M4 15L12 7L20 15" />
        </svg>''',
    'chevron-down': '''
        <svg width="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
            <path d="M4 9L12 17L20 9"/>
        </svg>''',
    'pencil': '''
        <svg xmlns="http://www.w3.org/2000/svg" height="{size}" viewBox="0 0 25 25" fill="{color}" stroke-width="2" transform="rotate(45)">
            <rect x="9" y="0" width="8" height="6"/>
            <rect x="9" y="7" width="1" height="10"/>
            <rect x="12" y="7" width="2" height="10"/>
            <rect x="16" y="7" width="1" height="10"/>
            <polygon points="9 18,17 18,13 25,9 18"></polygon>
        </svg>''',
    'toc': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="3" stroke="{color}" fill="{color}">
            <circle stroke="none" cx="3" cy="5" r="3"/>
            <circle stroke="none" cx="3" cy="13" r="3"/>
            <circle stroke="none" cx="3" cy="21" r="3"/>
            <line x1="8" y1="5" x2="24" y2="5"/>
            <line x1="8" y1="13" x2="24" y2="13" />
            <line x1="8" y1="21" x2="24" y2="21"/>
        </svg>''',
    'back': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" y1="13" x2="21" y2="13" />
            <path fill="none" d="M13 4L4 13L13 21" />
        </svg>''',
    'close': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" y1="4" x2="21" y2="21" />
            <line x1="4" y1="21" x2="21" y2="4" />
        </svg>''',
    'dots': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" fill="{color}">
          <circle cx="13" cy="5" r="3"/>
          <circle cx="13" cy="13" r="3"/>
          <circle cx="13" cy="21" r="3"/>
        </svg>''',
    'expand': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="21" x2="11" y2="14"/>
          <line x1="14" y1="11" x2="21" y2="4"/>
          <path fill="none" d="M13 4L21 4L21 13" />
          <path fill="none" d="M4 13L4 21L13 21" />
        </svg>''',
    'compress': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="21" x2="11" y2="14"/>
          <line x1="14" y1="11" x2="21" y2="4"/>
          <path fill="none" d="M14 4L14 11L21 11" />
          <path fill="none" d="M4 14L11 14L11 21" />
        </svg>''',
    'camera': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="4 8, 7 8,10 6, 16 6, 19 8, 22 8, 22 22, 4 22" fill="{color}"></polygon>
            <circle cx="13" cy="15" r="5" fill="black" stroke="white"/>
        </svg>''',
    'play': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg">
            <polygon points="4 4,21 13,4 21" fill="{color}"></polygon>
        </svg>''',
    'pause': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" fill="{color}">
            <rect x="4" y="4" width="7" height="17"/>
            <rect x="14" y="4" width="7" height="17"/>
        </svg>''',
    'loading': '''
        <svg xmlns="http://www.w3.org/2000/svg" height="{size}" viewBox="0 0 50 50">
            <path fill="{color}" d="M25,5A20.14,20.14,0,0,1,45,22.88a2.51,2.51,0,0,0,2.49,2.26h0A2.52,2.52,0,0,0,50,22.33a25.14,25.14,0,0,0-50,0,2.52,2.52,0,0,0,2.5,2.81h0A2.51,2.51,0,0,0,5,22.88,20.14,20.14,0,0,1,25,5Z">
                <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.5s" repeatCount="indefinite"/>
            </path>
        </svg>''',
}

class Icon(_HTML):
    def __init__(self, name: str, color:str = 'currentColor', size:str = '1em') :
        "Get an icon from the available icon set with a given color and size."
        if name not in _icons:
            raise ValueError(f'Icon {name} not found. Available icons: {", ".join(_icons.keys())}')
        
        _value = _icons[name].format(color=color, size=size).replace('#', '%23')  # replace # with %23 for svg
        super().__init__(_dedent(_value).strip()) # remove leading and trailing whitespace/newlines
        
    def __repr__(self):
        return f'Icon(css = {self.css}, svg = {self.value!r})'
    
    def __format__(self, spec):
        return f'{self._svg_inline:{spec}}' # important for f-strings be iinline to add in tables etc.
    
    @property
    def svg(self):
        "Get the SVG code of the icon."
        return self.value
    
    @property
    def _svg_inline(self):
        return re.sub(r' +', ' ', self.value).replace('\n', '') # remove newlines and extra spaces, keep 1
    
    @property
    def css(self):
        "Get the CSS code of the icon as dictionary of {'content': url(svg)}."
        return {'content': f"url('data:image/svg+xml;utf8,{self._svg_inline}')"}
        
        