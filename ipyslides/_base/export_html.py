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
    let box = document.querySelector('.SlideBox');
    let slide = box.querySelector('.SlideArea');

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
            document.documentElement.style.setProperty('--paddingBottom',Number(__PADBTM__/scale) + "px");
        };
    };
    window.dispatchEvent(new window.Event('resize')); // First time programatically

    let slides = document.querySelector(".SlidesWrapper");

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
        
    def _htmlize(self):
        content = ''
        for item in self.main:
            objs = item.contents # get conce
            frames, snums = [], []
            
            if not item._fidxs:
                frames = [objs]
                snums = [item._get_snum(0)]
            else:
                for fi, frame in enumerate(item._fidxs):
                    head, start, end, part = [frame.get(k, -1) - item._offset for k in ('head','start','end','part')]
                    frame_objs = []
                    
                    if head >= 0:
                        frame_objs.extend(objs[:head + 1])
                    
                    if not "part" in frame: # full content in range
                        frame_objs.extend(objs[start:end + 1])
                    else: # partial content in range
                        snapshots_persist = frame.get("_snapshots_persist")
                        snapshots_persist_idx = None
                        if isinstance(snapshots_persist, dict) and isinstance(snapshots_persist.get("idx"), int):
                            snapshots_persist_idx = snapshots_persist["idx"] - item._offset
                        for i in range(start, end + 1):
                            if i < part:
                                # Check if this writer has persisted snapshots metadata.
                                if snapshots_persist and i == snapshots_persist_idx and hasattr(objs[i], "fmt_html"):
                                    frame_objs.append(objs[i].fmt_html(snapshots_persist))
                                # Fallback: any completed snapshots writer before current part keeps only last rows
                                elif hasattr(objs[i], "fmt_html") and getattr(objs[i], "_snapshots_cols", None):
                                    clr = dict(getattr(objs[i], "_snapshots_cols", {}) or {})
                                    frame_objs.append(objs[i].fmt_html({"_snapshots_last_rows": clr}))
                                else:
                                    frame_objs.append(objs[i])
                            elif i > part:
                                frame_objs.append(f"<div style='visibility:hidden;'>{_fmt_html(objs[i])}</div>")
                            else: # i == part, can be Writer
                                if "col" in frame and hasattr(objs[i], "fmt_html"): # Writer with columns
                                    frame_objs.append(objs[i].fmt_html(frame))
                                else: # normal Writer
                                    frame_objs.append(objs[i])
                
                    frames.append(frame_objs)
                    snums.append(item._get_snum(fi))
            
            for k, (snum, objs) in enumerate(zip(snums, frames)):
                _html = item._speaker_notes(returns=True) # speaker notes at top if any, returns string
                for out in objs:
                    _html += f'<div class="jp-OutputArea-child"><div class="jp-OutputArea-output" style="width: 100%;">{_fmt_html(out)}</div></div>' 
                    # Important to have each content in similar node structure as notebook content

                _html = f'<div class="jp-OutputArea">{_html}</div>'

                number = ""
                if item.index > 0 and self.main.settings.footer.numbering:
                    number = f'<span class="Number">{snum}</span>' 

                sec_uid = item._sec_id if k == 0 else f"{item._sec_id}-{k}"
                sec_id = f'id="{sec_uid}"'
                content += textwrap.dedent(f'''
                    <section {sec_id}>
                        {self._get_css(item, sec_uid)}
                        <div class="SlideBox">
                            {item._get_bg_image(f'#{sec_uid}', ikws = item._bg_ikws)}
                            <div class="{item._css_class} export-only">
                                {_html}
                            </div>
                            {number}
                            {self._get_progress(item,k)}
                        </div>
                    </section>''')
        
        navui_class = '' if self.main.settings.footer._print_padding > 16 else 'NavHidden' 
        content += f'<div class="Footer {navui_class}">{self.main.settings.footer._to_html()}</div>'
        content += self._get_logo() # Both of these fixed
            
        theme_kws = self.main.settings._theme_kws
        
        if self.main.widgets.theme.value == "Jupyter":  # jupyterlab themes colors to export
            if self.main.widgets.iw._colors:
                theme_kws["colors"] = self.main.widgets.iw._colors
                    
        dom_classes = tuple(self.main._box._dom_classes)
        css_classes = [c for c in dom_classes if c.startswith('Slides')]
        if self.main.uid in dom_classes:
            css_classes.append(self.main.uid)
            
        overall_css = ''.join(f'{s._overall_css}' for s in self.main[:1] if s._overall_css) # only one time
        return doc_html(
            code_css    = self.main.widgets.htmls.hilite.value.replace(f'.{self.main.uid}',''), # remove id from code here
            style_css   = self.main.html('style', styles.style_css(**theme_kws, _root=True)).value + overall_css,
            content     = content, 
            script      = _script, 
            click_btns  = self.main.settings._get_clickers(), 
            css_class   = ' '.join(css_classes),
            padding_bottom = self.main.settings.footer._print_padding,
            )
    
    def _get_progress(self, slide, fidx=0):
        if not self.main.settings.footer.progress:
            return ''
        pv = self.main._progress_value(slide, fidx)
        if pv is None: return ''

        gradient = f'linear-gradient(to right, var(--accent-color) 0%,  var(--accent-color) {pv}%, var(--bg2-color) {pv}%, var(--bg2-color) 100%)'
        return f'<div class="Progress" style="background: {gradient};"></div>'
    
    def _get_css(self, slide, sec_uid):
        "uclass.SlidesWrapper → sec_id , .SlidesWrapper → sec_id, FooterBox → Footer"
        return (f'{slide._css}').replace( # xtml or str, runtime for colors per slide
            f".{self.main.uid}.SlidesWrapper", f"#{sec_uid}").replace(
            f".{self.main.uid}", f"#{sec_uid}").replace(
            "ShowSlide", "SlideArea").replace( # ShowSlide is used for runtime display but here it is SlideArea in export
            ".FooterBox", ".Footer"
            )
            
    def _get_logo(self):
        return f'''<div class="SlideLogo" {_inline_style(self.main.widgets.htmls.logo)}"> 
            {self.main.widgets.htmls.logo.value} 
        </div>'''
                
    def _writefile(self, path, overwrite = False):
        if os.path.isfile(path) and not overwrite:
            return print(f'File {path!r} already exists. Use overwrite=True to overwrite.')
        
        with open(path,'w', encoding="utf-8") as f: # encode to utf-8 to handle emojis
            f.write(self._htmlize()) 
            
    
    def export_html(self, path = 'Slides.html', overwrite = False):
        """Build html slides that you can print.
        
        - Use 'overrides.css' file in same folder to override CSS styles.
        - If a slide has only widgets or does not have single object with HTML representation, it will be skipped.
        - You can take screenshot (using system's tool) of a widget, save it using Clips GUI in side panel and laod as image to keep PNG view of a widget. 
        
        ::: note-info
            - PDF printing of slide width is 210mm (8.25in). Height is determined by aspect ratio provided.
            - Use `Save as PDF` option instead of Print PDF in browser to make links work in output PDF. Alsp enable background graphics in print dialog.
        """
        if not self._export_ready(): return
        _path = os.path.splitext(path)[0] + '.html' if path != 'Slides.html' else path
        export_func = lambda: self._writefile(_path, overwrite)
        self.main.widgets.iw._try_exec_with_fallback(export_func)
        
    def _export(self,btn):
        "Export to HTML slides on button click."
        if not self._export_ready(): return
        path = 'Slides.html'
        if os.path.isfile(path) and not self.main.widgets.checks.confirm.value:
            return self.main.notify(f'File {path!r} already exists. Select overwrite checkbox if you want to replace it.')
        
        self.export_html(path, overwrite = self.main.widgets.checks.confirm.value)
        self.main.notify(f'File saved: {path!r}',10)
        with suppress(BaseException): # Does not work on some systems, so safely continue.
            os.startfile(path) 
    
    def _export_ready(self):
        if not self.main._next_pending: return True
        self.main.notify(self.main.error("Export Error", "Please build pending slides by naviagting/clicking on 'Pending Slides' button before you can export to HTML.").value)
        return False