import re
import textwrap

from ..formatters import XTML

_icons = {
    'chevron': '''
        <svg width="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" transform="rotate({rotation})">
            <path d="M9 4L17 12L9 20" />
        </svg>''',
    'pencil': '''
        <svg xmlns="http://www.w3.org/2000/svg" height="{size}" viewBox="0 0 25 25" fill="{color}" stroke-width="2" transform="rotate({rotation})">
            <rect x="9" y="0" width="8" height="6"/>
            <rect x="9" y="7" width="1" height="10"/>
            <rect x="12" y="7" width="2" height="10"/>
            <rect x="16" y="7" width="1" height="10"/>
            <polygon points="9 18,17 18,13 25,9 18"></polygon>
        </svg>''',
    'bars': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="3" stroke="{color}" fill="{color}" transform="rotate({rotation})">
            <circle stroke="none" cx="3" cy="5" r="3"/>
            <circle stroke="none" cx="3" cy="13" r="3"/>
            <circle stroke="none" cx="3" cy="21" r="3"/>
            <line x1="8" y1="5" x2="24" y2="5"/>
            <line x1="8" y1="13" x2="24" y2="13" />
            <line x1="8" y1="21" x2="24" y2="21"/>
        </svg>''',
    'arrow': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" transform="rotate({rotation})">
            <path fill="none" d="M13 4L21 13L13 21M4 13L21 13" />
        </svg>''',
    'arrowb': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" transform="rotate({rotation})">
            <path fill="none" d="M13 4L21 13L13 21M4 13L21 13M22 4L22 21"/>
        </svg>''',
    'close': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" transform="rotate({rotation})">
            <line x1="4" y1="4" x2="21" y2="21" />
            <line x1="4" y1="21" x2="21" y2="4" />
        </svg>''',
    'dots': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" fill="{color}" transform="rotate({rotation})">
          <circle cx="13" cy="5" r="3"/>
          <circle cx="13" cy="13" r="3"/>
          <circle cx="13" cy="21" r="3"/>
        </svg>''',
    'expand': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" transform="rotate({rotation})">
          <line x1="4" y1="21" x2="11" y2="14"/>
          <line x1="14" y1="11" x2="21" y2="4"/>
          <path fill="none" d="M13 4L21 4L21 13" />
          <path fill="none" d="M4 13L4 21L13 21" />
        </svg>''',
    'compress': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" transform="rotate({rotation})">
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
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" transform="rotate({rotation})">
            <polygon points="4 4,21 13,4 21" fill="{color}"></polygon>
        </svg>''',
    'pause': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" fill="{color}" transform="rotate({rotation})">
            <rect x="4" y="4" width="7" height="17"/>
            <rect x="14" y="4" width="7" height="17"/>
        </svg>''',
    'stop': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" fill="{color}" transform="rotate({rotation})">
            <rect x="4" y="4" width="17" height="17"/>
        </svg>''',
    'loading': '''
        <svg xmlns="http://www.w3.org/2000/svg" height="{size}" viewBox="0 0 50 50" transform="rotate({rotation})">
            <path fill="{color}" d="M25,5A20.14,20.14,0,0,1,45,22.88a2.51,2.51,0,0,0,2.49,2.26h0A2.52,2.52,0,0,0,50,22.33a25.14,25.14,0,0,0-50,0,2.52,2.52,0,0,0,2.5,2.81h0A2.51,2.51,0,0,0,5,22.88,20.14,20.14,0,0,1,25,5Z">
                <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.25s" repeatCount="indefinite"/>
            </path>
        </svg>''',
    'circle': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg">
            <circle cx="13" cy="13" r="11" fill="none" stroke="{color}" stroke-width="2"/>
        </svg>''',
    'info': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg">
            <circle cx="13" cy="13" r="11" fill="none" stroke="{color}" stroke-width="2"/>
            <line x1="13" y1="21" x2="13" y2="12" stroke="{color}" stroke-width="5"/>
            <circle cx="13" cy="7.5" r="3" fill="{color}" stroke="none"/>
        </svg>''',
    'refresh': '''
        <svg height="{size}" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <path d=" M 37 18.8 A 17 17 4.2 1 1 32.2 8.2" stroke="{color}" stroke-width="3.5" fill="none"/>
            <path d="M36 11L30 0L24 10" fill="{color}" stroke="none"/>
        </svg>''',
    'laser': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg">
            <circle cx="13" cy="13" r="10" fill="none" stroke="{color}" stroke-width="3" filter="drop-shadow(0 0 1px {color})" opacity="0.2"/>
            <circle cx="13" cy="13" r="7" fill="none" stroke="{color}" stroke-width="2" filter="drop-shadow(0 0 4px {color})" opacity="0.7"/>
            <circle cx="13" cy="13" r="4" fill="{color}" stroke="white" stroke-width="2" filter="drop-shadow(0 0 5px {color})"/>
        </svg>''',
    'zoom-in': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" transform="rotate({rotation})">
            <circle cx="9" cy="9" r="8" fill="none" stroke="{color}"/>
            <line x1="17" y1="17" x2="21" y2="21" stroke="{color}" stroke-width="4"/>
            <line x1="6" y1="9" x2="12" y2="9" stroke="{color}"/>
            <line x1="9" y1="6" x2="9" y2="12" stroke="{color}"/>
        </svg>''',
    'zoom-out': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" transform="rotate({rotation})">
            <circle cx="9" cy="9" r="8" fill="none" stroke="{color}"/>
            <line x1="17" y1="17" x2="21" y2="21" stroke="{color}" stroke-width="4"/>
            <line x1="6" y1="9" x2="12" y2="9" stroke="{color}"/>
        </svg>''',
    'search': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" transform="rotate({rotation})">
            <circle cx="9" cy="9" r="8" fill="none" stroke="{color}"/>
            <line x1="17" y1="17" x2="21" y2="21" stroke="{color}" stroke-width="4"/>
        </svg>''',
    'code': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="7 8 2 13 7 18"></polyline>
            <polyline points="18 8 23 13 18 18"></polyline>
            <line x1="15" y1="4" x2="11" y2="21"></line>
        </svg>''',
    'win-maximize': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="2 4,23 4,23 21,2 21,2 4" fill="none" stroke="{color}"></polygon>
            <polygon points="2 4,23 4,23 8,2 8,2 4" fill="{color}" stroke="{color}"></polygon>
        </svg>''',
    'win-restore': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="2 6,19 6,19 21,2 21,2 6" fill="none" stroke="{color}"></polygon>
            <polygon points="2 8,19 8,19 10,2 10,2 8" fill="{color}" stroke="{color}"></polygon>
            <path d="M4 4L4 2L23 2L23 17L21 17" fill="none" stroke="{color}"/>
        </svg>''',
    'rows': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="rotate({rotation})">
            <path d="M2 2L23 2L23 23L2 23L2 2" fill="none" stroke="{color}"/>
            <line x1="6" y1="7" x2="19" y2="7" stroke="{color}" stroke-width="3" stroke-linecap="butt"/>
            <line x1="6" y1="12.5" x2="19" y2="12.5" stroke="{color}" stroke-width="3" stroke-linecap="butt"/>
            <line x1="6" y1="18" x2="19" y2="18" stroke="{color}" stroke-width="3" stroke-linecap="butt"/>
        </svg>''',
    'columns': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="rotate({rotation})">
            <polygon points="2 2,23 2,23 23,2 23,2 2" fill="none" stroke="{color}"></polygon>
            <polygon points="2 2,23 2,23 8,2 8,2 2" fill="{color}" stroke="{color}"></polygon>
            <line x1="12.5" y1="2" x2="12.5" y2="23" stroke="{color}"/>
        </svg>''',
    'settings': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="5" stroke="{color}" fill="{color}" transform="rotate({rotation})">
            <line x1="1" y1="12.5" x2="24" y2="12.5"/>
            <line x1="6.75" y1="22.46" x2="18.25" y2="2.54"/>
            <line x1="18.25" y1="22.46" x2="6.75" y2="2.54"/>
            <circle fill="white" cx="12.5" cy="12.5" r="6"/>
        </svg>''',
    'panel': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="2 2,23 2,23 23,2 23,2 2" fill="none" stroke="{color}"></polygon>
            <rect x="2" y="2" width="7" height="21" fill="{color}" stroke="{color}"/>
        </svg>''',
    'keyboard': '''
        <svg height="{size}" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="19" height="17" rx="2" fill="none"/>
            <circle cx="6.5" cy="8" r="1.5" fill="{color}" stroke="none"/>
            <circle cx="10.5" cy="8" r="1.5" fill="{color}" stroke="none"/>
            <circle cx="14.5" cy="8" r="1.5" fill="{color}" stroke="none"/>
            <circle cx="18.5" cy="8" r="1.5" fill="{color}" stroke="none"/>
            <circle cx="8.5" cy="12.5" r="1.5" fill="{color}" stroke="none"/>
            <circle cx="12.5" cy="12.5" r="1.5" fill="{color}" stroke="none"/>
            <circle cx="16.5" cy="12.5" r="1.5" fill="{color}" stroke="none"/>
            <circle cx="6.5" cy="17" r="1.5" fill="{color}" stroke="none"/>
            <line x1="10" y1="17" x2="15" y2="17" stroke-width="2.5"/>
            <circle cx="18.5" cy="17" r="1.5" fill="{color}" stroke="none"/>
        </svg>''',
    'swipe-on': '''
        <svg width="{size}" height="{size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" fill="none">
            <rect x="14" y="8" width="36" height="48" rx="16" stroke="{color}" stroke-width="6" fill="none"/>
            <line x1="32" y1="8" x2="32" y2="32" stroke="{color}" stroke-width="5"/>
            <line x1="12" y1="32" x2="52" y2="32" stroke="{color}" stroke-width="5"/>
            <circle cx="24" cy="22" r="4" fill="{color}" />
            <polyline points="8,38 4,32 8,26" stroke="{color}" stroke-width="5" fill="none"/>
            <polyline points="56,38 60,32 56,26" stroke="{color}" stroke-width="5" fill="none"/>
        </svg>''',
    'swipe-off': '''
        <svg width="{size}" height="{size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" fill="none">
            <rect x="14" y="8" width="36" height="48" rx="16" stroke="{color}" stroke-width="6" fill="none" opacity="0.5"/>
            <line x1="32" y1="8" x2="32" y2="32" stroke="{color}" stroke-width="5" opacity="0.5"/>
            <line x1="12" y1="32" x2="52" y2="32" stroke="{color}" stroke-width="5" opacity="0.5"/>
            <circle cx="24" cy="22" r="4" fill="{color}" opacity="0.5"/>
            <polyline points="8,38 4,32 8,26" stroke="{color}" stroke-width="5" fill="none" opacity="0.5"/>
            <polyline points="56,38 60,32 56,26" stroke="{color}" stroke-width="5" fill="none" opacity="0.5"/>
            <line x1="56" y1="8" x2="8" y2="56" stroke="{color}" stroke-width="6"/>
        </svg>''',
}

