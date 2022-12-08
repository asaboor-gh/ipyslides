# Author: Abdul Saboor
# CSS for ipyslides

theme_roots = {
'Inherit': ''':root {
	--heading-color: var(--jp-inverse-layout-color1,navy);
	--primary-fg:  var(--jp-inverse-layout-color0,black);
	--primary-bg: var(--jp-layout-color0,white);
	--secondary-bg:var(--jp-layout-color2,whitesmoke);
	--secondary-fg: var(--jp-inverse-layout-color4,#454545);
	--alternate-bg: var(--jp-layout-color2,whitesmoke);
	--hover-bg:var(--jp-border-color1,#D1D9E1);
 	--accent-color:var(--jp-brand-color1,navy);
    --pointer-color: var(--md-pink-A400,red);
	--text-size: __text_size__; /* Do not edit this, this is dynamic variable */
}
''',
'Light': ''':root {
	--heading-color: navy;
	--primary-fg: black;
	--primary-bg: white;
	--secondary-bg: whitesmoke;
	--secondary-fg: #454545;
	--alternate-bg: whitesmoke;
	--hover-bg: #D1D9E1;
	--accent-color: navy;
    --pointer-color: red;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
''',
'Fancy': ''':root {
	--heading-color: #105599;
	--primary-fg: #755;
	--primary-bg: #efefef;
	--secondary-bg: #effffe;
	--secondary-fg: #89E;
	--alternate-bg: #deddde;
	--hover-bg: #D1D9E1;
	--accent-color: #955200;
    --pointer-color: #FF7722;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
''',
'Dark': ''':root {
	--heading-color: snow;
	--primary-fg: white;
	--primary-bg: black;
	--secondary-bg: #353535;
	--secondary-fg: powderblue;
	--alternate-bg: #282828;
	--hover-bg: #264348;
	--accent-color: #d9e0e3;
    --pointer-color: blue;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
''',
'Material Light': ''':root {
	--heading-color: #4984c4;
	--primary-fg: #3b3b3b;
	--primary-bg: #fafafa;
	--secondary-bg: #e9eef2;
	--secondary-fg: #3b5e3b;
	--alternate-bg: #e9eef2;
	--hover-bg: #dae3ec;
	--accent-color: #4d7f43;
    --pointer-color: red;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
''',
'Material Dark': ''':root {
	--heading-color: #aec7e3;
	--primary-fg: #bebebe;
	--primary-bg: #282828;
	--secondary-bg: #383838;
	--secondary-fg: #fefefe;
	--alternate-bg: #383838;
	--hover-bg: #484848;
	--accent-color: #a8bfa3;
    --pointer-color: blue;
	--text-size: __text_size__; /* Do not edit this it is dynamic variable */
}
'''
}


