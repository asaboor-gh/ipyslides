<svg width="60px" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-linecap="butt" stroke-linejoin="round" stroke-width="7.071067811865476">
   <path d="M22.5 7.5L10 20L20 30L30 20L40 30L27.5 42.5" stroke="teal"/>
   <path d="M7.5 27.5L22.5 42.5" stroke="crimson"/>
   <path d="M32.5 32.5L20 20L30 10L42.5 22.5" stroke="red"/>
</svg>

# IPySlides

Create interactive slides programatically in [Jupyter](https://jupyter.org/)/[Voila](https://voila.readthedocs.io/en/stable/) with all kind of rich content. 

- Launch Example Notebook [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/massgh/ipyslides/HEAD?labpath=demo.ipynb)
- See [PDF-Slides](Slides.pdf)
![Overview](slide.png)
- Create cool animations like this one
![Animate](animate.gif)

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
In Jupyter Notebook:
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
# HTML/PDF Slides
- Use `slides.export_html` to build static slides that you can print as well.
- Content variety for export is limited. Widgets can not be exported unless an alternative representation is given by `Slides.alt` which also works to provide alternative export representation of any object.
- Any object including widget can be replaced for export using ` Slides.alt ` function which lets you paste a screenshot of that object or it's alternative html representation at runtime or export time.
- Paper width for printing is 10 inch (254mm) and height is determined by aspect ratio of slides.
- Use `Save as PDF` in browser to make links work in ouput PDF.

---
# Speaker Notes
- You can turn on speaker notes with a `Show Notes` check in setting panel. See module `Slides.notes` for details or see examples in `Slides.demo()`. 

> Notes is an experimantal feature, so use at your own risk. Avoid if you can.

---
# Caveats!
- Since Markdown is parsed using python (and we do not run notebook from outside e.g. with nbconvert), markdown cells are of no use. A better alternative is linking a markodwn file using `Slides.sync_with_file` and slides auto update when you save your edits. You can still write markdown in code cell with slide magic `%%slide number -m` to add to slides. 
- Slide number is necessary to be tracked by user in notebook, because cells are not linked to each other and multiple runs of a cell can lead to adding many slides with same content. To minimize this difficulty, use `-1` in place of a slide number to add numbering automatically in Jupyter Notebook and python file! Other cell code is preserved. You may need to rerun cell if creating slides in a for loop.

---

# Acknowledgements
- Slides application is based on [ipywidgets](https://github.com/jupyter-widgets/ipywidgets).
- Rich display mechanism, and collection of cell output to slides heavily rely on [IPython](https://github.com/ipython/ipython).
- [Python-Markdown](https://python-markdown.github.io/) is extensily used for content and extended where needed.
