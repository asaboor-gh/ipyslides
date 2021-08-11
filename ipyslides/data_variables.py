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
 }
 .SlidesWrapper .column:not(:first-child) {
	border-left: 2px solid var(--quote-bg);}
 
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
  
.SlidesWrapper p{
	color: var(--text-fg)!important;
}
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
    
.SlidesWrapper ol,ul {
	color:var(--text-fg)!important;
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
    
ls = LiveSlides(func=display_item,iterable=slides_iterable,accent_color='olive')
ls.set_footer()
ls.show()"""

settings_instructions = '''
#### Custom Theme
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