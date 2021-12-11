# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.
import textwrap, time

from ipywidgets.widgets.widget_layout import Layout
from .core import LiveSlides
from .utils import write, ihtml,plt2html, iwrite, __reprs__, textbox
from .objs_formatter import libraries
slides = LiveSlides()
slides.convert2slides(True)
slides.set_footer('Author: Abdul Saboor عبدالصبور')
slides.set_logo('''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="50" fill="blue"/>
        <text x="45%" y="45%" fill="white" font-size="4em" dominant-baseline="central" text-anchor="middle">↑</text>
        <text x="55%" y="60%" fill="white" font-size="4em" dominant-baseline="central" text-anchor="middle">↓</text></svg>''',width=50)

#title is skipped to show instructions  
with slides.slide(1): #slide 1
    with slides.source() as s:
        write('## I am created using `with slides.slide(1)` context manager!')
        write(f'I am {slides.alert("Alerted")} and I am *{slides.colored("colored and italic text","magenta","whitesmoke")}*')
    write(s)   
    
slides.shell.user_ns['write'] = write #Inject variable in IPython shell

#slide 2    
slides.shell.run_cell_magic('slide','2','write("## I am created using magic `%%slide 2`")')
#slide 3
online_sources = '''# IPySlides Online Running Sources 
Launch as voila slides (may not work as expected [^1])[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=voila%2Frender%2Fnotebooks%2Fipyslides.ipynb)
[Edit on Kaggle](https://www.kaggle.com/massgh/ipyslides)
Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=lab%2Ftree%2Fnotebooks%2Fipyslides.ipynb)
<br>
[^1]: Add references like this per slide. Use slides.cite() to add citations generally.
'''
@slides.frames(3,'## I am created using `@slides.frames`',online_sources)
def func(obj):
    slides.write(obj)
    with slides.source() as s:
        slides.write('------ Above text generated by this!-------')
        slides.write(slides.keep_format(obj))
    write(s)

#Now generate many slides in a loop
__contents = [f"""## IPython Display Objects
#### Any object with following methods could be in`write` command:
{', '.join([f'`_repr_{rep}_`' for rep in __reprs__])}
Such as `IPython.display.<HTML,SVG,Markdown,Code>` etc. or third party such as `plotly.graph_objects.Figure`.            
""",
f"""## Plots and Other Data Types
#### These objects are implemented to be writable in `write` command:
{', '.join([f"`{lib['name']}.{lib['obj']}`" for lib in libraries])}
Many will be extentended in future. If an object is not implemented, use `display(obj)` to show inline or use library's specific
command to show in Notebook outside `write`.
""",
f"""## Interactive Widgets
### Any object in `ipywidgets`{textbox('<a href="https://ipywidgets.readthedocs.io/en/latest/">Link to ipywidgtes right here using `textbox` command</a>')} 
or libraries based on ipywidgtes such as `bqplot`,`ipyvolume`,plotly's `FigureWidget`{slides.cite('pf','This is refernce to FigureWidget using `slides.cite` command')}(reference at end)
can be included in `iwrite` command. Text/Markdown/HTML inside `iwrite` is made available through `ihtml` command.
""",
'## Commands which do all Magic!']
for i in range(4,8):
    with slides.slide(i, background=f'linear-gradient(to right, olive 0%, olive {i*5}%, crimson {i*15}%, orange 100%)'):
        write(__contents[i-4])
        if i == 7:
            with slides.source() as s:
                write(slides.block_r('slides.write/ipyslide.utils.write',write),
                      slides.rows(slides.block_b('slides.iwrite/ipyslide.utils.iwrite',iwrite),
                       slides.block_b('slides.ihtml/ipyslide.utils.ihtml',ihtml)
                       )
                    )
                write("#### If an object does not render as you want, use `display(object)` or it's own library's mehod to display inside Notebook.")
            write(s)
# Matplotlib
with slides.slide(8,background='linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)'):
    with slides.source() as s:
        import numpy as np, matplotlib.pyplot as plt
        x = np.linspace(0,2*np.pi)
        with plt.style.context('ggplot'):
            fig, ax = plt.subplots(figsize=(3.4,2.6))
            _ = ax.plot(x,np.cos(x))
            
    write('## Plotting with Matplotlib')
    write(slides.block_g('Matplotlib inside block!',slides.alert('Alerting inside block!'),plt2html(caption='No need to save me in file, I directly show up here!'),s))

# Youtube
from IPython.display import YouTubeVideo
with slides.slide(9):
    with slides.source() as s:
        write(f"### Watching Youtube Video?")
        write(YouTubeVideo('Z3iR551KgpI',width='100%',height='266px'))
    write(s)
    
# Data Table
with slides.slide(10):
    with slides.source() as s:
        write('## Data Tables')
        write(slides.block_r('Here is Table',
            textwrap.dedent('''
            |h1|h2|h3|
            |---|---|---|
            |d1|d2|d3|
            |r1|r2|r3|
            ''')))
    write(s)

# Plotly and Pandas DataFrame only show if you have installed
with slides.slide(11,background='#800000'):
    with slides.source() as s:
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
            ('## Writing Altair Chart\nMay not work everywhere, needs javascript',chart)
            )
    write(s)
    
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
    with slides.source() as s:
        import ipywidgets as ipw
        btn = ipw.Button(description='Click Me To see Progress',layout=ipw.Layout(width='auto'))
        prog = ipw.IntProgress(value=10)
        html = ihtml(f"Current Value is {prog.value}")
        source_html = ipw.HTML()
        def onclick(btn):
            prog.value = prog.value + 10
            if prog.value > 90:
                prog.value = 0
            html.value = f"Current Value is {prog.value}"

        btn.on_click(onclick)
        
        write('## Interactive Apps on Slide\n Use `ipywidgets`, `bqplot`,`ipyvolume` , `plotly Figurewidget` etc. to show live apps like this!')
        iwrite([prog,btn,html], source_html,width_percents=[40,60])
        write("[Check out this app](https://massgh.github.io/pivotpy/Widgets.html#VasprunApp)")
    
    source_html.value = s.html #This is to show source code inside with block

# Animat plot in slides  
@slides.frames(14,*range(14,19))
def func(obj):
    fig, ax = plt.subplots()
    x = np.linspace(0,obj+1,50+10*(obj - 13))
    ax.plot(x,np.sin(x));
    ax.set_title(f'$f(x)=\sin(x)$, 0 < x < {obj - 13}')
    ax.set_axis_off()
    slides.write(f'### This is Slide {14}.{obj-13}\n and we are animating matplotlib',ax,width_percents=[30,70])

# Use enumerate to iterate over slides
for i,s in slides.enum_slides(15,17,background='var(--secondary-bg)'):
    with s:
        write(f'### This is Slide {i} added with `enum_slides`')

# Let's test notification API
for i in range(len(slides.iterable)):
    @slides.notify_at(i,timeout=2)
    def push_notification(idx): # idx is will pick i from decorator, just to show these are dummy varibales
        t = time.localtime()
        return f'Slide-{idx}<br/> Time-{t.tm_hour:02}:{t.tm_min:02}'       