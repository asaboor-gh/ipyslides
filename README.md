<svg width="60px" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-linecap="butt" stroke-linejoin="round" stroke-width="7.071067811865476">
   <path d="M22.5 7.5L10 20L20 30L30 20L40 30L27.5 42.5" stroke="teal"/>
   <path d="M7.5 27.5L22.5 42.5" stroke="crimson"/>
   <path d="M32.5 32.5L20 20L30 10L42.5 22.5" stroke="red"/>
</svg>

# IPySlides

Create interactive slides programatically in [Jupyter](https://jupyter.org/)/[Voila](https://voila.readthedocs.io/en/stable/) with all kind of rich content. 

- Launch Example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides/HEAD?labpath=demo.ipynb)
- See a [Demo Notebook](https://www.kaggle.com/massgh/ipyslides) at [Kaggle](https://www.kaggle.com/massgh)
- Watch a [Youtube Video](https://www.youtube.com/watch?v=thgLGl14-tg)
- See [PDF-Slides](Slides.pdf)
- See [PDF-Report](Report.pdf)
![Overview](slide.png)

---
# Changelog
You can see upto date documentation via `ipyslides.Slides().docs()`, so no additional changelog is created.

---
# Install
```shell
> pip install ipyslides
> pip install ipyslides[extra]
```
For development install, clone this repository and then
```shell
> cd ipyslides
> pip install -e .
```

---
# How to Use
- In Jupyter Notebook, do the follwoing:
```python
%load_ext ipyslides # It will display info to move further
slides = get_slides_instance()
```
- Above is equivalent to:
```python
import ipyslides as isd
slides = isd.Slides()
```
---

# Creating Slides
Please look at two presentations provided with `Slides.docs()`, `Slides.demo()` to see how slides are created. Moreover instruction in settings panel are at your finger tips.


---
# Content Types to Embed
You can embed anything that you can include in Jupyter notebook like ipywidgets, HTML, PDF, Videos etc.,including jupyter notebook itself! 

- IPython Display Objects, see `IPython` module.
- Plots and Other Data Types (matplotlib, plotly etc.)
- Jupyter Interactive Widgets (ipywidgets, bqplot ect.)
- Custom and Third Party Objects( which are not implemented in this library)
    - You can display with `display` command or library's specific display method.
    - You can serialize custom objects to HTML using `Slides.serializer` API.
- You can extend markdown syntax using `Slides.extender` API. See some good extensions to add from [PyMdown](https://facelessuser.github.io/pymdown-extensions/).


---
# PDF printing
To include all type of objects you need to make PDF manually.
Read instructions in side panel about PDF printing. See [PDF-Slides](IPySlides-Print.pdf)
If you just have HTML objects like `matplotolib plots`, `images`, `plotly`, `bokeh` charts etc. and not something like `ipywidgets`, see next section.

---
# HTML/PDF Report/Slides
- You can create beautiful HTML/PDF report from slides using `slides.export.report`. See [PDF-Report](IPySlides-Report.pdf)
- Use `slides.export.slides` to build static slides that you can print as well.
- Content variety for export is limited. Widgets can not be exported unless an alternative representation is given by `Slides.alt(widget, func(widget))`.
- Paper width for printing is 10 inch (254mm) and height is determined by aspect ration dropdown in settings panel.
- Use `Save as PDF` in browser to make links work in ouput PDF.

---
# Speaker Notes
- You can turn on speaker notes with a `Show Notes` check in setting panel. See module `Slides.notes` for details or see examples in `Slides.demo()`. 

> Notes is an experimantal feature, so use at your own risk. Avoid if you can.

---
# Known Limitations
- Since Markdown is parsed using python (and we do not run notebook from outside e.g. with nbconvert), markdown cells are of no use. You can still write markdown there and then convert to code cell with slide magic `%%slide number -m` to add to slides. 
- Slide number is necessary to be tracked by user in notebook, because cells are not linked to each other and multiple runs of a cell can lead to adding many slides with same content. Inside python scripts that run in linear fashion, you can use `Slides.AutoSlide().[title,slide,frames,from_markdown]`.
- Bounding box of slides for screenshots should be set by user (if not in fullscreen).

---

# Acknowledgements
- Slides application is based on [ipywidgets](https://github.com/jupyter-widgets/ipywidgets).
- Rich display mechanism, and collection of cell output to slides heavily rely on [IPython](https://github.com/ipython/ipython).
- [Python-Markdown](https://python-markdown.github.io/) is extensily used for content and extended where needed.
