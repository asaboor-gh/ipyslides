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
            document.documentElement.style.setProperty('--paddingBottom',Number(23/scale) + "px");
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
        
    def _htmlize(self):
        navui_class = '' if 'ShowFooter' in self.main._box._dom_classes else 'NavHidden' 
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
                goto_id = self._get_target_id(item,k)
                footer = f'<div class="Footer {navui_class}">{item.get_footer()}{self._get_progress(item,k)}</div>'

                number = ""
                if self.main.settings._footer_kws["numbering"]:
                    number = f'<span class="Number">{item.index or ""}</span>' # 0 handled

                content += textwrap.dedent(f'''
                    <section {sec_id}>
                        {self._get_css(item)}
                        <div class="SlideBox">
                            {self._get_bg_image(item)}
                            {self._get_logo()}
                            <div {goto_id} class="{item.css_class}">
                                {_html}
                            </div>
                            {number}
                            {footer}
                        </div>
                    </section>''')
            
        theme_kws = self.main.settings.theme_kws
        
        if self.main.widgets.theme.value == "Inherit":  # jupyterlab Inherit themes colors to export
            if self.main.widgets.iw._colors:
                theme_kws["colors"] = self.main.widgets.iw._colors
                self.main.widgets.iw._colors = {} # reset as user can change jupyter theme again          
            else:
                self.main.widgets.iw.msg_tojs = "SetColors" # only send from here as this only matters in export
                return None

        theme_css = styles.style_css(**theme_kws, _root=True)
        _style_css = slides_css.replace('__theme_css__', theme_css) # They have style tag in them.
        _code_css = self.main.widgets.htmls.hilite.value.replace(f'.{self.main.uid}','') # remove id from code here
        extra_class = 'ShowFooter' if 'ShowFooter' in self.main._box._dom_classes else ''
        return doc_html(_code_css,_style_css, content, _script, extra_class).replace(
            '__FOOTER__', self._get_clickables()).replace(
            '__HEIGHT__', f'{int(254/theme_kws["aspect"])}mm') # Slides height is determined by aspect ratio.
    
    def _get_sec_id(self, slide):
        sec_id = getattr(slide,'_sec_id','')
        return f'id="{sec_id}"' if sec_id else ''
    
    def _get_target_id(self, slide,fidx=0): # For goto buttons
        if fidx != 0: return '' # only first frame
        target = getattr(slide, '_target_id', '')
        return f'id="{target}"' if target else ''
    
    def _get_progress(self, slide, fidx=0):
        unit = 100/(self.main._iterable[-1].index or 1) # avoid zero division error or None
        pv = round(unit * ((slide.index or 0) - (slide.nf - fidx - 1)/slide.nf), 4)
        gradient = f'linear-gradient(to right, var(--accent-color) 0%,  var(--accent-color) {pv}%, var(--secondary-bg) {pv}%, var(--secondary-bg) 100%)'
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
    
    def _get_bg_image(self, slide):
        if not slide._bg_image:
            return ''
        sec_id = f"#{getattr(slide,'_sec_id','')}"
        return '<div class="BackLayer">' + slide._bg_image.replace(f".{self.main.uid}", sec_id) + '</div>'

    def _get_clickables(self):
        if len(self.main) < 2:
            return '' # no clicks for only title
        
        items = [getattr(item,'_sec_id','') for item in self.main]
        names = ['', *['●' for _ in items[1:-1]],'']
        
        if len(items) > 5: # we need only 0,25,50,75,100 % clickers
            imax = len(items) - 1
            items = [items[i] for i in [0, imax//4,imax//2, 3*imax//4, imax]]
            names = ' ◔◑◕ ' # spaces around for icons
        
        klasses = [f"clicker fa {c}" for c in ['fa-arrowbl',*['' for _ in names[1:-1]],'fa-arrowbr']]

        return "".join(f'<a href="#{key}" class="{klass}">{label}</a>' for (klass, label,key) in zip(klasses, names,items))
                
    def _writefile(self, path, content, overwrite = False):
        if os.path.isfile(path) and not overwrite:
            return print(f'File {path!r} already exists. Use overwrite=True to overwrite.')
        
        with open(path,'w', encoding="utf-8") as f: # encode to utf-8 to handle emojis
            f.write(content) 
            
    
    def export_html(self, path = 'slides.html', overwrite = False):
        """Build beautiful html slides that you can print.
        
        - Use 'overrides.css' file in same folder to override CSS styles.
        - If a slide has only widgets or does not have single object with HTML representation, it will be skipped.
        - You can take screenshot (using system's tool) of a widget and add it back to slide using `Slides.image_clip` to keep PNG view of a widget. 
        - You can paste a screenshot using `alt_clip` functionality as well.
        - To keep an empty slide, use at least an empty html tag inside an HTML like `IPython.display.HTML('<div></div>')`.
        
        ::: note-info
            - PDF printing of slide width is 254mm (10in). Height is determined by aspect ratio provided.
            - Use `Save as PDF` option instead of Print PDF in browser to make links work in output PDF.
        """
        return self._export_html(path=path, overwrite=overwrite, called_by_button=False)
    
    def _export_html(self, path = 'slides.html', overwrite = False, called_by_button=False):
        _path = os.path.splitext(path)[0] + '.html' if path != 'slides.html' else path
        content = self._htmlize()
        if content is None:
            if called_by_button:
                return 'RECLICK'
            else:
                return print("Inherit theme selected: Run export_html function again to export with jupyter theme colors!")

        self._writefile(_path, content, overwrite = overwrite)
        
    def _export(self,btn):
        "Export to HTML slides on button click."
        _dir = get_child_dir('ipyslides-export', create = True)
        path = os.path.join(_dir, 'slides.html')

        if os.path.isfile(path) and not self.main.widgets.checks.confirm.value:
            return self.main.notify(f'File {path!r} already exists. Select overwrite checkbox if you want to replace it.')
        
        out = self._export_html(path, overwrite = self.main.widgets.checks.confirm.value, called_by_button=True)
        if out == 'RECLICK':
            self.main.notify(f"{self.main.alert('Inherit theme selected:')} Click 'Export to HTML File' button again to export with jupyter theme colors!")
        else:
            self.main.notify(f'File saved: {path!r}',10)
            with suppress(BaseException):
                os.startfile(path) # Does not work on some systems, so safely continue.