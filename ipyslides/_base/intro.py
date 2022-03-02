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

how_to_slide = '''### Creating Slides
**Assuming you have `ls = ipyslides.LiveSlides()`**

- Use `ls.load_ipynb` to create slides from a notebook (same notebook too)
    - You do not need to keep track of slide numbers, any code and markdown cell will be picked in order.
    - Any cell with `#hide` on top will not be executed. 
    - No slides can be added in this programatically, it's a top to bottom linear process.
    - Markdown cells are picked this way.
    - Slides created with `%%slide` are picked.
    
- Use `ls.load_md` to create slides from markdown file and then can add slides over it.

- Proceed without any of above methods. (below points still apply to slides from `load_md`)
    - Edit and test cells in `ls.convert2slides(False)` mode.
    - Run cells in `ls.convert2slides(True)` mode from top to bottom. 
    - `%%slide integer` on cell top auto picks slide and `%%title` auto picks title page.
    - You can use context managers like `with ls.slide(): ...` and `with ls.title(): ...` in place of `%%slide` and `%%title` respectively.
'''

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

{how_to_slide}

```python
import ipyslides as isd 
slides = isd.LiveSlides()
slides.settings.set_animzation('zoom') 
@slides.frames(1,*objs)
def func(obj):
    write(obj) #This will create as many slides after the slide number 1 as length(objs)
#create a rich content title page with `%%title` or \n`with title():\n    ...`\n context manager.
slides.show() # Use it once to see slides
```
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
'''