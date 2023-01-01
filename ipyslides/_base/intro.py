from .icons import Icon as _Icon, _icons

# ONLY INSTRUCTIONS BELOW

how_to_ppt = '''### How to make Powerpoint Presentation from Bunch of Images
- Save all screenshots using `Save PNG` button and go to folder just created.
- You know the aspect ratio while taking screenshots, if not, read details of any of picture to find it.
- Open Powerpoint, got to `Design` tab and select `Slide Size`. If pictures here are of aspect ration 4:3 or 16:9, select that,
otherwise select `Custom Slide Size` and change size there according to found aspect ratio. 
- You will see a slide of your prefered size now. Go to `Insert` tab and select `Photo Album > New Photo Album`.
- Select `File/Disk` option to insert pictures and make sure `Picture Layout` option is `Fit to slide`.
- Now click `Create` and you will see all pictures as slides.

Do not use PDF from Powerpoint as that will lower quality, generate PDF from slides instead. 
{.note-warning}
'''

how_to_slide = ('''# Creating Slides
::: align-center
    alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`     
    center`today```

    ::: text-box
        sup`1`My University is somewhere in the middle of nowhere
        sup`2`Their University is somewhere in the middle of nowhere


**Assuming you have `slides = ipyslides.Slides()`**

- Proceed to create slides:
    - `%%slide integer` on cell top auto picks slide and `%%title` auto picks title page.
    - `%%slide integer -m` can be used to create slide from full markdown (extended one).
    - You can use context managers like `with slides.slide(): ...` and `with slides.title(): ...` in place of `%%slide` and `%%title` respectively.

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
%%slide 1 -m # new in 1.4.6
**Markdown here with extended options (see `slides.xmd_syntax` for info). Nested blocks are not supported**
 ```multicol 30 70 .success
 less content
 +++
 more content
 ```
```

```python run source
x = 1 + 2
print(x) 
```
There is a python block above with header `python run source`. We can display that block by  &lcub;&lcub;source&rcub;&rcub; as below:
{{source}} 

variable `x` defined there is shown here x = {{x}}. Only variables can be embeded in &lcub;&lcub;var&rcub;&rcub;, not expressions.
```python
@slides.frames(1,*objs)
def func(obj):
    write(obj) #This will create as many slides after the slide number 1 as length(objs)
```
```python
slides # This displays slides if on the last line of cell, or use `slides.show()`.
```

- Use `slides.from_markdown` to create multiple slides from markdown file/text.
    - Slides are added in order of content.
    - Slides should be separated by `---` (three dashes) in start of line.
```python .monokai
slides.from_markdown(path)
with slides.slide(2):
    write(slides[2].markdown) # write content of slide 2 from file
    plot_something() # Add other things to same file
    write_something()
```
- Use `slides.demo` to create example slides and start editing. Follow steps in first part.
- Use `slides.docs` to see upto date documentation.
- You can acess markdown content of an existing slide using `slides[key or index].markdown` if it has been created using `slides.from_markdown` or `%%slide i -m`.
- You can insert content usign `with slides[key or index].insert(index)` or `slides[key or index].insert_markdown` (1.7.7+).

**New in 1.7.2**
  
- Find special syntax to be used in markdown by `Slides.xmd_syntax`.
- You can now show citations on bottom of each slide by setting `citation_mode = 'footnote'` in `Slides` constructor.
- You can now access individual slides by indexing `s_i = slides[i]` where `i` is the slide index or by key as `s_3_1 = slides['3.1']` will give you slide which shows 3.1 at bottom.
- Basides indexing, you can access current displayed slide by `slides.current`.
- You can add new content to existing slides by using `with s_i.insert(where)` context. All new changes can be reverted by `s_i.reset()`.
- If a display is not complete, e.g. some widget missing on a slide, you can use `(slides.current, slides[index], slides[key]).update_display()` to update display.
- You can set overall animation by `slides.settings.set_animation` or per slide by `s_i.set_animation`
- You can now set CSS for each slide by `s_i.set_css` or `slides.running.set_css` at current slide.

**New in 1.7.5**    
Use `Slides.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
Also look at [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
    
**New in 2.0.1**    
Check out alert`slides.glassmorphic` (later alert`slides.settings.set_glassmorphic` in 2.0.8+) and alert`slides.clipboard_image ` to add glassmorphic and clipboard image support.

**New in 2.1.7**    
 
- You can now add table of contents using alert`Slides.toc ` and alert`Slides.section `. Remember to run slide with alert` toc ` at last as well to grab all contents.
- In Markdown settings, same thing can be done using alert`toc\`Toc Title\`` and alert`section\`key\``.
- You can use `Slides.goto_button` to add a button to go to jump to a slide.
- Inside a alert`\`\`\`python run` block in markdown, you can access `slides = get_slides_instance()` to get current slides instance and use all its methods.
- A new function `Slides.bullets` is added to add powerful bullet list from python objects.

**New in 2.2.0**

- A complete overhaul of CSS is done, so your custom CSS classes may be broken. You need to see `slides.docs` and read docs of `slides.fromat_css` as well as `slides.css_style` to know changes.
- Now you can use python dictionary inside `slides.format_ccs, slides.set_css, slides[0].set_css` functions to set CSS properties, with extended and concise syntax.
- In Custom Theme mode, now instead of editing a CSS file, you just need to set colors using `slides.settings.set_theme_colors`.

**New in 2.2.5**

- Inside Python script, you can now use auto numbering of slides with `slides.AutoSlides()`. See it's docs for details.

**New in 3.0.0**

- Python 3.8+, ipywidgets 8, IPython 8.7+ required. Previous version 2.x.x will still be supported for bug fixes.
- Slides now create a new view after each cell run with only content of that cell. This is streamlined so that Jupyter Lab, Classic Notebook, Voila and Jupyter Retro can all be supported.
- Citations are provided with ` Slides.set_citations ` function that accept json file or dictionary. On next run, these are loaded from disk, so it works in python scripts and voila as well. Make sure to set at start if you don't want to re-run all cells.
- Old syntax of alert`[key]:\`citation value\`` is removed in favor of single set_citations method which works everywhere. 
- Citations can be passed in any order, but sections need to be passed in order of appearance to render correctly.
''',
f'<h4 style=""color:green;"> 👈🏻 Read more instructions in left panel</h4>'
)
_icons = {key: _Icon(key, color="var(--accent-color)") for key in _icons}
for k,r  in zip('RLUD',[0,180,-90,90]):  # clockwise rotation sucks!
    _icons[k] = _Icon('chevron', color="var(--accent-color)",rotation=r)
