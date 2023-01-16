# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.
import time
from IPython import get_ipython

from ipyslides.writers import write
from ipyslides.formatters import libraries, __reprs__, plt2html
from ipyslides._base.intro import logo_svg

slides = get_ipython().user_ns['get_slides_instance']() # This will be availble in ipython namespace after any import of ipyslides

auto = slides.AutoSlides() # Does not work inside Jupyter notebook (should not as well)

slides.settings.set_footer('Author: Abdul Saboor عبدالصبور')
slides.settings.set_logo(logo_svg,width=60) # This is by defualt a logo of ipyslides
slides._citation_mode = 'global' # This could be changed by other functions
slides.set_citations({
        'pf': 'This is refernce to FigureWidget using `slides.cite` command',
        'This': 'I was cited for no reason',
    })

slides.run_cell("""
%%title -m
# Creating Slides
::: align-center
    alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`
    center`today```
    ::: text-box
        sup`1`My University is somewhere in the middle of nowhere
        sup`2`Their University is somewhere in the middle of nowhere
<h4 style=""color:green;"> 👈🏻 Read instructions in left panel</h4>
""")

#Demo for loading slides from a file or text block
s1, s2, *others = auto.from_markdown("""
section`Introduction` toc`### Contents`
---
proxy`something will be here in start`
# Introduction
To see how commands work, use `Slides.docs()` to see the documentation.
Here we will focus on using all that functionality to create slides.
```python run source
# get the slides instance under a python block in Markdown file, we will use it later to run a cell magic.
myslides = get_slides_instance() 
import ipyslides as isd
version = myslides.version
%xmd #### This is inline markdown parsed by magic {.note .warning}
```
Version: {{version}} as executed from below code in markdown. 
{{source}}
proxy`something will be here in end`
---
# IPySlides Online Running Sources 
::: note
    - [Edit on Kaggle](https://www.kaggle.com/massgh/ipyslides)
    - Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides/HEAD?labpath=demo.ipynb)
    - Watch a [Youtube Video](https://www.youtube.com/watch?v=ytfWIYbJteE)

[^1]: Add references like this per slide. Use slides.cite() or in markdown cite\`key\` to add citations generally.
  
""", trusted=True)


slides.shell.user_ns['write'] = write #Inject variable in IPython shell
# slide s2 has proxies to be filled in later
p1, p2 = s2.proxies   
with p1.capture():
    s2.get_source().display(collapsed = True)
    slides.goto_button(s2.number + 5, 'Skip 5 Slides',icon='plus')

with p2.capture():
    slides.write(f'alert`I was added at end by a given proxy, see the how it was done at the end of the slides`')


*others, last = auto.from_markdown(f"""
section`Variety of Content Types to Display` toc`### Contents`
---
## IPython Display Objects
#### Any object with following methods could be in`write` command:
{', '.join([f'`_repr_{rep}_`' for rep in __reprs__])}
Such as color[fg=navy,bg=skyblue]`IPython.display.[HTML,SVG,Markdown,Code]` etc. or third party such as `plotly.graph_objects.Figure`{{.warning}}.            
---
## Plots and Other **Data**{{style='color:var(--accent-color);'}} Types
#### These objects are implemented to be writable in `write` command:
{', '.join([f"`{lib['name']}.{lib['obj']}`" for lib in libraries])}
Many will be extentended in future. If an object is not implemented, use `display(obj)` to show inline or use library's specific
command to show in Notebook outside color[fg=teal,bg=whitesmoke]`write`.
---
## Interactive Widgets
### Any object in `ipywidgets`{slides.textbox('<a href="https://ipywidgets.readthedocs.io/en/latest/">Link to ipywidgtes right here using textbox command</a>')} 
or libraries based on ipywidgtes such as color[red]`bqplot`,color[green]`ipyvolume`,plotly's `FigureWidget` cite`pf`(reference at end)
can be included as well.
{{.warning}}
---
## Commands which do all Magic!
proxy`Add functions here`
""", trusted=True)


with slides.source.context(auto_display = False) as s:
    with last.proxies[0].capture():
        write([slides.classed(slides.doc(write,'Slides'),'block-green'), slides.classed(slides.doc(slides.parse,'Slides'),'block-red')])
        s.show_lines([0,1]).display()


