# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.
import textwrap, time
from io import StringIO
from IPython import get_ipython
from .utils import textbox
from .writers import write, iwrite
from .formatter import libraries, __reprs__
from ._base.intro import how_to_slide

slides = get_ipython().user_ns['_s_l_i_d_e_s_'] # get slides from notebook instead of creating new one
slides.settings.set_footer('Author: Abdul Saboor عبدالصبور')
slides.settings.set_logo('''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="50" fill="blue"/>
        <text x="45%" y="45%" fill="white" font-size="4em" dominant-baseline="central" text-anchor="middle">↑</text>
        <text x="55%" y="60%" fill="white" font-size="4em" dominant-baseline="central" text-anchor="middle">↓</text></svg>''',width=50)

#Demo for loading slides from a file or file-like object 
fp = StringIO('\n'.join(how_to_slide) + '''\n---
# Slide 1 {.Success}
```python run source
import ipyslides as isd
version = isd.__version__
%xmd #### This is inline markdown parsed by magic {.Note .Warning}
```
Version: {{version}} as executed from below code in markdown. 
{{source}}
---
# Slide 2 {.Success}
Created using `%%slide 2 -m` with markdown only
```multicol
# Column A
||### Sub column A {.Success}||### Sub column B ||
+++
# Column B
```
That version from last slide is still in memory. See it is there {{version}}
''')
slides.from_markdown(fp, trusted=True) # This will create first slide along with title page.

with slides.slide(1): #slide 1 will be modified with old and new content
    with slides.source.context(style='monokai', color='white', className='Mono') as s:
        slides.parse_xmd(slides.md_content[1])
        #display(*get_ipython().user_ns['outputs'])
        write('## I am created using `with slides.slide(1)` context( manager!')
        write(f'I am {slides.alert("Alerted")} and I am *{slides.colored("colored and italic text","magenta","whitesmoke")}*')
    s.focus_lines([0]).display()  #focus on line 0 
    slides.notes.insert('### Note for slide 1')
    
slides.shell.user_ns['write'] = write #Inject variable in IPython shell

#slide 2    
slides.shell.run_cell_magic('slide','2 -m',slides.md_content[2])
#slide 3
online_sources = '''# IPySlides Online Running Sources 
Launch as voila slides (may not work as expected [^1])[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=voila%2Frender%2Fnotebooks%2Fipyslides.ipynb)
{.Note .Error}

[Edit on Kaggle](https://www.kaggle.com/massgh/ipyslides)\n{.Note .Warning}

Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=lab%2Ftree%2Fnotebooks%2Fipyslides.ipynb)
{.Note .Success}

[^1]: Add references like this per slide. Use slides.cite() to add citations generally.
'''
@slides.frames(3,'## I am created using `@slides.frames`',online_sources)
def func(obj):
    with slides.source.context() as s:
        slides.write(obj)
        slides.notify_later()(lambda: 'That is a notification which shows you can use decorator this way as well')
    s.display()

#Now generate many slides in a loop
__contents = [f"""## IPython Display Objects
#### Any object with following methods could be in`write` command:
{', '.join([f'`_repr_{rep}_`' for rep in __reprs__])}
Such as `IPython.display.<HTML,SVG,Markdown,Code>` etc. or third party such as `plotly.graph_objects.Figure`{{.Warning}}.            
""",
f"""## Plots and Other **Data**{{style='color:var(--accent-color);'}} Types
#### These objects are implemented to be writable in `write` command:
{', '.join([f"`{lib['name']}.{lib['obj']}`" for lib in libraries])}
Many will be extentended in future. If an object is not implemented, use `display(obj)` to show inline or use library's specific
command to show in Notebook outside `write`.
""",
f"""## Interactive Widgets
### Any object in `ipywidgets`{textbox('<a href="https://ipywidgets.readthedocs.io/en/latest/">Link to ipywidgtes right here using `textbox` command</a>')} 
or libraries based on ipywidgtes such as `bqplot`,`ipyvolume`,plotly's `FigureWidget`{slides.cite('pf','This is refernce to FigureWidget using `slides.cite` command')}(reference at end)
can be included in `iwrite` command as well as other objects that can be passed to `write` with caveat of Javascript.
{{.Warning}}
""",
'## Commands which do all Magic!']
for i in range(4,8):
    with slides.slide(i, background='skyblue'):
        write(__contents[i-4])
        if i == 7:
            with slides.source.context() as s:
                write([slides.doc(write,'LiveSlides'), slides.doc(iwrite,'LiveSlides'), slides.doc(slides.parse_xmd,'LiveSlides')])
                write("#### If an object does not render as you want, use `display(object)` or it's own library's mehod to display inside Notebook.")
            
            s.show_lines([0,1]).display()
