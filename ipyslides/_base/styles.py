# Author: Abdul Saboor
# CSS for ipyslides

theme_roots = {
'Inherit': ''':root {
	--heading-fg: var(--jp-inverse-layout-color1,navy);
	--primary-fg:  var(--jp-inverse-layout-color0,black);
	--primary-bg: var(--jp-layout-color0,#cad3d3);
	--secondary-bg:var(--jp-layout-color2,#dce5e7);
	--secondary-fg: var(--jp-inverse-layout-color4,#454545);
	--tr-odd-bg: var(--jp-layout-color2,#e6e7e1);
	--tr-hover-bg:var(--jp-border-color1,lightblue);
 	--accent-color:var(--jp-brand-color2,navy);
    --pointer-color: var(--md-pink-A400,red);
	--text-size: __text_size__; /* Do not edit this, this is dynamic variable */
}
''',
'Light': ''':root {
	--heading-fg: navy;
	--primary-fg: black;
	--primary-bg: white;
	--secondary-bg: whitesmoke;
	--secondary-fg: #454545;
	--tr-odd-bg: whitesmoke;
	--tr-hover-bg: #D1D9E1;
	--accent-color: navy;
    --pointer-color: red;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
''',
'Fancy': ''':root {
	--heading-fg: #105599;
	--primary-fg: #755;
	--primary-bg: #efefef;
	--secondary-bg: #effffe;
	--secondary-fg: #89E;
	--tr-odd-bg: #deddde;
	--tr-hover-bg: #D1D9E1;
	--accent-color: #955200;
    --pointer-color: #FF7722;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
''',
'Dark': ''':root {
	--heading-fg: snow;
	--primary-fg: white;
	--primary-bg: black;
	--secondary-bg: #121212;
	--secondary-fg: powderblue;
	--tr-odd-bg: #181818;
	--tr-hover-bg: #264348;
	--accent-color: #d9e0e3;
    --pointer-color: blue;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
'''
}


