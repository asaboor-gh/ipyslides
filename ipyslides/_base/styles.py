# Author: Abdul Saboor
# CSS for ipyslides

theme_roots = {
'Inherit': ''':root {
	--heading-fg: var(--jp-inverse-layout-color1,navy);
	--primary-fg:  var(--jp-inverse-layout-color0,black);
	--primary-bg: var(--jp-layout-color0,white);
	--secondary-bg:var(--jp-layout-color2,whitesmoke);
	--secondary-fg: var(--jp-inverse-layout-color4,#454545);
	--tr-odd-bg: var(--jp-layout-color2,whitesmoke);
	--tr-hover-bg:var(--jp-border-color1,#D1D9E1);
 	--accent-color:var(--jp-brand-color1,navy);
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


def style_css(style_root = theme_roots['Inherit']):
	return style_root + ''' 
.SlideArea .TextBox { /* general text box for writing inline refrences etc. */
    font-size: 0.7em !important; 
    line-height: 0.75em !important;
    position:relative; 
    left:initial;
    top:initial;
    padding:2px 4px;
    color: var(--secondary-fg);
}
.SlideArea figure {
    margin: 8px !important; /* override default margin */
}
.SlideArea .zoom-container figure {
    width: 100% !important;
    object-fit:scale-down !important; /* If height goes out, scale down */
}
.SlideArea figcaption {
    font-size: 0.8em !important;
    line-height: 1em !important;
    padding-top: 0.2em !important;
}
.Center:not(.columns), .Center > *:not(.columns) {
    display:table !important;
    margin: 0 auto !important;
    width: auto !important; /* max-content creates oveflow, do not use it */
}
.Left:not(.columns) { 
    display:table !important; 
    width: auto !important; 
    margin-right: auto !important; 
    text-align:left !important;
}
.Right:not(.columns) { 
    display:table !important; 
    width: auto !important; 
    margin-left: auto !important; 
    text-align:right !important;
}

.RTL, .RTL > * {
    text-align:right !important;
    padding: 0 12px !important; /* to avoid cuts in RTL */
}

.Info > *:last-child, .Warning > *:last-child,
.Success > *:last-child, .Error > *:last-child,
.Right:not(.columns) >*:last-child,
.Left:not(.columns) >*:last-child,
.Center:not(.columns) >*:last-child{ 
    margin-bottom:0.1em !important;
}

.Info, .Warning, .Success, .Error, .Note { padding: 0.2em !important;}

.Warning, .Warning *:not(span) { color:#FFAC1C !important;}
.Success, .Success *:not(span) { color:green !important;}
.Error, .Error *:not(span) { color:red !important;}
.Info, .Info *:not(span) { color:skyblue !important;}
.Note{
    border: 1px solid var(--tr-hover-bg);
    border-radius: 0.2em;
}
.Note::before {
    content: 'ℹ';
    display: inline-flex;
    width: 1em;
    height: 1em;
    margin: 0 0.2em;
    justify-content:center;
    align-items:center;
    border: 1px solid var(--accent-color);
    border-radius: 1em;
    color: var(--accent-color);
}

.jp-OutputArea-child, 
.jp-OutputArea-child .jp-OutputArea-output { 
    background: transparent !important;
    background-color: transparent !important; 
    margin: 0 !important;
} /* For some themes */
.SlidesWrapper .jupyter-widgets:not(button) { 
    color: var(--primary-fg) !important;
} /* All widgets text */
.jp-RenderedHTMLCommon { 
    padding:0px;
    padding-right: 0px !important;
    font-size: var(--text-size);
} /* important for central layout */
.jp-RenderedHTMLCommon :not(pre) > code { 
    background-color: var(--secondary-bg); 
    color:var(--secondary-fg);
}
.jp-RenderedText, 
.jp-RenderedText pre {
    color:var(--primary-fg) !important;
}
.jp-RenderedHTMLCommon p {
    margin-bottom: 0.2em !important;
}
.widget-html:not(.LaserPointer), 
.widget-html .widget-html-content > div {
    display:grid !important; 
    font-size: var(--text-size) !important;
} /* Do not use overflow here */
.panel-text .widget-html-content {
    line-height: inherit !important;
}
.jp-LinkedOutputView, 
.SlidesWrapper, 
.SlidesWrapper * { 
    box-sizing:border-box;
}
.cell-output-ipywidget-background { /* VSCode issue */
    background: var(--theme-background,inherit) !important;
    margin: 8px 0px;} /* VS Code */
.SlidesWrapper *:not(.fa):not(i):not(span),
.SlideArea *:not(.fa):not(i):not(span){ /* Do not edit __textfont__, code does this. */
   font-family: "__textfont__", "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" !important;
}

.SlidesWrapper code>span,
.SlideArea code>span { /* Do not edit __codefont__, code does this. */
   font-family: "__codefont__", "SimSun-ExtB", "Cascadia Code","Ubuntu Mono", "Courier New" !important;
   font-size: 90% !important;
}

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

.SlideArea .columns {width:100%;max-width:100%;display:inline-flex;flex-direction:row;column-gap:2em;height:auto;}

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
    .SlideArea { min-width:100% !important;width:100% !important;} /* can't work without min-width */
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

.SlideArea { width: __content_width__ !important;} 
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

.highlight {
    min-width: 100% !important;
    width: 100% !important;
    max-width: 100vw !important;
    box-sizing: border-box !important;
    overflow: auto !important;
    padding: 0 !important;
    margin: 4px 0px !important; /* Opposite to padding to balance it */
    max-height: 400px; /* Try avoiding important here */
    height: auto !important;
    /* colors are set via settigs.set_code_style */
}
.highlight pre { /* works for both case, do not use > */
    display: grid !important;
    padding: 8px 4px 8px 4px !important; 
    overflow: auto !important;
    width: auto !important;
    box-sizing: border-box !important;
    height: auto;
    margin: 0px !important;
    counter-reset: line; /* important to add line numbers */
    background: none !important; /* This should be none as will given by the code_css */
}

.highlight code {
    counter-increment: line;
    display:inline-block !important; /* should be on new line */
    width:auto;
    min-width: calc(90% - 2.2em);
    background:transparent !important;
    white-space: pre !important;
    overflow-wrap: normal !important;
    box-sizing: border-box !important;
}
.highlight code:before{
    content: counter(line,decimal);
    position: sticky;
    top:initial;
    left:-4px;
    padding: 0 8px;
    display:inline-block; /* should be inline */
    text-align:right;
    -webkit-user-select: none;
    margin-left:-3em;
    margin-right: 8px;
    font-size: 80%;
}
.highlight  code > span {
    white-space: normal; /* for breaking words */
    word-break: break-word; /* for breaking words */
}
.highlight code.code-no-focus {
    opacity:0.3 !important;
}
.highlight code.code-focus {
    text-shadow: 0 0 1px var(--primary-bg);
}
span.lang-name {
    color: var(--accent-color);
    font-size: 0.8em;
}
.SlideArea div.PyRepr {
    margin: 4px !important;
    white-space:pre !important;
    max-height: 400px;
    height: auto !important;
    overflow: auto !important;
    overflow-wrap: break-word !important;
}

/* Docs have Python code only, so no need to have fancy things there */
.Docs {
    margin-bottom: 1em !important;
}
.Docs .highlight {
    border: none !important;
}
.Docs span.lang-name {
    display: none !important;
}
.SlidesWrapper blockquote, .SlidesWrapper blockquote>p {
	background: var(--secondary-bg);
	color: var(--secondary-fg);
}
    
.SlidesWrapper table {
 	border-collapse: collapse !important;
    min-width:auto;
    width:100%;
    font-size: 0.95em;
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
.highlight::-webkit-scrollbar { /* important for good display */
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
.highlight::-webkit-scrollbar-corner {
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
.ReloadButton {
    position: absolute;
    margin:auto;
    left:50%;
    top: 20px;
    transform: translateX(-50%);
    border: 2px solid red;
    border-radius: 1em 1em 0 1em !important;
    font-size: 20px;
    display:block !important;
    z-index: 200 !important;
}
.ReloadButton.Hidden {
    display: none !important;
}
/* Linked Area */
.jp-LinkedOutputView > div.jp-OutputArea >  div:first-child,
.jp-LinkedOutputView .SlidesWrapper .height-slider,
.SlidesWrapper.FullScreen .height-slider{
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
#rendered_cells .height-slider,
#rendered_cells .width-slider,
.SlidesWrapper.SideMode .height-slider,
.jp-LinkedOutputView .ExtraControls,
.jupyterlab-sidecar .ExtraControls {
    display: none !important;
}
'''

animations = {'zoom':'''
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
''',
'slide_h': '''
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
''',
'slide_v': '''
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
'''
}
animations['slide'] = animations['slide_h']# Backward compatibility

main_layout_css = '''
.SlidesWrapper .SlideArea { align-items: center;}
.SlidesWrapper .SlideArea .report-only {display:none !important;}
a.jp-InternalAnchorLink { display: none !important;}
.widget-inline-hbox .widget-readout  { min-width:auto !important;}
.jupyterlab-sidecar .SlidesWrapper,
.jp-LinkedOutputView .SlidesWrapper {
    width: 100% !important; 
    height: 100% !important;
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
.jp-LinkedOutputView>div {overflow:hidden !important;}


#rendered_cells .SlidesWrapper {
    position: fixed !important;
    width:100vw !important;
    height: 100vh !important;
    bottom: 0px !important;
    top: 0px !important;
    tight: 0px !important;
    left: 0px !important;
}
#rendered_cells .height-slider {display:none !important;}
#rendered_cells .window-fs {opacity:0.1 !important;}
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
    .SlidesWrapper .highlight, .SlideArea div.PyRepr {
        max-height:auto !important; /* Flow itself */
    }
    .SlideArea {
        width: 100% !important;
    }
}

.panel .capture-html { border: 1px solid var(--secondary-fg); }
.panel .capture-html figure {width:100%;margin:0;padding:0;background:var(--secondary-bg);}
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
/* Order of these matters */
.DisplaySwitch {
    display: none; /* Hide by default */
}
.jp-LabShell .DisplaySwitch,
body[data-retro] .DisplaySwitch {
    display:block !important;
    position:absolute !important;
    padding:4px !important;
    width: max-content !important;
    background: transparent !important;
    border:none !important;
    outline:none !important;
    font-size: 24px;
    box-shadow:none !important;
}
#rendered_cells .DisplaySwitch,
.SlidesWrapper.FullScreen .DisplaySwitch {
    display: none !important; /* in fullscreen */
}

.Intro summary {
    background: var(--secondary-bg);
    padding-left:0.2em;
    color: var(--accent-color);
    font-weight: bold;
}
.Intro summary::marker {
    content: '';
}
.Intro summary::after {
    content: 'show/hide';
    color: var(--secondary-fg);
    font-weight:normal;
    font-size: 80%;
    float:right;
    padding: 0.2em;
}
.capture-html * {
    font-size: 0.9em;
    line-height: 0.9em  !important;
}
'''


def sidebar_layout_css(span_percent = 40):
    return f'''
.jp-LabShell, body[data-retro]>div#main {{ /* Retrolab will also rise Notebook 7 */ 
    right: {span_percent}vw !important;
    margin-right:1px !important;
    min-width: 0 !important;
}}
body[data-kaggle-source-type] .jp-Notebook {{ /* For Kaggle */
    min-width: 0 !important;
    padding-right: {span_percent}vw !important;
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
'''


fullscreen_css = '''
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
.f17wptjy, 
#jp-top-panel,
#jp-menu-panel,
#jp-bottom-panel,
.lm-DockPanel-tabBar,
.jp-SideBar.lm-TabBar, 
.jupyterlab-sidecar .console-btn, 
.SlidesWrapper .voila-sidecar-hidden {
    display:none !important;
}
.SlidesWrapper.FullScreen .console-btn { display:block;} /* Show console button in fullscreen in jupyterlab only*/
html, body { background: var(--primary-bg);} /* Useful for Other tabs when Ctrl + Shift + ],[ pressed */
''' 

mpl_fs_css = '''
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
'''

loading_svg = '''<div style="position:absolute;left:0;top:0;z-index:51;">
    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 50 50">
  <path fill="var(--accent-color,navy)" d="M25,5A20.14,20.14,0,0,1,45,22.88a2.51,2.51,0,0,0,2.49,2.26h0A2.52,2.52,0,0,0,50,22.33a25.14,25.14,0,0,0-50,0,2.52,2.52,0,0,0,2.5,2.81h0A2.51,2.51,0,0,0,5,22.88,20.14,20.14,0,0,1,25,5Z">
    <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.5s" repeatCount="indefinite"/>
  </path></svg></div>'''