# Matplotlib
with slides.slide(8,background='linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)'):
    write('## Plotting with Matplotlib')
    with slides.source.context() as s:
        import numpy as np, matplotlib.pyplot as plt
        x = np.linspace(0,2*np.pi)
        with plt.style.context('ggplot'):
            fig, ax = plt.subplots(figsize=(3.4,2.6))
            _ = ax.plot(x,np.cos(x))
        write([ax, s.focus_lines([1,3,4])])
        

# Youtube
from IPython.display import YouTubeVideo
with slides.slide(9):
    with slides.source.context(style='vs',className="Youtube") as s:
        write(f"### Watching Youtube Video?")
        write(YouTubeVideo('Z3iR551KgpI',width='100%',height='266px'))
        @slides.notify_later()
        def push():
            t = time.localtime()
            return f'You are watching Youtube at Time-{t.tm_hour:02}:{t.tm_min:02}'
        
        s.display() # s = source.context(style='vs', className="Youtube")
    
# Data Table
with slides.slide(10):
    with slides.source.context() as s:
        write('## Data Tables')
        write(slides.block_r('Here is Table',
            textwrap.dedent('''
            |h1|h2|h3|
            |---|---|---|
            |d1|d2|d3|
            |r1|r2|r3|
            ''')))
        s.focus_lines([3,4,5,6]).display()

# Plotly and Pandas DataFrame only show if you have installed
with slides.slide(11,background='#800000'):
    with slides.source.context():
        try:
            import pandas as pd 
            import altair as alt
            alt.themes.enable('dark')
            df = pd.read_csv('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv')
            chart = alt.Chart(df,width=300,height=260).mark_circle(size=60).encode(
                x='sepal_length',
                y='sepal_width',
                color='species',
                size = 'petal_width',
                tooltip=['species', 'sepal_length', 'sepal_width','petal_width','petal_length']
                ).interactive()
            df = df.describe() #Small for display
        except:
            df = '### Install `pandas` to view output'
            chart = '### Install Altair to see chart'
        write(('## Writing Pandas DataFrame',df),
            ('## Writing Altair Chart\nMay not work everywhere, needs javascript\n{.Note .Warning}',chart)
            )
    slides.source.current.show_lines(range(5,12)).display() #Show source code of above block even without assignning to variable explicitly
    
try:
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar([1,5,8,9]))
except:
    fig = '### Install `plotly` to view output'
with slides.slide(12):
    write(('## Writing Plotly Figure',fig))

# Interactive widgets can't be used in write command, but still they are displayed.   

with slides.slide(13):
    with slides.source.context() as src:
        import ipywidgets as ipw
        import numpy as np, matplotlib.pyplot as plt
        
        write('## Interactive Apps on Slide\n Use `ipywidgets`, `bqplot`,`ipyvolume` , `plotly Figurewidget` etc. to show live apps like this!')
        grid, [(plot,button, _), code] = slides.iwrite([
            '## Plot will be here! Click button below to activate it!',
            ipw.Button(description='Click me to update race plot',layout=ipw.Layout(width='max-content')),
            "[Check out this app](https://massgh.github.io/pivotpy/Widgets.html#VasprunApp)"],src.focus_lines([4,5,6,7,*range(24,30)]))
        
        def update_plot():
            x = np.linspace(0,0.9,10)
            y = np.random.random((10,))
            _sort = np.argsort(y)
            
            fig,ax = plt.subplots(figsize=(3.4,2.6))
            ax.barh(x,y[_sort],height=0.07,color=plt.cm.get_cmap('plasma')(x[_sort]))
        
            for s in ['right','top','bottom']:
                ax.spines[s].set_visible(False)
            
            ax.set(title='Race Plot', ylim = [-0.05,0.95], xticks=[],yticks=[c for c in x],yticklabels=[rf'$X_{int(c*10)}$' for c in x[_sort]])
            global plot # only need if you want to change something on it inside function
            plot = grid.update(plot, fig) #Update plot each time
            
        def onclick(btn):
            plot_theme = 'dark_background' if 'Dark' in slides.settings.theme_dd.value else 'default'
            with plt.style.context(plot_theme):
                update_plot()

        button.on_click(onclick)
        update_plot() #Initialize plot
    
    slides.notes.insert('## Something to hide from viewers!')


