"""
Export Slides to HTML report and static HTML slides. It is used by program itself, 
not by end user.
"""
import os
from contextlib import suppress
from .export_template import doc_css, doc_html, slides_css
from ..formatters import code_css
from . import styles

class _HhtmlExporter:
    # Should be used inside Slides class only.
    def __init__(self, _instance_BaseSlides):
        self.main = _instance_BaseSlides
        self.main.widgets.ddowns.export.observe(self._export, names = ['value']) # Export button
        
    def _htmlize(self, allow_non_html_repr = False, as_slides = False, **kwargs):
        "page_size, slide_number are in kwargs"
        content = ''
        for item in self.main:
            _html = ''
            for out in item.contents:
                if hasattr(out, 'fmt_html'): # columns and dynamic data
                    _html += out.fmt_html(allow_non_html_repr = allow_non_html_repr)
                elif 'text/html' in out.data:
                    _html += out.data['text/html']
                elif allow_non_html_repr and (as_slides == False):
                    if 'text/plain' in out.data:
                        _html += out.data['text/plain']
                    else:
                        _html += f'<p style="color:red;">Object at {hex(id(out))} has no text/HTML representation.</p>'  
            if _html != '':  # If a slide has no content or only widgets, it is not added to the report/slides.    
                sec_id = self._get_sec_id(item)
                goto_id = self._get_target_id(item)
                footer = f'<div class="Footer">{item.get_footer()}</div>'
                content += (f'<section {sec_id}><div class="SlideBox"><div {goto_id} class="SlideArea">{_html}</div>{footer}</div></section>' 
                            if as_slides else f'<section {sec_id}>{_html}</section>')
        
        theme_kws = {**self.main.settings.theme_kws,'breakpoint':'650px'}
    
        theme_css = styles.style_css(**theme_kws, _root=True)
        if self.main.widgets.checks.reflow.value:
            theme_css = theme_css + f"\n.SlideArea *, ContentWrapper * {{max-height:max-content !important;}}\n" # handle both slides and report
        
        _style_css = (slides_css if as_slides else doc_css).replace('__theme_css__', theme_css) # They have style tag in them.
        _code_css = (self.main.widgets.htmls.hilite.value if as_slides else code_css(color='var(--primary-fg)')).replace(f'.{self.main.uid}','') # Remove uid from code css here
        
        return doc_html(_code_css,_style_css, content).replace(
            '__page_size__',kwargs.get('page_size','letter'))
    
    def _get_sec_id(self, slide):
        sec_id = getattr(slide,'_sec_id','')
        return f'id="{sec_id}"' if sec_id else ''
    
    def _get_target_id(self, slide): # For goto buttons
        target = getattr(slide, '_target_id', '')
        return f'id="{target}"' if target else ''

    def _writefile(self, path, content, overwrite = False):
        if os.path.isfile(path) and not overwrite:
            print(f'File {path!r} already exists. Use overwrite=True to overwrite.')
            return
        
        with open(path,'w') as f:
            f.write(content) 
            
    
    def report(self, path='report.html', allow_non_html_repr = True, page_size = 'letter', overwrite = False):
        """Build a beutiful html report from the slides that you can print. Widgets are not supported for this purpose.
        
        - allow_non_html_repr: (True), then non-html representation of the slides like text/plain will be used in report.
        - Use 'overrides.css' file in same folder to override CSS styles.
        - Use 'report-only' class to generate additional content that only appear in report.
        - Use 'slides-only' class to generate content that only appear in slides.
        """
        if self.main.citations and (self.main._citation_mode != 'global'):
            raise ValueError(f'''Citations in {self.main._citation_mode!r} mode are not supported in report. 
            Use Slides(citation_mode = "global" and run all slides again before generating report.''')
        
        _path = os.path.splitext(path)[0] + '.html' if path != 'report.html' else path
        content = self._htmlize(allow_non_html_repr = allow_non_html_repr, as_slides = False, page_size = page_size)
        content = content.replace('.SlideArea','').replace('SlidesWrapper','ContentWrapper')
        self._writefile(_path, content, overwrite = overwrite)
    
    def slides(self, path = 'slides.html', slide_number = True, overwrite = False):
        """Build beutiful html slides that you can print. Widgets are not supported for this purpose.
        
        - Use 'overrides.css' file in same folder to override CSS styles.
        - Use 'slides-only' and 'report-only' classes to generate slides only or report only content.
        - If a slide has only widgets or does not have single object with HTML representation, it will be skipped.
        - You can take screenshot (using system's tool) of a widget and add it back to slide using `Slides.image` to keep PNG view of a widget. 
        - To keep an empty slide, use at least an empty html tag inside an HTML like `IPython.display.HTML('<div></div>')`.
        """
        _path = os.path.splitext(path)[0] + '.html' if path != 'slides.html' else path
        content = self._htmlize(allow_non_html_repr = False, as_slides = True, slide_number = slide_number)
        self._writefile(_path, content, overwrite = overwrite)
        
    def _export(self,change):
        "Export to HTML report and slides on button click."
        _dir = os.path.abspath(os.path.join(self.main.notebook_dir, 'ipyslides-export'))
        if not os.path.isdir(_dir):
            os.makedirs(_dir)
            
        def further_action(path):
            self.main.notify(f'File saved: {path!r}')
            with suppress(BaseException):
                os.startfile(path) # Does not work on some systems, so safely continue.
            self.main.widgets.ddowns.export.value = 'Select' # Reset so next click on same button will work
        
        if self.main.widgets.ddowns.export.value == 'Report': 
            path = os.path.join(_dir, 'report.html')
            self.report(path, allow_non_html_repr = False, overwrite = True)
            further_action(path)
            
        elif self.main.widgets.ddowns.export.value == 'Slides': 
            path = os.path.join(_dir, 'slides.html')
            self.slides(path, overwrite = True)  
            further_action(path) 