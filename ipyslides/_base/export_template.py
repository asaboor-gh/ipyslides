# Template for building HTML from slides 

def doc_html(code_css, style_css, content, script, click_btns, css_class, padding_bottom):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg viewBox='0 0 50 50' xmlns='http://www.w3.org/2000/svg' fill='none' stroke='currentColor' stroke-linecap='butt' stroke-linejoin='round' stroke-width='7.07'%3E%3Cpath d='M22.5 7.5L10 20L20 30L30 20L40 30L27.5 42.5' stroke='%2343D675'/%3E%3Cpath d='M7.5 27.5L22.5 42.5' stroke='%234F8EF7'/%3E%3Cpath d='M32.5 32.5L20 20L30 10L42.5 22.5' stroke='%234F8EF7'/%3E%3C/svg%3E">
    <title>Slides</title>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script> 
    
    <style>{style_css}</style>
    {slides_css.replace("__PADBTM__",str(padding_bottom))}
    {code_css}

    <!-- Custom stylesheet, it must be in the same directory as the html file -->
    <link rel="stylesheet" href="overrides.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA==" crossorigin="anonymous" referrerpolicy="no-referrer" />

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
            styles: {{".MathJax_Display": {{"margin": "0.5em auto"}}}},
            linebreaks: {{ automatic: true }}
        }}
    }});
    </script>
    <!-- End of mathjax configuration -->
</head>
<body>
<div>
    {click_btns}
    <!-- Classes below work for both scenerios -->
    <div class="{css_class}">
    {content}
    </div>
</div>
</body>
{script.replace("__PADBTM__",str(padding_bottom))}
</html>
'''

slides_css = """<style>
.jupyter-only { display:none !important;}
a {text-decoration:none !important;}
a:hover {text-decoration:underline !important;}
p {margin-block: 0.25em !important;}
pre {white-space: break-spaces;} /* General rule unless specified in elements */
.toc-item {margin-block: 0.25em}
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
    line-height: 1.5 !important; /* Default line-height for all text to match Jupyter */
    box-sizing: border-box !important;
}
section {
	scroll-snap-align:start !important;
    scroll-snap-stop: always !important;
	display: block !important;
	height: 100vh !important;
	max-height: 100vh !important;
	min-width: 100vw !important;
	box-sizing: border-box !important;
    background: var(--bg1-color) !important; /* need for each slide */
}
section .SlideBox {
    width: 100vw !important;
    height: 100vh !important; 
    /* Extra CSS will come from export here */
    padding: 0 !important;
    box-sizing: border-box !important;
}
section .SlideBox > .Progress { 
    display: block !important; 
    box-sizing: border-box !important;
    margin: 0 !important;
    height: 2px !important;
    width: 100% !important;
    position: absolute !important;
    left:0 !important;
    bottom: 0 !important;
}
section:first-of-type .SlideBox > .Progress {width: 0 !important;}  /* avoid non-zero progress in title of print*/
section .SlideArea {
    /* Will be added by export */
	margin: auto !important;
	padding: 16px !important;
    box-sizing: border-box !important;
}
.SlidesWrapper .Footer { 
    padding: 0 !important; margin: 0 !important; 
    position: fixed !important;
    left:0;
    width: 100%;
    bottom: 2px !important;
    overflow: hidden !important;
}
.SlidesWrapper .Footer.NavHidden {
    background: none; /* no important here */
}
.SlidesWrapper .Footer > p {
    font-size: 14px !important;
    padding: 4px !important;
    padding-left: 8px !important; 
    display:block !important;
    margin:0 !important;
}
.SlidesWrapper .Footer.NavHidden > p {
    display:none !important;
}
.SlidesWrapper .SlideLogo {
    position: fixed !important;
    line-height: 0 !important; /* suppress bad line-height here */
}
.SlidesWrapper::-webkit-scrollbar,
.SlidesWrapper::-webkit-scrollbar-button,
.SlidesWrapper::-webkit-scrollbar-corner {
    display:none !important;
}

.SlidesWrapper.Scrolling .Progress,
.SlidesWrapper.Scrolling .Number {
    visibility: hidden !important;
    transition: visbility 200ms ease-in;
}
.SlidesWrapper .Number {
    color:var(--fg2-color);
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
    /* Page size is set in style_css */
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
        padding-bottom: __PADBTM__px !important; /* for avoiding overflow to bottom,same as under SlideArea */
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
        --paddingBottom: __PADBTM__px; /* fixed for printing */
    }
}
</style>
"""