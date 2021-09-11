# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.
from .core import LiveSlides
from .utils import write, plt2html, iwrite
slides = LiveSlides()
slides.convert2slides(True)
slides.set_footer('Author: Abdul Saboor')

#title is skipped to show instructions  
with slides.slide(1): #slide 1
    write('## I am created using `with slides.slide(1)` context manager!')
    
slides.shell.user_ns['write'] = write #Inject variable in IPython shell

#slide 2    
slides.shell.run_cell_magic('slide','2','write("## I am created using magic `%%slide 2`")')
#slide 3
@slides.slides(2,'## I am created using `@slides.slides`')
def func(item):
    write(item)

#Now generate many slides in a loop
for i in range(3,6):
    with slides.slide(i):
        write(f'## Slide {i} Title\n### Created in a loop')

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
''')

# Plotly and Pandas DataFrame only show if you have installed
try:
    import pandas as pd 
    import altair as alt
    alt.themes.enable('dark')
    df = pd.read_csv('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv').head()
    chart = alt.Chart(df,width=300,height=260).mark_circle(size=60).encode(
        x='sepal_length',
        y='sepal_width',
        color='species',
        size = 'petal_width',
        tooltip=['species', 'sepal_length', 'sepal_width','petal_width','petal_length']
        ).interactive()
except:
    df = '### Install `pandas` to view output'
    chart = '### Install Altair to see chart'
with slides.slide(9):
    write(('## Writing Pandas DataFrame\nSince it has `_repr_html_` method',df),
          ('## Writing Altair Chart\nSince it has `to_html` method',chart)
          )
    write("""```python
with slides.slide(9):
    write(('## Writing Pandas DataFrame\\nSince it has `_repr_html_` method',df),
          ('## Writing Altair Chart\\nSince it has `to_html` method',chart)
          )\n```"""
          )
    
try:
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar([1,5,8,9]))
except:
    fig = '### Install `plotly` to view output'
with slides.slide(10):
    write(('## Writing Plotly Figure\nSince it has `_repr_html_` method',fig))

# Interactive widgets can't be used in write command, but still they are displayed.   
import ipywidgets as ipw
btn = ipw.Button(description='Click Me To see Progress',layout=ipw.Layout(width='auto'))
prog = ipw.IntProgress(value=10)
def onclick(btn):
    prog.value = prog.value + 10
    if prog.value > 90:
        prog.value = 0

btn.on_click(onclick)

with slides.slide(11):
    write('## All IPython widgets support\n`ipywidgets`, `bqplot`,`ipyvolume` , `plotly Figurewidget` etc.')
    iwrite([ipw.IntSlider(value=10),prog],btn)

# Animat plot in slides  
@slides.slides(12,*range(13,18))
def func(item):
    fig, ax = plt.subplots()
    x = np.linspace(0,item+1,50+10*(item - 12))
    ax.plot(x,np.sin(x));
    ax.set_title(f'$f(x)=\sin(x)$, 0 < x < {item - 12}')
    ax.set_axis_off()
    write(f'### This is Slide {item}\n and we are animating matplotlib',plt2html(),width_percents=[30,70])