auto.from_markdown('section`Plotting and DataFrame` toc``')
    
# Matplotlib
with auto.slide() as sl:
    write('## Plotting with Matplotlib')
    with slides.source.context(auto_display = False) as s:
        import numpy as np, matplotlib.pyplot as plt
        plt.rcParams['svg.fonttype'] = 'none' # Global setting, enforce same fonts as presentation
        x = np.linspace(0,2*np.pi)
        with plt.style.context('ggplot'):
            fig, ax = plt.subplots(figsize=(3.4,2.6))
            _ = ax.plot(x,np.cos(x))
        write([ax, s.focus_lines([1,3,4])])

    sl.set_css({'background':'linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)'})
        
# Plotly and Pandas DataFrame only show if you have installed
with slides.source.context(auto_display = False) as source:
    try:
        import pandas as pd 
        df = pd.read_csv('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv')
        df = df.describe() #Small for display
    except:
        df = '### Install `pandas` to view output'
    
with auto.slide():
    write(('## Writing Pandas DataFrame',df, source))
   
with slides.source.context(False) as s:
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Bar(y=[1,5,8,9]))
    except:
        fig = '### Install `plotly` to view output'
    
with auto.slide():
    write(('## Writing Plotly Figure',fig, s))
    
def race_plot():
    import numpy as np
    import matplotlib.pyplot as plt
    
    x = np.linspace(0,0.9,10)
    y = np.random.random((10,))
    _sort = np.argsort(y)
    fig,ax = plt.subplots(figsize=(3.4,2.6))
    ax.barh(x,y[_sort],height=0.07,color=plt.cm.get_cmap('plasma')(x[_sort]))
    
    for s in ['right','top','bottom']:
        ax.spines[s].set_visible(False)
    
    ax.set(title='Race Plot', ylim = [-0.05,0.95], xticks=[],yticks=[c for c in x],yticklabels=[rf'$X_{int(c*10)}$' for c in x[_sort]])
    return fig
            

# Interactive widgets.   
with auto.slide():
    with slides.source.context(auto_display = False) as src:
        import ipywidgets as ipw
        
        write('''
            ## Interactive Apps with Widgets section`Interactive Widgets`
            Use `ipywidgets`, `bqplot`,`ipyvolume`, `plotly Figurewidget` etc. to show live apps like this!
            ::: note-tip
                Export to Slides/Report to see what happens to this slide and next slide!
            ''')
        write([
            plot_html := ipw.HTML('Plot will be here'),
            button := ipw.Button(description='Click me to update race plot',layout=ipw.Layout(width='max-content')),
            ], src)
        
        def update_plot():
            fig = race_plot()
            plot_html.value = plt2html(fig).value #Convert to html
            
        def onclick(btn):
            plot_theme = 'dark_background' if 'Dark' in slides.settings.theme_dd.value else 'default'
            with plt.style.context(plot_theme):
                update_plot()
        
        button.on_click(onclick)
        update_plot() #Initialize plot
        
    slides.source.from_callable(race_plot).display()
    
with auto.slide() as rslide:
    write('''
        ## Dynamic Content without Widgets
        Use refresh button below to update plot! Compare with previous slide!
        ''')
    
    @slides.on_refresh
    def plot_it():
        fig = race_plot()
        write(fig, rslide.get_source()) #Update plot each time refresh button is clicked
        
    slides.source.from_callable(race_plot).display() 
        

auto.from_markdown('section`Simple Animations with Frames` toc`### Contents`')
    
# Animat plot in slides  
@auto.frames(*range(14,19))
def func(obj,idx):
    if idx == 0:
        slides.goto_button(slides.running.number + 5, 'Skip All Next Frames')
    
    with slides.source.context(auto_display = False) as s:
        fig, ax = plt.subplots()
        x = np.linspace(0,obj+1,50+10*(idx+1))
        ax.plot(x,np.sin(x));
        ax.set_title(f'$f(x)=\sin(x)$, 0 < x < {idx+1}')
        ax.set_axis_off()
        slides.notes.insert(f'## This is under @frames decorator!')
        
    slides.write([f'### This is Slide {slides.running.number}.{idx}\n and we are animating matplotlib',
                  s.show_lines([idx])
                  ],ax,widths=[40,60])
    if idx == 0: #Only show source code of first frame
        s.show_lines([5]).display()
    slides.write(slides.cite('This'))
    
