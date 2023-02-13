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
        
    def _htmlize(self, as_slides = False, **kwargs):
        "page_size, slide_number are in kwargs"
        content = ''
        for item in self.main:
            _html = ''
            for out in item.contents:
                if hasattr(out, 'fmt_html'): # columns and dynamic data
                    _html += out.fmt_html()
                elif 'text/html' in out.data:
                    _html += out.data['text/html']
                
            if _html != '':  # If a slide has no content or only widgets, it is not added to the report/slides.    
                sec_id = self._get_sec_id(item)
                goto_id = self._get_target_id(item)
                footer = f'<div class="Footer">{item.get_footer()}{self._get_progress(item)}</div>'
                content += (f'<section {sec_id}><div class="SlideBox"><div {goto_id} class="SlideArea">{_html}</div>{footer}</div></section>' 
                            if as_slides else f'<section {sec_id}>{_html}</section>')
        
        theme_kws = {**self.main.settings.theme_kws,'breakpoint':'650px'}
    
        theme_css = styles.style_css(**theme_kws, _root=True)
        if self.main.widgets.checks.reflow.value:
            theme_css = theme_css + f"\n.SlideArea *, ContentWrapper * {{max-height:max-content !important;}}\n" # handle both slides and report
        
        _style_css = (slides_css if as_slides else doc_css).replace('__theme_css__', theme_css) # They have style tag in them.
        _code_css = (self.main.widgets.htmls.hilite.value if as_slides else code_css(color='var(--primary-fg)')).replace(f'.{self.main.uid}','') # Remove uid from code css here
        
        return doc_html(_code_css,_style_css, content).replace(
            '__page_size__',kwargs.get('page_size','letter')).replace( # Report
            '__HEIGHT__', f'{int(297*self.main.settings.aspect_dd.value)}mm') # Slides height is determined by aspect ratio.
    
    def _get_sec_id(self, slide):
        sec_id = getattr(slide,'_sec_id','')
        return f'id="{sec_id}"' if sec_id else ''
    
    def _get_target_id(self, slide): # For goto buttons
        target = getattr(slide, '_target_id', '')
        return f'id="{target}"' if target else ''
    
    def _get_progress(self, slide):
        prog = int(float(slide.label)/(float(self.main[-1].label) or 1)*100) # Avoid ZeroDivisionError if only one slide
        gradient = f'linear-gradient(to right, var(--accent-color) 0%,  var(--accent-color) {prog}%, var(--secondary-bg) {prog}%, var(--secondary-bg) 100%)'
        return f'<div class="Progress" style="background: {gradient};"></div>'
                

    def _writefile(self, path, content, overwrite = False):
        if os.path.isfile(path) and not overwrite:
            print(f'File {path!r} already exists. Use overwrite=True to overwrite.')
            return
        
        with open(path,'w') as f:
            f.write(content) 
            
    
    def report(self, path='report.html', page_size = 'letter', overwrite = False):
        """Build a beutiful html report from the slides that you can print. Widgets are supported via `Slides.alt(widget,func)`.
        
        - Use 'overrides.css' file in same folder to override CSS styles.
        - Use 'report-only' class to generate additional content that only appear in report.
        - Use 'slides-only' class to generate content that only appear in slides.
        - Use `Save as PDF` option in browser to make links work in output PDF.
        """
        if self.main.citations and (self.main._citation_mode != 'global'):
            raise ValueError(f'''Citations in {self.main._citation_mode!r} mode are not supported in report. 
            Use Slides(citation_mode = "global" and run all slides again before generating report.''')
        
        _path = os.path.splitext(path)[0] + '.html' if path != 'report.html' else path
        content = self._htmlize(as_slides = False, page_size = page_size)
        content = content.replace('.SlideArea','').replace('SlidesWrapper','ContentWrapper')
        self._writefile(_path, content, overwrite = overwrite)
    
    def slides(self, path = 'slides.html', slide_number = True, overwrite = False):
        """Build beutiful html slides that you can print. Widgets are supported via `Slides.alt(widget,func)`.
        
        - Use 'overrides.css' file in same folder to override CSS styles.
        - Use 'slides-only' and 'report-only' classes to generate slides only or report only content.
        - If a slide has only widgets or does not have single object with HTML representation, it will be skipped.
        - You can take screenshot (using system's tool) of a widget and add it back to slide using `Slides.image` to keep PNG view of a widget. 
        - To keep an empty slide, use at least an empty html tag inside an HTML like `IPython.display.HTML('<div></div>')`.
        
        ::: note-info
            - PDF printing of slide is done on paper of width 297mm (as A4). Height is determined by aspect ratio dropdown in sidebar panel.
            - Use `Save as PDF` option in browser to make links work in output PDF.
        """
        _path = os.path.splitext(path)[0] + '.html' if path != 'slides.html' else path
        content = self._htmlize(as_slides = True, slide_number = slide_number)
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
            self.report(path, overwrite = True)
            further_action(path)
            
        elif self.main.widgets.ddowns.export.value == 'Slides': 
            path = os.path.join(_dir, 'slides.html')
            self.slides(path, overwrite = True)  
            further_action(path) 