_icons["edit"] = _icons["pencil"].format(size="{size}", color="{color}", rotation=45)
for c, r in zip('rlud',(0, 180,-90,90)): # their base svgs should stilll be able to rotate any direction
    _icons[f"arrow{c}"] = _icons["arrow"].format(size="{size}", color="{color}", rotation=r)
    _icons[f"arrowb{c}"] = _icons["arrowb"].format(size="{size}", color="{color}", rotation=r)
    _icons[f"chevron{c}"] = _icons["chevron"].format(size="{size}", color="{color}", rotation=r)

def _inline_svg(value: str) -> str:
    # remove newlines and extra spaces, keep 1 space between attributes
    return re.sub(r' +', ' ', value).replace('\n', '').replace('#', '%23')  # replace # with %23 for svg
class Icon(XTML):
    "Get an icon from the available icon set with a given color and size. Not every icon supports rotation."
    available = tuple(sorted(_icons.keys()))
    def __init__(self, name: str, color:str = 'currentColor', size:str = '1em',rotation:int = 0) :
        if name not in _icons:
            raise KeyError(f'Icon {name} not found. Available icons: {", ".join(_icons.keys())}')
        
        _value = _icons[name].format(color=color, size=size, rotation = rotation).replace('#', '%23')  # replace # with %23 for svg
        super().__init__(textwrap.dedent(_value).strip()) # remove leading and trailing whitespace/newlines
        
    def __repr__(self):
        return f'Icon(css = {self.css}, svg = {self.value!r})'
    
    def __format__(self, spec):
        return f'{_inline_svg(self.value):{spec}}' # important for f-strings be iinline to add in tables etc.
    
    @property
    def svg(self):
        "Get the SVG code of the icon."
        return self.value
    
    @property
    def css(self):
        "Get the CSS code of the icon as dictionary of {'content': url(svg)}."
        return {'content': f"url('data:image/svg+xml;utf8,{_inline_svg(self.value)}')"}   
    
    @classmethod
    def get_css_class(cls, name):
        """Get CSS class to add for this an icon name. You need font awsome CSS in exported HTML 
        if you are using ipywidgets Button icons besides defined in this module. check `.available` class attribute for info on names."""
        klass = ' '.join(f"fa-{n}" for n in name.split()) # can be many icons
        return f"fa {klass}" if klass else ""