# IPySlides
Create Interactive Slides in [Jupyter](https://jupyter.org/)/[Voila](https://voila.readthedocs.io/en/stable/) with all kind of rich content. 

Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=lab%2Ftree%2Fnotebooks%2Fipyslides.ipynb)

See [PDF-Slides](IPySlides-Print.pdf)
![Overview](overview.jpg)

# Changelog
Content below assumes you have `ls = LiveSlides()`.
# 1.0.0 (Working...)
- `ipyslides.initialize(**kwargs)` now returns a `LiveSlides` instance instead of changing cell contents. This works everywhere including Google Colab.
- `LiveSlides`,`initialize` and  `init` cause exit from a terminal which is not based on `IPython`.
- Markdown and other than slides output now does not appear (height suppressed using CSS) in Voila.
- Keyboard vavigation now works in Voila. (Tested on Voila == 0.2.16)
# 0.9.9
- Javascript navigation is improved for Jupyterlab.
- The decorator `ls.slides` is renamed as `ls.frames` and now it adds one slide with many frames. This is useful to reveal slide contents in steps e.g. bullet points one by one.
# 0.9.8
- PDF printing is optimized. See [PDF-Slides](IPySlides-Print.pdf). You can hover over top right corner to reveal a slider to change view area while taking screenshot. Also you can select a checkbox from side panel to remove scrolling in output like code.
- You can now display source code using context manager `slides.source`.
- You can (not recommended) use browser's print PDF by pressing key `P` in jupyterlab but it only gives you current slide with many limitations, e.g. you need to collect all pages manually.

# 0.9.6
- Code line numbering is ON by default. You can set `ls.code_line_numbering(False)` to turn OFF.
- Add slides in for loop using `slides.enum_slides` function. It create pairs of index and slides. 
#### PDF Printing (Tested on Windows)
- PDF printing is now available. Always print in full screen or set `bbox` of slides. Read instructions in side panel. [PDF-Slides](IPySlides-Print.pdf)

# 0.9.5
- You can now give `function/class/modules` etc. (without calling) in `write` and source code is printed.
- Objects like `dict/set/list/numpy.ndarray/int/float` etc. are well formatted now.
- Any object that is not implemented yet returns its `__repr__`. You can alternatively show that object using `display` or library's specific method. 

# 0.9.4
- Now you can set logo image using `ls.set_logo` function.
- LaTeX's Beamer style blcoks are defined. Use `ls.block(...,bg='color')`, or with few defined colors like `ls.block_r`, `ls.block_g` etc.
- `@ls.slides` no more support live calculating slides, this is to avoid lags while presenting. 
# 0.9.3
- Add custom css under %%slide as well using `ls.write_slide_css`.
- Slides now open in a side area in Jupyterlab, so editing cells and output can be seen side by side. No more need of Output View or Sidecar.
## 0.9.1
- In Jupyterlab (only inline cell output way), you can use `Ctrl + Shift + C` to create consoles/terminals, set themes etc.
- Use `Ctrl + Shift + [`, `Ctrl + Shift + ]` to switch back and forth between notebooks/console/terminals and enjoy coding without leaving slides!

## 0.8.11
- All utilities commnads are now under `LiveSlides` class too, so you can use either 
`ipyslides.utils.command` or `ls.command` for `command` in `write`,`iwrite`,`file2code` etc.
## 0.8.10
- You can add two slides together like `ls1 + ls2`, title of `ls2` is converted to a slide inplace. 
- You can now change style of each slide usig `**css_props` in commands like `@ls.slides`, `with ls.slide` and `with ls.title`. 
- A new command `textbox` is added which is useful to write inline references. Same can be acheived with `slides.cite(...here=True)`. 
- You can use `ls.alert('text')`, `ls.colored('text',fg,bg)` to highlight text.

