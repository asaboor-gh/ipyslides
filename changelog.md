# Changelog
Content below assumes you have `ls = LiveSlides()`.

# 1.2.1
- Speaker Notes are added inside notebook as well, so in case you are sharing slides area of notebook in softwares like Zoom, Google Meets etc., that will be useful. No need to check `Show Notes` in this case. 
- Miscalleneous big fixes. 
# 1.2.0
### Speaker Notes 
- You can turn on speaker notes with a `Show Notes` check in side panel. Notes can be added to slides using `ls.notes` command. 
- Notes is an experimantal feuture, so use at your own risk. Do not share full screen, share a brwoser tab for slides and you can keep notes hidden from audience this way. 
### Source Overhauled
- `ls.source` is now to include sources from `strings`, `files`, and objects like `class, module, function`.  etc
Resulting object a widget that can be passed to both `write`, `iwrite` commands. Now use this to retrive a code block:
```python
with ls.source.context() as s:
    ...
    iwrite(s) # auto updates inside context manager in iwrite
write(s) # Can be only accessed outside conetext for other uses
```
`ls.source.from_[file,string,callable]` are other available functions and `ls.source.current` gives currently available source. 
You can show other languages' code from file/strings as well. 


### Other changes 
- `ls.enum_slides`, `ls.repeat` are removed.
- Added `ls.format_css` function, you can add a `className` in `[i]write` commnads and use CSS inside this. 


