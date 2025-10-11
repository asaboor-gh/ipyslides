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
 `raw-text`         | Text will be shown as printed style. {: .raw-text}
 `zoom-self`        | Zooms object on hover, when Zoom is enabled. {: .zoom-self}
 `zoom-child`       | Zooms child object on hover, when Zoom is enabled.
 `no-zoom`          | Disables zoom on object when it is child of 'zoom-child'.

Besides these CSS classes, you always have `Slide.set_css`, `Slides.html('style',...)` functions at your disposal.
'''

xmd_syntax = rf'''
## Extended Markdown
                                       
Extended syntax on top of [Python-Markdown](https://python-markdown.github.io/) supports almost full presentation from Markdown.

**Presentation Structure**{{.text-big}}

Slides & Frames Separators
: Triple dashes `---` is used to split text in slides inside markdown content of `Slides.build` function or markdown file.
Double dashes `--` is used to split text in frames. Alongwith this `%++` can be used to increment text on framed slide.

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
- With citations mode set as 'footnote', you can add alert`refs\`ncol_refs\`` or code`Slides.refs` to add citations anywhere on slide. If `ncol_refs` is not given, it will be picked from layout settings.
- Force a citation to be shown inline by appending a ! even in footnote mode, such as alert`\@key!` or alert`cite\`key1,key2!\``.
- In the synced markdown file (also its included files) through `Slides.sync_with_file`, you can add citations with block sytnax:                             
code["markdown"]`
 ::: citations [inline or footnote]
    \@key1: Saboor et. al., 2025
    \@key2: A citations can span multiple lines, but key should start on new line
`

---

**Content Blocks**{{.text-big}}

The general block syntax is `::: type-or-classes [args] attributes`.

- You can use `/` to divide css properties from node attributes such as `::: note-info border="1px solid red" / id="mynote" dir="ltr"`. Node attributes come after `/`.
- You can create inline blocks by adding `|` in header (only takes effect if body is empty), such as `::: block-red | text` will create a block with red background and text inside.
- Both `|` and `/` can be escaped in header by backslah to interpret them as literal characters instead of block body and attributes splitters respectively. 
- You can optionally continue block header on next multiple adjacent lines with `:` at start of each line. This multiline header is not available in \`\`\` blocks.
- Theme colors such as `fg1=red bg2=black` upto 3, can be assigned for each block to tweak look and feel of content.
- Blocks can be escaped by having a space before `:::` at start of line, such as ` ::: block-red` will not be parsed as block.
- Some block levels HTML tags are handled specially, such as p, pre, ul, ol, blockquote, details, summary, table.
- You can use `::: block` nested inside \`\`\` block at same indentation level but otherwise must be correctly indented.

::: table 1 4 caption-side=top bg3=#8988
    This table, itself created with a `::: table` block, lists common block types and their usage.
    Each of these blocks can have additional CSS classes and properties, besides the limited set shown below.
    
    | Block Syntax      | Description                                                                                                 |
    |:----------------- |:----------------------------------------------------------------------------------------------------------- |
    | `::: raw/pre`     | Raw text or preformatted text, no markdown parsing. Use `raw` or `pre` as first word in block. |
    | `::: code `       | Code block with syntax highlighting, parameters are passed to highlight function. |
    | `::: tag or classes` | tags are block level elements such as `p`, `details`, `summary`, `table`, `center`, etc. |
    | `::: columns/multicol [widths]` | Create columns with relative widths, e.g. `columns 4 6` for 40% and 60% width. Use `+++` separator to reveal content incrementally/make display columns. |
    | `::: md-[pos]` | Parse markdown in the block, with showing source code at `pos=[before,after,left,right]`. Add `-c` to collapse code and show on click. |
    | `::: table [col widths]` | Create a table with optional column widths, e.g. `::: table 1 2` for 33% and 66% width. Use `caption-side=top/bottom` to place caption on top/bottom.|
    | `::: citations [inline or footnote]` | Add citations in the block, with `inline` or `footnote` mode. Use `\@key: value` syntax to add citations in block. |
    | `::: display css_classes` | Create a block with specific CSS classes forcing display mode, it can break dom flow, but usefull to embed widget variables under blocks. |

---

**Layouts**{{.text-big}}

Inline Columns
: Inline columns/rows can be added by using alert`stack\`Column A || Column B\`` sytnax. You can escape pipe `|` with `\|` to use it as text inside stack. See at end how to nest such stacking.

Block Columns
: You can create columns using `::: columns` or `::: multicol` syntax. 
Column separator is triple plus `+++` if intended in display mode.

```md-before
::: columns 6 1 4 block-blue 
: border="1px dashed red"
    ::: block-red
        - `::: columns/muticol` with a +++ separator act like `write` command and reveal content incrementally when `%++` is used
        - children inside `columns` picks relative width from parent's `columns` block evem if '+++' is not used.
          In thise children should be visually blocks themselves like headings, paragraphs, lists etc or wrapped in `::: block` to make them obvious blocks like this one.
        - CSS classes and attributes can be used to style columns besides relative widths.
    
    ::: block-blue border="1px solid red" | alert`inline` color`block` text 
    
    ::: block-yellow border="2px solid orange" padding="10px"
        - Top level `columns` is necessary to create columns or use simple block with `display=flex`.
        and frame speactor is used at end of block.
        - Indentation is important, so use tabs or spaces consistently.
```

---

**Code Display**{{.text-big}}

Inline Code
: Inline code can be highlighted using alert`code\`code\`` syntax, e.g. color`code\`print('Hello')\`` → code`print('Hello')`.

Code Blocks
: Use standard markdown fenced code blocks or `::: code` blocks for syntax highlighting.

```md-left
    ```python
    print('Hello, I was highlighted from a code block!')
    ```
    
    ::: code language=bash name=Shell lineno=False style=vim
        echo "Hello, I was highlighted from a code block!"
        ls -l | grep ".py" | wc -l
```  
- In ` ::: code ` block, you need to set parameters that are passed to `code` function, such as `language`, `name`, `lineno`, `css_class`, etc.
- The \`\`\` code block does act like `::: code ` block and supports same parameters.

---

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
    
---

**Inline Python Functions**{{.text-big}}

Functions (that can also take extra args [python code as strings] as alert`func[arg1,x=2,y=A]\`arg0\``) include:

