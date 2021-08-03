# ipyslides
Create Interactive Slides in [Jupyter](https://jupyter.org/)/[Voila](https://voila.readthedocs.io/en/stable/) with all kind of rich content. 

# Install
```shell
> pip install ipyslides
```
For development install, clone this repository and then
```shell
> cd ipyslides
> pip install -e .
```

# Usage
```python
import ipyslides as isd 

isd.initilize() #This will create a title page and parameters in same cell

isd.insert(1) #This will create a slide in same cell where you run it 

isd.insert_style() #This will create a %%html cell with custom style

isd.insert_after(1) #This will create as many slides after the slide number 1 as length of list/tuple at cell end

isd.build() #This will build the presentation cell. After this go top and set __slides_mode = True and run all below.
```
> Each command is replaced by its output, so that when you run next time, you don't get duplicate slides. 

> For jupyterlab >= 3, do pip install sidecar for better presenting mode.

![LiveSlides](liveslides.gif)

## Content Types to Embed
You can embed anything that you can include in Jupyter notebook like ipywidgets,HTML,PDF,Videos etc.,including jupyter notebook itself! I am not kidding, see ![JupyterLab inside ipyslides](jlabslides.gif)
> Note: Websites may refuse to load in iframe. Jupyterlab was loaded inside itself, but refused in Voila. 

# Full Screen Presentation
- Use [Voila](https://voila.readthedocs.io/en/stable/) for full screen prsentations. Your notebook remains same, it is just get run by [Voila](https://voila.readthedocs.io/en/stable/).     
[Jupyterlab-Sidecar](https://github.com/jupyter-widgets/jupyterlab-sidecar) does not give 100% full screen experience but it is more useful in context of content types you can use e.g. showing magic of codeing inside slides!