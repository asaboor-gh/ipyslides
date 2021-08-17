title_page = '''from IPython.display import display, Markdown
from ipyslides import load_magics, convert2slides, write_title
from ipyslides.utils import write,plt2html,print_context

# Command below registers all the ipyslides magics that are used in this file
load_magics()
# Set this to True for Slides output
convert2slides(False) #Set this to True for Slides output


write_title("<div style='width:10px;height:100%;background:olive;'></div>",
"""# Interactive Slides  
<em style='color:red;'> Author: Abdul Saboor</em>

- Edit and test cells in `convert2slides(False)` mode.
- Run cells in `convert2slides(True)` mode from top to bottom. 
- `%%slide integer` on cell top auto picks slide or you can use `ipysildes.insert(slide_number)`
- ipyslides.insert_after(slide_number,*objs) generates slides dynamically handled by function `display_item`.
- Use `ls.align8center(False)` assuming `ls=LiveLSides()` to align slide's content top-left.

```python
import ipyslides as isd 
isd.initilize() #This will create a title page and parameters in same cell
isd.write_title() #create a rich content multicols title page.
isd.insert(1) #This will create a slide in same cell where you run it 
isd.insert_after(1,*objs) #This will create as many slides after the slide number 1 as length(objs)
isd.build() #This will build the presentation cell. After this go top and set `convert2slides(True)` and run all below.
```

> Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
> For JupyterLab >=3, do `pip install sidecar`. 
""",width_percents = [5,95])
'''
# CSS for ipyslides
light_root = ''':root {{
	--heading-fg: navy;
	--text-fg: black;
	--text-bg: #F3F3F3;
	--quote-bg: white;
	--quote-fg: purple;
	--tr-odd-bg: white;
	--tr-hover-bg: lightblue;
	--accent-color: navy;
	--text-size: {text_size};
}}
'''
dark_root = ''':root {{
	--heading-fg: snow;
	--text-fg: white;
	--text-bg: #21252B;
	--quote-bg: #22303C;
	--quote-fg: powderblue;
	--tr-odd-bg: black;
	--tr-hover-bg: gray;
	--accent-color: snow;
	--text-size: {text_size};
}}
'''
inherit_root = ''':root {{
	--heading-fg: inherit;
	--text-fg: inherit;
	--text-bg: inherit;
	--quote-bg: inherit;
	--quote-fg: inherit;
	--tr-odd-bg: inherit;
	--tr-hover-bg:skyblue;
 	--accent-color:skyblue;
	--text-size: {text_size};
}}
'''

