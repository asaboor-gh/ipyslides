# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.
import time, textwrap

from ipyslides.writers import write, iwrite
from ipyslides.formatters import libraries, __reprs__
from ipyslides._base.intro import logo_svg

markdown_str = """# Creating Slides
class`Center`
alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`

today``

class`TextBox`
sup`1`My University is somewhere in the middle of nowhere
sup`2`Their University is somewhere in the middle of nowhere
^^^
^^^
<h4 style=""color:green;"> 👈🏻 Read instructions in left panel</h4>
---
## Table of Contents
toc`-----------------`
---
# Introduction section`Introduction`
To see how commands work, use `Slides.docs()` to see the documentation.
Here we will focus on using all that functionality to create slides.
```python run source
# get the slides instance under a python block in Markdown file, we will use it later to run a cell magic.
myslides = get_slides_instance() 
import ipyslides as isd
version = isd.__version__
%xmd #### This is inline markdown parsed by magic {.Note .Warning}
```
Version: {{version}} as executed from below code in markdown. 
{{source}}
---
# IPySlides Online Running Sources 
Launch as voila slides (may not work as expected [^1])[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=voila%2Frender%2Fnotebooks%2Fipyslides.ipynb)
{.Note .Error}

[Edit on Kaggle](https://www.kaggle.com/massgh/ipyslides)
{.Note .Warning}

Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=lab%2Ftree%2Fnotebooks%2Fipyslides.ipynb)
{.Note .Success}

[^1]: Add references like this per slide. Use slides.cite() or in markdown cite\`key\` to add citations generally.
  
"""

