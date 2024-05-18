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


how_to_slide = """# Creating Slides
::: align-center
    alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`     
    center`today```

    ::: text-box
        sup`1`My University is somewhere in the middle of nowhere
        sup`2`Their University is somewhere in the middle of nowhere

::: note-warning
    Python 3.8+, ipywidgets 8+, IPython 8.7+ are required. Previous version 2.x.x will still be supported for bug fixes.

**After you initialize `slides = ipyslides.Slides()`**

- `%%slide integer` on cell top auto picks slide and `%%title` auto picks title page.
- `%%slide integer -m` can be used to create slide from full markdown (extended one).
- You can use context managers like `with slides.slide(): ...` and `with slides.title(): ...` in place of `%%slide` and `%%title` respectively.
- Inside python script, you can use auto numbering with `slides.AutoSlides().[get_next_number|title|slide|frames|from_markdown]`.

```python
import ipyslides as isd 
slides = isd.Slides()
slides.set_animation(main='flow') 
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
def func(obj):
    write(obj) #This will create as many slides after the slide number 1 as length(objs)
```
```python
slides # This displays slides if on the last line of cell, or use `slides.show()`.
```

Use `slides.from_markdown` to create multiple slides from markdown file/text.
    - Slides are added in order of content.
    - Slides should be separated by `---` (three dashes) in start of line.
    
```python .monokai
slides.from_markdown(start, content)
with slides.slide(2):
    write(slides[2].markdown) # write content of slide 2 from file
    plot_something() # Add other things to same file
    write_something()
```

::: note-tip
    - Use `Slides.demo` to create example slides.
    - Use `Slides.docs` to see upto date documentation.
    - Find special syntax to be used in markdown by `Slides.xmd_syntax`.
    - Use `Slides.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/). Also look at [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).

::: note-info
    - You can access individual slides by indexing `s_i = slides[i]` where `i` is the slide index or by key as `s_3_1 = slides['3.1']` will give you slide which shows 3.1 at bottom.
    - You can also access (preferred way) each slide by `slides.s8_1` that gives back slide with label 8.1 and so on.
    - Basides indexing, you can access current displayed slide by `slides.current`.
    - You can insert placeholders usign alert`proxy\`informative text to use later\`` and later can use `Slides.proxies[index].capture` to fill content such as plots.
    - If a display is not complete, e.g. some widget missing on a slide, you can use `(slides.current, slides[index], slides[key]).update_display()` to update display.
    - You can set overall animation by `slides.settings.set_animation` or per slide by `s_i.set_animation`
    - You can set CSS for each slide by `s_i.set_css` or `slides.running.set_css` at current slide.
    - Check out  alert`[Slides.settings, slide].set_bg_image` to add background effects overall and individual slides.
    - Use alert`Slides.clipboard_image ` to add cliboard image to slide.
    - Use `Slides.bullets` to add powerful bullet list from python objects.


::: note
    - You can add table of contents using using alert`toc\`Toc Title\``/alert`\`\`\`toc title \n summary of this section \n\`\`\`` and alert`section\`content\``.
    - Citations are provided with ` Slides.set_citations ` function that accept json file or dictionary. On next run, these are loaded from disk, so it works in python scripts and voila as well.
    - You can use `Slides.goto_button` to add a button to go to jump to a slide.
    - Inside a alert`\`\`\`python run` block in markdown, you can access `slides = get_slides_instance()` to get current slides instance and use all its methods.
    - In Custom Theme mode, you can set colors using `slides.settings.set_theme_colors`.
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

how_to_print = """
- Capture screenshot of current state of slide by camera button in toolbar or by pressing `S` key. 
    This will collect screenshots of current slide in order of capturing. 
- Press `Capture Screenshots of all Slides` button in side panel to capture a single image of each slide. 
    - Add images over it by manually capturing multiple states of a slide as shown in previous step.
    - Delete screenshots with dropdown in settings panel.
    - Set crop bounding box if not in fullscreen mode.
- Press `Save as PDF File` button to save all screenshots as PDF.

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

Having slides in focus, you can use follwoing keys/combinations:

{key_combs}
::: note
    - You can also swipe left/right from edges of screen ( within `±50px` edge range) on touch devices to change slides.
    - In exported slides, bottom-right includes few buttons to jump accross slides.

::: note-tip
    - Other keys are blocked so that you may not delete or do some random actions on notebook cells.
    - Jupyter[Retro, Notebook, Lab]/Voila is optimized for keyboard. Other frontends like VSCode, may not work properly.
    - Pressing `S` to save screenshot of current state of slide. Different slides' screenshots are kept in order.

### PDF Printing (by Screen Capture)
{how_to_print}

{how_to_slide}

::: note-info
    Slides should be only in top cell as it collects slides in local namespace, auto refresh is enabled.

::: note-warning
    Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
"""

instructions = f"""{more_instructions}
### Custom Theme
For custom themes, change below `Theme` dropdown to `Custom` and use `Slides.settings.set_theme_colors` to set colors.
          
--------
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

### Customize Slides
You can customize slides by inheriting from `Slides` class. 
For example if you want to have custom settings always enabled and
bottom information only on title slide, you can do so:
```python
class CustomSlides(isd.Slides):
    def __init__(self):
        super().__init__()
        self.settings.theme_dd.value = 'Custom' # Requires to set_theme_colors or will be Light theme
        self.progress_slider.observe(self.set_visible, names=['index'])
    
    def set_visible(self, change):
        if self.progress_slider.index == 0:
            self.widgets.footerbox.layout.visibility = 'visible'
        else:
            self.widgets.footerbox.layout.visibility = 'hidden'
```
"""
