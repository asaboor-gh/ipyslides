# ipyslides
Create Interactive Slides in Jupyter Notebook with all kind of rich content. 

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