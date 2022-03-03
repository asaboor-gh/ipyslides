# ONLY INSTRUCTIONS BELOW

how_to_ppt = '''### How to make Powerpoint Presentation from Bunch of Images
- Save all screenshots using `Save PNG` button and go to folder just created.
- You know the aspect ratio while taking screenshots, if not, read details of any of picture to find it.
- Open Powerpoint, got to `Design` tab and select `Slide Size`. If pictures here are of aspect ration 4:3 or 16:9, select that,
otherwise select `Custom Slide Size` and change size there according to found aspect ratio. 
- You will see a slide of your prefered size now. Go to `Insert` tab and select `Photo Album > New Photo Album`.
- Select `File/Disk` option to insert pictures and make sure `Picture Layout` option is `Fit to slide`.
- Now click `Create` and you will see all pictures as slides.

> Note: Do not use PDF from Powerpoint as that will lower quality, generate PDF from slides instead. 
'''

how_to_slide = ('''# Creating Slides
> Tip: You can use `ipyslides.demo()` to create example slides and start editing.

**Assuming you have `ls = ipyslides.LiveSlides()`**

- Proceed to create slides:
    - Edit and test cells in `ls.convert2slides(False)` mode.
    - Run cells in `ls.convert2slides(True)` mode from top to bottom. 
    - `%%slide integer` on cell top auto picks slide and `%%title` auto picks title page.
    - You can use context managers like `with ls.slide(): ...` and `with ls.title(): ...` in place of `%%slide` and `%%title` respectively.
```python
#------------ Cell 1 --------------------
import ipyslides as isd 
ls = isd.LiveSlides()
ls.convert2slides(True)
ls.settings.set_animzation('zoom') 
#------------ Cell 2 --------------------
%%title
# create a rich content title page
#------------ Cell 3 --------------------
%%slide 1
# slide 1 content
#------------ Cell 4 --------------------
@ls.frames(1,*objs)
def func(obj):
    write(obj) #This will create as many slides after the slide number 1 as length(objs)
#------------ Cell 5 --------------------
ls # This displays slides if on the last line of cell, or use `ls.show()`.
```

- Use `ls.from_markdown` to create slides from markdown file/StringIO and then can add slides over it.
    - Slides are added in order of content.
    - Slides should be separated by `---` (three dashes) in start of line.
    - You can add more slides besides created ones or modify existing ones using `ls.md_content`:
```python
ls.from_markdown(path, footer_text = 'Author Name')
with ls.slide(2):
    write(ls.md_content[2]) # write content of slide 2 from file
    plot_something() # Add other things to same file
    write_something()
```
''',
'<h4 style=""color:green;"> 👈🏻 Read more instructions in left panel</h4>'
)

more_instructions =f'''## How to Use

**Key Bindings**
Having your cursor over slides, you can use follwoing keys/combinations:

| Key (comb)                   | Action                                               | 
|------------------------------|------------------------------------------------------|
| `Space/RightArrowKey`        | Move to next slide                                   |
| `Shift + Space/LeftArrowKey` | Move to previous slide                               |
| `Ctrl + Shift + C`           | change the theme, create console/terminal etc        |
| `Ctrl + Shift + [/]`         | switch to other tabs like console/terminal/notebooks |
| `F`                          | fit/release slides to/from viewport                  |
| `T`                          | start/stop timer                                     |
| `Z`                          | toggle matplotlib/svg/image zoom mode                |
| `S`                          | save screenshot of current slide                     |
| `P`                          | print PDF of current slide                           |

**Tips**

- Other keys are blocked so that you may not delete or do some random actions on notebook cells.
- Jupyter/Retro Lab is optimized for keyboard. Other frontends like Classic Notebook, VSCode, Voila etc. may not work properly.
- Pressing `S` to save screenshot of current state of slide. Different slides' screenshots are in order whether you capture in order or not, 
but captures of multiple times in a slides are first to last in order in time.

### PDF Printing
There are two ways of printing to PDF.
- Capturing each screenshot based on slide's state (in order) and later using `Save PDF`. This is a manual process but you have full control of view of slide.
- Press `Print PDF` button and leave until it moves up to last slide and you will get single print per slide. If something don't load, increase `load_time` in `ls.print_settings` value and then print.

{how_to_slide[0]}

- LiveSlides should be only in top cell as it collects slides in local namespace, auto refresh is enabled.

> Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
'''

instructions = f'''{more_instructions}
{how_to_ppt}
### Custom Theme
For custom themes, change below `Theme` dropdown to `Custom`.
You will see a `custom.css` in current folder,edit it and change
font scale or set theme to another value and back to `Custom` to take effect. 
> Note: `custom.css` is only picked from current directory.
          
--------
For matching plots style with theme, run following code in a cell above slides.

**Matplotlib**
```python
import matplotlib.pyplot as plt
plt.style.use('ggplot')
#plt.style.available() #gives styles list
```

**Plotly**
```python
import plotly.io as pio
pio.templates.default = "plotly_white"
#pio.templates #gives list of styles
```
> Tip: Wrap your plotly figures in `plotly.graph_objects.FigureWidget` for quick rendering.

**Altair**
```python
import altair as alt
alt.themes.enable('dark')
#alt.themes #gives available themes
```

### Customize Slides
You can customize slides by inheriting from `LiveSlides` class. 
For example if you want to have custom theme and some other settings always enabled and
bottom information only on title slide, you can do so:
```python
class CustomSlides(isd.LiveSlides):
    def __init__(self):
        super().__init__()
        self.convert2slides(True)
        self.settings.theme_dd.value = 'Custom'
        self.progress_slider.observe(self.set_visible, names=['index'])
    
    def set_visible(self, change):
        if self.progress_slider.index == 0:
            self.widgets.navbox.children[0].layout.visibility = 'visible'
        else:
            self.widgets.navbox.children[0].layout.visibility = 'hidden'
```
'''