def style_css(style_root = theme_roots['Inherit']):
	return style_root + ''' 
.SlideArea .text-box { /* general text box for writing inline refrences etc. */
    font-size: 0.7em !important; 
    line-height: 0.99em !important;
    position:relative; 
    left:initial;
    top:initial;
    padding:2px 4px;
    color: var(--secondary-fg);
    /* Below are required to override behavior of span tag*/
    display: inline-block !important;
    white-space: break-spaces !important;
}
.SlideArea .citation {
    font-size: 0.8em !important; 
    line-height: 0.85em !important;
    display: flex !important;
    flex-direction: row !important;
}
.SlideArea .citation > a {margin-right: 0.3em !important;}
.SlideArea figure {
    margin: 8px !important; /* override default margin */
}
.SlideArea .zoom-container figure {
    object-fit:scale-down !important; /* If height goes out, scale down */
}
.SlideArea figcaption {
    font-size: 0.8em !important;
    line-height: 1em !important;
    padding-top: 0.2em !important;
}
.align-center:not(.columns), .align-center > *:not(.columns) {
    display:table !important;
    margin: 0 auto !important;
    width: auto !important; /* max-content creates oveflow, do not use it */
}
.align-left:not(.columns) { 
    display:table !important; 
    width: auto !important; 
    margin-right: auto !important; 
    text-align:left !important;
}
.align-right:not(.columns) { 
    display:table !important; 
    width: auto !important; 
    margin-left: auto !important; 
    text-align:right !important;
}

.rtl, .rtl > * {
    text-align:right !important;
    padding: 0 12px !important; /* to avoid cuts in rtl */
}

.info > *:last-child, .warning > *:last-child,
.success > *:last-child, .error > *:last-child,
.align-right:not(.columns) >*:last-child,
.align-left:not(.columns) >*:last-child,
.align-center:not(.columns) >*:last-child{ 
    margin-bottom:0.1em !important;
}

.info, .warning, .success, .error, .note { padding: 0.2em !important;}

.warning, .warning *:not(span) { color:#FFAC1C !important;}
.success, .success *:not(span) { color:green !important;}
.error, .error *:not(span) { color:red !important;}
.info, .info *:not(span) { color:skyblue !important;}
.note{
    border: 1px solid var(--hover-bg);
    border-radius: 0.2em;
    background: none; /* Fallback  for Inherit and Custom theme*/
    background: rgba(__light__,__light__,__light__,0.75);
}
.note::before {
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

.block {
    padding:8px;
    border-top: 3px solid var(--accent-color);
    background: var(--secondary-bg);
    margin-bottom: 0.9em;
}

.block-red {
    padding:8px;
    border-top: 3px solid red; /* Fallback  for Inherit and Custom theme*/
    border-top: 3px solid rgb(__light__, 0, 0);
    background: var(--secondary-bg); /* Fallback  for Inherit and Custom theme*/
    background: rgba(__light__,calc(__light__ - 20),calc(__light__ - 20),0.75);
    margin-bottom: 0.9em;
}

.block-green {
    padding:8px;
    border-top: 3px solid green; /* Fallback  for Inherit and Custom theme*/
    border-top: 3px solid rgb(0, __light__, 0);
    background: var(--secondary-bg); /* Fallback  for Inherit and Custom theme*/
    background: rgba(calc(__light__ - 20),__light__,calc(__light__ - 20),0.75);
    margin-bottom: 0.9em;
}

.block-blue {
    padding:8px;
    border-top: 3px solid blue; /* Fallback  for Inherit and Custom theme*/
    border-top: 3px solid rgb(0, 0, __light__);
    background: var(--secondary-bg); /* Fallback  for Inherit and Custom theme*/
    background: rgba(calc(__light__ - 20),calc(__light__ - 20),__light__,0.75);
    margin-bottom: 0.9em;
}
.block-yellow {
    padding:8px;
    border-top: 3px solid yellow; /* Fallback  for Inherit and Custom theme*/
    border-top: 3px solid rgb(__light__, __light__, 0);
    background: var(--secondary-bg); /* Fallback  for Inherit and Custom theme*/
    background: rgba(__light__,__light__,calc(__light__ - 20),0.75);
    margin-bottom: 0.9em;
}
.block-cyan {
    padding:8px;
    border-top: 3px solid cyan; /* Fallback  for Inherit and Custom theme*/
    border-top: 3px solid rgb(0,__light__, __light__);
    background: var(--secondary-bg); /* Fallback  for Inherit and Custom theme*/
    background: rgba(calc(__light__ - 20),__light__,__light__,0.75);
    margin-bottom: 0.9em;
}
.block-gray {
    padding:8px;
    border-top: 3px solid gray; /* Fallback  for Inherit and Custom theme*/
    border-top: 3px solid rgb(calc(__light__ - 10),calc(__light__ - 10),calc(__light__ - 10));
    background: var(--secondary-bg); /* Fallback  for Inherit and Custom theme*/
    background: rgba(calc(__light__ - 20),calc(__light__ - 20),calc(__light__ - 20),0.75);
    margin-bottom: 0.9em;
}
.block-magenta {
    padding:8px;
    border-top: 3px solid magenta; /* Fallback  for Inherit and Custom theme*/
    border-top: 3px solid rgb(__light__,0, __light__);
    background: var(--secondary-bg); /* Fallback  for Inherit and Custom theme*/
    background: rgba(__light__,calc(__light__ - 20),__light__,0.75);
    margin-bottom: 0.9em;
}

details {
    padding: 0.2em;
    background: var(--secondary-bg);
}
details > summary {
    color: var(--accent-color) !important;
    padding: 0.2em;
}
details > div {
    background: var(--primary-bg);
    padding: 0.2em;
}

.SlidesWrapper *:not(.fa):not(i):not(span):not(pre):not(code):not(.raw-text),
.SlideArea *:not(.fa):not(i):not(span):not(pre):not(code):not(.raw-text) { /* Do not edit __textfont__, code does this. */
   font-family: "__textfont__", "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" !important;
}

.SlidesWrapper code > span,
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

.SlideArea .columns {width:100%;max-width:100%;display:inline-flex;flex-direction:row;column-gap:2em;height:auto;}

@media screen and (max-width: __breakpoint_width__) { /* Computed Dynamically in notebook*/
    .SlideArea .columns {width:100%;max-width:100%;display:flex;flex-direction:column;}
    .SlideArea .columns>div[style] {width:100%!important;} /* important to override inline CSS */
}

.SlidesWrapper h1,
.SlidesWrapper h2,
.SlidesWrapper h3,
.SlidesWrapper h4,
.SlidesWrapper h5,
.SlidesWrapper h6 {
	color:var(--heading-color);
 	text-align: center;
	overflow:hidden; /* FireFox */
}
.SlidesWrapper h1 {margin-block: unset;font-size: 2.25em;  line-height: 1.5em;}
.SlidesWrapper h2 {margin-block: unset;font-size: 2em;line-height: 1.5em;}
.SlidesWrapper h3 {margin-block: unset;font-size: 1.5em;  line-height: 1.5em;}
.SlidesWrapper h4 {margin-block: unset;font-size: 1.25em;line-height: 1.5em;}
.SlidesWrapper h5 {margin-block: unset;font-size: 1em;  line-height: 1.5em;}
.SlidesWrapper .widget-text input {
    background: var(--primary-bg);
    color:var(--primary-fg);
}

.SlideArea { width: __content_width__ !important;} 
.SlideArea .footnote *,  .SlideArea .footnote li::marker {
    font-size:0.9em;
    line-height: 0.9em;
}
.SlidesWrapper hr {
    margin:0 !important;
    margin-block: 0.5em !important;
    border: none;
    width: auto;
    height: 2px;
    background: linear-gradient(to right, transparent,  var(--secondary-bg),var(--accent-color), var(--secondary-bg),transparent);
}
.SlideArea .footnote ol {
    margin-top: 0.5em !important;
}
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
    font-size: 80% !important;
    opacity:0.8 !important;
}
.highlight  code > span {
    white-space: pre: /*normal;  for breaking words */
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
.raw-text { /* Should be same in notebook cell */
    font-family: "__codefont__", "SimSun-ExtB", "Cascadia Code","Ubuntu Mono", "Courier New" !important;
    font-size: 90% !important;
    display: block !important;
    margin: 4px !important;
    height: auto !important;
    overflow: auto !important;
    overflow-wrap: break-word !important;
    padding: 0 0.3em !important;
} 
.SlideArea .raw-text { /* Should follow theme under slides */
    background: var(--secondary-bg) !important;
    color: var(--primary-fg) !important;
    max-height: 400px;
    white-space:pre !important;
}
.SlideArea pre {
    background: none !important;
    color: var(--primary-fg) !important;
}
.custom-print {
    margin-block: 0.5px !important; /* Two adjacant prints should look closer */
}
.goto-button {min-width:max-content;}
/* Associted with the above */
.goto-box {}
.goto-html {}

.SlidesWrapper.CaptureMode .SlideArea .goto-button {display:none !important;} /* Hide the goto-button in screenshot, it is not useful there */

/* Table of contents on slides */
.SlideArea .toc-item {border-right: 4px solid var(--secondary-bg);}
.SlideArea .toc-item.this {
    border-right: 4px solid var(--primary-fg);
    font-weight: bold !important;
}
.SlideArea .toc-item.next {opacity: 0.5;}

.SlideArea ul li::marker, .SlideArea ol li::marker {color:var(--accent-color);}
/* Citations on hover of object before it */
a.citelink > sup {
    font-weight:bold;
}
.citation.hidden {
    display:none !important;
}
*:hover + .citation.hidden {
    display:flex !important;
    border: 1px inset var(--hover-bg);
    background: var(--secondary-bg);
    padding: 0.2em;
}

/* docs have Python code only, so no need to have fancy things there */
.docs {
    margin-bottom: 1em !important;
}
.docs .highlight {
    border: none !important;
}
.docs span.lang-name {
    display: none !important;
}
.SlidesWrapper blockquote, .SlidesWrapper blockquote>p {
	background: var(--secondary-bg);
	color: var(--secondary-fg);
}
    
.SlidesWrapper table {
 	border-collapse: collapse !important;
    font-size: 0.95em;
    min-width:auto;
    width:100%;
    word-break:break-all;
    overflow: auto;
	color: var(--primary-fg)!important;
	background: var(--primary-bg)!important;
    border: 1px solid var(--alternate-bg) !important; /* Makes it pleasant to view */
}
.SlidesWrapper tbody>tr:nth-child(odd) {background: var(--alternate-bg)!important;}
.SlidesWrapper tbody>tr:nth-child(even) {background: var(--primary-bg)!important;}
.SlidesWrapper tbody>tr:hover {background: var(--hover-bg)!important;}


/* Make Scrollbars beautiful */
.SlidesWrapper, .SlidesWrapper  * { /* FireFox <3*/
    scrollbar-width: thin;
    scrollbar-color:var(--alternate-bg) transparent;
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
    background: var(--hover-bg) !important;
}
.SlidesWrapper ::-webkit-scrollbar-corner,
.highlight::-webkit-scrollbar-corner {
    display:none !important;
}   

/* Zoom container including Matplotlib figure SVG */
div.zoom-container { resize: both;}
div.zoom-container,
div.zoom-container > * {
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


loading_svg = '''<div style="position:absolute;left:0;top:0;z-index:51;">
    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 50 50">
  <path fill="var(--accent-color,navy)" d="M25,5A20.14,20.14,0,0,1,45,22.88a2.51,2.51,0,0,0,2.49,2.26h0A2.52,2.52,0,0,0,50,22.33a25.14,25.14,0,0,0-50,0,2.52,2.52,0,0,0,2.5,2.81h0A2.51,2.51,0,0,0,5,22.88,20.14,20.14,0,0,1,25,5Z">
    <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.5s" repeatCount="indefinite"/>
  </path></svg></div>'''
