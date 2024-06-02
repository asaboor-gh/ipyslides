# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.

def demo_slides(slides):
    slides.close_view() # Close any previous view to speed up loading 10x faster on average
    slides.clear() # Clear previous content
    raw_source = slides.code.cast(__file__).raw
    N = raw_source.count('.next_') + raw_source.count('\n---') + 1 # Count number of slides, +1 for run_cell there
    slides.create(*range(N)) # Create slides first, this is faster
    
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
                    
        vspace`2`Read instructions by clicking ℹ️ button in quick menu.
    """)
    #Demo for loading slides from a file or text block
    s1, s2 = slides.next_from_markdown("""
    section`Introduction` toc`### Contents`
    ---
    # Introduction
    proxy`something will be here in start`
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
    """, trusted=True)

    # slide s2 has proxies to be filled in later
    p1, p2 = s2.proxies   
    with p1.capture():
        s2.get_source().display(collapsed = True)

    with p2.capture():
        slides.write(f'alert`I was added at end by a given proxy, see the how it was done at the end of the slides`')


    slides.next_from_markdown(f"""
    section`Adding informative TOC` 
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
    """, trusted=True)

    # Matplotlib
    with slides.next_slide() as sl:
        slides.write('## Plotting with Matplotlib section`Plotting and DataFrame`')
        with slides.code.context(returns = True) as s:
            sl.set_css({'background':'linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)'})

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

    with slides.next_slide():
        slides.write(['## Writing Pandas DataFrame', df, source])
    
    with slides.code.context(returns = True) as s:
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(y=[1,5,8,9]))
        except:
            fig = '### Install `plotly` to view output'

    with slides.next_slide():
        slides.write(('## Writing Plotly Figure',fig, s))

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
    with slides.next_slide():
        with slides.code.context(returns = True) as src:
            import ipywidgets as ipw
            
            slides.write('''
                ## Interactive Apps with Widgets section`Interactive Widgets`
                Use `ipywidgets`, `bqplot`,`ipyvolume`, `plotly Figurewidget` etc. to show live apps like this!
                ::: note-tip
                    Export to Slides to see what happens to this slide and next slide!
                ''')
            plot_html = ipw.HTML('Plot will be here')
            button = ipw.Button(description='Click me to update race plot',layout=ipw.Layout(width='max-content'))

            slides.write([plot_html,button], src)

            def update_plot(btn):
                plot_html.value = race_plot().value #Convert to html string

            button.on_click(update_plot)
            update_plot(None) #Initialize plot

    with slides.next_slide() as rslide:
        slides.write('''
            ## Dynamic Content without Widgets
            Use refresh button below to update plot! Compare with previous slide!
            See alert`race_plot` function at end of slides.
            ''')
        
        def display_plot(): return race_plot().display()

        slides.write(lambda: slides.on_refresh(display_plot), rslide.get_source()) # Only first columns will update

    slides.next_from_markdown('section`Simple Animations with Frames` toc`### Contents`')

    forward_skipper = slides.goto_button('Skip All Next Frames')
    backward_skipper = slides.goto_button('Skip Previous Frames', icon='minus')
    
    # Animat plot in slides  
    @slides.next_frames(*range(14,19))
    def func(idx, obj):
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

        slides.write([f'### This is Slide {slides.this.number}.{idx}\n and we are animating matplotlib',
                      s.show_lines([idx]),
                      'cite`This` refs`1`'
                      ],ax,widths=[40,60])
        if idx == 0: #Only show source code of first frame
            s.show_lines([5]).display()

    slides.next_from_markdown('section`Controlling Content on Frames` toc`### Contents`')

    # Frames structure
    boxes = [f'<div style="background:var(--hover-bg);width:auto;height:2em;padding:8px;margin:8px;border-radius:4px;"><b class="align-center">{i}</b></div>' for i in range(1,5)]
    @slides.next_frames(*boxes, repeat=False)
    def f(idx, obj):
        slides.write('# Frames with \n#### `repeat = False`')
        slides.write(obj)

    @slides.next_frames(*boxes, repeat=True)
    def f(idx, obj):
        slides.this.set_animation(None) #Disable animation for showing bullets list
        slides.write('# Frames with \n#### `repeat = True` and Fancy Bullet List')
        slides.bullets(obj, marker='💘').display()

    @slides.next_frames(*boxes, repeat=[(0,1),(2,3)])
    def f(idx, obj):
        slides.write('# Frames with \n#### `repeat = [(0,1),(2,3)]`')
        slides.write(*obj)

    # Youtube
    from IPython.display import YouTubeVideo
    with slides.next_slide() as ys: # We will use this in next %%magic
        backward_skipper.display()
        forward_skipper.set_target()
        slides.format_css({'.goto-button .fa.fa-minus': slides.icon('arrow',color='crimson',rotation=180).css}).display()
    
        slides.write(f"### Watching Youtube Video?")
        slides.write('**Want to do some drawing instead?**\nClick on pencil icon and draw something on [tldraw](https://tldraw.com)!', slides.draw_button)

        slides.write(YouTubeVideo('thgLGl14-tg',width='100%',height='266px'))

        @slides.on_load
        def push():
            import time
            t = time.localtime()
            slides.notify(f'You are watching Youtube at Time-{t.tm_hour:02}:{t.tm_min:02}')

        ys.get_source().display(True) 


    with slides.next_slide() as s:
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
                slides.alt(ipw.IntSlider(),lambda w: f'<input type="range" min="{w.min}" max="{w.max}" value="{w.value}">'), # alt only works with widgets, but below display tricks works with any object
                lambda: display(ipw.Button(description='Click to do nothing'),metadata = {'text/html': '<button>Click to do nothing</button>'}), # This is a hack to display button as html in exported slides
                ipw.Checkbox(description='Select to do nothing',indent=False), 
                'proxy`Paste Checkbox Screenshot Here with Slides.clip_image function`'
            ]
        )
        s.get_source().display(True)

    slides.next_from_markdown(slides.fmt('''
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

    with slides.next_slide() as some_slide:
        slides.write('## Serialize Custom Objects to HTML\nThis is useful for displaying user defined/third party objects in slides section`Custom Objects Serilaization`')
        with slides.suppress_stdout(): # suppress stdout from register fuction below
            @slides.serializer.register(int)
            def colorize(obj):
                color = 'red' if obj % 2 == 0 else 'green'
                return f'<span style="color:{color};">{obj}</span>'
            slides.write(*range(10))

        some_slide.get_source().display()

    with slides.next_slide():
        slides.write('## This is all code to generate slides section`Code to Generate Slides`')
        slides.code.cast(slides.demo).display()
        slides.code.cast(__file__).display()

    with slides.next_slide():
        slides.write('Slides keep their full code if they are not made by @frames decorator!\n{.note .info}')
        slides.get_source().display()


    slides.navigate_to(0) # Go to title slide

    return slides