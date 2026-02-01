"""
CSS styles and XMarkdown syntax documentation for ipyslides.
This file contains descriptive text strings explaining available formatting options.
"""

from ..xmd import _md_extensions, _special_funcs

_special_funcs = '\n'.join(rf' -  alert`{k}`\`{v}\`' for k,v in _special_funcs.items())

css_styles = '''
Use any or combination of these styles in markdown blocks or `css_class` argument of writing functions:
                       
| css_class         | Formatting Style                                                                    
|:------------------|:---------------------------------------------------------
 `text-[value]`     | [value] should be one of tiny, small, big, large, huge.
 `align-[value]`    | [value] should be one of center, left, right.
 `rtl`              | اردو،  فارسی، عربی، ۔۔۔ {: .rtl}
 `info`             | Blue text. Icon ℹ️  for note-info class. {: .info}
 `tip`              | Blue text. Icon💡 for note-tip class. {: .tip}
 `warning`          | Orange text. Icon ⚠️ for note-warning class. {: .warning}
 `success`          | Green text. Icon ✅ for note-success class. {: .success}
 `error`            | Red text. Icon⚡ for note-error class. {: .error}
 `note`             | Text with note icon, can combine other classes as shown above. {: .note}
 `export-only`      | Hidden on main slides, but will appear in exported slides.
 `jupyter-only`     | Hidden on exported slides, but will appear on main slides.
 `block`            | Block of text/objects {: .block}
 `block-[color]`    | Block of text/objects with specific background color from <br> red, green, blue, yellow, cyan, magenta and gray.
 `[h,v]rules`       | Horizontal and vertical rules between children of a node. Combined with `ul` or `ol` for lists gives nice effect and can be used to create tabular grids.
 `raw-text`         | Text will be shown as printed style. {: .raw-text}
 `focus-self`       | Double-click on element to zoom into popup view. Double-click again or press close button to exit. {: .focus-self}
 `focus-child`      | Focus on child objects of node with this class. Same double-click to zoom in/out behavior.
 `no-focus `        | Disables focus on object when it is a direct child of 'focus-child'.

Besides these CSS classes, you always have `Slide.set_css`, `Slides.html('style',...)` functions at your disposal.
'''

