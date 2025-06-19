# Template for building HTML from slides 

def doc_html(code_css, style_css, content, script, click_btns, height, css_class):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg viewBox='0 0 50 50' xmlns='http://www.w3.org/2000/svg' fill='none' stroke='currentColor' stroke-linecap='butt' stroke-linejoin='round' stroke-width='7.07'%3E%3Cpath d='M22.5 7.5L10 20L20 30L30 20L40 30L27.5 42.5' stroke='teal'/%3E%3Cpath d='M7.5 27.5L22.5 42.5' stroke='crimson'/%3E%3Cpath d='M32.5 32.5L20 20L30 10L42.5 22.5' stroke='red'/%3E%3C/svg%3E">
    <title>Slides</title>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script> 
    
    <style>{style_css}</style>
    {slides_css.replace('__HEIGHT__', height)}
    {code_css}

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
    <div class="click-wrapper"> {click_btns} </div>
    <!-- Classes below work for both scenerios -->
    <div class="{css_class}">
    {content}
    </div>
</div>
</body>
{script}
</html>
'''

slides_css = """<style>
.jupyter-only { display:none !important;}
a {text-decoration:none !important;}
a:hover {text-decoration:underline !important;}
p {margin-block: 0.5em !important;}
pre {white-space: break-spaces;} /* General rule unless specified in elements */
.toc-item, .goto-button {margin-block: 0.25em}
.click-wrapper {
    position: fixed !important;
    left:calc(100% - 150px) !important; /* extra space for slide number */
    bottom:3px !important;
    width: 110px !important;
    height: 21px !important;
    display:flex !important;
    z-index: 6 !important;
    justify-content: space-evenly !important;
}
.click-wrapper .clicker {display:block;flex-grow:1;color:var(--accent-color);text-align:center;font-size:14px;height:21px;text-decoration:none !important;opacity:0.4;}
.click-wrapper .clicker:hover {color:var(--fg1-color);opacity:1;}
.SlidesWrapper {
	scroll-snap-type: x mandatory !important;
    display: flex !important;
    overflow-x: auto !important;
    overflow-y: hidden !important; 
    position: fixed !important;
    scroll-behavior: smooth;
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
section .SlideBox > .Footer > .Progress { 
    display: block !important; 
    box-sizing: border-box !important;
    margin-bottom: 0 !important;
    height: 3px !important;
    width: 100% !important;
}
section:first-of-type .SlideBox > .Footer > .Progress {width: 0 !important;}  /* avoid non-zero progress in title of print*/
section .SlideArea {
    /* Will be added by export */
	margin: auto !important;
	padding: 16px !important;
    box-sizing: border-box !important;
}
section .SlideBox > .Footer { 
    padding: 0 !important; margin: 0 !important; 
    position:absolute !important;
    left:0;
    width: 100%;
    bottom: 0 !important;
    overflow: hidden !important;
}
section .SlideBox > .Footer.NavHidden {
    background: none; /* no important here */
}
section .SlideBox > .Footer > p {
    font-size: 14px !important;
    padding: 4px !important;
    padding-left: 8px !important; 
    display:block !important;
    margin:0 !important;
}
section .SlideBox > .Footer.NavHidden > p {
    display:none !important;
}
.SlidesWrapper::-webkit-scrollbar,
.SlidesWrapper::-webkit-scrollbar-button,
.SlidesWrapper::-webkit-scrollbar-corner {
    display:none !important;
}
a.goto-button {
    padding: 2px;
    border: 1px solid var(--accent-color);
    border-radius: 6px;
    font-size: 16px;
}
a.goto-button:hover, a.goto-button:focus {
    box-shadow: 2px 2px 4px var(--bg2-color);
    background: var(--bg2-color);
}
a.goto-button:active {
    color: var(--pointer-color);
}

.SlidesWrapper.Scrolling .Footer,
.SlidesWrapper.Scrolling .Number,
.SlidesWrapper.Scrolling .SlideLogo {
    visibility: hidden !important;
    transition: visbility 200ms ease-in;
}
.SlidesWrapper .Number {
    color:var(--accent-color);
    position:absolute;
    right:8px;
    bottom:6px;
    font-size:16px;
    z-index:5;
}

@media print {
    * {
        --contentScale : 1 !important; /* Defualt for printing at same value */
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
        ::-webkit-scrollbar { height: 0 !important; width: 0 !important; }
    }
    @page {
        size: 254mm __HEIGHT__; /* 10 inch x decided by aspect by user*/
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
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        page-break-inside: avoid !important;
    }
    section .SlideArea {
        position: static !important; /*override from document as printing absolute is issue */
        overflow: hidden !important;
        page-break-inside: avoid !important;
    }
    .Slides-ShowFooter .SlideArea {
        --paddingBottom: 26px; /* Default at sacle 1 its at bottom, unlike slides in Notebook, so 3px more*/
    }
}
</style>
"""