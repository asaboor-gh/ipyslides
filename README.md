# einteract

[![](https://jupyterlite.rtfd.io/en/latest/_static/badge.svg)](https://asaboor-gh.github.io/einteract-docs/lab/index.html?path=einteract.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/asaboor-gh/einteract/HEAD?urlpath=%2Fdoc%2Ftree%2Feinteract-demo.ipynb)
[![PyPI version](https://badge.fury.io/py/einteract.svg)](https://badge.fury.io/py/einteract)
[![Downloads](https://pepy.tech/badge/einteract)](https://pepy.tech/project/einteract)

An enhanced interactive widget that lets you observe any trait of widgets, observe multiple functions and build beautiful dashboards which can be turned into full screen. This is a wrapper library around interact functionality in [ipyslides](https://github.com/asaboor-gh/ipyslides) which also provides rich content representations. 

![](interact.png)

See code of this simple yet fully customizable dashboard on binder [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/asaboor-gh/einteract/HEAD?urlpath=%2Fdoc%2Ftree%2Feinteract-demo.ipynb)

## Installation

You can install einteract using pip:

```bash
pip install einteract
```

Or if you prefer to install from source, clone the repository and in its top folder, run:

```bash
pip install -e .
```

## Interactive Playground
Run example on [![](https://jupyterlite.rtfd.io/en/latest/_static/badge.svg)](https://asaboor-gh.github.io/einteract-docs/lab/index.html?path=einteract.ipynb) and 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/asaboor-gh/einteract/HEAD?urlpath=%2Fdoc%2Ftree%2Feinteract-demo.ipynb)

## Features

- **InteractBase**: Create interactive dashboard applications with minimal code by extending the `InteractBase` class and defining methods with the `@callback` decorator.
- **Custom Widgets**: 
    - Included custom built widgets for enhanced interaction. 
    - Pass any DOMWidget as a parameter to `interact/interactive` functions unlike default `ipywidgets.interactive` behavior.
    - Observe any trait of the widget by `'widget_name.trait_name'` where `'widget_name'` is assigned to a `widget`/`fixed(widget)` in control parameters, OR `'.trait_name'` if `trait_name` exists on instance of interactive.
    - You can use '.fullscreen' to detect fullscreen change and do actions based on that.
    - Add `ipywidgets.Button` to hold callbacks which use it as paramter for a click
- **Plotly Integration**: Modified plotly support with additional traits like `selected` and `clicked`
- **HTML support**: 
    - Convert matplotlib plots to HTML format using `plt2html`.
    - Any (supported) python object can be converted to html using `html`, `hstack` and `vstack` function.
- **JupyTimer**: A non-blocking widget timer for Jupyter Notebooks without threading/asyncio.
- **Event Callbacks**: Easy widget event handling with the `@callback` decorator inside the subclass of `InteractBase` or multiple functions in `interact/interactive` functions.
- **Full Screen Mode**: Transform your dashboards into full-screen applications by added button.

## Usage Example

```python
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as ipw
import pandas as pd
import plotly.graph_objects as go
import einteract as ei

@ei.callback('out-click', throttle = 200) # limit click rate by 200 ms
def on_click(cdata,html):
    display(pd.DataFrame(cdata or {}))

def on_select(sdata, html):
    plt.scatter(sdata.get('xs',[]),sdata.get('ys',[]))
    html.value = ei.plt2html().value

def detect_fs(fig, fs):
    print("isfullscreen = ",fs)
    fig.layout.autosize = False # double trigger
    fig.layout.autosize = True

@ei.interact(
    on_select,
    on_click,
    detect_fs,
    fig = ei.patched_plotly(go.FigureWidget()), 
    html = ipw.HTML('**Select Box/Lesso on figure traces**'),
    A = (1,10), omega = (0,20), phi = (0,10),
    sdata = 'fig.selected', cdata = 'fig.clicked', fs = '.isfullscreen',
    app_layout={'left_sidebar':['A','omega','phi','html','out-main'], 'center': ['fig','out-click'],'pane_widths':[3,7,0]},
    grid_css={'.left-sidebar':{'background':'whitesmoke'},':fullscreen': {'height': '100vh'}}, 
    )
def plot(fig:go.FigureWidget, A, omega,phi): # adding type hint allows auto-completion inside function
    fig.data = []
    x = np.linspace(0,10,100)
    fig.add_trace(go.Scatter(x=x, y=A*np.sin(omega*x + phi), mode='lines+markers'))

```
![einteract.gif](einteract.gif)

## Comprehensive Examples
- Check out the [einteract-demo.ipynb](einteract-demo.ipynb) which demonstates subclassing `InteractBase`, using custom widgets, and observing multiple functions through the `@callback` decorator.
- See [Bandstructure Visualizer](https://github.com/asaboor-gh/ipyvasp/blob/d181ba9a1789368c5d8bc1460be849c34dcbe341/ipyvasp/widgets.py#L642) and [KPath Builder](https://github.com/asaboor-gh/ipyvasp/blob/d181ba9a1789368c5d8bc1460be849c34dcbe341/ipyvasp/widgets.py#L935) as comprehensive dashboards.
