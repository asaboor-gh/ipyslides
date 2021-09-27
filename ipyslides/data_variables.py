# Author: Abdul Saboor
# CSS for ipyslides
light_root = ''':root {
	--heading-fg: navy;
	--primary-fg: black;
	--primary-bg: white;
	--secondary-bg: #dce5e7;
	--secondary-fg: #454545;
	--tr-odd-bg: whitesmoke;
	--tr-hover-bg: lightblue;
	--accent-color: navy;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
'''
dark_root = ''':root {
	--heading-fg: snow;
	--primary-fg: white;
	--primary-bg: black;
	--secondary-bg: #121212;
	--secondary-fg: powderblue;
	--tr-odd-bg: #181818;
	--tr-hover-bg: #264348;
	--accent-color: #d9e0e3;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
'''
inherit_root = """:root {
	--heading-fg: var(--jp-inverse-layout-color1,navy);
	--primary-fg:  var(--jp-inverse-layout-color0,black);
	--primary-bg: var(--jp-layout-color0,#cad3d3);
	--secondary-bg:var(--jp-layout-color2,#dce5e7);
	--secondary-fg: var(--jp-inverse-layout-color4,#454545);
	--tr-odd-bg: var(--jp-layout-color2,#e6e7e1);
	--tr-hover-bg:var(--jp-border-color1,lightblue);
 	--accent-color:var(--jp-brand-color2,navy);
	--text-size: __text_size__; /* Do not edit this, this is dynamic variable */
}
"""

