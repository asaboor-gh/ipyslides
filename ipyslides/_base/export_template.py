# Template for building a report from slides 

def doc_html(code_css, style_css, content, script):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>IPySlides</title>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script> 
    
    {code_css}
    {style_css}

    <!-- Custom stylesheet, it must be in the same directory as the html file -->
    <link rel="stylesheet" href="overrides.css">

    <!-- Loading mathjax macro -->
    <!-- Load mathjax -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-AMS_HTML"></script>
    <!-- MathJax configuration -->
    <script type="text/x-mathjax-config">
    MathJax.Hub.Config({{
        tex2jax: {{
            inlineMath: [ ["$","$"] ],
            displayMath: [ ["$$","$$"] ],
            processEscapes: true,
            processEnvironments: true
        }},
        // align-center justify equations in code and markdown cells. Elsewhere
        // we use CSS to left justify single line equations in code cells.
        displayAlign: "center",
        "HTML-CSS": {{
            styles: {{".MathJax_Display": {{"margin": 0}}}},
            linebreaks: {{ automatic: true }}
        }}
    }});
    </script>
    <!-- End of mathjax configuration -->
</head>
<body>
<div>
    <div class="slides-only" style="position:fixed;right:4px;top:4px;z-index:6;"> __LOGO__ </div>
    <div class="slides-only click-wrapper" style="position:fixed;left:0;bottom:3px;z-index:6;height:15px;width:100%;"> __FOOTER__ </div>
    <!-- Classes below work for both scenerios -->
    <div class="SlidesWrapper">
    <center class="report-only" style="padding:16px;"> __LOGO__ </center>
    {content}
    </div>
</div>
</body>
{script}
</html>
'''

doc_css = '''<style type="text/css">
/* Author: Abdul Saboor */
__theme_css__
html { background: var(--secondary-bg, whitesmoke);}
body {
    background: var(--primary-bg, white);
    color: var(--primary-fg, black);
    width: 216mm;
    margin: 10mm auto;
    padding: 18mm 15mm 15mm 18mm;
}

body div.highlight, body div.highlight pre {
    width: 100% !important;
    }
    
figure, img, .zoom-child, table, .block {margin: 0 auto !important;} /* center images */
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
.slides-only, .jupyter-only {display:none !important;}
a {text-decoration:none !important;}
a:hover {text-decoration:underline !important;}

.SlidesWrapper h1, .SlidesWrapper h2,
.SlidesWrapper h3, .SlidesWrapper h4,
.SlidesWrapper h5, .SlidesWrapper h6 {
	color:var(--heading-color);
 	text-align: left !important;
    font-weight:normal;
	overflow:hidden; /* FireFox */
    margin-block: 0.2em 0.3em !important;
}

