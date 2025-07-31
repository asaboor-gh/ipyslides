"""
CSS styles and XMarkdown syntax documentation for ipyslides.
This file contains descriptive text strings explaining available formatting options.
"""

from ..xmd import _md_extensions

css_styles = '''
Use any or combinations of these styles in css_class argument of writing functions:
                       
| css_class         | Formatting Style                                                                    
|:------------------|:---------------------------------------------------------
 `text-[value]`     | [value] should be one of tiny, small, big, large, huge.
 `align-[value]`    | [value] should be one of center, left, right.
 `rtl`              | اردو،  فارسی، عربی، ۔۔۔ {: .rtl}
 `info`             | Blue text. Icon ℹ️  for note-info class. {: .info}
 `tip`              | Blue Text. Icon💡 for note-tip class. {: .tip}
 `warning`          | Orange Text. Icon ⚠️ for note-warning class. {: .warning}
 `success`          | Green text. Icon ✅ for note-success class. {: .success}
 `error`            | Red Text. Icon⚡ for note-error class. {: .error}
 `note`             | Text with note icon, can combine other classes as shown above. {: .note}
 `export-only`      | Hidden on main slides, but will appear in exported slides.
 `jupyter-only`     | Hidden on exported slides, but will appear on main slides.
 `block`            | Block of text/objects {: .block}
 `block-[color]`    | Block of text/objects with specific background color from <br> red, green, blue, yellow, cyan, magenta and gray.
 `raw-text`         | Text will be shown as printed style. {: .raw-text}
 `zoom-self`        | Zooms object on hover, when Zoom is enabled. {: .zoom-self}
 `zoom-child`       | Zooms child object on hover, when Zoom is enabled.
 `no-zoom`          | Disables zoom on object when it is child of 'zoom-child'.

Besides these CSS classes, you always have `Slide.set_css`, `Slides.html('style',...)` functions at your disposal.
'''
xmd_syntax = rf'''
**Extended Markdown**{{.text-large}}
                                       
Extended syntax for markdown is constructed to support almost full presentation from Markdown.

**Slides-specific syntax**{{.text-big}}

Notes
: alert`notes\`This is slide notes\``  to add notes to current slide

Slides & Frames Separators
: Triple dashes `---` is used to split text in slides inside markdown content of `Slides.build` function or markdown file.
Double dashes `--` is used to split text in frames. Alongwith this `%++` can be used to increment text on framed slide.

Citations
: - alert`cite\`key1,key2\`` / alert`\@key1,\@key2` to add citation to current slide. citations are automatically added in suitable place and should be set once using `Slides.set_citations` function (or see below).
- With citations mode set as 'footnote', you can add alert`refs\`ncol_refs\`` or hl`Slides.refs` to add citations anywhere on slide. If `ncol_refs` is not given, it will be picked from layout settings.
- Force a citation to be shown inline by appending a ! even in footnote mode, such as alert`\@key!` or alert`cite\`key1,key2!\``.
- In the synced markdown file (also its included files) through `Slides.sync_with_file`, you can add citations with block sytnax:                             
hl["markdown"]`
 ::: citations [inline or footnote]
    \@key1: Saboor et. al., 2025
    \@key2: A citations can span multiple lines, but key should start on new line
`

Sections & TOC
: alert`section\`content\`` to add a section that will appear in the table of contents.
alert`toc\`Table of content header text\`` to add a table of contents. See `Slides.docs()` for creating a `TOC` accompanied by section summary.

**General syntax**{{.text-big}}

- Use alert`fa\`icon_name\`` to add FontAwesome icons, e.g. fa\\`arrow-right\\` → fa`arrow-right`, fa\\`check\\` → fa`check`, fa\\`info-circle\\` → fa`info-circle` etc.
- Use syntax \`<link:[unique id here]:origin label>\` and \`<link:[unique id here same as origin]:target [back_label,optional]>\` to jump between slides. See `Slides.link` for more details.
- Variables can be shown as widgets or replaced with their HTML value (if no other formatting given) using alert`\%{{variable}}` (or legacy alert`\`{{variable}}\``) 
    (should be single curly braces pair wrapped by backticks after other formattings done) syntax. If a format_spec/conversion is provided like
    alert`\%{{variable:format_spec}}` or alert`\%{{variable!conversion}}`, that will take preference.
- A special formatting alert`\%{{variable:nb}}` is added (`version >= 4.5`) to display objects inside markdown as they are displayed in a Notebook cell.
    Custom objects serialized with `Slides.serializer` or serialized by `ipyslides` should be displayed without `:nb` whenever possible to appear in correct place in all contexts. e.g.
    a matplotlib's figure `fig` as shown in `\%{{fig:nb}}` will only capture text representation inplace and actual figure will be shown at end, while `\%{{fig}}` will be shown exactly in place.

::: note-tip
    - Variables are automatically updated in markdown when changed in Notebook for slides built purely from markdown.
        - You can also use hl`Slide[number,].rebuild(**kwargs)` to force update variables if some error happens. This is useful for setting unique values of a variable on each slide.
        - Markdown enclosed in hl`fmt(content, **vars)` will not expose encapsulated `vars` for updates later, like static stuff but useful inside python scripts to pick local scope variable.
        - In summary, variables are resolved by scope in the prefrence `rebuild > __main__`. Outer scope variables are overwritter by inner scope variables.
    - Use unique variable names on each slide to avoid accidental overwriting during update.
    - Varibales used as attributes like `\%{{var.attr}}` and indexing like `\%{{var[0]}}` / `\%{{var["key"]}}` will be update only if `var` itself is changed.
::: note-warning
    alert`\%{{variable:nb}}` breaks the DOM flow, e.g. if you use it inside heading, you will see two headings above and below it with splitted text. Its fine to use at end or start or inside paragraph.                                    

::: note-info
    - Widgets behave same with or without `:nb` format spec. 
    - Formatting is done using `str.format` method, so f-string like literal expressions are not supported, but you don't need to supply variables, just enclose text in `Slides.fmt`.
    - Variables are substituted from top level scope (Notebook's hl`locals()` / hl`globals()`). To use variables from a nested scope, use `Slides.fmt`.

::: note-warning block-red
    - Widgets and display variables are only shown propely in first level of nesting in `::: block` or \`\`\` blocks. Other HTML-like varaibles are shown in all levels.

- Cells in markdown table can be spanned to multiple rows/columns by attributes | cell text \{{: rowspan="2" colspan="1"}}| inside a cell, should be a space bewteen text and attributes.
- Escape a backtick with \\, i.e. alert`\\\` → \``. In Python >=3.12, you need to make escape strings raw, including the use of $ \LaTeX $ and re module.
- alert`include\`markdown_file.md[optional list slicing to pick lines from file such as [2:5], [10:]]\`` to include a file in markdown format. These files are watched for eidts if included in synced markdown file via `Slides.sync_with_file`.
- Inline columns/rows can be added by using alert`stack\`Column A || Column B\`` sytnax. You can escape pipe `|` with `\|` to use it as text inside stack. See at end how to nest such stacking.
- Block multicolumns are made using follwong syntax, column separator is triple plus `+++`:

```md-left
    ```multicol 2 3 .block-blue
        ```md-after
        ## Column A
        ```
    +++
        ## Column B
        ```multicol .block-red
        **Nested Column A**{{: .block-green}}
        +++
        **Nested Column B**{{: .block-yellow}}
        ```
    ```
```

- You can also create columns as below:

```md-before
::: columns 6 4 block-blue 
: border="1px dashed red"
    ::: block-red
        - `::: columns/muticol` with a +++ separator act like `write` command and reveal content incrementally when `%++` is used
        - children inside `columns` picks relative width from parent's `columns` block evem if '+++' is not used.
          In thise children should be visually blocks themselves like headings, paragraphs, lists etc or wrapped in `::: block` to make them obvious blocks like this one.
        - CSS classes and attributes can be used to style columns besides relative widths.
    
    ::: block-yellow border="2px solid orange" padding="10px"
        - Top level `columns` is necessary to create columns or use simple block with `display=flex`.
        and frame speactor is used at end of block.
        - Indentation is important, so use tabs or spaces consistently.
        - You can also use `::: multicol` interchangeably.
```

- Above block syntax is pretty flexible, you can use any CSS class and propeties in general.
- In `::: code` block, you need to set parameters that are passed to `highlight` function, such as `language`, `name`, `lineno`, `css_class`, etc.
    and optionally continue on next multiple adjacent lines with `:` at start of each line. This multline header is not available in \`\`\` blocks.
- You can use `/` to divide css properties from node attributes such as `::: note-info border="1px solid red" / id="mynote" dir="ltr"`. Node attributes come after `/`.
- Some block levels HTML tags are handled specially, such as p, pre, ul, ol, blockquote, details, summary, table.
- Theme colors such as `fg1=red bg2=black` upto 3, can be assigned for each block to tweek look and feel of content.
- You can use `::: block` nested inside \`\`\` block at same indentation level but otherwise need to be indented properly.

::: table 1 4 caption-side=top bg3=#8988
    This table shows how to use block syntax in markdown. It was itself wrapped in `::: table` block.
    Each of these blocks can have additional CSS classes and properties, besides the limited set shown below.
    
    | Block Syntax      | Description                                                                                                 |
    |:----------------- |:----------------------------------------------------------------------------------------------------------- |
    | `::: raw/pre`     | Raw text or preformatted text, no markdown parsing. Use `raw` or `pre` as first word in block. |
    | `::: code`        | Code block with syntax highlighting, parameters are passed to highlight function. |
    | `::: tag or classes` | tags are block level elements such as `p`, `details`, `summary`, `table`, `center`, etc. |
    | `::: columns/multicol [widths]` | Create columns with relative widths, e.g. `columns 4 6` for 40% and 60% width. Use `+++` separator to reveal content incrementally/make display columns. |
    | `::: md-[pos]` | Parse markdown in the block, with showing source code at `pos=[before,after,left,right]`. Add `-c` to collapse code and show on click. |
    | `::: table [col widths]` | Create a table with optional column widths, e.g. `::: table 1 2` for 33% and 66% width. Use `caption-side=top/bottm` to place caption on top/bottom.|
    | `::: citations [inline or footnote]` | Add citations in the block, with `inline` or `footnote` mode. Use `\@key: value` syntax to add citations in block. |
    

- Definition list syntax:
```md-left
Item 1 Header
: Item 1 details
Item 1 Header
: Item 1 details
```

- `md-[left,right,before,after]` and `multicol` support nesting via proper indentation, but it may be broken by display contexts. 
- Code blocks syntax highlighting. (there is an inline highlight syntax as well alert`hl\`code\``)

```python
print('Hello, I was highlighted from a code block!')
```     
                                                                      
- A whole block of markdown can be CSS-classed using syntax
```md-left -c
::: block-yellow
    Some **bold text**
```
    
::: block-red 
    - You can use `Slides.extender` to extend additional syntax using Markdown extensions such as 
        [markdown extensions](https://python-markdown.github.io/extensions/) and 
        [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/).
    - These markdown extensions are inluded by default hl`{_md_extensions}`.
    - You can serialize custom python objects to HTML using `Slides.serializer` function. Having a 
        `__format__` method in your class enables to use {{obj}} syntax in python formatting and \%{{obj}} in extended Markdown.

- Upto 4 level nesting is parsed in inline functions using (level + 1) number of alert`/` (at least two) within backticks in functions given below. 
```md-left -c
stack[(6,4),css_class="block-blue"]`////
    This always parse markdown in `returns=True` mode. ||
    stack[css_class="info"]`/// B ||
        color["skyblue"]`//alert`Alerted Text` Colored Text //`
    ///` 
////`
```

- Other options (that can also take extra args [python code as strings] as alert`func[arg1,x=2,y=A]\`arg0\``) include:
'''