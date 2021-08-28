# Author: Abdul Saboor
# CSS for ipyslides
light_root = ''':root {
	--heading-fg: navy;
	--text-fg: black;
	--text-bg: #F3F3F3;
	--quote-bg: white;
	--quote-fg: purple;
	--tr-odd-bg: white;
	--tr-hover-bg: lightblue;
	--accent-color: navy;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
'''
dark_root = ''':root {
	--heading-fg: snow;
	--text-fg: white;
	--text-bg: #21252B;
	--quote-bg: #22303C;
	--quote-fg: powderblue;
	--tr-odd-bg: black;
	--tr-hover-bg: gray;
	--accent-color: snow;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
'''
inherit_root = """:root {
	--heading-fg: var(--jp-inverse-layout-color1,navy);
	--text-fg:  var(--jp-inverse-layout-color0,black);
	--text-bg: var(--jp-layout-color0,#F3F3F3);
	--quote-bg:var(--jp-layout-color2,white);
	--quote-fg: var(--jp-inverse-layout-color4,purple);
	--tr-odd-bg: var(--jp-layout-color2,white);
	--tr-hover-bg:var(--jp-border-color1,lightblue);
 	--accent-color:var(--jp-brand-color2,navy);
	--text-size: __text_size__; /* Do not edit this, this is dynamic variable */
}
"""

