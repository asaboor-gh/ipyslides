# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.

from ipyslides.formatters import libraries, supported_reprs
from ipyslides.xmd import fmt

def demo_slides(slides):
    slides.close_view() # Close any previous view to speed up loading 10x faster on average
    slides.clear() # Clear previous content
    raw_source = slides.code.cast(__file__).raw
    N = raw_source.count('auto.') + raw_source.count('\n---') + 1 # Count number of slides, +1 for run_cell there
    slides.create(*range(N)) # Create slides first, this is faster
    
    write = slides.write # short name
    auto = slides.AutoSlides() # Does not work inside Jupyter notebook (should not as well)

    slides.settings.set_footer('Author: Abdul Saboor عبدالصبور')
    slides.set_citations({
            'pf': 'This is refernce to FigureWidget using alert`cite\`pf\`` syntax',
            'This': 'I was cited for no reason',
        }, mode = 'footnote')

    slides.run_cell("""
    %%title -m
    # Creating Slides
    ::: align-center
        alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`
        center`today```
        ::: text-box
            sup`1`My University is somewhere in the middle of nowhere
            sup`2`Their University is somewhere in the middle of nowhere
                    
    Read instructions by clicking ℹ️ button in quick menu.
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
    Version: `{version}` as executed from below code in markdown. 
    `{source}`
    proxy`something will be here in end`
    ---
    # IPySlides Online Running Sources 
    ::: note
        - [Edit on Kaggle](https://www.kaggle.com/massgh/ipyslides)
        - Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides/HEAD?labpath=demo.ipynb)
        - Watch a [Youtube Video](https://www.youtube.com/watch?v=ytfWIYbJteE)

    [^1]: Add references like this per slide or cite\`key\` to add citations generally.
    
    """, trusted=True)

    # slide s2 has proxies to be filled in later
    p1, p2 = s2.proxies   
    with p1.capture():
        s2.get_source().display(collapsed = True)

    with p2.capture():
        slides.write(f'alert`I was added at end by a given proxy, see the how it was done at the end of the slides`')


    *others, last = auto.from_markdown(f"""
    section`Variety of Content Types to Display` 
    ```toc ### Contents
    vspace`2` This is summary for current section created using block syntax of toc. See `Slides.xmd_syntax` for details.
                                       
    - Item 1
    - Item 2

    $$ E = mc^2 $$                        
    ```
                                       
    ```markdown
     ```toc Table of contents
     Extra content for current section which is on right
     ```
    ``` 
    ---
    ## IPython Display Objects
    #### Any object with following methods could be in`write` command:
    {', '.join([f'`_repr_{rep}_`' for rep in supported_reprs])}
    Such as color[fg=navy,bg=skyblue]`IPython.display.[HTML,SVG,Markdown,Code]` etc. or third party such as `plotly.graph_objects.Figure`.
    {{.warning}}
    ---
    ## Plots and Other **Data**{{style='color:var(--accent-color);'}} Types
    #### These objects are implemented to be writable in `write` command:
    {', '.join([f"`{lib['name']}.{lib['obj']}`" for lib in libraries])}
    Many will be extentended in future. If an object is not implemented, use `display(obj)` to show inline or use library's specific
    command to show in Notebook outside color[fg=teal,bg=whitesmoke]`write`.
    ---
    ## Interactive Widgets
    ### Any object in `ipywidgets` {slides.textbox('<a href="https://ipywidgets.readthedocs.io/en/latest/">Link to ipywidgtes right here using textbox command</a>')} 
    or libraries based on ipywidgtes such as color[red]`bqplot`,color[green]`ipyvolume`,plotly's `FigureWidget` cite`pf`(reference at end)
    can be included as well.
    {{.warning}}
    ---
    ## Commands which do all Magic!
    proxy`Add functions here`
    """, trusted=True)


    with slides.code.context(returns = True) as s:
        with last.proxies[0].capture():
            write([slides.classed(slides.doc(write,'Slides'),'block-green'), slides.classed(slides.doc(slides.parse,'Slides'),'block-red')])
            s.show_lines([0,1]).display()


    auto.from_markdown('section`Plotting and DataFrame` toc``')

    with auto.slide():
        write("## Use `ipyslides.Output` instead of `ipywidgets.Output`")
        with slides.code.context():
            import ipywidgets as ipw 

            with ipw.Output():
                write('''
                I was not suppoed to be shown, but alert`ipywidgets.Output` could not 
                capture me and I went to main capture stream!''')

            with (out := slides.Output()): # can by ipyslides.Output too
                print('I am safely captured here and will only be displayed if user wants to!')
            
            write(["**User wanted to write me below!**", 
                slides.alt(out, lambda w: 'HTML export for Output widget is not supported!')])

    # Matplotlib
    with auto.slide() as sl:
        write('## Plotting with Matplotlib')
        with slides.code.context(returns = True) as s:
            sl.set_css({'background':'linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)'})

            import numpy as np, matplotlib.pyplot as plt
            plt.rcParams['svg.fonttype'] = 'none' # Global setting, enforce same fonts as presentation
            x = np.linspace(0,2*np.pi)
            with plt.style.context('ggplot'):
                fig, ax = plt.subplots(figsize=(3.4,2.6))
                _ = ax.plot(x,np.cos(x))
            write(ax, s.focus_lines([0,3,4]))


    # Plotly and Pandas DataFrame only show if you have installed
    with slides.code.context(returns = True) as source:
        try:
            import pandas as pd 
            df = pd.read_csv('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv')
            df = df.describe() #Small for display
        except:
            df = '### Install `pandas` to view output'

    with auto.slide():
        write(['## Writing Pandas DataFrame', df, source])
    
    with slides.code.context(returns = True) as s:
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

        plot_theme = 'dark_background' if 'Dark' in slides.settings.theme_dd.value else 'default'
        with plt.style.context(plot_theme):        
            fig,ax = plt.subplots(figsize=(3.4,2.6))
            ax.barh(x,y[_sort],height=0.07,color = plt.colormaps['plasma'](x[_sort]))

        for s in ['right','top','bottom']:
            ax.spines[s].set_visible(False)

        ax.set(title='Race Plot', ylim = [-0.05,0.95], xticks=[],yticks=[c for c in x],yticklabels=[rf'$X_{int(c*10)}$' for c in x[_sort]])
        return slides.plt2html(fig, transparent=False, caption='A Silly Plot')


    # Interactive widgets.   
    with auto.slide():
        with slides.code.context(returns = True) as src:
            import ipywidgets as ipw

            write('''
                ## Interactive Apps with Widgets section`Interactive Widgets`
                Use `ipywidgets`, `bqplot`,`ipyvolume`, `plotly Figurewidget` etc. to show live apps like this!
                ::: note-tip
                    Export to Slides to see what happens to this slide and next slide!
                ''')
            plot_html = ipw.HTML('Plot will be here')
            button = ipw.Button(description='Click me to update race plot',layout=ipw.Layout(width='max-content'))

            write([plot_html,button], src)

            def update_plot(btn):
                plot_html.value = race_plot().value #Convert to html string

            button.on_click(update_plot)
            update_plot(None) #Initialize plot

        slides.code.cast(race_plot).display()

    with auto.slide() as rslide:
        write('''
            ## Dynamic Content without Widgets
            Use refresh button below to update plot! Compare with previous slide!
            ''')

        def display_plot(): return race_plot().display()

        write(lambda: slides.on_refresh(display_plot), rslide.get_source()) # Only first columns will update
        slides.code.cast(race_plot).display()

    auto.from_markdown('section`Simple Animations with Frames` toc`### Contents`')

    forward_skipper = slides.goto_button('Skip All Next Frames')
    backward_skipper = slides.goto_button('Skip Previous Frames', icon='minus')
    # Animat plot in slides  
    @auto.frames(*range(14,19))
    def func(obj,idx):
        if idx == 0:
            forward_skipper.display()
            backward_skipper.set_target()

        with slides.code.context(returns = True) as s:
            fig, ax = plt.subplots()
            x = np.linspace(0,obj+1,50+10*(idx+1))
            ax.plot(x,np.sin(x));
            ax.set_title(f'$f(x)=\sin(x)$, 0 < x < {idx+1}')
            ax.set_axis_off()
            slides.notes.insert(f'## This is under @frames decorator!')

        slides.write([f'### This is Slide {slides.running.number}.{idx}\n and we are animating matplotlib',
                      s.show_lines([idx]),
                      'cite`This` refs`1`'
                      ],ax,widths=[40,60])
        if idx == 0: #Only show source code of first frame
            s.show_lines([5]).display()

    auto.from_markdown('section`Controlling Content on Frames` toc`### Contents`')

    # Frames structure
    boxes = [f'<div style="background:var(--hover-bg);width:auto;height:2em;padding:8px;margin:8px;border-radius:4px;"><b class="align-center">{i}</b></div>' for i in range(1,5)]
    @auto.frames(*boxes, repeat=False)
    def f(obj,idx):
        slides.write('# Frames with \n#### `repeat = False`')
        slides.write(obj)

    @auto.frames(*boxes, repeat=True)
    def f(obj,idx):
        slides.running.set_animation(None) #Disable animation for showing bullets list
        slides.write('# Frames with \n#### `repeat = True` and Fancy Bullet List')
        slides.bullets(obj, marker='💘').display()

    @auto.frames(*boxes, repeat=[(0,1),(2,3)])
    def f(obj,idx):
        with slides.code.context(returns = True) as s:
            slides.write('# Frames with \n#### `repeat = [(0,1),(2,3)]`')
            slides.write(*obj)

        s.display()

    with auto.slide() as s:
        backward_skipper.display()
        forward_skipper.set_target()
        slides.format_css({'.goto-button .fa.fa-minus': slides.icon('arrow',color='crimson',rotation=180).css}).display()
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
        write('**Want to do some drawing instead?**\nClick on pencil icon and draw something on [tldraw](https://tldraw.com)!', slides.draw_button)

        write(YouTubeVideo('thgLGl14-tg',width='100%',height='266px'))

        @slides.on_load
        def push():
            import time
            t = time.localtime()
            slides.notify(f'You are watching Youtube at Time-{t.tm_hour:02}:{t.tm_min:02}')

        ys.get_source().display() 


    with auto.slide() as s:
        write('## Block API\nNew `block` API is as robust as `write` command. On top of it, it makes single unit of related content.')
        slides.block_red(
            [
                '### Table',
                '''
                |h1 |h2 |h3 |
                |---|---|---|
                |d1 |d2 |d3 |
                |r1 |r2 |r3 |
                ''',
            ], 
            [
                '### Widgets',
                slides.alt(ipw.IntSlider(),lambda w: f'<input type="range" min="{w.min}" max="{w.max}" value="{w.value}">'), # alt only works with widgets, but below display tricks works with any object
                lambda: display(ipw.Button(description='Click to do nothing'),metadata = {'text/html': '<button>Click to do nothing</button>'}), # This is a hack to display button as html in exported slides
                ipw.Checkbox(description='Select to do nothing',indent=False), # screenshot of this will be pasted in proxy below to export html
                'proxy`[Paste Checkbox Screenshot Here]`'
            ]
        )
        s.get_source().display()

    auto.from_markdown(slides.fmt('''
    %++
    ## $ \LaTeX $ in Slides
    --
    Use `$ $` or `$$ $$` to display latex in Markdown, or embed images of equations
    $ \LaTeX $ needs time to load, so keeping it in view until it loads would help.
    {.info}
    
    ::: note-tip
        Varibale formatting alongwith $ \LaTeX $ alert` \`{var}\` → `{var}`` is seamless.
    
    --
    ```multicol 50 50
    $$ \int_0^1\\frac{1}{1-x^2}dx $$
    {.align-left .text-big .info}
    +++
    --
    ::: success
        $$ ax^2 + bx + c = 0 $$
        {.text-huge}
    ```
    ''', var = "I was a variable" ), trusted=True)

    with auto.slide(), slides.code.context():
        slides.write(fmt('## Built-in CSS styles\n`{slides.css_styles}`'))

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
        slides.code.cast(slides.demo).display()
        slides.code.cast(__file__).display()

    with auto.slide():
        slides.write('Slides keep their full code if they are not made by @frames decorator!\n{.note .info}')
        slides.get_source().display()


    slides.navigate_to(0) # Go to title slide

    return slides