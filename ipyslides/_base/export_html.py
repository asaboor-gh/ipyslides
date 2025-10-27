"""
Export Slides to static HTML slides. It is used by program itself, 
not by end user.
"""
import os
import textwrap
from contextlib import suppress

from .export_template import doc_html
from . import styles
from ..writer import _fmt_html
from ..formatters import _inline_style

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
            document.documentElement.style.setProperty('--paddingBottom',Number(26/scale) + "px");
        };
    };
    window.dispatchEvent(new window.Event('resize')); // First time programatically

    let slides = document.getElementsByClassName("SlidesWrapper")[0];

    slides.addEventListener("scroll", (event) => {
        slides.classList.add("Scrolling");
        setTimeout(() => { slides.classList.remove("Scrolling");}, 300); // ensure scrollend if link clicked
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
        
    def _htmlize(self, progressbar):
        content = ''
        for item in self.main:
            objs = item.contents # get conce
            frames, fidxs = [], item._fidxs or [len(objs)]
            for n, idx in enumerate(fidxs):
                if isinstance(idx, int):
                    frames.append(objs[:idx]) #upto
                elif isinstance(idx, tuple):
                    idx, jdx = idx[0] - 1, idx[1] # Must be Writer at idx
                    frames.append([*objs[:idx], objs[idx].fmt_html(_pad_from = jdx)]) 
                elif isinstance(idx, range):
                    first = objs[:getattr(item, '_frame_top',0)] # add top to all in case of no join
                    frames.append([*first, *objs[idx.start:idx.stop]]) # frames not incremental
            
            
            for k, objs in enumerate(frames):
                _html = '' 
                for out in objs:
                    _html += f'<div style="width: 100%; box-sizing:border-box;">{_fmt_html(out)}</div>' # Important to have each content in a div, so that it can be same as notebook content

                if hasattr(item,'_refs'):
                    _html += item._refs.value # in case of footnote citations

                _html = f'<div class="jp-OutputArea">{_html}</div>'
                sec_id = self._get_sec_id(item)

                number = ""
                if self.main.settings.footer.numbering:
                    number = f'<span class="Number">{item.index or ""}</span>' # 0 handled

                content += textwrap.dedent(f'''
                    <section {sec_id}>
                        {self._get_css(item)}
                        <div class="SlideBox">
                            {self._get_bg_image(item)}
                            <div class="{item._css_class} export-only">
                                {_html}
                            </div>
                            {number}
                            {self._get_progress(item,k) if progressbar else ""}
                        </div>
                    </section>''')
        
        navui_class = '' if 'Slides-ShowFooter' in self.main._box._dom_classes else 'NavHidden' 
        content += f'<div class="Footer {navui_class}">{self.main.settings._get_footer(item, False)}</div>'
        content += self._get_logo() # Both of these fixed
            
        theme_kws = self.main.settings._theme_kws
        
        if self.main.widgets.theme.value == "Jupyter":  # jupyterlab themes colors to export
            if self.main.widgets.iw._colors:
                theme_kws["colors"] = self.main.widgets.iw._colors

        return doc_html(
            code_css    = self.main.widgets.htmls.hilite.value.replace(f'.{self.main.uid}',''), # remove id from code here
            style_css   = styles.style_css(**theme_kws, _root=True), 
            content     = content, 
            script      = _script, 
            click_btns  = self.main.settings._get_clickers(), 
            height      = f'{210/theme_kws["layout"].aspect:.3f}mm', 
            css_class   = ' '.join(c for c in self.main._box._dom_classes if c.startswith('Slides')),
            bar_loc     = 'bottom' if progressbar is True else str(progressbar), # True → bottom
            )
    
    def _get_sec_id(self, slide):
        sec_id = getattr(slide,'_sec_id','')
        return f'id="{sec_id}"' if sec_id else ''
    
    def _get_progress(self, slide, fidx=0):
        unit = 100/(self.main._iterable[-1].index or 1) # avoid zero division error or None
        pv = round(unit * ((slide.index or 0) - (slide.nf - fidx - 1)/slide.nf), 4)
        gradient = f'linear-gradient(to right, var(--accent-color) 0%,  var(--accent-color) {pv}%, var(--bg2-color) {pv}%, var(--bg2-color) 100%)'
        return f'<div class="Progress" style="background: {gradient};"></div>'
    
    def _get_css(self, slide):
        "uclass.SlidesWrapper → sec_id , .SlidesWrapper → sec_id, NavWrapper → Footer"
        sec_id = f"#{getattr(slide,'_sec_id','')}"
        return slide.css.value.replace(
            f".{self.main.uid}.SlidesWrapper", sec_id).replace(
            f".{self.main.uid}", sec_id).replace(
            ".NavWrapper", ".Footer"
            )
    def _get_logo(self):
        return f'''<div class="SlideLogo" {_inline_style(self.main.widgets.htmls.logo)}"> 
            {self.main.widgets.htmls.logo.value} 
        </div>'''
    
    def _get_bg_image(self, slide):
        if not slide._bg_image:
            return ''
        sec_id = f"#{getattr(slide,'_sec_id','')}"
        return '<div class="BackLayer">' + slide._bg_image.replace(f".{self.main.uid}", sec_id) + '</div>'
                
    def _writefile(self, path, overwrite = False, progressbar = True):
        if os.path.isfile(path) and not overwrite:
            return print(f'File {path!r} already exists. Use overwrite=True to overwrite.')
        
        with open(path,'w', encoding="utf-8") as f: # encode to utf-8 to handle emojis
            f.write(self._htmlize(progressbar)) 
            
    
    def export_html(self, path = 'Slides.html', overwrite = False, progressbar = True):
        """Build html slides that you can print.
        
        - Use 'overrides.css' file in same folder to override CSS styles.
        - If a slide has only widgets or does not have single object with HTML representation, it will be skipped.
        - You can take screenshot (using system's tool) of a widget, save it using Clips GUI in side panel and laod as image to keep PNG view of a widget. 
        - If progressbar is set to True, 'bottom' or 'top', a progressbar while shown accordingly. True → 'bottom'.
        
        ::: note-info
            - PDF printing of slide width is 210mm (8.25in). Height is determined by aspect ratio provided.
            - Use `Save as PDF` option instead of Print PDF in browser to make links work in output PDF. Alsp enable background graphics in print dialog.
        """
        if progressbar not in [True, False, 'top','bottom']:
            raise ValueError(f"progressbar should be one of True, False, 'top' or 'bottom', got {progressbar}")
        _path = os.path.splitext(path)[0] + '.html' if path != 'Slides.html' else path
        export_func = lambda: self._writefile(_path, overwrite, progressbar)
        self.main.widgets.iw._try_exec_with_fallback(export_func)
        
    def _export(self,btn):
        "Export to HTML slides on button click."
        path = 'Slides.html'
        if os.path.isfile(path) and not self.main.widgets.checks.confirm.value:
            return self.main.notify(f'File {path!r} already exists. Select overwrite checkbox if you want to replace it.')
        
        self.export_html(path, overwrite = self.main.widgets.checks.confirm.value)
        self.main.notify(f'File saved: {path!r}',10)
        with suppress(BaseException): # Does not work on some systems, so safely continue.
            os.startfile(path) 