def style_html(style_root = inherit_root):
	return '<style>\n' + style_root + ''' 
.SlideArea .TextBox { /* general text box for writing inline refrences etc. */
    font-size: 70% !important; 
    line-height: 80% !important;
    position:relative; 
    left:initial;
    top:initial;
    padding:2px 4px;
    color: var(--secondary-fg);
}
.SlidesWrapper .jupyter-widgets:not(button) { color: var(--primary-fg) !important;} /* All widgets text */
.jp-RenderedHTMLCommon { padding:0px;padding-right: 0px !important;font-size: var(--text-size);} /* important for central layout */
.jp-RenderedHTMLCommon :not(pre) > code { background-color: var(--secondary-bg); color:var(--secondary-fg);}
.jp-LinkedOutputView, .SlidesWrapper, .SlidesWrapper * { box-sizing:border-box;}
.cell-output-ipywidget-background { /* VSCode issue */
    background: var(--theme-background,inherit) !important;
    margin: 8px 0px;} /* VS Code */
.SlidesWrapper *:not(.fa):not(i):not(span) {
   font-family: sans-serif, "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" ;
}

.SlidesWrapper code>span {
   font-family: "SimSun-ExtB", "Cascadia Code","Ubuntu Mono", "Courier New";
   font-size: 80% !important;
}
.SlideArea .SlidesWrapper {max-height:calc(95vh - 100px);} /* in case of embed slides */ 
.SlidesWrapper {
	margin: auto;
	padding: 0px;
	background:var(--primary-bg);
	font-size: var(--text-size);
    color:var(--primary-fg);
	max-width:100vw; /* This is very important */
 }
.SlidesWrapper>:not(div), /* Do not change jupyterlab nav items */
.SlidesWrapper * {  
	color: var(--primary-fg);
}
.SlidesWrapper .panel {
    background:var(--primary-bg) !important;
    position:absolute;
    border:none;
    padding: 8px !important;
    width: 60% !important;
    z-index:102;
    top:0px !important;
    left:0px !important;
    box-shadow: 0 0 20px 20px var(--secondary-bg);
}
.SlidesWrapper .panel .float-cross-btn {
    position: absolute;
    top:8px;
    right:4px;
    width: 36px;
    height: 36px;
    border:none !important;
    outline:none !important;
    font-size: 24px;
    background: var(--primary-bg) !important;
}
.SlidesWrapper .panel>div:first-child {
    height:auto;
}
.SlidesWrapper .panel>div:last-child {padding-top:16px;min-height:max-content;} 

.SlidesWrapper .columns {width:99%;max-width:99%;display:inline-flex;flex-direction:row;column-gap:2em;height:auto;}

.SlidesWrapper .widget-hslider .ui-slider,
.SlidesWrapper .widget-hslider .ui-slider .ui-slider-handle {
    background: var(--accent-color);
    border: 1px solid var(--accent-color);
}

.prog_slider_box {
    width: 16px;
    padding: 0px 4px;
    opacity:0;
    overflow:hidden;
}
.prog_slider_box:hover, .prog_slider_box:focus {
    width: 50%;
    min-width: 30%; /* This is very important to force it */
    justify-content: center;
    opacity: 1;
}
.NavWrapper nav-box {
    align-items: bottom;
    height: max-content;
    justify-content: flex-start;
    }
.SlidesWrapper .arrows {opacity:0.4;font-size: 36px;padding:4px;}
.SlidesWrapper .arrows:hover, .SlidesWrapper .arrows:focus { opacity:1;}
.SlidesWrapper .controls {
    position:absolute;
    right:16px !important;
    bottom:0px !important;
    z-index:98; /* below matplotlib fullsreen */
    padding;0 !important;
    justify-content: flex-end !important;
    align-items:center !important;
    margin-bottom:16px !important;
    color: var(--accent-color);
    
}

@media screen and (max-width: 702px) {
    .SlidesWrapper .panel {width:100% !important;}
    .SlidesWrapper .controls {bottom:30px!important;right:0 !important;width:100%;justify-content: space-around !important;}
	.SlidesWrapper .controls button {width:30% !important;}
    .SlidesWrapper .SlideArea {padding-bottom: 50px !important;}
    .NavWrapper .progress {height:4px !important;}
    .SlidesWrapper .columns {width:100%;max-width:100%;display:flex;flex-direction:column;}
    .SlidesWrapper .columns>div[style] {width:100%!important;} /* important to override inline CSS */
    .prog_slider_box {
    	width: 40%;
    	opacity:0;
	}
}

.SlidesWrapper h1,h2,h3,h4,h5,h6{
	color:var(--heading-fg);
 	text-align:center;
	overflow:hidden; /* FireFox */
}
.SlidesWrapper .widget-inline-hbox .widget-readout  {box-shadow: none;color:var(--primary-fg) !important;}
.SlidesWrapper .SlideArea h1 {margin-block: unset;font-size: 3em;  line-height: 1.5em;}
.SlidesWrapper .SlideArea h2 {margin-block: unset;font-size: 2.5em;line-height: 1.5em;}
.SlidesWrapper .SlideArea h3 {margin-block: unset;font-size: 2em;  line-height: 1.5em;}
.SlidesWrapper .SlideArea h4 {margin-block: unset;font-size: 1.5em;line-height: 1.5em;}
.SlidesWrapper .SlideArea h5 {margin-block: unset;font-size: 1em;  line-height: 1.5em;}

.SlideArea .footnote *,  .SlideArea .footnote li::marker {
    font-size:0.8em;
    line-height: 0.6em;
}
.SlideArea hr {
    margin:0 !important;
}
.SlideArea .footnote ol {
    margin-top: 0.5em !important;
}

.SlidesWrapper .widget-inline-hbox .widget-label,
.SlidesWrapper .widget-inline-hbox .widget-readout  {
    color:var(--primary-fg);
} 

#jp-top-panel, #jp-bottom-panel, #jp-menu-panel {color: inherit;}

.SlidesWrapper pre {
    color: var(--primary-fg)!important;
    padding: 0px 4px !important;
    overflow-x: auto !important;
    background: var(--secondary-bg) !important;
}
.SlidesWrapper pre>code {background:transparent !important;color: var(--primary-fg)!important;}
.SlidesWrapper blockquote, .SlidesWrapper blockquote>p {
	background: var(--secondary-bg);
	color: var(--secondary-fg);
}
    
.SlidesWrapper table {
 	border-collapse: collapse !important;
    min-width:auto;
    width:100%;
    font-size: small;
    word-break:break-all;
    overflow: auto;
	color: var(--primary-fg)!important;
	background: var(--primary-bg)!important;
}
.SlidesWrapper tbody>tr:nth-child(odd) {background: var(--tr-odd-bg)!important;}
.SlidesWrapper tbody>tr:nth-child(even) {background: var(--primary-bg)!important;}
.SlidesWrapper tbody>tr:hover {background: var(--tr-hover-bg)!important;}

.NavWrapper {max-width:100% !important;}
.NavWrapper .progress {background: var(--secondary-bg)!important;}
.NavWrapper .progress .progress-bar {background: var(--accent-color)!important;}
.SlidesWrapper button {
    color: var(--accent-color)!important;
    border-radius:0px;
    background: transparent !important;}

.SlidesWrapper .widget-dropdown > select, 
.SlidesWrapper .widget-dropdown > select > option {
	color: var(--primary-fg)!important;
	background: var(--primary-bg)!important;
}
.SlidesWrapper .widget-play .jupyter-button {
    background: var(--secondary-bg);
    color: var(--accent-color)!important;
}
.SlidesWrapper :is(.SlideBox, .panel) :is(button, .jupyter-button) { 
    border: 1px solid var(--accent-color);
    border-radius: 4px;
    min-height: 28px;
}

.SlidesWrapper .jupyter-button:hover:enabled,
.SlidesWrapper .jupyter-button:focus:enabled {
    outline:none !important;
    opacity:1 !important;
    box-shadow:none !important;
    background:var(--hover-bg);
    text-shadow: 0 0 2px var(--primary-bg), 0 0 4px var(--accent-color);
}
.SlideArea .SlidesWrapper :is(.NavWrapper, .controls) button{ border: none !important;} /* embeded slides */
.sidecar-only {background: transparent;box-shadow: none;min-width:max-content; opacity:0.6;}
.sidecar-only:hover, .sidecar-only:focus {opacity:1;}

/* Make Scrollbars beautiful */
.SlidesWrapper, .SlidesWrapper  * { /* FireFox <3*/
    scrollbar-width: thin;
    scrollbar-color:var(--tr-odd-bg) transparent;
}
/* Other monsters */  
.SlidesWrapper ::-webkit-scrollbar {
    height: 4px;
    width: 4px;
    background: none !important;
}
.SlidesWrapper ::-webkit-scrollbar-thumb {
    background: var(--tr-odd-bg) !important;
}
.SlidesWrapper ::-webkit-scrollbar-corner {
    display:none !important;
    background: none  !important;
}   
.CodeMirror {padding-bottom:8px !important; padding-right:8px !important;} /* Jupyter-Lab make space in input cell */
/* Matplotlib figure SVG */
div.fig-container>svg{
  background: var(--primary-bg);
  transition: transform .2s; /* Animation */
}    
.pygal-chart {  /* it doesnt show otherwise */
    min-width:300px;
    width:100%;
    height:auto;
}  
</style>'''

