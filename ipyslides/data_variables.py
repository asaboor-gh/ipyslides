title_page = '''__slides_mode = False #Set this to True and run all cells below
#Fixed Parameters Initialization
__slides_dict = {} #Don't edit
__dynamicslides_dict = {} #Don't edit

from IPython.display import display, Markdown
from ipyslides import load_magics

# Command below registers all the ipyslides magics that are used in this file
load_magics()

# Do NOT change variable name, just edit value or create title slide using %%title in a cell
# %%title cell should only be used once and should contain display statements instead of returning anything
__slides_title_page=""" # Interactive Slides  
<em> Author: Abdul Saboor</em>

- Edit and test cells in `__slides_mode = False` mode
- Run cells in `__slides_mode = True` mode from top to bottom. 
- `%%slide integer` on cell top auto picks slide or you can use `ipysildes.insert(slide_number)`
- List or tuple assigned to \_\_dynamicslides_dict['d\{slide_number\}'] generates slides dynamically

```python
import ipyslides as isd 
isd.initilize() #This will create a title page and parameters in same cell
isd.insert_title() #This will capture the title page with magice %%title
isd.insert(1) #This will create a slide in same cell where you run it 
isd.insert_after(1) #This will create as many slides after the slide number 1 as length of list/tuple at cell end
isd.build() #This will build the presentation cell. After this go top and set __slides_mode = True and run all below.
```

> Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.

> For JupyterLab >=3, do `pip install sidecar`. 
"""
'''

style_root = ''':root {{
	--heading-fg: {heading_fg};
	--text-fg: {text_fg};
	--text-bg: {text_bg};
	--quote-bg: {quote_bg};
	--quote-fg: {quote_fg};
	--text-size: {text_size};
}}
'''
style_colors = {
    'heading_fg': 'inherit',
    'text_fg' : 'inherit',
    'text_bg' : 'inherit',
    'quote_bg': 'inherit',
    'quote_fg': 'inherit'
}
def style_html(style_root_formatted = style_root.format(**style_colors,text_size='16px')):
	return '<style>\n' + style_root_formatted + '''    
.SlidesWrapper {
	margin: auto;
	padding: 0px;
	background:var(--text-bg);
	font-size: var(--text-size);
 }

.SlidesWrapper h1,h2,h3,h4,h5,h6{
	color:var(--heading-fg);
 	text-align:center;
}
.SlidesWrapper h1 {font-size: 4em;}
.SlidesWrapper h2 {font-size: 3.5em;}
.SlidesWrapper h3 {font-size: 3em;}
.SlidesWrapper h4 {font-size: 2em;}
  
.SlidesWrapper p{
	color: var(--text-fg)!important;
	font-size: 1.2em;
}
.SlidesWrapper blockquote, .SlidesWrapper blockquote>p {
	background: var(--quote-bg);
	color: var(--quote-fg) !important;
 	font-size: 1em;
}
    
.SlidesWrapper ol,ul{
	color:var(--text-fg)!important;
 	font-size: 1.2em;
}
.SlidesWrapper table {
    min-width:auto;
    width:100%;
    word-break:break-all;
    overflow: auto;
	font-size: 1em;
	color: var(--text-fg)!important;
}
</style>'''

build_cell = """# Only this cell should show output. For JupyterLab >=3, pip install sidecar
# ------ Slides End Here -------- 

from ipyslides.core import collect_slides, LiveSlides

slides_iterable = collect_slides() #Get all slides content in order

# Edit this function to act on all dynmaically generated slides
def display_item(item):
    if isinstance(item,(str,dict,list,tuple,int,float)):
        display(Markdown(f'### Given {type(item)}: {item}'))
    else:
        item.show() # displays output of %%slide
    
ls = LiveSlides(func=display_item,iterable=slides_iterable, 
                    title_page_md=title_page_md,color_fg='#3D4450',color_bg='whitesmoke')
ls.set_footer()
ls.show()"""

settings_instructions = '''
#### Custom Theme
For custom themes, change colors in instance attribute of `ipyslides.LivSlides.theme_colors`
```python
# if you did set ls = LivSlides()
ls.theme_colors = {'heading_fg': 'inherit', 'text_fg': 'inherit', 'text_bg': 'inherit', 'quote_bg': 'inherit', 'quote_fg': 'inherit'}
# Change color values and assign back to ls.theme_colors and change Theme selector above to trigger changes. 
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