def style_html(style_root = inherit_root):
	return '<style>\n' + style_root + ''' 
.cell-output-ipywidget-background {
    background: var(--theme-background,inherit) !important;
    margin: 8px 0px;} /* VS Code */
.SlidesWrapper *:not(.fa):not(i):not(span) {
   font-family: sans-serif, "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" ;
}
.SlidesWrapper code>span {
   font-family: "Cascadia Code","Ubuntu Mono","Courier New";
}
.textfonts .SlidesWrapper {max-height:calc(90vh - 100px);} /* in case of embed slides */ 
.SlidesWrapper {
	margin: auto;
	padding: 0px;
	background:var(--text-bg);
	font-size: var(--text-size);
	max-width:100vw; /* This is very important */
 }
.SlidesWrapper .panel {
    background:var(--text-bg) !important;
    position:absolute;
    border:none;
    padding: 8px !important;
    width: 60% !important;
    z-index:101;
    top:0px !important;
    left:0px !important;
    box-shadow: 0 0 20px 20px var(--quote-bg);
}
.SlidesWrapper .panel>div:first-child {
    box-shadow: inset 0 0 8px var(--quote-bg);
    padding:4px;
    height:32px!important;
}
.SlidesWrapper .panel>div:first-child:hover,
.SlidesWrapper .panel>div:first-child:focus {height: 50% !important;}
.SlidesWrapper .panel>div:last-child {padding-top:16px;}
.SlidesWrapper .columns {width:max-content;max-width:95%;display:inline-flex;flex-direction:row;column-gap:2em;}

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
    right:0px !important;
    bottom:0px !important;
    z-index:98; /* below mpl */
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
    .SlidesWrapper .textfonts {padding-bottom: 50px !important;}
    .NavWrapper .progress {height:4px !important;margin-top:-2px !important;}
    .SlidesWrapper .columns {max-width:95%;display:flex;flex-direction:column;}
    .SlidesWrapper .columns>div[style] {width:100%!important;} /* important to override inline CSS */
    .prog_slider_box {
    	width: 40%;
    	opacity:0;
	}
}
 
.jp-RenderedHTMLCommon {font-size: var(--text-size);} /* For Voila */

.SlidesWrapper h1,h2,h3,h4,h5,h6{
	color:var(--heading-fg);
 	text-align:center;
	overflow:hidden; /* FireFox */
}
.SlidesWrapper .widget-inline-hbox .widget-readout  {box-shadow: none;color:var(--text-fg) !important;}
.SlidesWrapper .textfonts h1 {margin-block: unset;font-size: 3em;  line-height: 1.5em;}
.SlidesWrapper .textfonts h2 {margin-block: unset;font-size: 2.5em;line-height: 1.5em;}
.SlidesWrapper .textfonts h3 {margin-block: unset;font-size: 2em;  line-height: 1.5em;}
.SlidesWrapper .textfonts h4 {margin-block: unset;font-size: 1.5em;line-height: 1.5em;}
.SlidesWrapper .textfonts h5 {margin-block: unset;font-size: 1em;  line-height: 1.5em;}

.SlidesWrapper .widget-inline-hbox .widget-label,
.SlidesWrapper .widget-inline-hbox .widget-readout  {
    color:var(--text-fg);
}
  
.SlidesWrapper :is(.textfonts,.panel,.NavWrapper) :is(p,ul,ol,li),
.SlidesWrapper>:not(div), /* Do not change jupyterlab nav items */
.SlidesWrapper footer {  
	color: var(--text-fg);
}
#jp-top-panel, #jp-bottom-panel, #jp-menu-panel {color: inherit;}

.SlidesWrapper pre, .SlidesWrapper code {
    color: var(--text-fg)!important;
    padding: 0px 4px !important;
    overflow-x: auto !important;
    background: var(--quote-bg) !important;
}

.SlidesWrapper blockquote, .SlidesWrapper blockquote>p {
	background: var(--quote-bg);
	color: var(--quote-fg) !important;
}
    
.SlidesWrapper table {
 	border-collapse: collapse !important;
    min-width:auto;
    width:100%;
    font-size: small;
    word-break:break-all;
    overflow: auto;
	color: var(--text-fg)!important;
	background: var(--text-bg)!important;
}
.SlidesWrapper tbody>tr:nth-child(odd) {background: var(--tr-odd-bg)!important;}
.SlidesWrapper tbody>tr:nth-child(even) {background: var(--text-bg)!important;}
.SlidesWrapper tbody>tr:hover {background: var(--tr-hover-bg)!important;}

.NavWrapper {max-width:100% !important;}
.NavWrapper .progress {background: var(--quote-bg)!important;}
.NavWrapper .progress .progress-bar {background: var(--accent-color)!important;}
.SlidesWrapper button {
    color: var(--accent-color)!important;
    border-radius:0px;
    background: transparent !important;}

.SlidesWrapper .widget-dropdown > select, 
.SlidesWrapper .widget-dropdown > select > option {
	color: var(--text-fg)!important;
	background: var(--text-bg)!important;
}
.SlidesWrapper .widget-play .jupyter-button {
    background: var(--quote-bg);
    color: var(--accent-color)!important;
}
.SlidesWrapper .panel button, .SlidesWrapper .panel .jupyter-button{ 
    border: 1px solid var(--accent-color);
    border-radius: 4px;
    }
.SlidesWrapper .jupyter-button:hover:enabled,
.SlidesWrapper .jupyter-button:focus:enabled {
    outline:none !important;
    opacity:1 !important;
    box-shadow:none !important;
    background:var(--hover-bg);
}
.sidecar-only {background: transparent;box-shadow: none;min-width:max-content; opacity:0.6;}
.sidecar-only:hover, .sidecar-only:focus {opacity:1;}
/* Make Scrollbars beautiful */
.SlidesWrapper, .SlidesWrapper  * { /* FireFox <3*/
    scrollbar-width: thin;
    scrollbar-color:var(--tr-odd-bg) transparent;
}
/* Other monsters */  
:not(.jp-Notebook, .CodeMirror-hscrollbar, .CodeMirror-vscrollbar)::-webkit-scrollbar {
    height: 4px;
    width: 4px;
    background: none;
}
:not(.jp-Notebook, .CodeMirror-hscrollbar, .CodeMirror-vscrollbar)::-webkit-scrollbar-thumb {
    background: var(--tr-odd-bg);
}
:not(.jp-Notebook, .CodeMirror-hscrollbar, .CodeMirror-vscrollbar)::-webkit-scrollbar-corner {
    display:none;
    background: none;
}   

/* Matplotlib figure SVG */
div.fig-container>svg{
  background: var(--text-bg);
  transition: transform .2s; /* Animation */
}      
</style>'''