animations = {'zoom':'''<style>
.SlideBox {
    animation-name: zoom; animation-duration: 600ms;
    animation-timing-function: linear;
}
@keyframes zoom {
     0% { transform: scale(0.05); }
    25% { transform: scale(0.35); }
    50% { transform: scale(0.55); }
	75% { transform: scale(0.85); }
   100% { transform: scale(1); }
}
</style>''',
'slide': '''<style>
.SlideBox {
    animation-name: slide; animation-duration: 600ms;
    animation-timing-function: cubic-bezier(0.1, -0.6, 0.2, 0);
}
@keyframes slide {
     from { transform: translateX(120%);}
     to { transform: translateX(0); }
}
</style>
'''
}

main_layout_css = '''<style>
.SlidesWrapper .SlideArea { align-items: center;}
a.jp-InternalAnchorLink { display: none !important;}
.widget-inline-hbox .widget-readout  { min-width:auto !important;}
.jupyterlab-sidecar .SlidesWrapper,
.jp-LinkedOutputView .SlidesWrapper {
    width: 100% !important; height: 100% !important;
}               
.jupyterlab-sidecar .SlidesWrapper .voila-sidecar-hidden,
.jp-LinkedOutputView .SlidesWrapper .voila-sidecar-hidden,
#rendered_cells .SlidesWrapper .voila-sidecar-hidden {
    display: none;
}
/* next Three things should be in given order */
.sidecar-only {display: none;} /* No display when ouside sidecar,do not put below next line */
.jupyterlab-sidecar .sidecar-only, .jp-LinkedOutputView>div .sidecar-only,
.jp-Cell-outputArea>div .sidecar-only {display: block;}
.SlideArea .SlidesWrapper .sidecar-only {display: none;} /* No fullscreen for embeded slides */ 
.jp-LinkedOutputView>div {overflow:hidden !important;}


#rendered_cells .SlidesWrapper {
    position: absolute;
    width:100% !important;
    height: 100% !important;
    bottom: 0px !important;
    top: 0px !important;
    tight: 0px !important;
    left: 0px !important;
}
.SlidesWrapper {z-index: 10 !important;}
<style>'''


