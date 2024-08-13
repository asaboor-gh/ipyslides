# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.

def demo_slides(slides):
    slides.close_view() # Close any previous view to speed up loading 10x faster on average
    slides.clear() # Clear previous content
    raw_source = slides.code.cast(__file__).raw
    N = raw_source.count('.build') + raw_source.count('\n---') + 1 # Count number of slides, +1 for run_cell there
    slides.create(range(N)) # Create slides first, this is faster
    
    slides.settings.footer.text = 'Author: Abdul Saboor عبدالصبور'
    slides.set_citations({
            'pf': r'This is refernce to FigureWidget using alert`cite\`pf\`` syntax',
            'This': 'I was cited for no reason',
        }, mode = 'footnote')

    slides.run_cell("""
    %%slide 0 -m
    # Creating Slides
    ::: align-center
        alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`
        center`today```
        ::: text-box
            sup`1`My University is somewhere in the middle of nowhere
            sup`2`Their University is somewhere in the middle of nowhere
                    
        vspace`2`Read instructions by clicking ℹ️ button in quick menu
    """)
    #Demo for loading slides from a file or text block
    slides.build_(f"""
    section`Introduction` toc`### Contents`
    ---
    # Introduction
    Create a variable `x` in notebook to update this `{{x}}`
                  
    To see how commands work, use hl`Slides.docs()` to see the documentation.
    Here we will focus on using some of that functionality to create slides.
                  
    Version: `{slides.version}`
    """)

    slides.build(-1, slides.fmt("""
    section`Adding informative TOC` 
    ```multicol .block-blue
    toc[True]`### Contents`
    +++
    vspace`1` This is summary for current section created using block syntax of toc. See `Slides.xmd_syntax` for details.
                                    
    - Item 1
    - Item 2

    $$ E = mc^2 $$ 
    `{btn}`                       
    ```
                                       
    ```markdown
     ```multicol .block-blue
     toc[True]`### Contents`
     +++
     Extra content for current section which is on right
     ```
    ``` 
    """,btn=slides.draw_button))

    # Matplotlib
    with slides.build_() as sl:
        slides.write('## Plotting with Matplotlib section`Plotting and DataFrame`')
        with slides.code.context(returns = True) as s:
            sl.set_css({'--bg1-color':'linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)'})

            import numpy as np, matplotlib.pyplot as plt
            plt.rcParams['svg.fonttype'] = 'none' # Global setting, enforce same fonts as presentation
            x = np.linspace(0,2*np.pi)
            with plt.style.context('ggplot'):
                fig, ax = plt.subplots(figsize=(3.4,2.6))
                _ = ax.plot(x,np.cos(x))
            slides.write(ax, s.focus_lines([0,3,4]))


    # Plotly and Pandas DataFrame only show if you have installed
    with slides.code.context(returns = True) as source:
        try:
            import pandas as pd 
            df = pd.read_csv('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv')
            df = df.describe() #Small for display
        except:
            df = '### Install `pandas` to view output'

    slides.build(-1, lambda s: slides.write(['## Writing Pandas DataFrame', df, source]))
    
    with slides.code.context(returns = True) as s:
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(y=[1,5,8,9]))
        except:
            fig = '### Install `plotly` to view output'

    slides.build(-1,lambda s:(['## Writing Plotly Figure',fig, s]))

    def race_plot():
        import numpy as np
        import matplotlib.pyplot as plt

        x = np.linspace(0,0.9,10)
        y = np.random.random((10,))
        _sort = np.argsort(y)

        plot_theme = 'dark_background' if 'Dark' in slides.settings.theme.value else 'default'
        with plt.style.context(plot_theme):        
            fig,ax = plt.subplots(figsize=(3.4,2.6))
            ax.barh(x,y[_sort],height=0.07,color = plt.colormaps['plasma'](x[_sort]))

        for s in ['right','top','bottom']:
            ax.spines[s].set_visible(False)

        ax.set(title='Race Plot', ylim = [-0.05,0.95], xticks=[],yticks=[c for c in x],yticklabels=[rf'$X_{int(c*10)}$' for c in x[_sort]])
        return slides.plt2html(fig, transparent=False, caption='A Silly Plot')

    with slides.build(-1) as rslide:
        slides.write('''
            ## Refreshable Content
            Use refresh button below to update plot!
            See alert`race_plot` function at end of slides.
            ''')
        
        def display_plot(): return race_plot().display()

        slides.write(lambda: slides.interact(display_plot), rslide.get_source()) # Only first columns will update

    slides.build(-1,'section`Simple Animations with Frames` toc`### Contents`')

    forward_skipper = slides.goto_button('Skip All Next Frames', icon='arrowr')
    backward_skipper = slides.goto_button('Skip Previous Frames', icon='arrowl')
    
    # Animat plot in slides  
    with slides.build_():
        backward_skipper.set_target()
        slides.write("## Animating Matplotlib!", forward_skipper)

        with slides.code.context(returns = True) as s:
            for idx in slides.fsep.loop(range(10,19)):
                fig, ax = plt.subplots()
                x = np.linspace(0,idx,50)
                ax.plot(x,np.sin(x))
                ax.set_title(rf'$f(x)=\sin(x)$, 0 < x < {idx+1}')
                ax.set_xlim([0,18])
                ax.set_axis_off()
                slides.write(s.focus_lines([idx - 10]),ax,widths=[60,40])

    slides.build(-1,'section`Controlling Content on Frames` toc`### Contents`')

    # Frames structure
    boxes = [slides.html('h1', f"{c}",style="background:var(--bg3-color);margin-block:0.05em !important;") for c in range(1,5)]
    with slides.build(-1) as s:
        slides.write('# Default Frames')
        s.get_source().focus_lines([2,3]).display()
        slides.fsep()
        for item in slides.fsep.loop(boxes):
            slides.write(item)

    with slides.build(-1) as s:
        slides.write('# Frames with \n#### hl`fsep.join()` and Fancy Bullet List yoffset`0`')
        s.get_source().focus_lines([2,3,4]).display()
        slides.fsep()
        slides.fsep.join()
        for item in slides.fsep.loop(boxes):
            slides.bullets([item], marker='💘').display()

    with slides.build(-1) as s:
        slides.write('# Frames with \n#### hl`fsep.join()` and 2x2 grid of boxes yoffset`0`')
        s.get_source().focus_lines(range(2,7)).display()
        slides.fsep()
        slides.fsep.join()
        objs = [boxes[:2],boxes[2:]]
        widths = [(1,3),(3,2)]
        for ws, cols in slides.fsep.loop(zip(widths,objs)):
            slides.write(*cols, widths=ws)

    # Youtube
    from IPython.display import YouTubeVideo
    with slides.build(-1) as ys: # We will use this in next %%magic
        backward_skipper.display()
        forward_skipper.set_target()
        
        slides.write(f"### Watching Youtube Video?")
        slides.write('**Want to do some drawing instead?** Click on button on the right!', slides.draw_button, widths=[3,1])

        slides.write(YouTubeVideo('thgLGl14-tg',width='100%',height='266px'))

        @slides.on_load
        def push(slide):
            import time
            t = time.localtime()
            slides.notify(f'You are watching Youtube on slide {slide.index} at Time-{t.tm_hour:02}:{t.tm_min:02}')

        ys.get_source().display(True) 


    with slides.build(-1) as s:
        import ipywidgets as ipw
        slides.write('## Block API\nNew `block` API is as robust as `write` command. On top of it, it makes single unit of related content.')
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
                slides.alt(lambda w: f'<input type="range" min="{w.min}" max="{w.max}" value="{w.value}">', ipw.IntSlider()), 
                slides.alt('<button>Click to do nothing</button>', ipw.Button(description='Click to do nothing')), 
                ipw.Checkbox(description='Select to do nothing',indent=False), 
                slides.clip('test.png')
            ]
        )
        s.get_source().display(True)

    slides.build(-1, slides.fmt(r'''
    %++
    ## $ \LaTeX $ in Slides
    Use `$ $` or `$$ $$` to display latex in Markdown, or embed images of equations
    $ \LaTeX $ needs time to load, so keeping it in view until it loads would help.
    {.info}
                                
    --                           
    ::: note-tip
        Varibale formatting alongwith $ \LaTeX $ alert` \`{var}\` → `{var}`` is seamless.
    
    --
    ```multicol 50 50
    $$ \int_0^1\\frac{1}{1-x^2}dx $$
    {.align-left .text-big .info}
    +++
    ::: success
        $$ ax^2 + bx + c = 0 $$
        {.text-huge}
    ```
    ''', var = "I was a variable" ))

    with slides.build(-1) as some_slide:
        slides.write('## Serialize Custom Objects to HTML\nThis is useful for displaying user defined/third party objects in slides section`Custom Objects Serilaization`')
        with slides.suppress_stdout(): # suppress stdout from register fuction below
            @slides.serializer.register(int)
            def colorize(obj):
                color = 'red' if obj % 2 == 0 else 'green'
                return f'<span style="color:{color};">{obj}</span>'
            slides.write(*range(10))

        some_slide.get_source().display()

    @slides.build(-1)
    def _(slide):
        '## This is all code to generate slides section`Code to Generate Slides`'
        slides.code.cast(slides.demo).display()
        slides.code.cast(__file__).display()

    slides.build(-1, lambda s: slides.get_source().display())

    slides.navigate_to(0) # Go to title slide

    return slides