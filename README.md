# IPySlides
Create Interactive Slides in [Jupyter](https://jupyter.org/)/[Voila](https://voila.readthedocs.io/en/stable/) with all kind of rich content. 

Launch example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=lab%2Ftree%2Fnotebooks%2Fipyslides.ipynb)

![Overview](overview.jpg)

# 0.8.4 Cangelog
- Keyboard and touchscreen navigation could be enabled using `LiveSlides.enable_navigation_javascript()`.
- `@slides(...,calculate_now=True)` could be used to calculate slides in advance or just in time. Default is `True`.   

# 0.8.3 Changelog
If you have `ls = LiveSlides()`:
- You can now use `ls.cite` method to create citations which you can write at end by `ls.write_citations` command.
- `ls.insert_after` no longer works, use 
```python
@ls.slides(after_slide_number,*objs)
def func(obj):
    write(obj) #etc. for each obj in objs
```
decorator which is more pythonic way. 
# Changes in Version 0.8
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

# Full Screen Presentation
- Jupyterlab 3.0+ has full screen eneabled from any view:
    - Direct output of cell can be turned into fullscreen.
    - Linked output view using `Create New Output View` command is very useful, so you can edit and see output right there. 
    - If you have installed [Jupyterlab-Sidecar](https://github.com/jupyter-widgets/jupyterlab-sidecar), slides automatically open in it.
- Use [Voila](https://voila.readthedocs.io/en/stable/) for full screen prsentations. Your notebook remains same, it is just get run by Voila, may not work as expected.     

- Slides in Jupyter Lab are theme aware in `Inherit` theme mode, so theme of slides changes based on editor theme.


> Very thankful to [Python-Markdown](https://python-markdown.github.io/) which enabled to create `write` command as well as syntax highliting.