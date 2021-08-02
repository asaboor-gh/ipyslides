title_page = '''__slides_mode = False #Set this to True and run all cells below
#Fixed Parameters Initialization
__slides_dict = {} #Don't edit
__dynamicslides_dict = {} #Don't edit

from IPython.display import display, Markdown
from ipyslides import load_magics

# Command below registers all the ipyslides magics that are used in this file
load_magics()

# Do NOT change variable name, just edit value
title_page_md=""" # Interactive Slides  
<em> Author: Abdul Saboor</em>

- Edit and test cells in `__slides_mode = False` mode
- Run cells in `__slides_mode = True` mode from top to bottom. 
- `%%slide integer` on cell top auto picks slide or you can use `ipysildes.insert(slide_number)`
- List or tuple assigned to \_\_dynamicslides_dict['d\{slide_number\}'] generates slides dynamically
- Use `ipysildes.insert_style()` for customing slides

```python
import ipyslides as isd 
isd.initilize() #This will create a title page and parameters in same cell
isd.insert(1) #This will create a slide in same cell where you run it 
isd.insert_style() #This will create a %%html cell with custom style
isd.insert_after(1) #This will create as many slides after the slide number 1 as length of list/tuple at cell end
isd.build() #This will build the presentation cell. After this go top and set __slides_mode = True and run all below.
```

> Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.

> For JupyterLab >=3, do `pip install sidecar`. 
"""
'''

style_html = '''%%html 
<style>
:root {
	--heading-fg: red;
	--text-fg: purple;
	--text-bg: inherit;
	 --quote-bg: inherit;
	--quote-fg: green;
}
    
.SlidesWrapper {
	margin: auto;
	padding: 16px 0px 0px 16px;
	background:var(--text-bg);
 }
    
.SlidesWrapper h1,h2,h3,h4,h5,h6{
	color:var(--heading-fg);
}
    
.SlidesWrapper p{
	 color: var(--text-fg)!important;
}
    
.SlidesWrapper blockquote, .SlidesWrapper blockquote>p {
	background: var(--quote-bg);
	color: var(--quote-fg) !important;
}
    
.SlidesWrapper ol,ul{
	color:inherit;
}
.SlidesWrapper table {
    min-width:auto;
    width:100%;
    word-break:break-all;
    overflow: auto;
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
                    title_page_md=title_page_md,accent_color='red')
ls.show()"""