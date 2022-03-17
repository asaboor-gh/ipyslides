# IPySlides
Create Interactive Slides in [Jupyter](https://jupyter.org/)/[Voila](https://voila.readthedocs.io/en/stable/) with all kind of rich content. 

- Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=lab%2Ftree%2Fnotebooks%2Fipyslides.ipynb)
- See a [Demo Notebook at Kaggle](https://www.kaggle.com/massgh/ipyslides). 
- See [PDF-Slides](IPySlides-Print.pdf)
![Overview](overview.jpg)

# Changelog
Above version 1.4.0, users can see upto date documentation via `ipyslides.LiveSlides().load_docs()`, so no additional changelog will be created in future. 
See old [changelog](changelog.md)

# Install
```shell
> pip install ipyslides >= 1.4.1
```
For development install, clone this repository and then
```shell
> cd ipyslides
> pip install -e .
```
# Creating Slides
> Tip: You can use `ipyslides.LiveSlides().demo()` to create example slides and start editing.

```python
#------------ Cell 1 --------------------
import ipyslides as isd 
ls = isd.LiveSlides()
ls.convert2slides(True)
ls.settings.set_animzation('zoom') 
#------------ Cell 2 --------------------
%%title
# create a rich content title page
#------------ Cell 3 --------------------
%%slide 1
# slide 1 content
#------------ Cell 4 --------------------
@ls.frames(1,*objs)
def func(obj):
    write(obj) #This will create as many slides after the slide number 1 as length(objs)
#------------ Cell 5 --------------------
ls # This displays slides if on the last line of cell, or use `ls.show()`.
```
#### You can load slides from a markdown file
slides separator should be --- (three dashes)
```python
ls.from_markdown(path, footer_text = 'Author Name')
with ls.slide(2):
    write(ls.md_content[2]) # write content of slide 2 from file
    plot_something() # Add other things to same file
    write_something()
```

#### You can see documentation slides with:
```python
ls.load_docs()
```

# Content Types to Embed
You can embed anything that you can include in Jupyter notebook like ipywidgets,HTML,PDF,Videos etc.,including jupyter notebook itself! 

> Note: Websites may refuse to load in iframe.

## IPython Display Objects
Any object with following methods could be in `write` command:
`_repr_pretty_`, `_repr_html_`, `_repr_markdown_`, `_repr_svg_`, `_repr_png_`, `_repr_jpeg_`, `_repr_latex_`, `_repr_json_`, `_repr_javascript_`, `_repr_pdf_`
Such as `IPython.display.<HTML,SVG,Markdown,Code>` etc. or third party such as `plotly.graph_objects.Figure`.

## Plots and Other Data Types (0.8.7+)
These objects are implemented to be writable in `write` command:
`matplotlib.pyplot.Figure`, `altair.Chart`, `pygal.Graph`, `pydeck.Deck`, `pandas.DataFrame`, `bokeh.plotting.Figure`.
Many will be extentended in future. If an object is not implemented, use `display(obj)` to show inline or use library's specific command to show in Notebook outside `write`.

## Interactive Widgets
Any object in `ipywidgets` or libraries based on `ipywidgtes` such as `bqplot`,`ipyvolume`,plotly's `FigureWidget`
can be included in `iwrite` command. `iwrite` also renders other objects except Javascript.
# Full Screen Presentation
- Jupyterlab 3.0+ has full screen eneabled from any view:
- Use [Voila](https://voila.readthedocs.io/en/stable/) for full screen prsentations. Your notebook remains same, it is just get run by Voila, may not work as expected.     

- Slides in Jupyter Lab are theme aware in `Inherit` theme mode, so theme of slides changes based on editor theme.

# PDF printing
Read instructions in side panel about PDF printing. See [PDF-Slides](IPySlides-Print.pdf)
# Speaker Notes (1.2.0+) (Experimental)
- You can turn on speaker notes with a `Show Notes` check in side panel. Notes can be added to slides using `ls.notes.insert` (`ls.notes` in < 1.2.1) command. 
- Notes is an experimantal feuture, so use at your own risk. Do not share full screen, share a brwoser tab for slides and you can keep notes hidden from audience this way. 
# Known Limitations
- Slide number is necessary to be tracked by user, as notebook cells are not linked to each other and multiple runs of a cell can lead to adding many slides with same content. 
- Bounding box of slides for screenshots should be set by user (if not in fullscreen).

# Customize Slides
You can customize slides by inheriting from `LiveSlides` class. 
For example if you want to have custom theme and some other settings always enabled and
bottom information only on title slide, you can do so:
```python
class CustomSlides(isd.LiveSlides):
    def __init__(self):
        super().__init__()
        self.settings.theme_dd.value = 'Custom'
        self.progress_slider.observe(self.set_visible, names=['index'])
    
    def set_visible(self, change):
        if self.progress_slider.index == 0:
            self.widgets.footerbox.layout.visibility = 'visible'
        else:
            self.widgets.footerbox.layout.visibility = 'hidden'
```

> Very thankful to [Python-Markdown](https://python-markdown.github.io/) which enabled to create `write` command as well as syntax highliting.