auto.from_markdown('section`Controlling Content on Frames` toc`### Contents`')
    
# Frames structure
boxes = [f'<div style="background:var(--hover-bg);width:auto;height:2em;padding:8px;margin:8px;border-radius:4px;"><b class="align-center">{i}</b></div>' for i in range(1,5)]
@auto.frames(*boxes, repeat=False)
def f(obj,idx):
    slides.write('# Frames with \n#### `repeat = False`')
    slides.write(obj)
@auto.frames(*boxes, repeat=True,frame_height='100%')
def f(obj,idx):
    slides.running.set_animation(None) #Disable animation for showing bullets list
    slides.write('# Frames with \n#### `repeat = True` and Fancy Bullet List')
    slides.bullets(obj, marker='💘').display()
    
@auto.frames(*boxes, repeat=[(0,1),(2,3)])
def f(obj,idx):
    if idx == 1:
        slides.goto_button(slides.running.number - 5, 'Skip Frames',icon='minus')
        slides.format_css({'.goto-button .fa.fa-minus': slides.icon('arrow',color='crimson',rotation=180).css}).display()
    
    with slides.source.context(auto_display = False) as s:
        slides.write('# Frames with \n#### `repeat = [(0,1),(2,3)]`')
        slides.write(*obj)
        
    s.display()
    
with auto.slide() as s:
    slides.write('## Displaying image from url from somewhere in Kashmir color[crimson]`(کشمیر)` section`Miscellaneous Content`')
    try:
        slides.image(r'https://assets.gqindia.com/photos/616d2712c93aeaf2a32d61fe/master/pass/top-image%20(1).jpg').display()
    except:
        slides.write('Could not retrieve image from url. Check internt connection!\n{.error}')
    s.get_source().display()

# Youtube
from IPython.display import YouTubeVideo
with auto.slide() as ys: # We will use this in next %%magic
    write(f"### Watching Youtube Video?")
    
    write(YouTubeVideo('thgLGl14-tg',width='100%',height='266px'))
    @slides.on_load
    def push():
        t = time.localtime()
        slides.notify(f'You are watching Youtube at Time-{t.tm_hour:02}:{t.tm_min:02}')
        
    ys.get_source().display() 
    

with auto.slide() as s:
    write('## Data Tables')
    write(slides.block_r('Here is Table','<hr/>','''
        |h1|h2|h3|
        |---|---|---|
        |d1|d2|d3|
        |r1|r2|r3|
        '''))
    s.get_source().focus_lines([3,4,5,6]).display()
    

auto.from_markdown('''
## $\LaTeX$ in Slides
Use `$ $` or `$$ $$` to display latex in Markdown, or embed images of equations
$\LaTeX$ needs time to load, so keeping it in view until it loads would help.
{.note-warning}

$$\int_0^1\\frac{1}{1-x^2}dx$$
''', trusted=True)

with auto.slide(), slides.source.context():
    slides.write('## Built-in CSS styles')
    slides.css_styles.display()
    
auto.from_markdown('section`Custom Objects Serilaization` toc`### Contents`')

with auto.slide() as some_slide:
    slides.write('## Serialize Custom Objects to HTML\nThis is useful for displaying user defined/third party objects in slides')
    with slides.suppress_stdout(): # suppress stdout from register fuction below
        @slides.serializer.register(int)
        def colorize(obj):
            color = 'red' if obj % 2 == 0 else 'green'
            return f'<span style="color:{color};">{obj}</span>'
        slides.write(*range(10))
        
    some_slide.get_source().display()
    
with auto.slide():
    slides.write('## This is all code to generate slides section`Code to Generate Slides`')
    slides.source.from_callable(slides.demo).display()
    slides.source.from_file(__file__).display()
    
with auto.slide():
    slides.write('Slides keep their full code if they are not made by @frames decorator!\n{.note .info}')
    slides.get_source().display()

     
with auto.slide() as bib_slide:
    slides.write('citations`## Reference via Markdown\n----`') 
    bib_slide.get_source().display()
    

slides.navigate_to(0) # Go to title slide