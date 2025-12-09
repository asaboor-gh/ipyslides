# Author: Abdul Saboor
# This demonstrates that you can generate slides from a .py file too, which you can import in notebook.

def demo_slides(slides):
    slides.close_view() # Close any previous view to speed up building (minor effect but visually better)
    slides.clear() # Clear previous content
    raw_source = slides.code.cast(__file__).raw
    N = raw_source.count('.build') + raw_source.count('\n---') 
    slides.create(range(N)) # Create slides first, this is faster
    
    slides.settings.footer.text = slides.get_logo("1em") + 'Author: Abdul Saboor عبدالصبور'
    slides.set_citations(r'''
        @pf: This is refernce to FigureWidget using alert`cite\`pf\`` syntax
        @This: I was cited for no reason
    ''')

    # title slide should alway be overwritten by 0 
    slides.build(0, """
    ```md-src.collapsed
    # Creating Slides
    ::: align-center width=50%
        alert`Abdul Saboor`^`1`, Unknown Author^`2`
        center`//today``//`
        ::: align-left text-box
            ^`1`My University is somewhere in the middle of nowhere
            ^`2`Their University is somewhere in the middle of nowhere
    
    ::: display align-center               
        vspace`2`Right click (or click on footer) to open context menu and click on fa`info` icon for instructions.
    ```
    <md-src/>
    """)
    
    # build_ is same as build(-1)
    slides.build_(f"""
    section`Introduction` toc`### Contents`
    ---
    # Introduction
                  
    To see how commands work, use code`Slides.docs()` to see the documentation.
    Here we will focus on using some of that functionality to create slides.
    
    ::: note-info
        This slide was built purely from markdown, so you can create
        a variable `test` to overwite this → %{{test}}
                  
    Version: `{slides.version}`
    """)

    slides.build(-1, """
    ::: md-after
        section`Adding informative TOC` 
        ```multicol .block-blue
        toc[True]`### Contents`
        +++
        vspace`1` This is summary for current section created using block syntax of toc. See `Slides.xmd.syntax` for details.

        - Item 1
        - Item 2

        $$ E = mc^2 $$ 
        %{btn}  

        ::: note-tip
            Above `btn` variable can be updated later via `Slides[number,].vars.update` method.                 
        ```                                
    """,btn=slides.draw_button)

    # Matplotlib
    with slides.build_() as sl:
        slides.write('## Plotting with Matplotlib section`Plotting and DataFrame`')
        with slides.code.context(returns = True) as s:
            sl.set_css(bg1 = 'linear-gradient(to right, #FFDAB9 0%, #F0E68C 100%)')

            import numpy as np, matplotlib.pyplot as plt
            plt.rcParams['svg.fonttype'] = 'none' # Global setting, enforce same fonts as presentation
            x = np.linspace(0,2*np.pi)
            with plt.style.context('ggplot'):
                fig, ax = plt.subplots(figsize=(3.4,2.6))
                _ = ax.plot(x,np.cos(x))
            slides.write(ax, s.focus([0,3,4]))
            slides.write('Double click on the plot to focus on it!')


    # Plotly and Pandas DataFrame only show if you have installed
    with slides.code.context(returns = True) as source:
        try:
            import pandas as pd 
            df = pd.read_csv('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv')
            df = df.describe() #Small for display
        except:
            df = '### Install `pandas` to view output'

    slides.build(-1, lambda s: slides.write(['## Writing Pandas DataFrame', df, source]))
    
    with slides.code.context(returns = True) as source:
        try:
            import ipywidgets as ipw
            import plotly.graph_objects as go

            fig = slides.patched_plotly(go.FigureWidget()) # prefere Widget for interactivity and correct display
            fig.add_trace(go.Bar(y=[1,5,8,9], customdata=["A","B"]))
            
            # We have clicked and selected traits on patched plotly
            html = ipw.HTML()

            def observe_click(change):
                html.value = "<br/>".join(f"  {k} = {v}" for k, v in change['new'].items())

            fig.observe(observe_click, names='clicked')
            box = ipw.HBox([fig, html])

        except:
            box = '### Install `plotly` to view output'

    slides.build(-1,lambda s: slides.write(['## Writing Plotly Figure',box, source]))

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
        
        def display_plot(btn): return race_plot().display()
        
        slides.write(
            slides.dl.interactive(display_plot, btn = slides.dl.button('Refresh Plot', icon='refresh')), 
            rslide.get_source()
        ) # Only first columns will update

    with slides.build(-1) as s:
        slides.write('## Animations with Widgets')
        anim = slides.AnimationSlider(nframes=20, interval=100, continuous_update=False)
        css = {'grid-template-columns': '1fr 2fr', '.out-main': {'height': '2em'}}

        @slides.dl.interact(post_init = lambda self: self.set_css(css), html = slides.as_html_widget(''), source=s.get_source().as_widget(), anim=anim)
        def _(html, source, anim):
            html.value = race_plot().value
            print(f'Animation Frame: {anim}') # goes to output area

    with slides.build(-1) as s:
        import numpy as np
        import matplotlib.pyplot as plt

        def plot_sine():
            plt.plot(np.sin(np.linspace(0,10,100)))

        lw = slides.ListWidget(description='Execute a code block',
            options = [
                lambda: print(np.random.random((10,2))),
                lambda: plt.plot(np.random.random((10,2))),
                plot_sine,
            ], transform = lambda value: slides.code(value).inline.value # need simple code, otherwise defult transform is fine
        )

        def run(c):
            if callable(c): c() # avoid None value when not selected
            plt.show()
        
        css = {'.out-main': {'height':'300px'}, 'grid':'auto-flow / 1fr', '.lang-name': {'display': 'none'}} # just single column
        it = slides.dl.interactive(run, c = lw, post_init = lambda self: self.set_css(css)) 
        slides.write(['### Rich Content code`ListWidget`', it],s.get_source())


    slides.build(-1,'section`Simple Animations with Frames` toc`### Contents`')

    skipper = slides.link('Skip All Next Frames', 'Skip Previous Frames', icon='arrowr', back_icon='arrowl')
    
    # Animat plot in slides  
    with slides.build_():
        slides.write("## Animating Matplotlib!", skipper.origin)

        with slides.code.context(returns = True) as s:
            for idx in slides.PAGE.iter(range(10,19)):
                fig, ax = plt.subplots(figsize=(3.4,2.6))
                x = np.linspace(0,idx,50)
                ax.plot(x,np.sin(x))
                ax.set_title(rf'$f(x)=\sin(x)$, 0 < x < {idx+1}')
                ax.set_xlim([0,18])
                ax.set_axis_off()
                slides.write(s.focus([idx - 10]),ax,widths=[60,40])

                if idx == 10:
                    slides.write('Unlike `interact/interactive`, this animation is based on slide frames, all of which are exported to HTML.',css_class='note-tip')

    slides.build(-1,'section`Controlling Content on Frames` toc`### Contents`')

    # Frames structure
    boxes = [slides.html('h1', f"{c}",style="background:var(--bg3-color);margin-block:0.05em !important;") for c in range(1,5)]
    with slides.build(-1) as s:
        slides.write('# Frames with \n#### code`PAGE.iter()` and Fancy Bullet List yoffset`0`')
        s.get_source().focus([2,3,4]).display()
        slides.PAGE() # want to show source alone first
        for item in slides.PAGE.iter(boxes):
            slides.bullets([item], marker='💘').display()

    with slides.build(-1) as s:
        slides.write('# Frames with \n#### code`PART.iter()` and 2x2 grid of boxes')
        s.get_source().focus(range(2,7)).display()
        objs = [boxes[:2],boxes[2:]]
        widths = [(1,3),(3,2)]
        for ws, cols in slides.PART.iter(zip(widths,objs)):
            slides.write(*cols, widths=ws)

    # Youtube
    from IPython.display import YouTubeVideo
    with slides.build(-1) as ys: # We will use this in next %%magic
        skipper.target.display()
        
        slides.write(f"### Watching Youtube Video?")
        slides.write('**Want to do some drawing instead?** Click on button on the right!', slides.draw_button, widths=[3,1])

        slides.write(
            YouTubeVideo('thgLGl14-tg',width='100%',height='266px'),
            YouTubeVideo('XZt-lH8Za3Q',width='100%',height='266px'),
        )

        @slides.on_load
        def push(slide):
            import time
            t = time.localtime()
            slides.notify(f'You are watching Youtube on slide {slide.index} at Time-{t.tm_hour:02}:{t.tm_min:02}')

        ys.get_source().display(True) 


    with slides.build(-1) as s:
        import ipywidgets as ipw
        slides.write('## Blocks with CSS classes')
        slides.write(
            [
                '### Table',
                '''
                ::: table 1 2 1 width=100%
                    |h1 |h2 |h3 |
                    |---|---|---|
                    |d1 |d2 |d3 |
                    |r1 |r2 |r3 |
                
                line`200`
                ### A rich content table
                ''',
                slides.table([[slides.icon('loading'), 2,3],[3,'code`import numpy as np`', 5]],headers=['h1','h2','h3'],widths=[3,5,1]),
            ], 
            [
                '### Widgets',
                slides.alt(lambda w: f'<input type="range" min="{w.min}" max="{w.max}" value="{w.value}">', ipw.IntSlider()), 
                slides.alt('<button>Click to do nothing</button>', ipw.Button(description='Click to do nothing')), 
                ipw.Checkbox(description='Select to do nothing',indent=False), 
            ], css_class="block-red"
        )
        s.get_source().display(True)

    slides.build(-1, r'''
    ## $ \LaTeX $ in Slides
    Use `$ $` or `$$ $$` to display latex in Markdown, or embed images of equations
    $ \LaTeX $ needs time to load, so keeping it in view until it loads would help.
    {.info}
                                
    --                           
    ::: note-tip
        Varibale formatting alongwith $ \LaTeX $ alert`\%{var} → %{var}` is seamless.
    
    --
    ::: md-src.collapsed
        ++
        ```multicol 50 50
        $$ \int_0^1\\frac{1}{1-x^2}dx $$
        {.align-left .text-big .info}
        +++
        ::: success
            $$ ax^2 + bx + c = 0 $$
            {.text-huge}
        ```
    <md-src/>
    ''', var = "'I was a variable'")

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
        slides.write(f'## This is all code to generate slides section`Code to Generate Slides`\n{slides.esc(slides.demo)}')
        slides.code.cast(__file__).display()

    slides.build(-1, lambda s: slides.get_source().display())

    slides.navigate_to(0) # Go to title slide

    return slides