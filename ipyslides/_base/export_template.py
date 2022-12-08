# Template for building a report from slides 

doc_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>IPySlides</title>
    
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
        // align-center justify equations in code and markdown cells. Elsewhere
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
    <div class="SlidesWrapper">
    __content__
    </div>
</div>
</body>
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

.SlidesWrapper h1, .SlidesWrapper h2,
.SlidesWrapper h3, .SlidesWrapper h4,
.SlidesWrapper h5, .SlidesWrapper h6 {
	color:var(--heading-color);
 	text-align: left !important;
	overflow:hidden; /* FireFox */
    margin-block: 0.6em 0.5em !important;
}

.SlidesWrapper h1, .SlidesWrapper h2 {
	margin-block: 1.2em 1em !important; /* need more space for h1 and h2 */
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
    code, span, figure, img, svg, .zoom-container, blockquote { 
        page-break-inside: avoid !important; 
    }
    ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
    div.highlight, pre, .raw-text {
        height:auto;
        max-height: auto !important; 
        overflow-wrap: break-word !important; 
    }
    section:first-child {page-break-after: always;margin: auto auto !important;}
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
    scroll-snap-stop: always !important;
	display: flex !important;
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
    box-sizing: border-box !important;
}
section span.html-slide-number {
    width: auto;
    height: 1.3em;
    padding: 0.1em;
    margin: auto 8px 8px auto;
    color: var(--secondary-fg);
    font-size: 0.7em;
}
.SlidesWrapper::-webkit-scrollbar:vertical,
.SlidesWrapper::-webkit-scrollbar-button,
.SlidesWrapper::-webkit-scrollbar-corner {
    display:none !important;
}
.SlidesWrapper::-webkit-scrollbar {
    background: var(--secondary-bg, whitesmoke) !important;
    height: 4px !important;
}
.SlidesWrapper::-webkit-scrollbar-thumb, 
.SlidesWrapper::-webkit-scrollbar-track-piece:start {
    background-color: var(--accent-color, navy) !important;
}

@media print {
    * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
    }
    @page {
        size: letter landscape;
        margin-top: 0 !important;
        margin-right: 0 !important;
        margin-left: 0 !important;
        margin-bottom: 0 !important;
    }

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
        display: flex !important;
        margin: 0 !important;
        page-break-inside: avoid !important;
        page-break-after: always !important;
    }
    section:last-of-type {
        page-break-after: avoid !important;
    }
    section .SlideArea {
        height: auto !important;
        max-height: 100% !important;
        box-sizing: border-box;
        overflow: hidden !important;
        max-width: 100% !important;
        margin: auto !important;
        page-break-inside: avoid !important;
    }
    ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
}
</style>
"""