def _key(k): return f'<span style="border: 1px solid var(--secondary-fg); background:var(--secondary-bg);border-radius:4px;padding:2px 6px;min-width:2em;">{k}</span>'
key_combs = f'''
| Key (comb) and associated button(s)                                        | Action                                               | 
|----------------------------------------------------------------------------|------------------------------------------------------|
| {_key('&#9141;')} / {_key('▸')} {_icons["R"]}, {_icons["D"]}               | Move to next slide                                   |
| {_key('⇧')} + {_key('&#9141;')} / {_key('◂')} {_icons["L"]}, {_icons["U"]} | Move to previous slide                               |
| {_key('Z')} {_icons["zoom-in"]}, {_icons["zoom-out"]}                      | Toggle `image/.zoom-self/.zoom-child > *` zoom mode  |
| {_key('S')} {_icons["camera"]}                                             | Save screenshot of current slide                     |
| {_key('P')}                                                                | print PDF of current slide                           |
| {_key('F')} {_icons["expand"]}, {_icons["compress"]}                       | Toggle Fullscreen mode                               |
| {_key('Esc')}                                                              | Exit Fullscreen mode                                 |
| {_key('W')} {_icons["win-maximize"]}, {_icons["win-restore"]}              | Fit/restore slides to/from window's viewport         |
| {_key('G')} {_icons["dots"]}, {_icons["close"]}                            | Toggle settings panel                                |
| {_key('L')} {_icons["laser"]}, {_icons["circle"]}                          | Toggle Laser Pointer ON/OFF                          |
'''

more_instructions =f'''## How to Use

**Key Bindings**{{.success}} {_Icon("pencil", color="var(--accent-color)", rotation=45)}

Having your cursor over slides, you can use follwoing keys/combinations:

{key_combs}

> You can also swipe left/right from edges of screen ( within `±50px` edge range) on touch devices to change slides.

**Tips**{{.success}}

- Other keys are blocked so that you may not delete or do some random actions on notebook cells.
- Jupyter/Retro Lab is optimized for keyboard. Other frontends like Classic Notebook, VSCode, Voila etc. may not work properly.
- Pressing `S` to save screenshot of current state of slide. Different slides' screenshots are in order whether you capture in order or not, 
but captures of multiple times in a slides are first to last in order in time.

### PDF Printing
- Capture screenshot of current state of slide by camera button in toolbar or by pressing `S` key. 
    This will collect screenshots of current slide in order of capturing. 
    This is a manual process but you can collect content as you want. You can hover top-right corner to use a slider to adjust height of visible content.
- Press `Capture All` button in side panel to capture a single image of each slide. Then you can add images over it by manually capturing.
- Press `Save PDF` button to save all screenshots as PDF.

{how_to_slide[0]}

- Slides should be only in top cell as it collects slides in local namespace, auto refresh is enabled.

Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
{{.note-warning}}
'''

instructions = f'''{more_instructions}
{how_to_ppt}
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
'''

logo_svg = '''<svg width="60px" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="50" fill="var(--accent-color)"/>
    <text x="50%" y="50%" fill="var(--secondary-bg" font-size="18px" font-weight="bolder" dominant-baseline="central" text-anchor="middle">IPySlides</text>
</svg>'''