# Animat plot in slides  
@slides.frames(14,*range(14,19))
def func(obj):
    with slides.source.context() as s:
        fig, ax = plt.subplots()
        x = np.linspace(0,obj+1,50+10*(obj - 13))
        ax.plot(x,np.sin(x));
        ax.set_title(f'$f(x)=\sin(x)$, 0 < x < {obj - 13}')
        ax.set_axis_off()
        slides.notes.insert(f'## This is under @frames decorator, so it will be shown only in first frame')
        slides.notify_later()(lambda: f'This is under @frames decorator, so it will be shown only in first frame')
        
    slides.write([f'### This is Slide {14}.{obj-13}\n and we are animating matplotlib',
                  s.show_lines([obj-14])
                  ],ax,width_percents=[40,60])
    if obj == 14:
        s.show_lines([5,6]).display()
        
# Frames structure
boxes = [f'<div style="background:var(--tr-hover-bg);width:auto;height:auto;padding:8px;margin:8px;border-radius:4px;"><h1>{i}</h1></div>' for i in range(1,10)]
@slides.frames(15,*boxes, repeat=False)
def f(obj):
    slides.write('# Frames with \n#### `repeat = False`')
    slides.write(obj)

@slides.frames(16,*boxes, repeat=True)
def f(obj):
    slides.write('# Frames with \n#### `repeat = True`')
    slides.write(*obj,className='Warning')
    
@slides.frames(17,*boxes, repeat=[(0,1,2),(3,4,5),(6,7,8)])
def f(obj):
    with slides.source.context() as s:
        slides.write('# Frames with \n#### `repeat = [(0,1,2),(3,4,5),(6,7,8)]`')
        slides.write(*obj)
    s.display()

with slides.slide(18):
    with slides.source.context() as s:
        slides.write(['## Displaying image from url from somewhere in Kashmir (کشمیر)',
                      slides.image(r'https://assets.gqindia.com/photos/616d2712c93aeaf2a32d61fe/master/pass/top-image%20(1).jpg')],
                     className='Success')
    s.display()

with slides.slide(19):
    slides.write('## $\LaTeX$ in Slides\nUse `$ $` or `$$ $$` to display latex in Markdown, or embed images of equations')
    slides.write('$\LaTeX$ needs time to load, so `slides.pre_compute_display()` will help\n{.Note .Warning}')
    slides.write([r'\$\$\int_0^1\frac{1}{1-x^2}dx\$\$',
                r'$$\int_0^1\frac{1}{1-x^2}dx$$'
                ])  

with slides.slide(20):
    slides.write('## Built-in CSS styles')
    with slides.source.context() as s:
        with slides.print_context():
            slides.css_styles
            
        slides.write('Info',className='Info')
        slides.write('Warning',className='Warning')
        slides.write('سارے جہاں میں دھوم ہماری زباں کی ہے۔',className='Right RTL')
    s.display()

with slides.slide(21):
    with slides.source.context() as s:
        slides.rows(
            '## Can skip `write` commnad sometimes',
            slides.cols('### Column A','### Column B',className='Info'),
            '||### Column C {.Warning}||### Column D {.Success}||',
        ).display()
        slides.image(r'https://assets.gqindia.com/photos/616d2712c93aeaf2a32d61fe/master/pass/top-image%20(1).jpg').display()
    s.display()