def style_html(style_root_formatted = inherit_root.format(text_size='16px')):
	return '<style>\n' + style_root_formatted + '''    
.SlidesWrapper {
	margin: auto;
	padding: 0px;
	background:var(--text-bg);
	font-size: var(--text-size);
	max-width:100vw; /* This is very important */
 }
.SlidesWrapper .panel { background: var(--quote-bg);border:4px solid var(--text-bg);}
.SlidesWrapper .panel .panel-text { background: var(--text-bg);}
.SlidesWrapper .columns {max-width:95%;display:inline-flex;flex-direction:row;column-gap:2em;}

@media screen and (max-width: 702px) {
  	.NavWrapper .nav-box {
    	display:block;
    	height: max-content !important;
    	padding-bottom:32px;
	}
	.NavWrapper .nav-box>div:not(:first-child) button {
        width:50% !important;
    }
    .NavWrapper .progress {height:4px !important;margin-top:-2px !important;}
    .SlidesWrapper .columns {max-width:98%;display:flex;flex-direction:column;}
    .SlidesWrapper .columns>div[style] {width:100%!important;} /* important to override inline CSS */
}
 
.jp-RenderedHTMLCommon {font-size: var(--text-size);} /* For Voila */

.SlidesWrapper h1,h2,h3,h4,h5,h6{
	color:var(--heading-fg);
 	text-align:center;
}
.SlidesWrapper .widget-inline-hbox .widget-readout  {box-shadow: none;color:var(--text-fg) !important;}
.SlidesWrapper .textfonts h1 {margin-block: unset;font-size: 3em;  line-height: 1.5em;}
.SlidesWrapper .textfonts h2 {margin-block: unset;font-size: 2.5em;line-height: 1.5em;}
.SlidesWrapper .textfonts h3 {margin-block: unset;font-size: 2em;  line-height: 1.5em;}
.SlidesWrapper .textfonts h4 {margin-block: unset;font-size: 1.5em;line-height: 1.5em;}
.SlidesWrapper .textfonts h5 {margin-block: unset;font-size: 1em;  line-height: 1.5em;}

.SlidesWrapper .widget-inline-hbox .widget-label,
.SlidesWrapper .widget-inline-hbox .widget-readout  {
    color:var(--text-fg);
}
  
.SlidesWrapper :is(.textfonts,.panel,.NavWrapper) :is(p,ul,ol,li),
.SlidesWrapper>:not(div){  /* Do not change jupyterlab nav items */
	color: var(--text-fg);
}
#jp-top-panel, #jp-bottom-panel, #jp-menu-panel {color: inherit;}

.SlidesWrapper pre, .SlidesWrapper code {
    color: var(--text-fg)!important;
    padding: 0px 4px !important;
    overflow-x: auto !important;
    background: var(--quote-bg) !important;
}

.SlidesWrapper blockquote, .SlidesWrapper blockquote>p {
	background: var(--quote-bg);
	color: var(--quote-fg) !important;
}
    
.SlidesWrapper table {
 	border-collapse: collapse !important;
    min-width:auto;
    width:100%;
    font-size: small;
    word-break:break-all;
    overflow: auto;
	color: var(--text-fg)!important;
	background: var(--text-bg)!important;
}
.SlidesWrapper tbody>tr:nth-child(odd) {background: var(--tr-odd-bg)!important;}
.SlidesWrapper tbody>tr:nth-child(even) {background: var(--text-bg)!important;}
.SlidesWrapper tbody>tr:hover {background: var(--tr-hover-bg)!important;}

.NavWrapper {max-width:100% !important;}
.NavWrapper .progress {background: var(--quote-bg)!important;}
.NavWrapper .progress .progress-bar {background: var(--accent-color)!important;}
.SlidesWrapper button {
    color: var(--accent-color)!important;
    border-radius:0px;
    background: transparent !important;}

.SlidesWrapper .widget-dropdown > select, 
.SlidesWrapper .widget-dropdown > select > option {
	color: var(--text-fg)!important;
	background: var(--text-bg)!important;
}
.SlidesWrapper .widget-play .jupyter-button {
    background: var(--quote-bg)!important;
    color: var(--accent-color)!important;
    boder-radius: 0px;
} 
.sidecar-only {font-size: 24px !important;background: transparent;border-shadow: none;}
.sidecar-only:hover, .sidecar-only:focus {
    animation-name: example; animation-duration: 2s;
    animation-timing-function: ease-in-out;}
</style>'''

build_cell = """# Only this cell should show output. For JupyterLab >=3, pip install sidecar
# ------ Slides End Here -------- 

from ipyslides.core import collect_slides, LiveSlides

slides_iterable = collect_slides() #Get all slides content in order

# Edit this function to act on all dynmaically generated slides
def display_item(item):
    if isinstance(item,(str,dict,list,tuple,int,float)):
        write(f'### Given {type(item)}: {item}')
    else:
        display(item) # You will get idea what is it and modify this function to handle it.
    
ls = LiveSlides(func=display_item,iterable=slides_iterable)
ls.align8center(True) # Set False to align top-left corner
ls.set_footer()
ls.show()"""

settings_instructions = '''#### Custom Theme
For custom themes, change colors in instance attribute of `ipyslides.LivSlides.theme_colors`
```python
# if you did set ls = LivSlides()
theme_root = ls.get_theme_root()
# edit values of colors you want, don't edit keys.
ls.set_theme_root(theme_root)
ls.set_font_scale(font_scale:float) #changes layout fonts scaling. 
```          

--------
For matching plots style with theme, run following code in a cell above slides.
#### Matplotlib
```python
import matplotlib.pyplot as plt
plt.style.use('ggplot')
#plt.style.available() #gives styles list
```
#### Plotly
```python
import plotly.io as pio
pio.templates.default = "plotly_white"
#pio.templates #gives list of styles
```
> Tip: Wrap your plotly figures in `plotly.graph_objects.FigureWidget` for quick rendering.
'''

animation_css = '''<style>
.textfonts :is(h1,h2,h3,h4,h5,h6,p,ul,li,ol,blockquote,q,table,pre) {
    animation-name: zoom; animation-duration: 600ms;
    animation-timing-function: linear;
}
@keyframes zoom {
     0% { transform: scale(0.05); }
    25% { transform: scale(0.35); }
    50% { transform: scale(0.55); }
	75% { transform: scale(0.85); }
   100% { transform: scale(1); }
}
</style>'''