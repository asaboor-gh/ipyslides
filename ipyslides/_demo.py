# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.
from .core import LiveSlides
from .utils import write, ihtml,plt2html, iwrite, __reprs__, textbox
from .objs_formatter import libraries
slides = LiveSlides()
slides.convert2slides(True)
slides.set_footer('Author: Abdul Saboor')

#title is skipped to show instructions  
with slides.slide(1): #slide 1
    write('## I am created using `with slides.slide(1)` context manager!')
    write(f'I am {slides.alert("Alerted")} and I am *{slides.colored("colored and italic text","magenta","whitesmoke")}*')
    write("""```python
write(f'I am {slides.alert("Alerted")} and I am *{slides.colored("Colored and italic text","magenta","whitesmoke")}*')
```""")
    
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
@slides.slides(2,'## I am created using `@slides.slides`',online_sources)
def func(item):
    slides.write(item)
    slides.write('------ Above text generated by this!-------')
    slides.write(slides.keep_format(item))

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
"""]
for i in range(3,6):
    with slides.slide(i,background='#556B2F'):
        write(__contents[i-3])

# Matplotlib
import numpy as np, matplotlib.pyplot as plt
x = np.linspace(0,2*np.pi)
with plt.style.context('ggplot'):
    fig, ax = plt.subplots(figsize=(3.4,2.6))
    _ = ax.plot(x,np.cos(x))
with slides.slide(6):
    write('## Plotting with Matplotlib')
    write(plt2html(caption='No need to save me in file, I directly show up here!'))

# Youtube
from IPython.display import YouTubeVideo
with slides.slide(7):
    write(f"### Watching Youtube Video?")
    write(YouTubeVideo('Z3iR551KgpI',width='100%',height='266px'))
    
# Data Table
with slides.slide(8):
    write('''## Data Tables
|h1|h2|h3|
|---|---|---|
|d1|d2|d3|
|r1|r2|r3|
''',
'''```shell
|h1|h2|h3|
|---|---|---|
|d1|d2|d3|
|r1|r2|r3|
```''')

# Plotly and Pandas DataFrame only show if you have installed
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
with slides.slide(9,background='#800000'):
    write(('## Writing Pandas DataFrame',df),
          ('## Writing Altair Chart\nMay not work everywhere, needs javascript',chart)
          )
    
try:
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar([1,5,8,9]))
except:
    fig = '### Install `plotly` to view output'
with slides.slide(10):
    write(('## Writing Plotly Figure',fig))

# Interactive widgets can't be used in write command, but still they are displayed.   
import ipywidgets as ipw
btn = ipw.Button(description='Click Me To see Progress',layout=ipw.Layout(width='auto'))
prog = ipw.IntProgress(value=10)
html = ihtml(f"Current Value is {prog.value}")
def onclick(btn):
    prog.value = prog.value + 10
    if prog.value > 90:
        prog.value = 0
    html.value = f"Current Value is {prog.value}"

btn.on_click(onclick)

with slides.slide(11):
    write('## Interactive Apps on Slide\n Use `ipywidgets`, `bqplot`,`ipyvolume` , `plotly Figurewidget` etc. to show live apps like this!')
    iwrite(prog,[btn,html])
    write("[Check out this app](https://massgh.github.io/pivotpy/Widgets.html#VasprunApp)")

# Animat plot in slides  
@slides.slides(12,*range(13,18))
def func(item):
    fig, ax = plt.subplots()
    x = np.linspace(0,item+1,50+10*(item - 12))
    ax.plot(x,np.sin(x));
    ax.set_title(f'$f(x)=\sin(x)$, 0 < x < {item - 12}')
    ax.set_axis_off()
    slides.write(f'### This is Slide {item}\n and we are animating matplotlib',ax,width_percents=[30,70])
