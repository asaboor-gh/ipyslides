""" This module is to collect content related functions together in a place.
Useful while writing markdown slides, without intefering with the rest of the code.

New in 1.4.6
"""
#import warnings
from .__version__ import __version__
major,minor, patch = map(int,__version__.split('.'))
if major >= 2:
    if minor < 2:
        print('DeprecationWarning: module "ipyslides.parsers" is being deprecated.\n' 
        'Use function "get_slides_instance" inside a python block in markdown to access same functionality!')
    if minor >= 2:
        raise DeprecationWarning(('module "ipyslides.parsers" is deprecated.\n' 
        'Use function "get_slides_instance" inside a python block in markdown to access same functionality!'))

from .core import _private_instance as __pi
notify          = __pi.notify
notify_later    = __pi.notify_later
parse_xmd       = __pi.parse_xmd
write           = __pi.write
iwrite          = __pi.iwrite
source          = __pi.source
get_source      = __pi.get_source
css_styles      = __pi.css_styles
plt2html        = __pi.plt2html
bokeh2html      = __pi.bokeh2html
highlight       = __pi.highlight
serializer      = __pi.serializer

__all__ = ['notify','notify_later','parse_xmd','write','iwrite','source','get_source','css_styles','plt2html','bokeh2html','highlight','serializer']

from .utils import *
from .utils import __all__ as __all_utils

__all__.extend(__all_utils)