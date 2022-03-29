# Template for building a report from slides 

doc_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>IPySlides Report</title>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script> 
    
    __code_css__
    __style_css__

    <!-- Custom stylesheet, it must be in the same directory as the html file -->
    <link rel="stylesheet" href="overrides.css">

    <!-- Loading mathjax macro -->
    <!-- Load mathjax -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-AMS_HTML"></script>
    <!-- MathJax configuration -->
    <script type="text/x-mathjax-config">
    MathJax.Hub.Config({
        tex2jax: {
            inlineMath: [ ["$","$"] ],
            displayMath: [ ["$$","$$"] ],
            processEscapes: true,
            processEnvironments: true
        },
        // Center justify equations in code and markdown cells. Elsewhere
        // we use CSS to left justify single line equations in code cells.
        displayAlign: "center",
        "HTML-CSS": {
            styles: {".MathJax_Display": {"margin": 0}},
            linebreaks: { automatic: true }
        }
    });
    </script>
    <!-- End of mathjax configuration -->
</head>
<body>
<div>
    <!-- Classes below work for both scenerios -->
    <div class="Content-Area SlidesWrapper">
    __content__
    </div>
</div>
</body>
</html>
'''

doc_css = '''<style type="text/css">
/* Author: Abdul Saboor */
:root {
	--primary-fg: black;
	--primary-bg: white;
	--secondary-bg: whitesmoke;
	--secondary-fg: #454545;
	--tr-odd-bg: whitesmoke;
	--tr-hover-bg: #D1D9E1;
	--accent-color: navy;
}
html { background: var(--secondary-bg, whitesmoke);}
body {
    background: var(--primary-bg, white);
    color: var(--primary-fg, black);
    width: 216mm;
    margin: 10mm auto;
    padding: 18mm 15mm 15mm 18mm;
}

h1,h2,h3,h4,h5,h6 { color: var(--accent-color, black); }
body div.highlight, body div.highlight pre {
    width: 100% !important;
    }
figure, img, .zoom-container, table, .block {margin: 0 auto !important;} /* center images */
div.columns { /* ovveride slides css */
    width:100%;
    max-width:100%;
    display:inline-flex !important;
    flex-direction:column !important;
    height:auto;
}
div.columns > div[style*="width:"] {
    width:100% !important;
    max-width:100% !important;
}
.slides-only {display:none !important;}

