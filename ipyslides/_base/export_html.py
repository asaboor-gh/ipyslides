"""
Export Slides to static HTML slides. It is used by program itself, 
not by end user.
"""
import os
import textwrap
from contextlib import suppress
from .export_template import doc_html, slides_css
from . import styles
from ..writer import _fmt_html
from ..utils import get_child_dir

_script = '''<script>
    let box = document.getElementsByClassName('SlideBox')[0];
    let slide = box.getElementsByClassName('SlideArea')[0];

    window.onresize = function() {
        let rectBox = box.getBoundingClientRect();
        let rectSlide = slide.getBoundingClientRect();
        console.log(rectBox, rectSlide);
        let oldScale = document.documentElement.style.getPropertyValue('--contentScale');
        let old = oldScale ? oldScale : 1;
        let scaleH = old*rectBox.height/rectSlide.height;
        let scaleW = old*rectBox.width/rectSlide.width;
        let scale = scaleH > scaleW ? scaleW : scaleH;
        if (scale) { // Only add if not null or somethings
            document.documentElement.style.setProperty('--contentScale',scale);
        };
    };
    window.dispatchEvent(new window.Event('resize')); // First time programatically

    let slides = document.getElementsByClassName("SlidesWrapper")[0];

    slides.addEventListener("scroll", (event) => {
        slides.classList.add("Scrolling");
    })
    slides.addEventListener("scrollend", (event) => {
        slides.classList.remove("Scrolling");
    })
</script>'''


class _HhtmlExporter:
    # Should be used inside Slides class only.
    def __init__(self, _instance_BaseSlides):
        self.main = _instance_BaseSlides
        self.main.widgets.buttons.export.on_click(self._export) # Export button
        
    def _htmlize(self, **kwargs):
        "page_size, slide_number are in kwargs"
        navui_class = '' if self.main.widgets.checks.navgui.value else 'NavHidden' 
        content = ''
        for item in self.main:
            _html = '' 
            for out in item.contents:
                _html += f'<div style="width: 100%; box-sizing:border-box;">{_fmt_html(out)}</div>' # Important to have each content in a div, so that it can be same as notebook content
            
            if hasattr(item,'_refs'):
                _html += item._refs.value # in case of footnote citations
            
            _html = f'<div class="jp-OutputArea">{_html}</div>'
            sec_id = self._get_sec_id(item)
            goto_id = self._get_target_id(item)
            footer = f'<div class="Footer {navui_class}">{item.get_footer()}{self._get_progress(item)}</div>'
            content += textwrap.dedent(f'''
                <section {sec_id}>
                    {self._get_css(item)}
                    <div class="SlideBox">
                        {self._get_logo()}
                        <div {goto_id} class="SlideArea">
                            {_html}
                        </div>
                        {footer}
                    </div>
                </section>''')
            
        theme_kws = self.main.settings.theme_kws
        theme_css = styles.style_css(**theme_kws, _root=True)
        _style_css = slides_css.replace('__theme_css__', theme_css) # They have style tag in them.
        _code_css = self.main.widgets.htmls.hilite.value.replace(f'.{self.main.uid}','') # remove id from code here
        
        return doc_html(_code_css,_style_css, content, _script).replace(
            '__FOOTER__', self._get_clickables()).replace(
            '__HEIGHT__', f'{int(254/theme_kws["aspect"])}mm') # Slides height is determined by aspect ratio.
    
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
    
    def _get_css(self, slide):
        "uclass.SlidesWrapper -> sec_id , .SlidesWrapper -> sec_id, NavWrapper -> Footer"
        sec_id = f"#{getattr(slide,'_sec_id','')}"
        return slide.css.value.replace(
            f".{self.main.uid}.SlidesWrapper", sec_id).replace(
            f".{self.main.uid}", sec_id).replace(
            ".NavWrapper", ".Footer"
            )
    def _get_logo(self):
        return f'''<div class="SlideLogo" style="position:absolute;right:4px;top:4px;"> 
            {self.main.widgets.htmls.logo.value} 
        </div>'''

    def _get_clickables(self):
        if len(self.main) < 2:
            return '' # no clicks for only title
        
        items = [getattr(item,'_sec_id','') for item in self.main if '.' not in item.label] # only main slides
        names = ['⇤', *['●' for _ in items[1:-1]],'⇥']
        
        if len(items) > 5: # we need only 0,25,50,75,100 % clickers
            imax = len(items) - 1
            items = [items[i] for i in [0, imax//4,imax//2, 3*imax//4, imax]]
            names = '⇤◔◑◕⇥'

        return "".join(f'<a href="#{key}" class="clicker">{label}</a>' for (label,key) in zip(names,items))
                
    def _writefile(self, path, content, overwrite = False):
        if os.path.isfile(path) and not overwrite:
            print(f'File {path!r} already exists. Use overwrite=True to overwrite.')
            return
        
        with open(path,'w', encoding="utf-8") as f: # encode to utf-8 to handle emojis
            f.write(content) 
            
    
    def export_html(self, path = 'slides.html', slide_number = True, overwrite = False):
        """Build beutiful html slides that you can print. Widgets are supported via `Slides.alt(widget,func)`.
        
        - Use 'overrides.css' file in same folder to override CSS styles.
        - If a slide has only widgets or does not have single object with HTML representation, it will be skipped.
        - You can take screenshot (using system's tool) of a widget and add it back to slide using `Slides.image` to keep PNG view of a widget. 
        - To keep an empty slide, use at least an empty html tag inside an HTML like `IPython.display.HTML('<div></div>')`.
        
        ::: note-info
            - PDF printing of slide width is 254mm (10in). Height is determined by aspect ratio provided.
            - Use `Save as PDF` option instead of Print PDF in browser to make links work in output PDF.
        """
        _path = os.path.splitext(path)[0] + '.html' if path != 'slides.html' else path
        content = self._htmlize(slide_number = slide_number)
        self._writefile(_path, content, overwrite = overwrite)
        
    def _export(self,btn):
        "Export to HTML slides on button click."
        _dir = get_child_dir('ipyslides-export', create = True)
        path = os.path.join(_dir, 'slides.html')
        self.export_html(path, overwrite = True)  
        self.main.notify(f'File saved: {path!r}',10)
        with suppress(BaseException):
            os.startfile(path) # Does not work on some systems, so safely continue.