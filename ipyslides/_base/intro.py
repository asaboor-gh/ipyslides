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
{.Note .Warning}
'''

how_to_slide = ('''# Creating Slides
class`Center`
alert`Abdul Saboor`sup`1`, Unknown Authorsup`2`

today``

class`TextBox`
sup`1`My University is somewhere in the middle of nowhere
sup`2`Their University is somewhere in the middle of nowhere
^^^
^^^

**Assuming you have `ls = ipyslides.LiveSlides()`**

- Proceed to create slides:
    - `%%slide integer` on cell top auto picks slide and `%%title` auto picks title page.
    - `%%slide integer -m` can be used to create slide from full markdown (extended one).
    - You can use context managers like `with ls.slide(): ...` and `with ls.title(): ...` in place of `%%slide` and `%%title` respectively.

```python
import ipyslides as isd 
ls = isd.LiveSlides()
ls.set_animation(main='zoom') 
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
**Markdown here with extended options (see `ls.xmd_syntax` for info). Nested blocks are not supported**
 ```multicol 30 70 .Success
 less content
 +++
 more content
 ```
```

```python
%%slide 2 -s # new in 1.7.7
var = some_long_computation() # This will run only first time or when cell code chnages.
```

```python run source
x = 1 + 2
print(x) # will be printed on slide in somehwewere top as print appears first of all. 
# Use `with ls.capture_std() as std:  print();std.stdout` to see at exactly where it is printed.
```
There is a python block above with header `python run source`. We can display that block by  &lcub;&lcub;source&rcub;&rcub; as below:
{{source}} 

variable `x` defined there is shown here x = {{x}}. Only variables can be embeded in &lcub;&lcub;var&rcub;&rcub;, not expressions.
```python
@ls.frames(1,*objs)
def func(obj):
    write(obj) #This will create as many slides after the slide number 1 as length(objs)
```
```python
ls # This displays slides if on the last line of cell, or use `ls.show()`.
```

- Use `ls.from_markdown` to create multiple slides from markdown file/text.
    - Slides are added in order of content.
    - Slides should be separated by `---` (three dashes) in start of line.
```python .monokai
ls.from_markdown(path)
with ls.slide(2):
    write(ls[2].markdown) # write content of slide 2 from file
    plot_something() # Add other things to same file
    write_something()
```
- Use `ls.demo` to create example slides and start editing. Follow steps in first part.
- Use `ls.docs` to see upto date documentation.
- You can acess markdown content of an existing slide using `ls[key or index].markdown` if it has been created using `ls.from_markdown` or `%%slide i -m`.
- You can insert content usign `with ls[key or index].insert(index)` or `ls[key or index].insert_markdown` (1.7.7+).

**New in 1.7.2**
  
- Find special syntax to be used in markdown by `LiveSlides.xmd_syntax`.
- You can now show citations on bottom of each slide by setting `citation_mode = 'footnote'` in `LiveSlides` constructor.
- You can now access individual slides by indexing `s_i = ls[i]` where `i` is the slide index or by key as `s_3_1 = ls['3.1']` will give you slide which shows 3.1 at bottom.
- Basides indexing, you can access current displayed slide by `ls.current`.
- You can add new content to existing slides by using `with s_i.insert(where)` context. All new changes can be reverted by `s_i.reset()`.
- If a display is not complete, e.g. some widget missing on a slide, you can use `(ls.current, ls[index], ls[key]).update_display()` to update display.
- You can set overall animation by `ls.set_overall_animation` or per slide by `s_i.set_animation`
- You can now set CSS for each slide by `s_i.set_css` or `ls.set_slide_css` at current slide.

**New in 1.7.5**    
Use `LiveSlides.extender` to add [markdown extensions](https://python-markdown.github.io/extensions/).
Also look at [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
    
**New in 1.7.7**        
Use `slides[i].insert_markdown({'index': 'markdown_string',...})` to insert markdown (pasrsed objects) at indices.   
`%%slide i -s` can be used to execute code just once in current session. It will run again if code changes in cell.

''',
'<h4 style=""color:green;"> 👈🏻 Read more instructions in left panel</h4>'
)

key_combs = '''
| Key (comb)                   | Action                                               | 
|------------------------------|------------------------------------------------------|
| `Space/RightArrowKey`        | Move to next slide                                   |
| `Shift + Space/LeftArrowKey` | Move to previous slide                               |
| `Ctrl + Shift + C`           | Change the theme, create console/terminal etc        |
| `Ctrl + Shift + [/]`         | Switch to other tabs like console/terminal/notebooks |
| `W`                          | Fit/restore slides to/from window's viewport                  |
| `T`                          | Start/stop timer                                     |
| `Z`                          | Toggle matplotlib/svg/image zoom mode                |
| `S`                          | Save screenshot of current slide                     |
| `P`                          | print PDF of current slide                           |
| `F`                          | Enetr Fullscreen mode                                |
| `Esc`                        | Exit Fullscreen mode                                 |
'''

more_instructions =f'''## How to Use

**Key Bindings**{{.Success}}

Having your cursor over slides, you can use follwoing keys/combinations:

{key_combs}

> You can also swipe left/right from edges of screen ( within `±50px` edge range) on touch devices to change slides.

**Tips**{{.Success}}

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

- LiveSlides should be only in top cell as it collects slides in local namespace, auto refresh is enabled.

Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
{{.Note .Warning}}
'''

instructions = f'''{more_instructions}
{how_to_ppt}
### Custom Theme
For custom themes, change below `Theme` dropdown to `Custom`.
You will see a `custom.css` in current folder,edit it and change
font scale or set theme to another value and back to `Custom` to take effect. 

`custom.css` is only picked from current directory.
{{.Note .Info}}
          
--------
For matching plots style with theme, run following code in a cell above slides.

**Matplotlib**{{.Success}}
```python
import matplotlib.pyplot as plt
plt.style.use('ggplot')
#plt.style.available() #gives styles list
plt.rcParams['svg.fonttype'] = 'none' # or 'path' Enforces same fonts in plots as in presentation slides or use
```

**Plotly**{{.Success}}
```python
import plotly.io as pio
pio.templates.default = "plotly_white"
#pio.templates #gives list of styles
```
Wrap your plotly figures in `plotly.graph_objects.FigureWidget` for quick rendering.
{{.Note .Info}}

**Altair**{{.Success}}
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
        self.settings.theme_dd.value = 'Custom'
        self.progress_slider.observe(self.set_visible, names=['index'])
    
    def set_visible(self, change):
        if self.progress_slider.index == 0:
            self.widgets.footerbox.layout.visibility = 'visible'
        else:
            self.widgets.footerbox.layout.visibility = 'hidden'
```
'''

logo_svg = '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="50" fill="var(--accent-color)"/>
    <text x="50%" y="50%" fill="var(--secondary-bg" font-size="18px" font-weight="bolder" dominant-baseline="central" text-anchor="middle">IPySlides</text>
</svg>'''