animation_css = '''<style>
.textfonts :is(h1,h2,h3,h4,h5,h6,p,ul,li,ol,blockquote,q,table,pre) {
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
</style>'''

main_layout_css = '''<style>
.SlidesWrapper .textfonts { align-items: center;}
a.jp-InternalAnchorLink { display: none !important;}
.widget-inline-hbox .widget-readout  { min-width:auto !important;}
.jupyterlab-sidecar .SlidesWrapper,
.jp-LinkedOutputView .SlidesWrapper {
    width: 100% !important; height: 100% !important;
}
.SlidesWrapper pre, code { background:inherit !important; color: inherit !important;
                height: auto !important; overflow:hidden;}
                
.jupyterlab-sidecar .SlidesWrapper .voila-sidecar-hidden,
.jp-LinkedOutputView .SlidesWrapper .voila-sidecar-hidden,
#rendered_cells .SlidesWrapper .voila-sidecar-hidden{
    display: none;
}
/* next Three things should be in given order */
.sidecar-only {display: none;} /* No display when ouside sidecar,do not put below next line */
.jupyterlab-sidecar .sidecar-only, .jp-LinkedOutputView>div .sidecar-only,
.jp-Cell-outputArea>div .sidecar-only {display: block;}
.textfonts .SlidesWrapper .sidecar-only {display: none;} /* No fullscreen for embeded slides */ 
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

fullscreen_css = '''<style>
/* Works in Sidecar and Linked Output View */
.jupyterlab-sidecar > .jp-OutputArea-child, 
.SlidesWrapper, 
.jp-LinkedOutputView>div,
.jp-Cell-outputArea>div {
    flex: 1;
    position: fixed;
    bottom: 0px;
    left: 0px;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 100;
    margin: 0px;
    padding: 0;
    background:var(--text-bg);
} 
.textfonts .SlidesWrapper { position:relative;width:90%;max-width:100%;height:unset;left:unset;bottom:unset;}  
.jp-SideBar.lm-TabBar, .f17wptjy, #jp-bottom-panel { display:none !important;}
#jp-top-panel, #jp-menu-panel {display:none !important;} /* in case of simple mode */
.lm-DockPanel-tabBar {display:none;}
.SlidesWrapper .voila-sidecar-hidden{display: none;} 
</style>'''

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
Assuming you have `ls = LiveSlides()`
- Edit and test cells in `ls.convert2slides(False)` mode.
- Run cells in `ls.convert2slides(True)` mode from top to bottom. 
- `%%slide integer` on cell top auto picks slide and %%title auto picks title page.
- You can use context managers like `ls.slide()` and `ls.title()` in place of `%%slide` and `%%title` respectively.

```python
import ipyslides as isd 
isd.initilize() #This will create a title page and parameters in same cell
slides = isd.core.LiveSlides() #Collects and build slides, auto refresh when content of slide is changed.
slides.insert_after(1,*objs,func) #This will create as many slides after the slide number 1 as length(objs)
#create a rich content title page with `%%title` or \n`with title():\n    ...`\n context manager.
slides.show() # Use it once to see slides
```
- LiveSlides should be only in top cell as it collects slides in local namespace, auto refresh is enabled.
> Note: For LiveSlides('A'), use %%slideA, %%titleA, LiveSlides('B'), use %%slideB, %%titleB so that they do not overwite each other's slides.

> Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.

> For JupyterLab >=3, you can do `pip install sidecar` as bonus.

> After clicking a button you can use Enter key to forward/backward slides. If you click on slider handle between two buttons,
> (by hovering between buttons) you can use keyboard to navigate slides. 
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
'''