def editing_layout_css(span_percent = 40):
    return f'''<style>
div.jp-NotebookPanel-notebook div.SlidesWrapper {{
    position:fixed !important;
    right:39px;
    height:calc(100% - 118px) !important;
    width:{span_percent}vw !important;
    bottom:30px !important;
    box-shadow: -2px 0px 2px -1px var(--jp-toolbar-border-color,gray);
}}
div.jp-NotebookPanel-notebook {{
    padding-right: {span_percent}vw !important;
}}
div.jp-NotebookPanel-notebook .height-slider {{
    display: none !important;
}}
</style>
'''

fullscreen_css = '''<style>
/* Works in Sidecar and Linked Output View */
/*.jupyterlab-sidecar > .jp-OutputArea-child,*/ 
/* jp-OutputArea-output>div, .jp-LinkedOutputView>div */
/* No need of above now, works everywhere */
.SlidesWrapper.FullScreen {      
    flex: 1;
    position: fixed;
    bottom: 0px;
    left: 0px;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 100;
    margin: 0px;
    padding: 0;
    background:var(--primary-bg);
} 
.SlideArea .SlidesWrapper { position:relative;width:90%;max-width:95%;height:unset;left:unset;bottom:unset;}  
.jp-SideBar.lm-TabBar, .f17wptjy, #jp-bottom-panel { display:none !important;}
#jp-top-panel, #jp-menu-panel {display:none !important;} /* in case of simple mode */
.lm-DockPanel-tabBar {display:none;}
.SlidesWrapper .voila-sidecar-hidden{display: none;}
.SlidesWrapper.FullScreen .console-btn {display:block;} /* Show console button in fullscreen in jupyterlab only*/
.jupyterlab-sidecar .console-btn {display:none;} /* Hide console button in sidecar as not works there */
html,body {background: var(--primary-bg);} /* Useful for Other tabs when Ctrl + Shift + ],[ pressed */
</style>''' 


navigation_js = '''
let arrows = document.getElementsByClassName('arrows');
let boxes = document.getElementsByClassName('SlidesWrapper');
let mplBtn = document.getElementsByClassName('mpl-zoom');
let winFs = document.getElementsByClassName('window-fs');
/* Keyboard events */
// Find solution for background issues
function keyOnSlides(e) {
    e.preventDefault();
    let key = e.keyCode;
    if (key === 37) { 
        arrows[0].click(); // Prev
        arrows[0].focus();
    } else if (key === 39 || key === 32) { 
        arrows[1].click(); // Next or Spacebar
        arrows[1].focus();
    } else if (key === 90) { 
        mplBtn[0].click(); // Z 
    } else if (key === 88 || key === 68) {
        alert("Pressing X or D,D may cut selected cell! Move cursor away from slides to capture these keys!");
        e.stopPropagation(); // stop propagation to jupyterlab events
        e.cut = false;
        e.deleteCell = false;
        return false;
    } else if (key === 70) { 
        winFs[0].click(); // F
    } else {
        e.stopPropagation(); // stop propagation to jupyterlab events
        return false; // Do not pass other keys
    }; 
    e.stopPropagation(); // stop propagation to jupyterlab events  
};


for (let i = 0; i < boxes.length; i++) {
    boxes[i].onmouseenter = function() {
      document.onkeydown = keyOnSlides; 
    }; 
    boxes[i].onmouseleave = function() {
      document.onkeydown = null; 
    };  
};
'''

