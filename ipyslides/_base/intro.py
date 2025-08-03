from .icons import Icon as _Icon

# ONLY INSTRUCTIONS BELOW

def get_logo(height="60px", text = None):
    width = 250 if text else 50
    V = text if isinstance(text, str) else ''
    return f'''<svg height="{height}" viewBox="0 0 {width} 50" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-linecap="butt" stroke-linejoin="round" stroke-width="7.071067811865476">
        <path d="M22.5 7.5L10 20L20 30L30 20L40 30L27.5 42.5" stroke="#43D675"/>
        <path d="M7.5 27.5L22.5 42.5" stroke="#4F8EF7"/>
        <path d="M32.5 32.5L20 20L30 10L42.5 22.5" stroke="#4F8EF7"/>
        <text x="55" y="37.5" stroke-width="0" fill="currentColor" style="font-size:1.5em;font-weight:bold;">{V}</text>
    </svg>'''


how_to_slide = r"""#### Creating Slides
```python
import ipyslides as isd 
slides = isd.Slides()
```
```python
%%slide 0
# You can use `with slides.build(0):` contextmanager for it as well.
```
```python
%%slide 1
# slide 1 content
# You can use `with slides.build(1):` contextmanager for it as well.
```
```python
%%slide 2 -m 
**Markdown here with extended options (see `slides.xmd.syntax` for info). Nested blocks are not supported**
 ```multicol 30 70 .success
 less content
 +++
 more content
 ```
```


```python
with slides.build(-1):
    print("I will be on all frames in any case")
    slides.fsep()
    print("-1 will pick latest slide number!")
    slides.fsep(stack=True)
    print("I will be incremented to previous content becuase stack=True in line above!")
```

```python
slides.build(-1, slides.fmt('''
Markdown content can create many slides at once here!
fmt can encapsulate varaiables like \%{var}.
This is useful inside python scripts. Markdown not encapsulated
by fmt can be used to update varaiables from notebook later.
''',var="I am a variable"))
```

```python
slides # This displays slides if on the last line of cell, or use code`slides.show()`.
```

::: note-info
    - Use `-1` in place of a slide number to add numbering automatically in Jupyter Notebook and python file! Other cell code is preserved. You may need to rerun cell if creating slides in a for loop.

::: note-tip
    - Use `Slides.docs` to see upto date documentation.
    - Use `Slides.demo` to create example slides.
    - Use  `Slides.sync_with_file` to live edit and update slides through a markdown file.
    - Find special syntax to be used in markdown by `Slides.xmd.syntax`.
    - Use `Slides.xmd.extensions` to add [markdown extensions](https://python-markdown.github.io/extensions/). Also look at [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
"""

_icons = {key: _Icon(key, color="var(--accent-color)") for key in _Icon.available}

def _key(k): # other properties in CSS
    return f'<kbd style="min-width:2em;text-align:center;display:inline-block;">{k}</kbd>'


key_maps = {
    "▸, Space": "Next slide",
    "◂, Ctrl + Space": "Previous slide",
    "Z": "Toggle objects zoom mode",
    "P": "Print PDF of current slide",
    "F": "Toggle fullscreen",
    "Esc": "Exit fullscreen",
    "S": "Toggle settings panel",
    "L": "Toggle LASER pointer",
    "E": "Edit Source Cell/View Variables", 
    "K": "Show keyboard shortcuts",
}

key_combs = f"""
| Shortcut                                    | Button                                            | Action                 | 
|:--------------------------------------------|---------------------------------------------------|:-----------------------|
| {_key('&#9141;')}/{_key('▸')}               | {_icons["chevronr"]}                              | Move to next slide     |
| {_key('Ctrl')} + {_key('&#9141;')}/{_key('◂')} | {_icons["chevronl"]}                           | Move to previous slide |
| {_key('Ctrl')} + {_key('0')}/{_key('0')}    | {_icons['arrowbl']}/{_icons['arrowbr']}       | Jump to Star/End of slides |
| {_key('Ctrl')} + {_key('[1-9]')}/{_key('[1-9]')} |                                       | Shift [1-9] slides left/right |
| {_key('Z')}                                 | {_icons["zoom-in"]}, {_icons["zoom-out"]}         | {key_maps["Z"]}        |
| {_key('F')}                                 | {_icons["expand"]}, {_icons["compress"]}          | {key_maps["F"]}        |
| {_key('Esc')}                               |                                                   | {key_maps["Esc"]}      |
| {_key('S')}                                 | {_icons["settings"]}, {_icons["close"]}           | {key_maps["S"]}        |
| {_key('E')}                                 | {_icons["code"]}                                  | {key_maps["E"]}        |
| {_key('L')}                                 | {_icons["laser"]}, {_icons["circle"]}             | {key_maps["L"]}        |
| {_key('K')}                                 |                                                   | {key_maps["K"]}        |
""" 

how_to_print = f"""
You can also get PDF from exported HTML file. Use `Save as PDF` and enable background graphics when printing to keep links working.

For widgets and other objects's snapshots to be available in exported
slides, use alert`Slides.alt`. You can paste screenshots from system tool 
into Clips GUI in side panel. On Linux, you need alert` xclip ` or alert`wl-paste` installed.

::: note-tip
    - You might want to reflow content for export purpose. Use checkbox in settings panel to enable it.
    - In case of Inherit theme selected, you can ensure Jupyterlab colors in exported HTML by rerunning `export_html` or reclicking export button.
"""
more_instructions = f"""{get_logo('2em', 'IPySlides')}
::: note-tip
    - In JupyterLab, right click on the slides and select `Create New View for Output` for optimized display.
    - To jump to source cell and back to slides by clicking buttons, set `Windowing mode` in Notebook settings to `defer` or `none`.

**Key Bindings**{{.success}} {_Icon("pencil", color="var(--accent-color)", rotation=45)}

{key_combs}

#### PDF Printing
{how_to_print}

{how_to_slide}

::: note-warning
    Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
"""

instructions = f"""{more_instructions}
#### Custom Theme
For custom themes, use `Slides.settings.theme.colors`.
          
For matching plots style with theme, run following code in a cell above slides.

**Matplotlib**{{.success}}
```python
import matplotlib.pyplot as plt
plt.style.use('ggplot')
#plt.style.available() #gives styles list
plt.rcParams['svg.fonttype'] = 'none' # or 'path' Enforces same fonts in plots as in presentation slides or use
```

**Plotly**{{.success}}
```python
import plotly.io as pio
pio.templates.default = "plotly_white"
#pio.templates #gives list of styles
```
Wrap your plotly figures in `plotly.graph_objects.FigureWidget` for quick rendering.
{{.note-info}}

**Altair**{{.success}}
```python
import altair as alt
alt.themes.enable('dark')
#alt.themes #gives available themes
```

#### Inherit Slides
You can customize slides by inheriting from `Slides` class. 

```python
class WorkSlides(isd.Slides):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings(
            logo=dict(src='<My office logo source file>'),
            layout=dict(aspect=4/3, center=False),
        )
```
"""