# 1.1.0
- Commnd `iwrite` now returns a displayed grid and references to objects passed. So you can update live things on slides (see `ipyslides.demo` for it). It now accept other objects like matplotlib's figure etc.
```python
grid, x = iwrite('X') 
grid, (x,y) = iwrite('X','Y')
grid, (x,y) = iwrite(['X','Y'])
grid, [(x,y),z] = iwrite(['X','Y'],'Z')
#We unpacked such a way that we can replace objects with new one using `grid.update`
new_obj = grid.update(x, 'First column, first row with new data') #You can update same `new_obj` withit's own widget methods.
```
- `ls.source` is now an HTML widget, so it can update itself within context manager block when written inside `iwrite` command. Same widget can be passed to `write` command but will not be updated.
- `ls.get_cell_code` is no more there in favor for `ls.source`.
- `ls.fmt2cols` is renamed to `ls.format_html` and expanded to any number of objects/columns. Result can be passed to both writing commands. `ls.ihtml` is deprecated for same reason. Just a single function is okay.
# 1.0.9
- `ls.source` now let you capture source code into a variable and do not show bydefault, but this way you can write source code anywhere you want. 
```python
with ls.source() as src:
    x = do_something()
write(x,src) #will be displayed in two side by side columns, it was not that flexible before
```
- Even if you do not explicitly assign `ls.source() as s:`, you can still access current code block using `ls.current_source`. 
- `ls.get_cell_code` will be deprecated in future in favor of verstile `ls.source`.
- Theming is modified a little bit and a new `Fancy` theme is added. 
- Bug fixes and improvements in CSS. 
# 1.0.7 
- Layout/Functionality is fixed for [RetroLab](https://github.com/jupyterlab/retrolab) which will be base for classical notebook version 7 in future.
- `ls.sig(callable)` displays signature and `ls.doc(callable)` display signature alongwith docs in contrast to `write(callable)` directly which displays code as well. 

# 1.0.5
- `ls.image` now accepts `im = PIL.Image.open('path')` object and displays if `im` is not closed. You can display `numpy.array` from `numpy` or `opencv` image by converting it to `PIL.Image.fromarry(array)` or using `plt.imshow(array)` on it and then `write(plt.gcf())`. 
- `html_node` function is added to separaetly add HTML without parsing it. It can display itself if on the last line of notebook's cell or can be passed to `write`,`ihtml` commands as well.

# 1.0.4
- Laser pointer 🔴 is added, you can customize it's color in custom theme. 
- `ipyslides.initialize` now has argument `markdown_file`. You can write presentation from a markdown file. Slides separator is `---` (three dashes). For example:
```
_________ Markdown File Content __________
# Talk Title
---
# Slide 1 
---
# Slide 2
___________________________________________
```
This will create two slides along with title page. 
- `ls.enable_zoom(object)` will zoom that object when hovered on it while `Zoom Items` button is ON (or `Z` pressed in Jupyterlab)
- `ls.raw` will print a string while preserving whitspaces and new lines. 
- `ls.svg`,`ls.image`(ls.file2image is just an alias now for ls.image) can now take url or data to display image.
- `ls.repeat` can be used to remind you of something via notification at given time interval. You can infact create a timer with combination of `ls.repeat` and `ls.notify`. 
- Besides just matplotlib's figure, now everything inside `ls.image`, `ls.svg`,`ls.enable_zoom` will go full screen on hover with `Zoom Items` toggle button ON. 

# 1.0.3
- Now you can send notificatios based on slide using `@ls.notify_at` decorator. This is dynamic operation, so if you need to show time during slides(look at demo slide), it will show current time. Notifications are hidden during screenshot by app's mechanism, not external ones. You can turn ON/OFF notifications from settings panel. 
- Use `Save PNG` button to save all screenshots in a folder in sequence. You can create a `Powerpoint Presentation` from these picture by following instructions in side panel or from the generated file `Make-PPT.md` along pictures.
# 1.0.2
- Javascript navigation works now after browser's refresh.
- User can now decide whether to display slides inline or in sidebar using a button in Jupyterlab. (Sorry other IDEs, you are not flexible to do this, use Voila in that case.)
- Multiple views of slides can capture keyboard events separately.
- All instances of LivSlides are now aware of each other for theme switch and inline/sidebar toggle. If one instance go in sidebar, others fall to inline. If one go fullscreen, others go minimized. 
- Bugs fixed and improvements added.
# 1.0.1
- Animations now have slide direction based on going left or right. `ipysides.data_variables.animations` now have `slide_h` and `slide_v` for horizontal and vertical sliding respectively. 
- You can now set text and code fonts using `ls.set_font_family(text_font, code_font)`.
- Many bugs fixed including Voila's static breakpoint. 
# 1.0.0 
- `ipyslides.initialize(**kwargs)` now returns a `LiveSlides` instance instead of changing cell contents. This works everywhere including Google Colab.
- `LiveSlides`,`initialize` and  `init` cause exit from a terminal which is not based on `IPython`.
- Markdown and other than slides output now does not appear (height suppressed using CSS) in Voila.
- Keyboard vavigation now works in Voila. (Tested on Voila == 0.2.16) 
- Test and add slides bounding box form slides left panel's box using `L,T,R,B` input and see screenshot immediately there. This is in addition and independent to `ls.set_print_settings(bbox)`.

# 0.9.9
- Javascript navigation is improved for Jupyterlab.
- The decorator `ls.slides` is renamed as `ls.frames` and now it adds one slide with many frames. This is useful to reveal slide contents in steps e.g. bullet points one by one.
# 0.9.8
- PDF printing is optimized. See [PDF-Slides](IPySlides-Print.pdf). You can hover over top right corner to reveal a slider to change view area while taking screenshot. Also you can select a checkbox from side panel to remove scrolling in output like code.
- You can now display source code using context manager `slides.source`.
- You can (not recommended) use browser's print PDF by pressing key `P` in jupyterlab but it only gives you current slide with many limitations, e.g. you need to collect all pages manually.

# 0.9.6
- Code line numbering is ON by default. You can set `ls.code_line_numbering(False)` to turn OFF.
- Add slides in for loop using `slides.enum_slides` function. It create pairs of index and slides. 
#### PDF Printing (Tested on Windows)
- PDF printing is now available. Always print in full screen or set `bbox` of slides. Read instructions in side panel. [PDF-Slides](IPySlides-Print.pdf)

# 0.9.5
- You can now give `function/class/modules` etc. (without calling) in `write` and source code is printed.
- Objects like `dict/set/list/numpy.ndarray/int/float` etc. are well formatted now.
- Any object that is not implemented yet returns its `__repr__`. You can alternatively show that object using `display` or library's specific method. 

# 0.9.4
- Now you can set logo image using `ls.set_logo` function.
- LaTeX's Beamer style blcoks are defined. Use `ls.block(...,bg='color')`, or with few defined colors like `ls.block_r`, `ls.block_g` etc.
- `@ls.slides` no more support live calculating slides, this is to avoid lags while presenting. 
# 0.9.3
- Add custom css under %%slide as well using `ls.write_slide_css`.
- Slides now open in a side area in Jupyterlab, so editing cells and output can be seen side by side. No more need of Output View or Sidecar.
## 0.9.1
- In Jupyterlab (only inline cell output way), you can use `Ctrl + Shift + C` to create consoles/terminals, set themes etc.
- Use `Ctrl + Shift + [`, `Ctrl + Shift + ]` to switch back and forth between notebooks/console/terminals and enjoy coding without leaving slides!

## 0.8.11
- All utilities commnads are now under `LiveSlides` class too, so you can use either 
`ipyslides.utils.command` or `ls.command` for `command` in `write`,`iwrite`,`file2code` etc.
## 0.8.10
- You can add two slides together like `ls1 + ls2`, title of `ls2` is converted to a slide inplace. 
- You can now change style of each slide usig `**css_props` in commands like `@ls.slides`, `with ls.slide` and `with ls.title`. 
- A new command `textbox` is added which is useful to write inline references. Same can be acheived with `slides.cite(...here=True)`. 
- You can use `ls.alert('text')`, `ls.colored('text',fg,bg)` to highlight text.

## 0.8.7
- Support added for objects `matplotlib.pyplot.Figure`, `altair.Chart`, `pygal.Graph`, `pydeck.Deck`, `pandas.DataFrame`, `bokeh.plotting.Figure` to be directly in `write` command.
- `write` command now can accept `list/tuple` of content, items are place in rows.
## 0.8.5
- `@ls.slides(...,calculate_now=True)` could be used to calculate slides in advance or just in time. Default is `True`. 
- You can now use `ipyslides.utils.iwrite` to build complex layout of widgets like ipywidgets, bqplot etc. (and text using `ipyslides.utils.ihtml`).  

## 0.8.3
- You can now use `ls.cite` method to create citations which you can write at end by `ls.write_citations` command.
- `ls.insert_after` no longer works, use 
```python
@ls.slides(after_slide_number,*objs)
def func(obj):
    write(obj) #etc. for each obj in objs
```
decorator which is more pythonic way. 
## 0.8.0 +
> Note: All these points may not or only partially apply to earlier versions. So use stable API above version 8.
- Before this version, slides were collected using global namespace, which only allowed one presentation per
notebook. Now slides are stored in local namespace, so no restriction on number of slides per notebook.
- To acheive local namespace, functions are moved under class LiveSlide and it registers magics too. So now you will
be able to use `%%slide, %%title` magics. Now you will use context managers as follows
```python
ls = LiveSlides()
ls.convert2slides(True)

with ls.title():
    ...
with ls.slide(<slide number>):
    ...
ls.insert_after(<slide number>,*objs, func)
```
- `ipyslides.initialize()` can write all above code in same cell. 
> Note: For LiveSlides('A'), use %%slideA, %%titleA, LiveSlides('B'), use %%slideB, %%titleB so that they do not overwite each other's slides.
- You can elevate simple cell output to fullscreen in Jupyterlab >= 3.
- `with ls.slide` content manager is equivalent to `%%slide` so make sure none of them overwrite each other.

- Auto refresh is enabled. Whenever you execute a cell containing `%%title`, `with ls.title`, `%%slide`, `with ls.slide` or `ls.insert_after`, slides get updated automatically.
- LiveSlides should be only in top cell. As it collects slides in local namespace, it can not take into account the slides created above itself.