.SlidesWrapper h1, .SlidesWrapper h2 {
	margin-block: 0.4em 0.7em !important; /* need more space for h1 and h2 */
}
@page {
    size: __page_size__;
    margin-top: 18mm !important;
    margin-bottom: 15mm !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding: 0 18mm 0 15mm !important;
}
@page:first {
    margin-top: 0mm !important; /* already 18mm padding */
}
@media print {
    :root {
        --contentScale : 1 !important; /* Deafult for printing at same value */
	    --heading-color: navy;
	    --primary-fg: black;
	    --primary-bg: white;
	    --secondary-bg: whitesmoke;
	    --secondary-fg: #454545;
	    --alternate-bg: whitesmoke;
	    --hover-bg: #D1D9E1;
	    --accent-color: navy;
    }
    * {
        color-adjust: exact !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }
    body {
        background: var(--primary-bg, white) !important;
        color: var(--primary-fg, black) !important;
        margin: 0 !important;
        display: table;
        table-layout: fixed;
        padding-top: 18mm;
        padding-bottom: 18mm;
        height: auto;
    }
    code, span, figure, img, svg, .zoom-child, .zoom-self, blockquote { 
        page-break-inside: avoid !important; 
    }
    ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
    div.highlight, pre, .raw-text {
        height:auto;
        max-height: auto !important; 
        overflow-wrap: break-word !important; 
    }
    section:first-child {
        page-break-after: always;
    }
    .page-break {page-break-after: always !important;}
    table { page-break-inside:auto; }
    tr    { page-break-inside:avoid; page-break-after:auto; }
    h1,h2,h3,h4 { page-break-before : auto !important; page-break-after : avoid !important; page-break-inside : avoid !important; }
    
    /* Blocks should be handled properly in white scenerio*/
    .note {background: rgba(250,250,250,0.75);}
    .block-red {background: rgba(250,230,230,0.75);}
    .block-green {background: rgba(230,250,230,0.75);}
    .block-blue {background: rgba(230,230,250,0.75);}
    .block-yellow {background: rgba(250,250,230,0.75);}
    .block-cyan {background: rgba(230,250,250,0.75);}
    .block-gray {background: rgba(230,230,230,0.75);}
    .block-magenta {background: rgba(250,230,250,0.75);}
}
</style>
'''

slides_css = """<style>
__theme_css__
.report-only, .jupyter-only { display:none !important;}
a {text-decoration:none !important;}
a:hover {text-decoration:underline !important;}
.click-wrapper {
    display:flex;
    justify-content: space-evenly;
}
.click-wrapper .clicker {display:block;flex-grow:1;text-align:center;font-size:14px;height:15px;opacity:0;}
.click-wrapper .clicker:hover {background:var(--secondary-bg);color:var(--accent-color);opacity:1;text-decoration:none !important;}
.SlidesWrapper {
	scroll-snap-type: x mandatory !important;
    display: flex !important;
    overflow-x: auto !important;
    overflow-y: hidden !important; 
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    height: 100vh !important;
    width: 100vw !important;
}
section {
	scroll-snap-align:start !important;
    scroll-snap-stop: always !important;
	display: block !important;
	height: 100vh !important;
	max-height: 100vh !important;
	min-width: 100vw !important;
	box-sizing: border-box !important;
}
section .SlideBox {
    width: 100vw !important;
    height: 100vh !important; 
    /* Extra CSS will come from export here */
    padding: 0 !important;
    box-sizing: border-box !important;
}
section .SlideBox > .Footer > .Progress { display: none !important; }
section .SlideArea {
    /* Will be added by export */
	margin: auto !important;
	padding: 1em !important;
    box-sizing: border-box !important;
}
section .SlideBox > .Footer { 
    background: var(--primary-bg); /* no important here */
    padding: 0 !important; margin: 0 !important; 
    position:absolute;
    left:0;
    width: 100%;
    bottom: 0;
}
section .SlideBox > .Footer.NavHidden {
    background: none; /* no important here */
}
section .SlideBox > .Footer > p {
    font-size: 14px !important;
    padding: 4px !important;
    padding-left: 0.7em !important; 
    display:block !important;
    margin:0 !important;
}
section .SlideBox > .Footer.NavHidden > p {
    display:none !important;
}
.SlidesWrapper::-webkit-scrollbar:vertical,
.SlidesWrapper::-webkit-scrollbar-button,
.SlidesWrapper::-webkit-scrollbar-corner {
    display:none !important;
}
.SlidesWrapper::-webkit-scrollbar {
    background: var(--secondary-bg, whitesmoke) !important;
    height: 3px !important;
}
.SlidesWrapper::-webkit-scrollbar-thumb, 
.SlidesWrapper::-webkit-scrollbar-track-piece:start {
    background-color: var(--accent-color, navy) !important;
}
a.goto-button {
    padding: 2px;
    border: 1px solid var(--accent-color);
    border-radius: 6px;
    font-size: 16px;
}
a.goto-button:hover, a.goto-button:focus {
    box-shadow: 2px 2px 4px var(--secondary-bg);
    background: var(--secondary-bg);
}
a.goto-button:active {
    color: var(--pointer-color);
}

@media print {
    * {
        --contentScale : 1 !important; /* Deafult for printing at same value */
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
    }
    @page {
        size: 254mm __HEIGHT__; /* 10 inch x decided by aspect_ratio by user*/
        margin-top: 0 !important;
        margin-right: 0 !important;
        margin-left: 0 !important;
        margin-bottom: 0 !important;
    }
    .click-wrapper .clicker {opacity:1 !important;color:transparent !important;} /* without full opacity it does not show*/
    .SlidesWrapper {
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        height: auto !important;
    }
    section {
        display: block !important;
        margin: 0 !important;
        padding: 0 !important;
        page-break-inside: avoid !important;
        page-break-after: always !important;
        overflow: hidden !important; /* otherwise it throws text to next page */
        padding-bottom: 2em !important; /* for avoiding overflow to bottom,2em is a reasonable space */
    }
    section:last-of-type {
        page-break-after: avoid !important;
    }
    section .SlideBox {
        page-break-inside: avoid !important;
    }
    section .SlideBox > .Footer > .Progress { 
        display: block !important; 
        box-sizing: border-box;
        height: 3px !important;
        width: 100% !important;
    }
    section:first-of-type .SlideBox > .Footer > .Progress {width: 0 !important;}  /* avoid non-zero progress in title of print*/
    section .SlideArea {
        position: static !important; /*override from document as printing absolute is issue */
        overflow: hidden !important;
        page-break-inside: avoid !important;
    }
    ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
}
</style>
"""