xmd_syntax = rf'''
## Extended Markdown
--                                       
Extended syntax on top of [Python-Markdown](https://python-markdown.github.io/) supports almost full presentation from Markdown.

**Presentation Structure**{{.text-big}}

Slides, Pages and Parts Separators
: Triple dashes `---` is used to split text in slides inside markdown content of `Slides.build` function or markdown file.
Double dashes `--` (`PAGE` in Python) is used to split text in pages. 
Both `---` and `--` should be on their own lines in main content (not inside block syntax) to be recognized as slide/page separators.
Double plus `++` (`PART` in Python) can be used to increment objects in parts on slide/page.
A `++` on its own line before `columns` block will make it reveal content incrementally, provided that columns are separated by `+++`.
The combinations of pages and parts create frames on slides. Note that only `++` allows content on same line after it and following lines.

Sections & TOC
: alert`section\`content\`` to add a section that will appear in the table of contents.
alert`toc\`Table of content header text\`` to add a table of contents. See `Slides.docs()` for creating a `TOC` accompanied by section summary.

Notes
: alert`notes\`This is slide notes\``  to add notes to current slide.

Including Files
: alert`include\`markdown_file.md[optional list slicing to pick lines from file such as [2:5], [10:]]\`` to include a file in markdown format.
These files are watched for edits if included in synced markdown file via `Slides.sync_with_file`.

Citations
: - alert`cite\`key1,key2\`` / alert`\@key1,\@key2` to add citation to current slide. citations are automatically added in suitable place and should be set once using `Slides.set_citations` function (or see below).
- You can add alert`refs\`ncol_refs\`` or code` Slides.refs ` to add citations anywhere on slide. If \`ncol_refs\` is not given, it will be picked from layout settings.
  Using alert`refs\`ncol_refs, key1, key2,...\`` will show only citations for given keys on that place. It is useful on slides with frames to show relevant citations on each frame.
  Unused citations will be added automatically at end of slide.
- Force citations to be shown inline by appending a !, such as alert`\@key!` or alert`cite\`key1,key2!\``.
- In the synced markdown file (also its included files) through `Slides.sync_with_file`, you can add citations with block sytnax:                             
code["markdown"]`
 ::: citations
    \@key1: Saboor et. al., 2025
    \@key2: A citations can span multiple lines, but key should start on new line
`

--

**Content Blocks**{{.text-big}}

The general block syntax is `::: type-or-classes [args] attributes`.

- You can use `/` to divide css properties from node attributes such as `::: note-info border="1px solid red" / id="mynote" dir="ltr"`. Node attributes come after `/`. 'data-' prefixed attributes can appear anywhere.
- You can create inline blocks by adding `|` in header (only takes effect if body is empty), such as `::: block-red | text` will create a block with red background and text inside.
- Both `|` and `/` can be escaped in header by backslah to interpret them as literal characters instead of block body and attributes splitters respectively. 
- You can optionally continue block header on next multiple adjacent lines with `:` at start of each line. This multiline header is not available in \`\`\` blocks.
- Theme colors such as `fg1=red bg2=black` upto 3, can be assigned for each block to tweak look and feel of content.
- Blocks can be escaped by having a space before `:::` at start of line, such as ` ::: block-red` will not be parsed as block.
- Some block levels HTML tags are handled specially, such as p, pre, ul, ol, blockquote, details, summary, table.
- You can use `::: block` nested inside \`\`\` block at same indentation level but otherwise must be correctly indented.
- Bullet points are hard to stylize, so use `::: ul/ol` blocks to create lists with custom styles and in side have `::: li` blocks for each item.
  e.g. a per item marker can be added using `::: li list-style="'👉'" | item text` besides all other CSS styles, or a `data-marker` attribute directly.

::: table 1 4 caption-side=top bg3=#8988
    This table, itself created with a `::: table` block, lists common block types and their usage.
    Each of these blocks can have additional CSS classes and properties, besides the limited set shown below.
    
    | Block Syntax      | Description                                                                                                 |
    |:----------------- |:----------------------------------------------------------------------------------------------------------- |
    | `::: raw/pre`     | Raw text or preformatted text, no markdown parsing. Use `raw` or `pre` as first word in block. |
    | `::: code [focused lines]`  | Code block with syntax highlighting, parameters are passed to highlight function. |
    | `::: tag or classes` | tags are block level elements such as `p`, `details`, `summary`, `table`, `center`, etc. |
    | `::: columns [widths]` | Create columns with relative widths, e.g. `columns 4 6` for 40% and 60% width. Use `+++` separator to reveal content incrementally/make display columns. |
    | `::: md-[before,after,var_name] [focused lines]` | Parse markdown in the block, with showing source code at before or after or assign a variable name and use as `<md-var_name/>`.|
    | `::: table [col widths]` | Create a table with optional column widths, e.g. `::: table 1 2` for 33% and 66% width. Use `caption-side=top/bottom` to place caption on top/bottom.|
    | `::: citations` | Add citations in the block (only in `sync_with_file` context) instead of `Slides.set_citations`. Use `\@key: value` syntax on its own line to add citations in block. |
    | `::: display css_classes` | Create a block with specific CSS classes forcing display mode, it can break dom flow, but usefull to embed widget variables under blocks. |

::: details
    ::: summary | Important Notes on `md-` and `code` blocks
    - Variable created with `md-var_name` can be used anywhere in markdown using `<md-var_name/>` to display source code.
    - `md-[position or variable]` accepts same parameters as `code` block for syntax highlighting and get deleted on first use.
    - Both `code` and `md-var` blocks support attribute access such as `::: code.collapsed` or `::: md-var.inline` to show selected view. 
    You can also use `::: code 1 3` to focus on specific lines based on index 1 in markdown unlike Python.
--

**Layouts**{{.text-big}}

Inline Columns
: Inline columns/rows can be added by using alert`stack\`Column A || Column B\`` sytnax. You can escape pipe `|` with `\|` to use it as text inside stack. See at end how to nest such stacking.

Block Columns
: You can create columns using `::: columns` syntax. 
Column separator is triple plus `+++` if intended in display mode and should be a `++` before block to make it incremental.

```md-before
::: columns 6 1 4 block-blue 
: border="1px dashed red"
    ::: block-red
        - `::: columns/muticol` with a +++ separator act like `write` command and reveal content incrementally when `++` is used before block.
        - children inside `columns` picks relative width from parent's `columns` block evem if '+++' is not used.
          In thise children should be visually blocks themselves like headings, paragraphs, lists etc or wrapped in `::: block` to make them obvious blocks like this one.
        - CSS classes and attributes can be used to style columns besides relative widths.
    
    ::: block-blue border="1px solid red" | alert`inline` color`block` text 
    
    ::: ul block-yellow border="2px solid orange" list-style=disc
        ::: li list-style="'👉'" 
            Top level `columns` is necessary to create columns or use simple block with `display=flex`.
            and frame speactor is used at end of block.
        <li data-marker=ℹ️> Indentation is important, so use tabs or spaces consistently.</li>
        ::: li | This follows disc marker from parent `ul` block.
```

--

**Code Display**{{.text-big}}

Inline Code
: Inline code can be highlighted using alert`code\`code\`` syntax, e.g. color`code\`print('Hello')\`` → code`print('Hello')`.

Code Blocks
: Use standard markdown fenced code blocks or `::: code ` blocks for syntax highlighting.

```md-src
::: columns
    <md-src/>
    +++
    ```python
    print('Hello, I was highlighted from a code block!')
    ```
    ::: code 2 language=bash name=Shell lineno=False style=vim
        echo "Hello, I was highlighted from a code block!"
        ls -l | grep ".py" | wc -l
``` 

```md-src.collapsed
::: details
    ::: summary | Click to see important notes on code blocks 
    - In ` ::: code ` block, you need to set parameters that are passed to `code` function, such as `language`, `name`, `lineno`, `css_class`, etc.
    - The \`\`\` code block does act like `::: code ` block and supports same parameters.
    - You can focus on specific lines in code blocks using line numbers (1-based) such as `::: code 2 4 5` to focus on lines 2, 4 and 5 visually. 
    - You can also use `::: code.collapsed` or `::: code.inline` to show collapsed or inline view of code block respectively.
    <md-src/>
```

--

**Variables Substitution**{{.text-big}}

Variables from Python code can be embedded directly into Markdown.

**Basic Usage**
: - **Syntax**: Use alert`\%{{variable}}` to display a variable which is lazily resolved and safely escaped from markdown parsing.
- **Formatting**: Apply formatting using alert`\%{{variable:format_spec}}` or conversions with alert`\%{{variable!conversion}}`. This works like Python's `str.format` method.
- **Notebook Display**: To render an object as it would appear in a notebook output cell, use alert`\%{{variable:nb}}`. This is useful for complex objects like plots.
- For custom objects, it's better to use `Slides.serializer` to define their HTML representation, which allows them to be displayed correctly in place with such as `\%{{fig}}`. 
  Using `\%{{fig:nb}}` might show the object at the end of the slide.

**Variable Scope & Updates**
: - **Live Updates**: Variables are automatically updated in your slides when their values change in the notebook if not held inside `Slide[number,].vars` deepest scope.
- **Scope Resolution**: Variables are resolved from per-slide variables (set by `build` or `Slide.vars.update`), then from the notebook's global scope if a slide is built purely from markdown.
    In functions which take markdown string such as `write`, `html`, variables are taken from notebook's global scope only. Use `fmt` to encapsulate variables from local scopes.
- **Forcing Updates**: You can force a refresh of variables on a specific slide using code`Slide[number,].vars.update(**kwargs)`. This is also useful for setting unique variable values on different slides.
- **Attribute/Index Access**: When using expressions like `\%{{var.attr}}` or `\%{{var['key']}}`, the output will only update if the base variable `var` itself is reassigned.

**Important Notes**
: - Use unique variable names for each slide to prevent unintended updates.
- Widgets and objects using `:nb` are only displayed correctly in the first level of nested blocks.
- The alert`\%{{variable:nb}}` formatter can sometimes disrupt the document flow if used inside elements like headings. 
  It's safest to use it on its own line or within a paragraph.
- Widgets behave same with or without `:nb` format spec. 
- Formatting is done using `str.format` method, so f-string like literal expressions are not supported.
    
--

**Inline Python Functions**{{.text-big}}

Functions (that can also take extra args [python code as strings] as alert`func[arg1,x=2,y=A]\`arg0\``) include:

::: block-red
{_special_funcs}

::: note-info
    You can also use `Slides.esc`/`isd.esc` class to lazily escape variables/expressions/output of functions from being parsed inside f-strings.
    This should be rarely used when your markdown contains a lot of $ \LaTeX $ equations to avoid excessively escaping them with curly braces in favor of few escaped variables.

Upto 4 level nesting is parsed in inline functions using (level + 1) number of alert`/` (at least two) within backticks in functions given below. 
```md-src_var
::: columns
    <md-src_var/>
    +++
    stack[(6,4),css_class="block-blue"]`////
        This always parse markdown in `returns=True` mode. ||
        stack[css_class="info"]`/// B ||
            color["skyblue"]`//alert`Alerted Text` Colored Text //`
        ///` 
    ////`
```

--
**General Syntax**{{.text-big}}

- Use alert`include\`markdown_file.md[optional list slicing to pick lines from file such as [2:5], [10:]]\`` to include a file in markdown format.
- Use alert`fa\`icon_name\`` to add FontAwesome icons, e.g. fa\`arrow-right\` → fa`arrow-right`, fa\["green"\]\`check\` → fa["green"]`check`, fa\["blue"\]\`info-circle\` → fa["blue"]`info-circle` etc.
- Use syntax \`<link:[unique id here]:origin label>\` and \`<link:[unique id here same as origin]:target [back_label,optional]>\` to jump between slides. See `Slides.link` for more details.
- Cells in markdown table can be spanned to multiple rows/columns by attributes `| cell text \{{: rowspan="2" colspan="1"}}|` inside a cell, should be a space bewteen text and attributes.
- Escape a backtick with backslash, i.e. alert`\\` → \``, other escape characters include alert`@, %, /, |`. In Python >=3.12, you need to make escape strings raw, including the use of $ \LaTeX $ and re module.
- Use `_\`sub\`` and `^\`sup\``  for subscript and superscript respectively, e.g. H_`2`O, E = mc^`2`.
- See `Slides.css_styles` for available CSS classes to use in markdown blocks and other places.
- See `Slides.css_animations` for available CSS animation classes to use in markdown blocks and other places.
- Definition list syntax:
```md-src.inline
::: columns
    <md-src/> 
    +++
    Item 1 Header
    : Item 1 details ^`1`
    Item 1 Header
    : Item 1 details _`2`
```

**Extending Syntax**{{.text-big}}

::: block-red 
    - You can use `Slides.xmd.extensions` to extend additional syntax using Markdown extensions such as 
        [markdown extensions](https://python-markdown.github.io/extensions/) and 
        [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
    - These markdown extensions are inluded by default code`{_md_extensions}`.
    - You can serialize custom python objects to HTML using `Slides.serializer` function. Having a 
        ` __format__ ` method in your class enables to use {{obj}} syntax in python formatting and \%{{obj}} in extended Markdown.
'''