::: block-red
{_special_funcs}

::: note-info
    You can also use `Slides.esc`/`isd.esc` class to lazily escape variables/expressions/output of functions from being parsed inside f-strings.
    This should be rarely used when your markdown contains a lot of $ \LaTeX $ equations to avoid excessively escaping them with curly braces in favor of few escaped variables.

Upto 4 level nesting is parsed in inline functions using (level + 1) number of alert`/` (at least two) within backticks in functions given below. 
```md-left
stack[(6,4),css_class="block-blue"]`////
    This always parse markdown in `returns=True` mode. ||
    stack[css_class="info"]`/// B ||
        color["skyblue"]`//alert`Alerted Text` Colored Text //`
    ///` 
////`
```

---
**General Syntax**{{.text-big}}

- Use alert`include\`markdown_file.md[optional list slicing to pick lines from file such as [2:5], [10:]]\`` to include a file in markdown format.
- Use alert`fa\`icon_name\`` to add FontAwesome icons, e.g. fa\`arrow-right\` → fa`arrow-right`, fa\`check\` → fa`check`, fa\`info-circle\` → fa`info-circle` etc.
- Use syntax \`<link:[unique id here]:origin label>\` and \`<link:[unique id here same as origin]:target [back_label,optional]>\` to jump between slides. See `Slides.link` for more details.
- Cells in markdown table can be spanned to multiple rows/columns by attributes `| cell text \{{: rowspan="2" colspan="1"}}|` inside a cell, should be a space bewteen text and attributes.
- Escape a backtick with backslash, i.e. alert`\\` → \``, other escape characters include alert`@, %, /, |`. In Python >=3.12, you need to make escape strings raw, including the use of $ \LaTeX $ and re module.
- Use `_\`sub\`` and `^\`sup\``  for subscript and superscript respectively, e.g. H_`2`O, E = mc^`2`.
- See `Slides.css_styles` for available CSS classes to use in markdown blocks and other places.
- Definition list syntax:
```md-left
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