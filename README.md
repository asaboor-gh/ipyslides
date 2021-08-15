# ipyslides
Create Interactive Slides in [Jupyter](https://jupyter.org/)/[Voila](https://voila.readthedocs.io/en/stable/) with all kind of rich content. 
  
Launch example slides at [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides-voila/HEAD?urlpath=voila%2Frender%2Fnotebooks%2Fipyslides-0-2-0.ipynb)

Launch in notebook mode 
[![Binder](https://mybinder.org/badge_logo.svg)](https://hub.gke2.mybinder.org/user/massgh-ipyslides-voila-s80b9whb/lab/tree/notebooks/ipyslides-0-2-0.ipynb)

![Overview](overview.jpg)

# Install
```shell
> pip install ipyslides
```
For development install, clone this repository and then
```shell
> cd ipyslides
> pip install -e .
```
# Demo
See a [Demo Notebook at Kaggle](https://www.kaggle.com/massgh/ipyslides),
[Version>0.2.0]https://www.kaggle.com/massgh/ipyslides-0-2-0)
![Slides2Video](kaggle.gif)

# Usage
```python
import ipyslides as isd 

isd.initilize() #This will create a title page and parameters in same cell

isd.write_title() #create a rich content multicols title page.

isd.insert(1) #This will create a slide in same cell where you run it 

isd.insert_after(1,*objs) #This will create as many slides after the slide number 1 as length(objs)

isd.build() #This will build the presentation cell. After this go top and set `convert2slides(True)` and run all below.
```
> Each command is replaced by its output, so that when you run next time, you don't get duplicate slides. 

> For jupyterlab >= 3, do pip install sidecar for better presenting mode.

## Content Types to Embed
You can embed anything that you can include in Jupyter notebook like ipywidgets,HTML,PDF,Videos etc.,including jupyter notebook itself! 
![JupyterLab inside ipyslides](jlabslides.gif)
> Note: Websites may refuse to load in iframe.

# Full Screen Presentation
- Use [Voila](https://voila.readthedocs.io/en/stable/) for full screen prsentations. Your notebook remains same, it is just get run by [Voila](https://voila.readthedocs.io/en/stable/).     
- Install [Jupyterlab-Sidecar](https://github.com/jupyter-widgets/jupyterlab-sidecar). Fullscreen support is added natively in version > 0.4!

# Multi Column Support
Starting version 0.2.0, you can use `MultiCols` class to display connected content like `ipwidgets` in columns. 

> Very thankful to [Python-Markdown](https://python-markdown.github.io/) which enabled to create `write` command as well as syntax highliting.