def style_html(style_root = theme_roots['Inherit']):
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
div(.Info, .Warning, .Success, .Error) *:last-child { margin-bottom:0.2em;}
.Info, .Warning, .Success, .Error, 
.Info *, .Warning *, .Success *, .Error * { 
    display:flex;
    flex-direction:column;
    justify-content:flex-start;
    align-items:baseline !important;
}
.Warning { color:#FFAC1C;padding:4px;border-radius:4px; border-left:4px solid #FFAC1C;}
.Warning * { color:#FFAC1C !important;}
.Success { color:green;padding:4px;border-radius:4px; border-left:4px solid green; }
.Success * { color:green !important;}
.Error { color:red;padding:4px;border-radius:4px; border-left:4px solid red; }
.Error * { color:red !important;}
.Info { color:skyblue;padding:4px;border-radius:4px; border-left:4px solid skyblue; }
.Info * { color:skyblue !important;}

.jp-OutputArea-child, .jp-OutputArea-child .jp-OutputArea-output { background: transparent !important;background-color: transparent !important; margin: 0 !important;} /* For some themes */
.SlidesWrapper .jupyter-widgets:not(button) { color: var(--primary-fg) !important;} /* All widgets text */
.jp-RenderedHTMLCommon { padding:0px;padding-right: 0px !important;font-size: var(--text-size);} /* important for central layout */
.jp-RenderedHTMLCommon :not(pre) > code { background-color: var(--secondary-bg); color:var(--secondary-fg);}
.jp-RenderedText, .jp-RenderedText pre {color:var(--primary-fg) !important;}
.widget-html:not(.LaserPointer), .widget-html .widget-html-content > div {display:grid !important; font-size: var(--text-size) !important;} /* Do not use overflow her */
.jp-LinkedOutputView, .SlidesWrapper, .SlidesWrapper * { box-sizing:border-box;}
.cell-output-ipywidget-background { /* VSCode issue */
    background: var(--theme-background,inherit) !important;
    margin: 8px 0px;} /* VS Code */
.SlidesWrapper *:not(.fa):not(i):not(span) { /* Do not edit __textfont__, code does this. */
   font-family: __textfont__, "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" ;
}

.SlidesWrapper code>span { /* Do not edit __codefont__, code does this. */
   font-family: __codefont__, "SimSun-ExtB", "Cascadia Code","Ubuntu Mono", "Courier New";
   font-size: 90% !important;
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
    height: calc(100% - 48px) !important;
    box-shadow: 0 0 20px 20px var(--secondary-bg);
}

.SlidesWrapper .panel .float-cross-btn {
    border:none !important;
    outline:none !important;
    font-size: 24px;
    background: var(--primary-bg) !important;
} 
.SlidesWrapper .panel>div:first-child {
    height:auto;
    min-height:250px;
}
.SlidesWrapper .panel>div:last-child {padding-top:16px;min-height:max-content;} 

.SlideArea .columns {width:99%;max-width:99%;display:inline-flex;flex-direction:row;column-gap:2em;height:auto;}

.SlidesWrapper .widget-hslider .ui-slider,
.SlidesWrapper .widget-hslider .ui-slider .ui-slider-handle {
    background: var(--accent-color);
    border: 1px solid var(--accent-color);
}

.ProgBox {
    width: 16px;
    padding: 0px 4px;
    opacity:0;
    overflow:hidden;
}
.ProgBox:hover, .ProgBox:focus {
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
    color: var(--accent-color) !important;
    
}
.controls .widget-button > i { color: var(--accent-color) !important;}

@media screen and (max-width: __breakpoint_width__) { /* Computed Dynamically in Notebook*/
    .SlidesWrapper .panel {width:100% !important;}
    .SlidesWrapper .controls {bottom:30px!important;right:0 !important;width:100%;justify-content: space-around !important;}
	.SlidesWrapper .controls button {width:30% !important;}
    .SlidesWrapper .SlideArea {padding-bottom: 50px !important;}
    .NavWrapper .progress {height:4px !important;}
    .SlideArea .columns {width:100%;max-width:100%;display:flex;flex-direction:column;}
    .SlideArea .columns>div[style] {width:100%!important;} /* important to override inline CSS */
    .SlideArea .columns .widget-html
    .ProgBox {
    	width: 40%;
    	opacity:0;
	}
}

.SlidesWrapper h1,
.SlidesWrapper h2,
.SlidesWrapper h3,
.SlidesWrapper h4,
.SlidesWrapper h5,
.SlidesWrapper h6 {
	color:var(--heading-fg);
 	text-align: center;
	overflow:hidden; /* FireFox */
}
.SlidesWrapper .widget-inline-hbox .widget-readout  {box-shadow: none;color:var(--primary-fg) !important;}
.SlidesWrapper .SlideArea h1 {margin-block: unset;font-size: 3em;  line-height: 1.5em;}
.SlidesWrapper .SlideArea h2 {margin-block: unset;font-size: 2.5em;line-height: 1.5em;}
.SlidesWrapper .SlideArea h3 {margin-block: unset;font-size: 2em;  line-height: 1.5em;}
.SlidesWrapper .SlideArea h4 {margin-block: unset;font-size: 1.5em;line-height: 1.5em;}
.SlidesWrapper .SlideArea h5 {margin-block: unset;font-size: 1em;  line-height: 1.5em;}
.SlidesWrapper .widget-text input {
    background: var(--primary-bg);
    color:var(--primary-fg);
}

.SlideArea .footnote *,  .SlideArea .footnote li::marker {
    font-size:0.9em;
    line-height: 0.9em;
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

div.codehilite, div.codehilite pre {
    min-width: 100% !important;
    witdh: 100% !important;
    max-width: 100vw !important;
    box-sizing: border-box !important;
}
div.codehilite pre { /* works for both case, do not use > */
    color: var(--primary-fg)!important;
    padding: 8px 4px 8px 4px !important; 
    overflow: auto !important;
    background: var(--secondary-bg) !important;
    counter-reset: line; /* important to add line numbers */
}

div.codehilite code {
    counter-increment: line;
    display:inline-block !important; /* should be on new line */
    width:max-content;
    min-width:100%;
}
div.codehilite code:before{
    content: counter(line,decimal);
    position: sticky;
    top:initial;
    left:-4px;
    padding: 0 8px;
    background:var(--secondary-bg);
    color: var(--secondary-fg);
    display:inline-block; /* should be inline */
    width:1.2em;
    text-align:right;
    -webkit-user-select: none;
    margin-left:-3em;
    margin-right: 8px;
    font-size: 80%;
}
div.codehilite code.code-no-focus {
    opacity:0.3 !important;
}
div.codehilite code.code-focus {
    text-shadow: 0 0 1px var(--primary-bg);
}

div.codehilite {  
    margin: 4px 0px !important; /* Opposite to padding to balance it */
    max-height: 400px; /* Try avoiding important here */
    height: auto !important;
    overflow: auto !important;
    display:inline-flex !important; /* for ::before */
    padding-top: 1.5em !important;
    box-shadow: 0 1.6em 0 0 var(--secondary-bg) inset;
    border-radius:4px!important;
}
div.codehilite::before {
    content: '🔴 🟡 🟢 Python';
    position:absolute;
    font-size:0.7em;
    z-index:2;
    background: var(--secondary-bg);
    border-radius: 8px 8px 0 0;
    box-sizing:border-box;
    margin-top: -2em;
    padding:4px 8px;
    height:2em;
}
.widget-html div.codehilite::before {padding-top: 0 !important;}
div.highlight, .widget-html div.codehilite {display:inline-flex !important;}
.SlidesWrapper div.PyRepr {
    margin: 4px !important;
    white-space:pre !important;
    max-height: 400px;
    height: auto !important;
    overflow: auto !important;
}
div.codehilite pre > code {
    background:transparent !important;
    color: var(--primary-fg)!important;
    white-space: pre !important;
    display:inline-block !important;
    width:auto;
    min-width: 90% !important;
    overflow-wrap: normal !important;
    margin-left:2.2em;
    padding-left: 4px;
}
div.codehilite  code > span {
    white-space: normal !important;
}
div.codehilite pre > code:hover {
    background: var(--tr-hover-bg) !important;
}
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
    border: 1px solid var(--tr-odd-bg) !important; /* Makes it pleasant to view */
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
    background: transparent !important;
}
.codehilite::-webkit-scrollbar { /* important for good display */
    background: var(--secondary-bg) !important;
}
.SlidesWrapper ::-webkit-scrollbar:hover {
    background: var(--secondary-bg) !important;
}
.SlidesWrapper ::-webkit-scrollbar-thumb {
    background: transparent !important;
}
.SlidesWrapper ::-webkit-scrollbar-thumb:hover{
    background: var(--tr-hover-bg) !important;
}
.SlidesWrapper ::-webkit-scrollbar-corner,
.codehilite::-webkit-scrollbar-corner {
    display:none !important;
}   
.CodeMirror {padding-bottom:8px !important; padding-right:8px !important;} /* Jupyter-Lab make space in input cell */
/* Zoom container including Matplotlib figure SVG */

div.zoom-container,
div.zoom-container > * {
    background: var(--primary-bg);
    display:flex !important; /* To align in center */
    flex-direction: column !important; /* To have caption at bottom */
    align-items:center !important;
    justify-content:center !important;
    transition: transform .2s; /* Animation */
}  
  
.pygal-chart {  /* it doesnt show otherwise */
    min-width:300px;
    width:100%;
    height:auto;
}  
.SlideArea .block {
    background: var(--primary-bg);
    border-radius: 4px;
}
div.LaserPointer { /* For laser pointer */
    position:absolute !important;
    width:12px;
    height:12px;
    left:-50px; /* Hides when not required , otherwise handled by javascript*/
    z-index:101; /* below side panel but above zoomed image */
    border-radius:50%;
    border: 2px solid white;
    background: var(--pointer-color);
    box-shadow: 0 0 4px 2px white, 0 0 6px 6px var(--pointer-color);
    display:none; /* Initial setup. Display will be set using javascript only */
    overflow:hidden !important; /* To hide at edges */
}
/* Linked Area */
.jp-LinkedOutputView > div.jp-OutputArea >  div:first-child,
.jp-LinkedOutputView div.SlidesWrapper .height-slider{
   display: none !important;
}
.jp-LinkedOutputView, 
.jp-LinkedOutputView > div.jp-OutputArea,
.jp-LinkedOutputView > div.jp-OutputArea > div.jp-OutputArea-output{
     display:flex;
    height: 100%;
    width:100%;
    padding:0;
    margin:0;
}
.jp-LinkedOutputView div.SlidesWrapper{
    height: 100% !important;
    width: 100% !important;
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
'slide_h': '''<style>
.SlideBox {
    animation-name: slide; animation-duration: 400ms;
    animation-timing-function: cubic-bezier(.2,.7,.8,.9);
}
.SlideBox.Prev { /* .Prev acts when moving slides backward */
    animation-name: slidePrev; animation-duration: 400ms;
    animation-timing-function: cubic-bezier(.2,.7,.8,.9);
}
@keyframes slide {
     from { transform: translateX(100%);}
     to { transform: translateX(0); }
}
@keyframes slidePrev {
     from { transform: translateX(-100%);}
     to { transform: translateX(0); }
}
</style>
''',
'slide_v': '''<style>
.SlideBox {
    animation-name: slide; animation-duration: 400ms;
    animation-timing-function: cubic-bezier(.2,.7,.8,.9);
}
.SlideBox.Prev { /* .Prev acts when moving slides backward */
    animation-name: slidePrev; animation-duration: 400ms;
    animation-timing-function: cubic-bezier(.2,.7,.8,.9);
}
@keyframes slide {
     from { transform: translateY(100%);}
     to { transform: translateY(0); }
}
@keyframes slidePrev {
     from { transform: translateY(-100%);}
     to { transform: translateY(0); }
}
</style>
'''
}
animations['slide'] = animations['slide_h']# Backward compatibility

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
#rendered_cells div.jp-OutputArea.jp-Cell-outputArea,
#rendered_cells div.jp-RenderedMarkdown.jp-MarkdownOutput{
    height:0 !important;
} /* Suppress other outputs and markdown output in Voila */
/*.jp-LabShell .SlidesWrapper .height-slider {display:none;}*/
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
#rendered_cells .window-fs {display:none;}
.SlidesWrapper {z-index: 10 !important;}

@media print {
   .SlidesWrapper, .SlidesWrapper.FullScreen {
       height: auto !important;
   }
   .controls, .NavWrapper button, .float-control, div.LaserPointer {
       display:none !important;
   }
    .NavWrapper p {
        margin-left:16px;
    }
    pre, .SlideBox, .SlidesWrapper, .SlideArea {
        height: auto !important;
    }
    .SlidesWrapper div.codehilite, .SlidesWrapper div.PyRepr {
        max-height:auto !important; /* Flow itself */
    }
}

.float-control {
    position: absolute;
    right:0;
    top:0;
    width:32px;
    height:32px;
    z-index: 51;
    background:var(--primary-bg);
    opacity:0;
    overflow:hidden;
    padding:4px;
}
.float-control:hover,.float-control:focus {
    width:max-content;
    height:50%;
    opacity:1;
}
.Inline-Notes {
    border: 1px solid var(--accent-color);
    border-radius:4px;
    background: var(--primary-bg);
    color: var(--primary-fg);
    width: 85% !important; /* For see all */
}
    
.Inline-Notes > div {
    display: flex;
    flex-direction:column;
    justify-content: space-between;
    padding:4px;
}
/* Order of below two lines matters */
body .DisplaySwitch, .SlideArea .DisplaySwitch {display:none !important;} /* No switch for embeded slides */
.jp-LabShell .DisplaySwitch, body[data-retro] .DisplaySwitch{display:block !important;}

.jp-LabShell .DisplaySwitch,
body[data-retro] .DisplaySwitch {
    width:max-content;
    display:flex !important;
    flex-direction:row !important;
    padding-left:16px !important;
}
.jp-LabShell .DisplaySwitch>div>button
body[data-retro] .DisplaySwitch>div>button {
    background:transparent;
    border: none;
    color: var(--accent-color);
    width:60px;
    border-radius:0 !important;
    min-width:36px;
}
.jp-LabShell .DisplaySwitch>div>button.mod-active,
body[data-retro] .DisplaySwitch>div>button.mod-active {
    color:var(--primary-bg);
    background:var(--accent-color);
}
.jp-LabShell .DisplaySwitch>div,
body[data-retro] .DisplaySwitch>div {
    display:inline-flex;
    flex-direction:row;
    width:150px;
    border: 1px solid var(--accent-color);
    padding: 2px 0px;
}
<style>'''


def sidebar_layout_css(span_percent = 40):
    return f'''<style>
.jp-LabShell, body[data-retro]>div#main {{ /* Retrolab will also rise Notebook 7 */ 
    right: {span_percent}vw !important;
    margin-right:1px !important;
    min-width: 0 !important;
}}
.kLqJVm .jp-Notebook {{ /* For Kaggle */
    min-width: 0 !important;
    padding-right: {span_percent}vw !importnat;
}}
.jp-LabShell .SlidesWrapper,
body[data-retro] .SlidesWrapper {{
    position:fixed;
    top:0px !important;
    right:0px !important;
    height: 100% !important;
    width: {span_percent}vw !important; 
}}
/* Very important to keep slides ON even Notebook hidden */
.jp-LabShell .jp-NotebookPanel.p-mod-hidden {{
    display:block !important;
    height:0 !important;
    min-height:0 !important;
    border:none !important;
}}
</style>'''


fullscreen_css = '''<style>
.SlidesWrapper:not(.FullScreen) { display:none;} /*Hide All and display, leave only one */
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
.SlideArea .SlidesWrapper, .SlideArea .SlidesWrapper.FullScreen { /* Do Not apply Fullscreen in embed mode */
        display:unset;position:relative;width:90%;max-width:95%;height:unset;left:unset;bottom:unset;}  
