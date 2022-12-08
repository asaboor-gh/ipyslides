# This should not be used by user, but is used by ipyslides to generate layout of slides

layout_css = '''
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
/*.jp-LabShell .SlidesWrapper .Height-Slider {display:none;}*/
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
#rendered_cells .Height-Slider {display:none !important;}
#rendered_cells .FullWindow-Btn {opacity:0.1 !important;}
.SlidesWrapper {z-index: 10 !important;}

@media print {
   .SlidesWrapper, .SlidesWrapper.FullWindow {
       height: auto !important;
   }
   .Controls, .NavWrapper button, .FloatControl, div.LaserPointer {
       display:none !important;
   }
    .NavWrapper p {
        margin-left:16px;
    }
    pre, .SlideBox, .SlidesWrapper, .SlideArea {
        height: auto !important;
    }
    .SlidesWrapper .highlight, .SlideArea .raw-text {
        max-height:auto !important; /* Flow itself */
    }
    .SlideArea {
        width: 100% !important;
    }
}

.SidePanel .CaptureHtml { border: 1px solid var(--secondary-fg); }
.SidePanel .CaptureHtml figure {width:100%;margin:0;padding:0;background:var(--secondary-bg);}
.FloatControl {
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
.FloatControl:hover,.FloatControl:focus {
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
.DisplaySwitch{
    display: none; /* Hide by default */
}

.jp-LabShell .DisplaySwitch,
body[data-retro] .DisplaySwitch,
body[data-notebook] .DisplaySwitch {
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
.SlidesWrapper.FullWindow .DisplaySwitch {
    display: none !important; /* in fullscreen */
}
.CompareSwitch.mod-active {
    background: transparent !important;
    border:none !important;
    outline:none !important;
    box-shadow:none !important;
    opacity: 1 !important;
    color: var(--pointer-color) !important;
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
.CaptureHtml * {
    font-size: 0.9em;
    line-height: 0.9em  !important;
}

/* Table of contents panel */
.TOC {
    backdrop-filter: blur(200px);
    margin: 4px 36px; 
    padding: 0.5em;
    position: absolute;
    min-width: 60% !important;
    height: calc(100% - 8px) !important;
    box-sizing:border-box;
    z-index: 100;
    border-radius: 4px;
    border: 1px solid var(--hover-bg);
}
@media screen and (max-width: __breakpoint_width__) { /* Computed Dynamically in Notebook*/
    .TOC {min-width: calc(100% - 72px) !important;}
}
.TOC .goto-box {
    justify-content: space-between;
    height: auto;
    width: auto;
    box-sizing:border-box !important;
}
.TOC .goto-box:hover {font-weight:bold;}
.TOC .goto-button {
    position: absolute;
    width: 100%;
    height: 100%;
    box-sizing:border-box;
    padding:0;
    margin:0;
}
.TOC .Menu-Item {font-size: 24px !important;}
.TOC .goto-html {
    width:100%;
    height:max-content;
    box-sizing:border-box;
}
.TOC .goto-html .widget-html-content {
    box-sizing: border-box;
    padding-left:2em !important;
    display: flex;
    flex-direction: row;
    flex-wrap:nowrap;
    justify-content:space-between !important;
    align-items:top;
}
.TOC .goto-html .widget-html-content  span:first-of-type {
    position:absolute;
    top:0 !important; /*must have thing */
    height:100%;
    margin-left:-2em !important;
}

.widget-html.jupyter-widgets-disconnected { display:none !important; } /* Hide disconnected html widgets to avoid spacing issues */

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
.SidePanel-text .widget-html-content {
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
    
.SlidesWrapper .SidePanel {
    backdrop-filter: blur(200px);
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

.SlidesWrapper .SidePanel .SidePanel-Btn {
    border:none !important;
    outline:none !important;
    font-size: 24px;
    background: transparent !important;
}

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
.NavWrapper NavBox {
    align-items: bottom;
    height: max-content;
    justify-content: flex-start;
    }
.SlidesWrapper .Arrows {opacity:0.4;font-size: 36px;padding:4px;}
.SlidesWrapper .Arrows:hover, .SlidesWrapper .Arrows:focus { opacity:1;}
.SlidesWrapper .Controls {
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
.Controls .widget-button > i { color: var(--accent-color) !important;}

@media screen and (max-width: __breakpoint_width__) { /* Computed Dynamically in Notebook*/
    .SlidesWrapper .SidePanel {width:100% !important;}
    .SlidesWrapper .Controls {bottom:30px!important;right:0 !important;width:100%;justify-content: space-around !important;}
	.SlidesWrapper .Controls button {width:30% !important;}
    .SlidesWrapper .SlideArea {padding-bottom: 50px !important;}
    .NavWrapper .progress {height:4px !important;}
    .SlideArea { min-width:100% !important;width:100% !important;} /* can't work without min-width */
    .SlideArea .columns .widget-html
    .ProgBox {
    	width: 40%;
    	opacity:0;
	}
}

.SlidesWrapper .widget-inline-hbox .widget-readout  {box-shadow: none;color:var(--primary-fg) !important;}
.SlidesWrapper .widget-html-content pre, 
.SlidesWrapper .widget-html-content code, 
.SlidesWrapper .widget-html-content p {
    font-size: 100% !important; /* otherwise it is so small */
}

.SlidesWrapper .widget-inline-hbox .widget-label,
.SlidesWrapper .widget-inline-hbox .widget-readout  {
    color:var(--primary-fg);
} 

#jp-top-panel, #jp-bottom-panel, #jp-menu-panel {color: inherit;}

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
.SlidesWrapper :is(.SlideBox, .SidePanel) :is(button, .jupyter-button) { 
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

.CodeMirror {padding-bottom:8px !important; padding-right:8px !important;} /* Jupyter-Lab make space in input cell */

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

/* Export Button */
.SlidesWrapper .Export-Btn .mod-active{
    box-shadow: none !important;
}
.SlidesWrapper .Export-Btn > div {
    border: 1px inset var(--hover-bg);
    padding:4px;
    border-radius:4px;
}

.SlidesWrapper .Export-Btn > div > button:last-of-type {
    display:none !important; /* Hide the third button, it's there on python side for a purpose */
    }

/* Linked Area */
.jp-LinkedOutputView > div.jp-OutputArea >  div:first-child,
.jp-LinkedOutputView .SlidesWrapper .Height-Slider,
.SlidesWrapper.FullWindow .Height-Slider{
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
#rendered_cells .Height-Slider,
#rendered_cells .Width-Slider,
.SlidesWrapper.SideMode .Height-Slider,
.jp-LinkedOutputView .ExtraControls,
.jupyterlab-sidecar .ExtraControls {
    display: none !important;
}
'''