.Content-Area .TextBox { /* general text box for writing inline refrences etc. */
    font-size: 0.7em !important; 
    line-height: 0.75em !important;
    position:relative; 
    left:initial;
    top:initial;
    padding:2px 4px;
    color: var(--secondary-fg);
}
.Content-Area figure {
    margin: 8px !important; /* override default margin */
}
.Content-Area .zoom-container figure {
    width: 100% !important;
    object-fit:scale-down !important; /* If height goes out, scale down */
}
.Content-Area figcaption {
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

.Content-Area *:not(.fa):not(i):not(span){ /* Do not edit __textfont__, code does this. */
   font-family: __textfont__, "Noto Sans Nastaleeq",-apple-system, "BlinkMacSystemFont", "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Open Sans", "Helvetica Neue", "Icons16" ;
}

.Content-Area code>span { /* Do not edit __codefont__, code does this. */
   font-family: __codefont__, "SimSun-ExtB", "Cascadia Code","Ubuntu Mono", "Courier New";
   font-size: 90% !important;
}

.Content-Area .footnote *,  .Content-Area .footnote li::marker {
    font-size:0.9em;
    line-height: 0.9em;
}
.Content-Area hr {
    margin:0 !important;
}
.Content-Area .footnote ol {
    margin-top: 0.5em !important;
}

div.highlight {
    min-width: 100% !important;
    width: 100% !important;
    max-width: 100vw !important;
    box-sizing: border-box !important;
    overflow: auto !important;
    border-left: 2px solid var(--tr-hover-bg);
    border-radius: 2px;
    padding: 0 !important;
    margin: 4px 0px !important; /* Opposite to padding to balance it */
    height: auto !important;
    background: transparent !important;
}
div.highlight pre { /* works for both case, do not use > */
    display: grid !important;
    color: var(--primary-fg);
    padding: 8px 4px 8px 4px !important; 
    overflow: auto !important;
    width: auto !important;
    box-sizing: border-box !important;
    height: auto;
    margin: 0px !important;
    background: var(--secondary-bg) !important;
    counter-reset: line; /* important to add line numbers */
}

div.highlight code {
    counter-increment: line;
    display:inline-block !important; /* should be on new line */
    width:auto;
    min-width: calc(90% - 2.2em);
    background:transparent !important;
    color: var(--primary-fg);
    white-space: pre !important;
    overflow-wrap: normal !important;
    padding-left:2.2em;
    box-sizing: border-box !important;
}
div.highlight code:hover {
    background: var(--tr-hover-bg) !important;
}
div.highlight code:hover::before {
    background: none !important;
}
div.highlight code:before{
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
div.highlight  code > span {
    white-space: normal; /* for breaking words */
    word-break: break-word; /* for breaking words */
}
div.highlight code.code-no-focus {
    opacity:0.3 !important;
}
div.highlight code.code-focus {
    text-shadow: 0 0 1px var(--primary-bg);
}
span.lang-name {
    color: var(--accent-color);
    font-size: 0.8em;
}
.Content-Area div.PyRepr {
    margin: 4px !important;
    white-space:pre !important;
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
.Content-Area blockquote, .Content-Area blockquote>p {
	background: var(--secondary-bg);
	color: var(--secondary-fg);
}
    
.Content-Area table {
 	border-collapse: collapse !important;
    min-width:auto;
    width:100%;
    word-break:break-all;
    overflow: auto;
	color: var(--primary-fg)!important;
	background: var(--primary-bg)!important;
    border: none !important; /* Makes it pleasant to view */
    border-spacing: 0 !important;
    border-color: transparent !important;
}
.Content-Area tbody>tr:nth-child(odd) {background: var(--tr-odd-bg)!important;}
.Content-Area tbody>tr:nth-child(even) {background: var(--primary-bg)!important;}
.Content-Area tbody>tr:hover {background: var(--tr-hover-bg)!important;}

/* Make Scrollbars beautiful */
.Content-Area, .Content-Area  * { /* FireFox <3*/
    scrollbar-width: thin;
    scrollbar-color:var(--tr-odd-bg) transparent;
}
/* Other monsters */  
.Content-Area ::-webkit-scrollbar {
    height: 4px;
    width: 4px;
    background: transparent !important;
}
.highlight::-webkit-scrollbar { /* important for good display */
    background: var(--secondary-bg) !important;
}
.Content-Area ::-webkit-scrollbar:hover {
    background: var(--secondary-bg) !important;
}
.Content-Area ::-webkit-scrollbar-thumb {
    background: transparent !important;
}
.Content-Area ::-webkit-scrollbar-thumb:hover{
    background: var(--tr-hover-bg) !important;
}
.Content-Area ::-webkit-scrollbar-corner,
.highlight::-webkit-scrollbar-corner {
    display:none !important;
}   
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
.Content-Area .block {
    background: var(--primary-bg);
    border-radius: 4px;
}

@page {
    size: __page_size__;
    margin-top: 18mm !important;
    margin-bottom: 15mm !important;
}
@page:first {
    margin-top: 0mm !important; /* already 18mm padding */
}
@media print {
    * {
        color-adjust: exact !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }
    body {
        margin: 0;
        display: table;
        table-layout: fixed;
        padding-top: 18mm;
        padding-bottom: 18mm;
        height: auto;
    }
    code, span, figure, img, svg, .zoom-container, blockquote { 
        page-break-inside: avoid !important; 
    }
    ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
    div.highlight, pre, div.PyRepr {
        height:auto;
        max-height: auto !important; 
        overflow-wrap: break-word !important; 
    }
    section:first-child {page-break-after: always;margin: auto 0 !important;}
    table { page-break-inside:auto; }
    tr    { page-break-inside:avoid; page-break-after:auto; }
    h1,h2,h3,h4 { page-break-before : auto !important; page-break-after : avoid !important; page-break-inside : avoid !important; }
    
}
</style>
'''

slides_css = """<style>
.report-only { display:none !important;}
.SlidesWrapper {
	scroll-snap-type: x mandatory !important;
    display: flex !important;
    overflow-x: auto !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    height: 100vh !important;
    width: 100vw !important;
}
section {
	scroll-snap-align:start !important;
	display: grid !important;
	height: 100vh !important;
	max-height: 100vh !important;
	min-width: 100vw !important;
	box-sizing: border-box !important;
}
section .SlideArea {
	height: auto !important;
	max-height: 100vh !important;
	box-sizing: border-box;
	overflow-y: auto !important;
	width: 90vw !important;
	margin: auto !important;
	padding: 1em !important;
}
@media print {
    ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
    /* It is a fixed page, no need to tweak other things */
}
</style>
"""