css_animations = '''
## 🎬 IPySlides Content Animations

--

All animations are **fully composable** - combine multiple animation classes to create complex effects! Use `anim-group` on a parent container to apply staggered animations to all children.

- Python functions accepting `css_class` parameter can use these animation classes directly, such as `Slide.write(..., css_class='anim-slide-left anim-zoom')` and tweak variables if `**css_props` parameter is available.
- You can used `Slides.run_animation` on demand with optional selector to target specific elements on slide after they are built. `dashlab` integration automatically runs animations after content inside changes.

Animation Class        | Description                                                                                                 | Effective Variables (`--time`: 0.6s, `--delay`: 0s` for all)
:----------------------|:------------------------------------------------------------------------------------------------------------|:-------------------------------------------
`anim-appear`          | Simple fade-in effect. {: .anim-appear}                                                                     | None (only `--time`, `--delay`)
`anim-slide-[direction]` | Slide in from specified direction: `left`, `right`, `up`, `down`, `tl`, `tr`, `bl`, `br`. {: .anim-slide-up} | `--distance`: CSS length (default: 120px)
`anim-wipe-[direction]` | Wipe/reveal from edge: `left`, `right`, `up`, `down`. Linear clip-path reveal. | None (only `--time`)
`anim-iris`           | Circular reveal (camera iris/aperture effect). Center customizable via `--origin`. {: .anim-iris} | `--origin`: Position as "X Y" (default: "50% 50%").
`anim-zoom` / `anim-zoom-[x,y]` | Zoom in effect, optionally specify axis: `x` or `y`. Respects `--origin`. {: .anim-zoom-x} | `--scale`: Number (default: 0.5)
`anim-rotate`         | Rotate in effect. Respects `--origin`. {: .anim-rotate} | `--angle`: CSS angle (default: 180deg)
`anim-spin`           | Spin in with 2x rotation + scale. Respects `--origin`. {: .anim-spin} | `--scale`, `--angle`
`anim-skew-[left,right]` | Skew in to left or right. {: .anim-skew-left} | `--distance`, `--skew`: angle (default: 20deg)
`anim-blur`           | Blur in effect. {: .anim-blur} | `--blur`: CSS length (default: 10px)
`anim-brighten`       | Brighten from dark + blur. {: .anim-brighten} | `--blur`: CSS length (default: 10px)
`anim-flip-x` / `anim-flip-x-reverse` | 3D flip on horizontal axis. Respects `--origin`. {: .anim-flip-x} | `--perspective`: CSS length (default: 800px)
`anim-flip-y` / `anim-flip-y-reverse` | 3D flip on vertical axis. Respects `--origin`. {: .anim-flip-y} | `--perspective`: CSS length (default: 800px)
`anim-perspective-[direction]` | 3D perspective from: `up`, `down`, `left`, `right`. {: .anim-perspective-up} | `--perspective`, `--distance`
`anim-bounce`         | Bouncy entrance with slide + scale. {: .anim-bounce} | `--distance`, `--scale`
`anim-swing`          | Swing from anchor. Respects `--origin`. {: .anim-swing} | `--scale`, `--origin` (e.g., "top center")
`anim-elastic`        | Elastic bounce timing. {: .anim-elastic} | `--scale`
`anim-group`          | **Power mode!** Applies staggered animations to all children. | All variables + auto stagger (sine curve)

### 🎨 Global Variables (Customizable)
- Add on children of `anim-group` or individual animated elements to tweak animation effects.
- You can set these via calculating in python systimatically for multiple elements and pass through variables embeding.

Variable | Default | Description
:--------|:--------|:-----------
`--time` | 0.6s | Animation duration
`--distance` | 120px | Translation distance for slides
`--angle` | 180deg | Rotation angle
`--scale` | 0.5 | Scale factor (0-1)
`--blur` | 10px | Blur intensity
`--perspective` | 800px | 3D perspective depth
`--skew` | 20deg | Skew angle
`--origin` | 50% 50% | **Universal origin** for transform-origin and iris center. Can add per item in `anim-group` like any other CSS property.
`--delay` | 0s | Individual delay automatically calculated from sine curve (use on specific elements)

--

### 💡 Usage Examples

**Basic Animations**
```md-after
::: block anim-slide-up
    Slides up from bottom

::: block anim-iris
    Opens like camera iris from center

::: block anim-wipe-left
    Wipes in from right edge
```

**Composable Animations** (Stack Multiple!)
```md-after
::: block anim-slide-left anim-rotate anim-zoom
    Slides, rotates, and zooms at once!

::: block anim-blur anim-brighten anim-slide-up
    Fades in with blur from dark

::: block anim-iris anim-zoom --origin="0% 0%"
    Iris opens from top-left corner while zooming!
```

--

**Custom Variables**
```md-after
::: block anim-slide-up anim-zoom --distance=200px --scale=0.2 --time=1s
    Custom distance, scale, and timing!

::: block anim-iris --origin="100% 100%"
    Iris opens from bottom-right corner

::: block anim-rotate --origin="left center" --angle=360deg
    Rotates 360° around left edge
```

**🌟 Power Mode: `anim-group`** (Staggered Animations)
```md-after
::: ul anim-group anim-slide-left anim-zoom
    ::: li | Item 1 (0ms delay)
    ::: li | Item 2 (~84ms delay)
    ::: li | Item 3 (~188ms delay)
    ::: li | Item 4 (~295ms delay)
    // Delays follow smooth sine curve: 100ms per 10 items
```

--

**Per Item Origins** (Dynamic Effects)
```md-after
::: ul anim-group anim-iris anim-rotate
    ::: li --origin="33% 50%" | Each item opens from different origin
    ::: li --origin="50% 50%" | With rotation
    ::: li --origin="67% 50%" | Staggered naturally
```

**Advanced Combinations**
```md-after.collapsed
::: columns anim-group
    ::: block anim-slide-left border="1px solid red" padding="10px"
        Slide in from left
    ::: block anim-zoom border="1px solid green" padding="10px"
        Zoom in
    ::: block anim-rotate --angle=60deg border="1px solid blue" padding="10px"
        Rotate 60°
    ::: block anim-slide-up anim-zoom border="1px solid orange" padding="10px"
        Slide up + Zoom

::: block-red anim-elastic anim-blur --blur=20px
    Elastic bounce with heavy blur!

::: block anim-flip-x anim-zoom --origin="center bottom"
    Flips up from bottom while zooming!
```

--

### ✨ Key Features

- ✅ **Fully Composable** - Mix any animations by stacking classes
- ✅ **Universal `--origin`** - Controls transform-origin AND iris center position
- ✅ **No order dependency** - `anim-zoom anim-rotate` = `anim-rotate anim-zoom`
- ✅ **Smart stagger** - `anim-group` auto-calculates delays with sine curve (100ms/10 items)
- ✅ **Per item positioning** - Use `--origin` per item on children of `anim-group` for dynamic effects
- ✅ **Print-friendly** - All animations visible in print/PDF mode
- ✅ **No reverse animation** - Instantly visible on backward navigation
- ✅ **Easy customization** - Override any variable inline or globally

### 🎯 Pro Tips

1. **Combine wisely**: `anim-slide-up anim-zoom anim-rotate` creates dramatic entrances
2. **Use `anim-group` for lists**: Automatically staggers children for smooth reveals
3. **Control origin**: Set `--origin` to change rotation/zoom/iris center point
5. **Test combinations**: 27+ base animations = **1000+ possible combinations!**
6. **Timing matters**: Adjust `--time` for slower/faster effects
7. **Iris from corners**: Use `--origin: 0% 0%` or `100% 100%` for dramatic reveals

**The power is in composition!** 🚀
'''