.jp-SideBar.lm-TabBar, .f17wptjy, #jp-bottom-panel { display:none !important;}
#jp-top-panel, #jp-menu-panel {display:none !important;} /* in case of simple mode */
.lm-DockPanel-tabBar {display:none;}
.SlidesWrapper .voila-sidecar-hidden {display: none;}
.SlidesWrapper.FullScreen .console-btn {display:block;} /* Show console button in fullscreen in jupyterlab only*/
.jupyterlab-sidecar .console-btn {display:none;} /* Hide console button in sidecar as not works there */
html,body {background: var(--primary-bg);} /* Useful for Other tabs when Ctrl + Shift + ],[ pressed */
</style>''' 



mpl_fs_css = '''<style>
/* Pop out matplotlib's SVG on click/hover */
div.zoom-container > *:focus, div.zoom-container > *:hover{
    position:fixed;
    left:100px;
    top:0px;
    z-index:100;
    width: calc(100% - 200px);
    height: 100%;
    object-fit:scale-down !important;
    box-shadow: 0px 0px 200px 200px rgba(15,20,10,0.8); 
} 

@media screen and (max-width: __breakpoint_width__) { /* Computed dynamically */
    div.zoom-container > *:focus, div.zoom-container > *:hover{
        width:100%;
        height: calc(100% - 200px);
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
