from .icons import Icon as _Icon, _icons

# ONLY INSTRUCTIONS BELOW

def get_logo(height="60px", text = None):
    width = 250 if text else 50
    V = text if isinstance(text, str) else ''
    return f'''<svg height="{height}" viewBox="0 0 {width} 50" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-linecap="butt" stroke-linejoin="round" stroke-width="7.071067811865476">
        <path d="M22.5 7.5L10 20L20 30L30 20L40 30L27.5 42.5" stroke="teal"/>
        <path d="M7.5 27.5L22.5 42.5" stroke="crimson"/>
        <path d="M32.5 32.5L20 20L30 10L42.5 22.5" stroke="red"/>
        <text x="55" y="37.5" stroke-width="0" fill="currentColor" style="font-size:1.5em;font-weight:bold;">{V}</text>
    </svg>'''


how_to_slide = """#### Creating Slides
```python
import ipyslides as isd 
slides = isd.Slides()
```
```python
%%title
# create a rich content title page
```
```python
%%slide 1
# slide 1 content
```
```python
%%slide 2 -m 
**Markdown here with extended options (see `slides.xmd_syntax` for info). Nested blocks are not supported**
 ```multicol 30 70 .success
 less content
 +++
 more content
 ```
```

```python
@slides.frames(3,*objs)
def func(frame_index, frame_content):
    write(frame_content) #This will create as many slides after the slide number 1 as length(objs)
```
```python
slides # This displays slides if on the last line of cell, or use `slides.show()`.
```

::: note-info
    - You can use context managers like `with slides.slide(): ...` and `with slides.title(): ...` in place of `%%slide` and `%%title` respectively.
    - Inside python script, you can use auto numbering with `Slides.[next_number|next_slide|next_frames|next_from_markdown]`.

::: note-tip
    - Use `Slides.docs` to see upto date documentation.
    - Use `Slides.demo` to create example slides.
    - Use  `Slides.sync_with_file` to live edit and update slides through a markdown file.
    - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
    - Use `Slides.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/). Also look at [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
"""

_icons = {key: _Icon(key, color="var(--accent-color)") for key in _icons}
for k, r in zip("RLUD", [0, 180, -90, 90]):  # clockwise rotation sucks!
    _icons[k] = _Icon("chevron", color="var(--accent-color)", rotation=r)


def _key(k): # other properties in CSS
    return f'<kbd style="min-width:2em;text-align:center;display:inline-block;">{k}</kbd>'


key_maps = {
    "▸, Space": "Next slide",
    "◂, Ctrl + Space": "Previous slide",
    "Z": "Toggle objects zoom mode",
    "S": "Take screenshot",
    "P": "Print PDF of current slide",
    "F": "Toggle fullscreen",
    "Esc": "Exit fullscreen",
    "V": "Toggle fit to viewport [voila only]",
    "G": "Toggle settings panel",
    "L": "Toggle LASER pointer",
    "E": "Edit Source Cell of Current Slide", 
    "K": "Show keyboard shortcuts",
}

key_combs = f"""
| Shortcut                                    | Button                                            | Action                 | 
|---------------------------------------------|---------------------------------------------------|------------------------|
| {_key('&#9141;')}/{_key('▸')}               | {_icons["R"]}, {_icons["D"]}                      | Move to next slide     |
| {_key('Ctrl')} + {_key('&#9141;')}/{_key('◂')} | {_icons["L"]}, {_icons["U"]}                   | Move to previous slide |
| {_key('Ctrl')} + {_key('0')}/{_key('0')}    | {_key('⇤')}/{_key('⇥')}                      | Jump to Star/End of slides |
| {_key('Ctrl')} + {_key('[1-9]')}/{_key('[1-9]')} |                                       | Shift [1-9] slides left/right |
| {_key('Z')}                                 | {_icons["zoom-in"]}, {_icons["zoom-out"]}         | {key_maps["Z"]}        |
| {_key('S')}                                 | {_icons["camera"]}                                | {key_maps["S"]}        |
| {_key('F')}                                 | {_icons["expand"]}, {_icons["compress"]}          | {key_maps["F"]}        |
| {_key('Esc')}                               |                                                   | {key_maps["Esc"]}      |
| {_key('V')}                                 | {_icons["win-maximize"]}, {_icons["win-restore"]} | {key_maps["V"]}        |
| {_key('G')}                                 | {_icons["settings"]}, {_icons["close"]}           | {key_maps["G"]}        |
| {_key('E')}                                 | {_icons["code"]}                                  | {key_maps["E"]}        |
| {_key('L')}                                 | {_icons["laser"]}, {_icons["circle"]}             | {key_maps["L"]}        |
| {_key('K')}                                 |                                                   | {key_maps["K"]}        |
""" 

how_to_print = f"""
Screenshot of current state of slide can be taken by camera button in toolbar or by pressing {_key('S')}. 
Order of screenshots is preserved. To capture all slides screenshots, follow process as below.

- Press alert`Capture Screenshots of all Slides` button in side panel to capture a single image of each slide. 
    - Add images over it by manually capturing multiple states of a slide as shown above.
    - Delete screenshots with dropdown (all or current slide only and can retake).
- After all screenshots are ready:
    - Press alert`Set Crop Bounding Box` to crop an image which applies to all.
    - Press alert`Save as PDF File` button to save all cropped screenshots as PDF.

::: note-warning
    Avoid scrolling during taking screenshot. You will set same bounding box for all screenshots
    which can change position if scrolled.

::: note-tip
    You can also get PDF from exported HTML file, but can't have the freedom of capturing 
    many views of single slide.
"""
more_instructions = f"""{get_logo('2em', 'IPySlides')}
::: note-tip
    In JupyterLab, right click on the slides and select `Create New View for Output` for optimized display.

**Key Bindings**{{.success}} {_Icon("pencil", color="var(--accent-color)", rotation=45)}

{key_combs}

#### PDF Printing (by screen capture)
{how_to_print}

{how_to_slide}

::: note-warning
    Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
"""

instructions = f"""{more_instructions}
#### Custom Theme
For custom themes, use `Slides.settings.set_theme_colors` function.
          
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
    def __init__(self):
        super().__init__()
        self.apply(
            logo=dict(src='<My office logo source file>'),
            layout=dict(aspect=4/3, center=False),
        )
```
"""