mpl_fs_css = '''<style>
/* Pop out matplotlib's SVG on click/hover */
div.fig-container>svg:focus, div.fig-container>svg:hover{
    position:fixed;
    left:100px;
    top:0px;
    z-index:100;
    width: calc(100vw - 200px);
    height: 100%;
    box-shadow: 0px 0px 200px 200px rgba(15,20,10,0.8); 
}  
@media screen and (max-width: 702px) {
    div.fig-container>svg:focus, div.fig-container>svg:hover{
    width:100%;
    height: calc(100vh - 200px);
    top: 100px;
    left:0px;
    }
} 
</style>
'''

loading_svg = '''<div style="position:absolute;left:0;top:0;z-index:51;">
    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 50 50">
  <path fill="var(--accent-color,navy)" d="M25,5A20.14,20.14,0,0,1,45,22.88a2.51,2.51,0,0,0,2.49,2.26h0A2.52,2.52,0,0,0,50,22.33a25.14,25.14,0,0,0-50,0,2.52,2.52,0,0,0,2.5,2.81h0A2.51,2.51,0,0,0,5,22.88,20.14,20.14,0,0,1,25,5Z">
    <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.5s" repeatCount="indefinite"/>
  </path></svg></div>'''
# ONLY INSTRUCTIONS BELOW

more_instructions =f'''# How to Use
### Jupyter Lab Only
Having your cursor over slides:

- Press `Ctrl + Shift + C` to change the theme, create console/terminal etc.
- Press `Ctrl + Shift + [`, `Ctrl + Shift + ]` to switch to other tabs like console/terminal/notebooks and do coding without leaving slides!
- Press `F` to toggle fullscreen mode.

### Jupyter Lab + Others (Notebook, VSCode, Voila etc.)
May not work in others but Lab is optimized.

- Press `Z` to toggle matplotlib zoom mode.
- Press `Space` or right arrow key `>` to advance to next slide, left arrow key `<` to go back.

#### Assuming you have `ls = LiveSlides()`
- Edit and test cells in `ls.convert2slides(False)` mode.
- Run cells in `ls.convert2slides(True)` mode from top to bottom. 
- `%%slide integer` on cell top auto picks slide and %%title auto picks title page.
- You can use context managers like `ls.slide()` and `ls.title()` in place of `%%slide` and `%%title` respectively.

```python
import ipyslides as isd 
isd.initilize() #This will create a title page and parameters in same cell
slides = isd.core.LiveSlides() #Collects and build slides, auto refresh when content of slide is changed.
@slides.slides(1,*objs)
def func(obj):
    write(obj) #This will create as many slides after the slide number 1 as length(objs)
#create a rich content title page with `%%title` or \n`with title():\n    ...`\n context manager.
slides.show() # Use it once to see slides
```
- LiveSlides should be only in top cell as it collects slides in local namespace, auto refresh is enabled.
> Note: For LiveSlides('A'), use %%slideA, %%titleA, LiveSlides('B'), use %%slideB, %%titleB so that they do not overwite each other's slides.

> Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.
'''

settings_instructions = f'''{more_instructions}
### Custom Theme
For custom themes, change above theme dropdown to `Custom`.
You will see a `custom.css` in current folder,edit it and chnage
font scale or set theme to another value and back to `Custom` to take effect. 
> Note: `custom.css` is only picked from current directory.
          
--------
For matching plots style with theme, run following code in a cell above slides.
### Matplotlib
```python
import matplotlib.pyplot as plt
plt.style.use('ggplot')
#plt.style.available() #gives styles list
```
### Plotly
```python
import plotly.io as pio
pio.templates.default = "plotly_white"
#pio.templates #gives list of styles
```
> Tip: Wrap your plotly figures in `plotly.graph_objects.FigureWidget` for quick rendering.
### Altair
```python
import altair as alt
alt.themes.enable('dark')
#alt.themes #gives available themes
```
'''