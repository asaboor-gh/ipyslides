""" This module is to collect content related functions together in a place.
Useful while writing markdown slides, without intefering with the rest of the code.

New in 1.4.6
"""
from .core import _private_instance as __pi
cite            = __pi.cite
write_citations = __pi.write_citations
write_slide_css = __pi.write_slide_css
notify          = __pi.notify
notify_later    = __pi.notify_later
insert_notes    = __pi.notes.insert
parse_xmd       = __pi.parse_xmd
write           = __pi.write
iwrite          = __pi.iwrite
source          = __pi.source
css_styles      = __pi.css_styles
plt2html        = __pi.plt2html
bokeh2html      = __pi.bokeh2html
highlight       = __pi.highlight

__all__ = ['cite', 'write_citations', 'write_slide_css', 'notify', 'notify_later', 'insert_notes', 'parse_xmd', 'write', 'iwrite', 'source', 'css_styles', 'plt2html', 'bokeh2html', 'highlight']
from .utils import *
from .utils import __all__ as __all_utils

__all__.extend(__all_utils)