def sidebar_layout_css(span_percent = 40):
    return f'''
.jp-LabShell, body[data-retro]>div#main, body[data-notebook]>div#main {{ /* Retrolab will also rise Notebook 7 */ 
    right: {span_percent}vw !important;
    margin-right:1px !important;
    min-width: 0 !important;
}}
body[data-kaggle-source-type] .jp-Notebook {{ /* For Kaggle */
    min-width: 0 !important;
    padding-right: {span_percent}vw !important;
}}
.jp-LabShell .SlidesWrapper,
body[data-retro] .SlidesWrapper,
body[data-notebook] .SlidesWrapper{{
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
/* Override hiding on scroll in Notebook V7 and associated view of Jupyter lab*/
.jp-WindowedPanel-window > div.jp-Cell {{
    display: block !important; 
}}
'''

fullscreen_css = '''
.SlidesWrapper.FullWindow {      
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
.SlidesWrapper.FullWindow .console-btn { display:block;} /* Show console button in fullscreen in jupyterlab only*/
html, body { background: var(--primary-bg);} /* Useful for Other tabs when Ctrl + Shift + ],[ pressed */
''' 

zoom_hover_css = '''
/* Pop out matplotlib's SVG on click/hover */
div.zoom-container > *:focus, div.zoom-container > *:hover{
    position:fixed;
    background: var(--primary-bg);
    left:100px;
    top:0px;
    z-index:100;
    width: calc(100% - 200px);
    height: 100%;
    object-fit: scale-down !important;
    box-shadow: 0px 0px 200px 200px rgba(15,20,10,0.8); 
} 

@media screen and (max-width: __breakpoint_width__) { /* Computed dynamically */
    div.zoom-container > *:focus, div.zoom-container > *:hover{
        background: var(--primary-bg);
        width:100%;
        height: calc(100% - 200px);
        top: 100px;
        left:0px;
    }
}
'''

def glass_css(opacity = 0.75,blur_radius = 50):
    return f'''.BackLayer, .BackLayer .Front {{
        position: absolute !important;
        top:0 !important;
        left:0 !important;
        width: 100% !important;
        height: 100% !important;
        box-sizing:border-box !important;
        overflow:hidden;
        margin:0;
    }}
    .BackLayer img{{
        position: absolute;
        left:0;
        top:0;
        width: 100%;
        height: 100%;
        object-fit:cover;
        filter: blur({blur_radius}px);
    }}
    .BackLayer .Front {{
        background: var(--primary-bg);
        opacity:{opacity};
    }}'''