## 0.8.7
- Support added for objects `matplotlib.pyplot.Figure`, `altair.Chart`, `pygal.Graph`, `pydeck.Deck`, `pandas.DataFrame`, `bokeh.plotting.Figure` to be directly in `write` command.
- `write` command now can accept `list/tuple` of content, items are place in rows.
## 0.8.5
- `@ls.slides(...,calculate_now=True)` could be used to calculate slides in advance or just in time. Default is `True`. 
- You can now use `ipyslides.utils.iwrite` to build complex layout of widgets like ipywidgets, bqplot etc. (and text using `ipyslides.utils.ihtml`).  

## 0.8.3
- You can now use `ls.cite` method to create citations which you can write at end by `ls.write_citations` command.
- `ls.insert_after` no longer works, use 
```python
@ls.slides(after_slide_number,*objs)
def func(obj):
    write(obj) #etc. for each obj in objs
```
decorator which is more pythonic way. 
## 0.8.0 +
> Note: All these points may not or only partially apply to earlier versions. So use stable API above version 8.
- Before this version, slides were collected using global namespace, which only allowed one presentation per
notebook. Now slides are stored in local namespace, so no restriction on number of slides per notebook.
- To acheive local namespace, functions are moved under class LiveSlide and it registers magics too. So now you will
be able to use `%%slide, %%title` magics. Now you will use context managers as follows
```python
ls = LiveSlides()
ls.convert2slides(True)

with ls.title():
    ...
with ls.slide(<slide number>):
    ...
ls.insert_after(<slide number>,*objs, func)
```
- `ipyslides.initialize()` can write all above code in same cell. 
> Note: For LiveSlides('A'), use %%slideA, %%titleA, LiveSlides('B'), use %%slideB, %%titleB so that they do not overwite each other's slides.
- You can elevate simple cell output to fullscreen in Jupyterlab >= 3.
- `with ls.slide` content manager is equivalent to `%%slide` so make sure none of them overwrite each other.

- Auto refresh is enabled. Whenever you execute a cell containing `%%title`, `with ls.title`, `%%slide`, `with ls.slide` or `ls.insert_after`, slides get updated automatically.
- LiveSlides should be only in top cell. As it collects slides in local namespace, it can not take into account the slides created above itself.

# Install
```shell
> pip install ipyslides>=0.8
```
For development install, clone this repository and then
```shell
> cd ipyslides
> pip install -e .
```
# Editable Demo
See a [Demo Notebook at Kaggle](https://www.kaggle.com/massgh/ipyslides). You can edit it yourself.



> For jupyterlab >= 3, do pip install sidecar for better presenting mode.

# Content Types to Embed
You can embed anything that you can include in Jupyter notebook like ipywidgets,HTML,PDF,Videos etc.,including jupyter notebook itself! 

> Note: Websites may refuse to load in iframe.
> Note: You can embed one intsnace of slides `ls1' inside other instance `ls2' using `ls2.insert_after(<N>,ls1.box)`. This is very cool.
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
can be included in `iwrite` command. Text/Markdown/HTML inside `iwrite` is made available through `ihtml` command.
# Full Screen Presentation
- Jupyterlab 3.0+ has full screen eneabled from any view:
    - Direct output of cell can be turned into fullscreen.
    - Linked output view using `Create New Output View` command is very useful, so you can edit and see output right there. 
    - If you have installed [Jupyterlab-Sidecar](https://github.com/jupyter-widgets/jupyterlab-sidecar), slides automatically open in it.
- Use [Voila](https://voila.readthedocs.io/en/stable/) for full screen prsentations. Your notebook remains same, it is just get run by Voila, may not work as expected.     

- Slides in Jupyter Lab are theme aware in `Inherit` theme mode, so theme of slides changes based on editor theme.

# Known Limitations
- Since `ipyslides` is built on ipywidgets and slides are displayed using `Output` widget, We do not have option to launch two windows to make speakernotes. If `Output` widget get enabled to function in multiwindows, we will introduce `speaker notes`.
- Slide number is necessary to be tracked by user, as notebook cells are not linked to each other and multiple runs of a cell can lead to adding many slides with same content. 
- Bounding box of slides for screenshots should be set by user (if not in fullscreen), because javascript may return incorrect value on scaled displays.  
> Very thankful to [Python-Markdown](https://python-markdown.github.io/) which enabled to create `write` command as well as syntax highliting.