def demo(slides_instance):
    "We can import `ipyslides.Slides` and use it to create slides, but we will use the slides instance passed to this function."
    slides = slides_instance
    slides.close_view() # Close any previous view to speed up loading 10x faster on average
    slides.clear() # Clear previous content
    slides._citation_mode = 'global' # Set citation mode to global if set otherwise by user
    
    # Create shortcut for autoslide/autoframes, but DO NOT do it in Notebook, you may get countless slides there with each run.
    def autoslide(*args,**kwargs): return slides.slide(slides.auto_number, *args, **kwargs) 
    def autoframes(*args,**kwargs): return slides.frames(slides.auto_number, *args, **kwargs) 
        
    slides.settings.set_footer('Author: Abdul Saboor عبدالصبور')
    slides.settings.set_logo(logo_svg,width=60) # This is by defualt a logo of ipyslides
    slides._citation_mode = 'global' # This could be changed by other functions
    slides.set_citations({'pf': 'This is refernce to FigureWidget using `slides.cite` command'})

    #Demo for loading slides from a file or text block 
    s0, s1, s2, *others = slides.from_markdown(0,markdown_str, trusted=True)

    with s0.insert(0):
        s0.source.display(collapsed = True)

    slides.shell.user_ns['write'] = write #Inject variable in IPython shell

    # Insert source of slide 2    
    with s2.insert(0):
        s2.source.display(collapsed = True)
        slides.goto_button(slides.running.number+5, 'Skip 5 Slides')

    s2.insert_markdown({-1: f'alert`I was added at end using \`s2.insert_markdown\``'})

    #Now generate many slides in a loop
    __contents = [f"""
    ## IPython Display Objects section`Variety of Content Types to Display`
    #### Any object with following methods could be in`write` command:
    {', '.join([f'`_repr_{rep}_`' for rep in __reprs__])}
    Such as color[navy_skyblue]`IPython.display.[HTML,SVG,Markdown,Code]` etc. or third party such as `plotly.graph_objects.Figure`{{.Warning}}.            
    """,
    f"""
    ## Plots and Other **Data**{{style='color:var(--accent-color);'}} Types
    #### These objects are implemented to be writable in `write` command:
    {', '.join([f"`{lib['name']}.{lib['obj']}`" for lib in libraries])}
    Many will be extentended in future. If an object is not implemented, use `display(obj)` to show inline or use library's specific
    command to show in Notebook outside color[teal_whitesmoke]`write`.
    """,
    f"""
    ## Interactive Widgets
    ### Any object in `ipywidgets`{slides.textbox('<a href="https://ipywidgets.readthedocs.io/en/latest/">Link to ipywidgtes right here using textbox command</a>')} 
    or libraries based on ipywidgtes such as color[red]`bqplot`,color[green]`ipyvolume`,plotly's `FigureWidget` cite`pf`(reference at end)
    can be included in `iwrite` command as well as other objects that can be passed to `write` with caveat of Javascript.
    {{.Warning}}
    """,
    '## Commands which do all Magic!']
    
    for i, content in enumerate(__contents):
        with autoslide(props_dict = {'':dict(background = 'skyblue')}):
            write(textwrap.dedent(content))
            if i == 3:
                with slides.source.context(auto_display = False) as s:
                    write([slides.doc(write,'Slides'), slides.doc(iwrite,'Slides'), slides.doc(slides.parse_xmd,'Slides')])
                    write("#### If an object does not render as you want, use `display(object)` or register it as you want using `@Slides.serializer.register` decorator")

                s.show_lines([0,1]).display()

    # Matplotlib
    with autoslide(props_dict = {'': dict(background='linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)')}):
        write('## Plotting with Matplotlib section`Plotting and DataFrame`')
        with slides.source.context(auto_display = False) as s:
            import numpy as np, matplotlib.pyplot as plt
            plt.rcParams['svg.fonttype'] = 'none' # Global setting, enforce same fonts as presentation
            x = np.linspace(0,2*np.pi)
            with plt.style.context('ggplot'):
                fig, ax = plt.subplots(figsize=(3.4,2.6))
                _ = ax.plot(x,np.cos(x))
            write([ax, s.focus_lines([1,3,4])])

    # Plotly and Pandas DataFrame only show if you have installed
    try:
        with slides.source.context(auto_display = False) as source:
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
        
    with autoslide(props_dict = {'':dict(background='#800000')}):
        write(('## Writing Pandas DataFrame',df))
        source.show_lines([0,3,11]).display()
    
    with autoslide():
        slides.write(('## Writing Altair Chart\nMay not work everywhere, needs javascript\n{.Note .Warning}',chart))
        source.show_lines(range(1,11)).display()
       
    try:
        with slides.source.context(False) as s:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(y=[1,5,8,9]))
    except:
        fig = '### Install `plotly` to view output'
        
    with autoslide():
        write(('## Writing Plotly Figure',fig))
        s.display()

    # Interactive widgets.   
    with autoslide():
        with slides.source.context(auto_display = False) as src:
            import ipywidgets as ipw
            import numpy as np, matplotlib.pyplot as plt

            write('## Interactive Apps on color[var(--accent-color)]`Slide`\n Use `ipywidgets`, `bqplot`,`ipyvolume` , `plotly Figurewidget` etc. to show live apps like this!')
            writer, (plot,button, _), code = slides.iwrite([
                '## Plot will be here! Click button below to activate it! section`Interactive Widgets`',
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
                writer.update(plot, fig) #Update plot each time

            def onclick(btn):
                plot_theme = 'dark_background' if 'Dark' in slides.settings.theme_dd.value else 'default'
                with plt.style.context(plot_theme):
                    update_plot()

            button.on_click(onclick)
            update_plot() #Initialize plot

        slides.notes.insert('## Something to hide from viewers!')


    # Animat plot in slides  
    @autoframes(*range(14,19))
    def func(obj,idx):
        slides.write('section`Simple Animations with Frames`')
        if idx == 0:
            slides.goto_button(slides.running.number + 4, 'Skip All Next Frames')
        
        with slides.source.context(auto_display = False) as s:
            fig, ax = plt.subplots()
            x = np.linspace(0,obj+1,50+10*(idx+1))
            ax.plot(x,np.sin(x));
            ax.set_title(f'$f(x)=\sin(x)$, 0 < x < {idx+1}')
            ax.set_axis_off()
            slides.notes.insert(f'## This is under @frames decorator!')
            slides.notify_later()(lambda: f'This is under @frames decorator!')

        slides.write([f'### This is Slide {slides.running.number}.{idx}\n and we are animating matplotlib',
                      s.show_lines([idx])
                      ],ax,width_percents=[40,60])
        if idx == 0: #Only show source code of first frame
            s.show_lines([5,6]).display()

        slides.write(slides.cite('This'))

    # Frames structure
    boxes = [f'<div style="background:var(--tr-hover-bg);width:auto;height:2em;padding:8px;margin:8px;border-radius:4px;"><b class="Center">{i}</b></div>' for i in range(1,5)]
    @autoframes(*boxes, repeat=False)
    def f(obj,idx):
        slides.write('# Frames with \n#### `repeat = False` section`Controlling Content on Frames`')
        slides.write(obj)

    @autoframes(*boxes, repeat=True)
    def f(obj,idx):
        slides.running.set_animation(None) #Disable animation for showing bullets list
        slides.write('# Frames with \n#### `repeat = True` and Fancy Bullet List')
        slides.bullets(obj, marker='💘').display()

    @autoframes(*boxes, repeat=[(0,1),(2,3)])
    def f(obj,idx):
        with slides.source.context(auto_display = False) as s:
            slides.write('# Frames with \n#### `repeat = [(0,1),(2,3)]`')
            slides.write(*obj)
        s.display()

    with autoslide():
        with slides.source.context(auto_display = False) as s:
            slides.goto_button(slides.running.number - 5, 'Skip All Previous Frames')
            slides.write('## Displaying image from url from somewhere in Kashmir color[crimson]`(کشمیر)` section`Miscellaneous Content`')
            try:
                slides.image(r'https://assets.gqindia.com/photos/616d2712c93aeaf2a32d61fe/master/pass/top-image%20(1).jpg').display()
            except:
                slides.write('Could not retrieve image from url. Check internt connection!',className='Error')
            s.display()
    
    # Youtube
    from IPython.display import YouTubeVideo
    with autoslide():
        with slides.source.context(auto_display = False, style='vs',className="Youtube") as s:
            write(f"### Watching Youtube Video?")
            write(YouTubeVideo('Z3iR551KgpI',width='100%',height='266px'))
            @slides.notify_later()
            def push():
                t = time.localtime()
                return f'You are watching Youtube at Time-{t.tm_hour:02}:{t.tm_min:02}'

            s.display() # s = source.context(style='vs', className="Youtube")
        
    # Data Table
    slides.shell.run_cell_magic('slide',f'{slides.auto_number}',"""
    with myslides.source.context(auto_display = False) as s:
        write('## Data Tables')
        # Remember myslides variable was assigned in a python block in markdown just in start. Magic!
        write(myslides.block_r('Here is Table','<hr/>','''
            |h1|h2|h3|
            |---|---|---|
            |d1|d2|d3|
            |r1|r2|r3|
            '''))
        s.focus_lines([3,4,5,6]).display()
    """)

    slides.from_markdown(slides.auto_number, '''
    ## $\LaTeX$ in Slides
    Use `$ $` or `$$ $$` to display latex in Markdown, or embed images of equations
    $\LaTeX$ needs time to load, so keeping it in view until it loads would help.
    {.Note .Warning}

    \$\$\int_0^1\\frac{1}{1-x^2}dx\$\$
    $$\int_0^1\\frac{1}{1-x^2}dx$$
    ''', trusted=True)

    with autoslide():
        slides.write('## Built-in CSS styles')
        with slides.source.context():
            slides.css_styles.display()
            slides.write('Info',className='Info')
            slides.write('Warning',className='Warning')
            slides.write('سارے جہاں میں دھوم ہماری زباں کی ہے۔',className='Right RTL')

    with autoslide(),slides.source.context():
        slides.rows(
            '## Can skip `write` commnad sometimes',
            slides.cols('### Column A','### Column B',className='Info'),
            '||### Column C {.Warning}||### Column D {.Success}||',
        ).display()
        slides.write('----') # In Python < 3.8, context manager does not properly handle end of code block, so use this to end context

    with autoslide():
        slides.write('## Serialize Custom Objects to HTML\nThis is useful for displaying user defined/third party objects in slides section`Custom Objects Serilaization`')
        with slides.suppress_stdout(): # suppress stdout from register fuction below
            with slides.source.context(auto_display = False) as s:
                @slides.serializer.register(int)
                def colorize(obj):
                    color = 'red' if obj % 2 == 0 else 'green'
                    return f'<span style="color:{color};">{obj}</span>'

                slides.write(*range(10))

            s.display()
        
    with autoslide():
        slides.write('## This is all code to generate slides section`Code to Generate Slides`')
        slides.source.from_file(__file__).display()
        
    with autoslide():
        slides.write('Slides made by using `from_markdown` or `%%slide` magic preserve their full code\n{.Note .Info}')
        slides.get_source().display()
         
    with autoslide(props_dict = {'': dict(background='#9ACD32')}):
        with slides.source.context():
            slides.write('citations`## Reference via Markdown\n----`',
                         ['## Reference via Python API\n----',
                          *slides.citations])
            slides.write('Markdown is easier to write and read, but Python API is more powerful.')
            
    with slides.slide(1): #slide 1 will be modified with old and new content
        with slides.source.context(auto_display = False, style='monokai', color='white', className='Mono') as s:
            slides.parse_xmd(s1.markdown) #s1 was assigned as `s0, s1, s2 = slides.from_markdown...` in start.
            slides.write('I was re-executed at end to grab all table of contents and new content!')
        s.display()
    
    slides.navigate_to(0) # Go to title slide
    return slides

if __name__ == '__main__':
    print('WARNING: This file is not meant to be run directly. Import in Jupyter Notebook instead!')