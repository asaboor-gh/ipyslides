
function updateProgress(show, numSlides, numFrames, index, fidx) {
    if (!show) {
        return 'transparent';
    }
    let unit = 100/((numSlides - 1) || 1); // avoid zero division error or None
    let pv = Math.round(unit * (index - (numFrames - fidx - 1)/numFrames) * 10000)/10000;
    let gradient = `linear-gradient(to right, var(--accent-color) 0%,  var(--accent-color) ${pv}%, var(--bg2-color) ${pv}%, var(--bg2-color) 100%)`;
    return gradient
}

// Function to fix IDs and references in cloned elements, especially for matplotlib SVGs
function fixIDsAndRefs(clone, cloneIndex = 0) {
  const idMap = {};

  // Step 1: assign unique IDs for all elements in the clone
  clone.querySelectorAll('[id]').forEach(el => {
    const oldId = el.id;
    const newId = `${oldId}__${cloneIndex}`;
    idMap[oldId] = newId;
    el.id = newId;
  });

  // Step 2: update all attributes containing # references
  clone.querySelectorAll('*').forEach(el => {
    for (const attr of el.getAttributeNames()) {
      const val = el.getAttribute(attr);
      if (!val || !val.includes('#')) continue;

      let newVal = val;
      Object.entries(idMap).forEach(([oldId, newId]) => {
        newVal = newVal.replace(new RegExp(`#${oldId}\\b`, 'g'), `#${newId}`);
      });
      if (newVal !== val) el.setAttribute(attr, newVal);
    }
  });

  return clone;
}

function tldrawLinks(box) { // Add a print-only link in draw button 
    box.querySelectorAll('.Draw-Btn.Menu-Item').forEach((btn) => {
        let cs = window.getComputedStyle(btn); // we need to preserve size
        let newBtn = document.createElement('button');
        newBtn.className = 'print-only Draw-Btn';
        newBtn.innerHTML = `<a href="https://www.tldraw.com" target="_blank" rel="noopener noreferrer" class="fa fa-edit" style="width:100%;height:auto;"></a>`;
        newBtn.style.cssText = `width: ${cs.width};height: ${cs.height};margin: ${cs.margin};opacity:1;`; // copy layout styles and keep clearly visible
        btn.parentNode.insertBefore(newBtn, btn.nextSibling); // insert after draw button
        btn.classList.add('jupyter-only'); // hide original button in print
        window._printOnlyObjs.push(newBtn); // keep track for cleanup, becomes duplicate otherwise on multiple prints
    });
}

function printSlides(box, model) {
    let slides = Array.from(box.getElementsByClassName('SlideArea')); 
    window._printOnlyObjs = [];
    const frameCounts = model.get('_nfs') || {}; // get frame counts per slid
    const parts = model.get('_pfs') || {}; // get part counts per slide
    const fkws = model.get('_fkws') || {}; // get footer kws
    box.style.setProperty('--printPadding', fkws.pad + 'px'); // set padding for print mode
    tldrawLinks(box);
    
    for (let n = 0; n < slides.length; n++) {
        let slide = slides[n];
        
        slide.querySelector('.jp-OutputArea').scrollTop = 0; // scroll OutputArea to top to avoid cutoffs
        // Extract slide number from class (e.g., 'n25' -> 25)
        const slideNum = parseInt([...slide.classList].find(cls => /^n\d+$/.test(cls))?.slice(1)) || null;
        const numFrames = slideNum !== null ? (frameCounts[slideNum] || 1) : 1;
        slide.style.setProperty('--bar-bg-color', updateProgress(fkws.bar, slides.length, numFrames, n, 0));
        slide.style.setProperty('--slide-number', n) // set slide number for CSS only if needed
        slide.style.setProperty('--show-snumber', fkws.snum ? 'block' : 'none'); // show only if numbered
        // ensure background image is set for printing, if user may not naviagted all slides or message was sent when slides were not yet loaded
        setBgImage(slide); // main Image is not needed for print, only per slides
        
        if (slide.classList.contains('base') && numFrames > 1) {
            let lastInserted = slide; // to keep insertion order
            
            for (let i = 1; i < numFrames; i++) { // single frame is already there
                let clone = slide.cloneNode(true); // deep clone
                clone.classList.remove('base'); // remove base class to avoid CCS clashes
                clone.classList.add('print-only'); // avoid cluttering screen view
                clone.querySelector('.Slide-UID')?.remove(); // remove section id from clone
                clone.style.setProperty('--bar-bg-color', updateProgress(fkws.bar, slides.length, numFrames, n, i));
                clone.querySelector('.jp-OutputArea').style.maxHeight = '100%'; // force to avoid spilling over padding of slide
                
                // Set visibility of parts if any, Do not change this to CSS only as
                // clones were not working proprly with already set with CSS anyway, after all struggle, here is brute force way
                if (parts[slideNum] && parts[slideNum][i] !== undefined) {
                    let outputs = Array.from(clone.querySelector('.jp-OutputArea').childNodes); // corresponds to contents on python side
                    let part = parts[slideNum][i];
                    // console.log(part);
                    for (let j = 0; j < outputs.length; j++) {
                        // console.log(i,j);
                        if (part.row !== undefined) { // incremental frames
                            if (j > part.row) {
                                outputs[j].setAttribute('data-hidden','true'); // rest handled by CSS
                            }
                            if (part.col !== undefined && j === part.row) {
                                // specific column hiding inside last visible row
                                let cols = outputs[j].querySelectorAll('.columns.writer:first-of-type > div');
                                for (let k=0; k < cols.length; k++) {
                                    if (k >= part.col) {
                                        cols[k].setAttribute('data-hidden','true'); // keep content to avoid reflow
                                    }
                                }
                            }
                        } else if (Array.isArray(part) && !part.includes(j)) { // non-incremental frames
                            outputs[j].remove(); // will not need to show again, so it safe to remove from layout
                        }
                    }
                }
                clone = fixIDsAndRefs(clone, i); // ensure unique IDs and refs in clone
                window._printOnlyObjs.push(clone);
                slide.parentNode.insertBefore(clone, lastInserted.nextSibling);
                lastInserted = clone; // update last inserted
            }
        }
    }
    // Clean up AFTER print dialog closes
    window.addEventListener('afterprint', function cleanup() {
        for (let obj of window._printOnlyObjs) {
            obj.remove();
        }
        delete window._printOnlyObjs;
        window.removeEventListener('afterprint', cleanup); // cleanup listener
    }, { once: true }); // or use { once: true } instead of removeEventListener
    
    setTimeout(() => {   
        window.print();
    }, 1000); // slight delay to ensure rendering
}

const keyMessage = {
    'f': 'TFS', // Toggle Fullscreen with F but with click from button
    's': 'TPAN', // Setting panel
    'k': 'KSC', // keyboard shortcuts
    'e': 'EDIT', // Edit source cell
    'l': 'TLSR', // . toggle laser, enables this on purely numpad keyboards
}

function keyboardEvents(box,model) {
    function keyOnSlides(e) {
        e.preventDefault(); // stop default actions
        e.stopPropagation(); // stop propagation to jupyterlab events and other views 
        if (e.target !== box){
            return true; // inside componets should work properly, avoid going outside
        }; 

        // Block keyboard navigation for extra safety when in popup focus mode
        if (box.classList.contains('mode-inactive')) {
            return; // extra safety
        }

        let key = e.key; // True unicode key
        let message = '';
        if ('/*'.includes(key)) {
            message = "SHIFT:" + (key === '/' ? "-5" : "5"); // Shift slide by 5
        } else if (key === 'x' || key === 'd') {
            alert("Pressing X or D,D may cut selected cell! Click outside slides to capture these keys!");
            e.stopPropagation(); // stop propagation to jupyterlab events
            return false;
        } else if (key === 'm'){
            alert("Pressing M could change cell to Markdown and vanish away slides!");
            e.stopPropagation();   // M key
            return false;
        }  else if (key === 'Enter') { 
            e.stopPropagation();   // Don't let it pass over slides though, still can't hold Shift + Enter
            return true; // Enter key or Escape key should act properly
        } else if (key === 'ArrowLeft' || key === '-') { // -, <
            message = 'PREV';
        } else if (key === 'ArrowRight' || key === '+' || key === ' ') { // Space, +,  >
            message = 'NEXT';
        } else if (key in keyMessage && !e.ctrlKey){
            message = keyMessage[key];
        } else if (e.ctrlKey && key === 'p') { // Ctrl + Shift + P is picked by system, so using Alt instead
            message = e.altKey ? 'PRINT2' : 'PRINT'; // Ctrl + P for print, Ctrl + Alt + P for print merged frames
        } 

        model.set("msg_topy", message);
        model.save_changes();
    }
    
    box.onkeydown = keyOnSlides;
};

function handleMessage(model, msg, box) {
    if (msg === "TFS") {
        if (document.fullscreenElement) {
            document.exitFullscreen(); // No box.fullscreen
        } else {
            box.requestFullscreen();
            box.focus(); // it gets unfocused, no idea why
        }
    } else if (msg === 'RESCALE') {
        setScale(box, model);
    } else if (msg === "SwitchView") {
        let slideNew = box.getElementsByClassName("ShowSlide")[0];
        slideNew.style.visibility = 'visible';
        slideNew.querySelector('.jp-OutputArea').scrollTop = 0; // scroll reset is important
        setBgImage(slideNew); // ensure background image is set if not yet
        setMainBgImage(slideNew, box) // set background image if any on current slide

        let others = box.getElementsByClassName("HideSlide");
        for (let slide of others) {
            if (slide.style.visibility === 'visible') {
                slide.style.visibility = 'hidden';
            };
        }
    } else if (msg === "SetIMG") { // set background image content area to slide background
        box.querySelectorAll('.SlideArea').forEach(setBgImage); // only set which are not yet set
    } else if (msg.includes("THEME:")) {
        let theme = msg.replace("THEME:","");

        if (theme.includes("jupyterlab")) {
            let jpTheme = document.body.getAttribute('data-jp-theme-name');
            jpTheme = (jpTheme?jpTheme:"").toLowerCase(); // handle custom themes name too by lowercase
            if (jpTheme.includes("dark")) {
                theme = "dark"; // update
            } else if (jpTheme.includes("light")) {
                theme = "light"; // update
            }
        }
        let container = box.getElementsByClassName("Draw-Widget")[0].getElementsByClassName("tl-container")[0];
        container.classList.remove((theme === "light") ? "tl-theme__dark" : "tl-theme__light")
        container.classList.add("tl-theme__" + theme) // worst way to do it, internal frames are changed with CSS
    } else if (msg === "CloseView") { // deletes node without closing comm to kernl
        if (box) { // may be nothing there left already
            box.remove();
        }
    } else if (msg === "SetColors") { // sent by export_html function only
        setColors(model, box);
    } else if (msg === "PRINT") {
        printSlides(box, model);
    } 
};

function setBgImage(slide) {
    let bgImage = slide.querySelector('.BackLayer.print-only'); // it's in first child only
    if (bgImage) {
        // remove from current position and reinsert at back, avoid duplicate memory usage
        bgImage.remove();
        slide.insertBefore(bgImage, slide.firstChild); // to be a at back, need to be first child    
        bgImage.style.zIndex = 0; // ensure at back further
    }
}

function setMainBgImage(slide, target) {
    let bgImage = slide.querySelector('.BackLayer.print-only'); // take from slide
    let targetBg = target.querySelector('.BackLayer'); // target backlayer
    if (bgImage) {
        targetBg.innerHTML = bgImage.innerHTML; // clone content
        targetBg.id = bgImage.id; // keep same id for filters etc
    } else {
        targetBg.innerHTML = ""; // clear if none
        targetBg.id = ""; // clear id too
    }
}

function keepThisViewOnly(box){
    let uid = box.getAttribute("uid");
    let slides = document.querySelectorAll(`[uid='${uid}']`); // This avoids other notebooks Slides
    slides.forEach((slide) => {
        if (slide !== box) { // only keep this view
            slide.remove(); // deletes node, but keeps comm live
        }
    })
}

function handleChangeFS(box,model){
    if (box === document.fullscreenElement) {
        model.set("msg_topy", "FS")
    } else {
        model.set("msg_topy", "!FS")
    };
    model.save_changes();
}

function handleToastMessage(toast, msg) {
    if (msg.content){
        function onClick(){
            clearTimeout(toast.timerId); // clear previous timout even if null
            toast.style.top="-120%";
            toast.innerHTML = "";
        };
        onClick(); // Clear up previous things
        
        if (msg.content === "x") {
            return false; // do nothing, cleared above 
        }

        let div = document.createElement('div');
        div.style = "padding:8px;font-size:16px;" // inline fonts are better
        div.innerHTML = msg.content;
        let btn = document.createElement('button');
        btn.innerHTML = "<i class='fa fa-close'></i>";
        btn.onclick = onClick;
        toast.appendChild(btn);
        toast.appendChild(div);
        toast.style.top="4px";

        if (msg.timeout) {
            toast.timerId = setTimeout(onClick,msg.timeout) // already set to ms in python 
        }
    }
}

function setScale(box, model) {
    let sbox = box.querySelector('.SlideBox');
    let slide = box.querySelector('.SlideArea');
    if (!sbox || !slide) {
        return false; // not ready yet
    }
    
    let rectBox = sbox.getBoundingClientRect();
    let rectSlide = slide.getBoundingClientRect();

    let oldScale = box.style.getPropertyValue('--contentScale');
    
    if (!oldScale) {
        oldScale = 1; // default
    }
   
    let scaleH = oldScale*rectBox.height/rectSlide.height;
    let scaleW = oldScale*rectBox.width/rectSlide.width; 
    let scale = scaleH > scaleW ? scaleW : scaleH;
    
    if(!scale) { // Only set if there is one, don't set null
        return false; // This will ensure if Notebook is hidden, scale stays same
    }
    const pad = model.get('_fkws').pad || 23; // padding bottom, default 23px for footer space
    box.style.setProperty('--contentScale',scale);
    box.style.setProperty('--paddingBottom',Number(pad/scale) + "px");
}

function handleScale(box, model) {
    const resizeObs = new ResizeObserver((entry) => {
        setScale(box, model);
    });

    resizeObs.observe(box);
    setScale(box, model); // First time set
}

// Avoid clicks passing through to underlying clickable elements
const INTERACTIVE_SEL = "a, button, input, select, textarea, area[href], summary, [contenteditable='true']";  

function handleBoxClicks(box, model) {
    // Handle single clicks for navigation and blocking
    box.addEventListener('click', function(event) {
        // First, check for interactive elements that should handle their own clicks
        if (event.target.closest(INTERACTIVE_SEL)) {
            event.stopPropagation(); // stop propagation to underlying slides
            return true; // let the click happen
        }
        
        // Check if in focus mode, do not pass clicks to slides to avoid accidental slide changes
        if (event.target.closest('.mode-popup-active') || box.classList.contains('mode-inactive')) {
            event.stopPropagation(); // stop propagation to underlying slides
            event.preventDefault(); // stop default actions
            return; // Exit early
        }
        
        // Handle edge clicks for navigation (only on SlideArea or SlideBox)
        if (!event.target.classList.contains('SlideArea') && !event.target.classList.contains('SlideBox')) {
            return; // Only handle clicks on slide area or wrapping box itself
        }
        
        const rect = box.getBoundingClientRect(); 
        const clickX = event.clientX - rect.left;
        const edgeWidth = 16; // 16px padding area
        let message = '';
        
        if (clickX <= edgeWidth) {
            message = 'PREV'; // Clicked on left edge
        } else if (clickX >= rect.width - edgeWidth) {
            message = 'NEXT'; // Clicked on right edge
        }
        
        if (message) {
            event.preventDefault();
            event.stopPropagation();
            model.set("msg_topy", message);
            model.save_changes();
        }
    });

    // Handle double-click for entering focus mode
    box.addEventListener('dblclick', function(event) {
        // Check for interactive elements - they should handle their own double-clicks (text selection, etc.)
        if (event.target.closest(INTERACTIVE_SEL)) {
            return; // Let interactive elements handle their own double-clicks
        }
        
        event.preventDefault(); 
        event.stopPropagation();
        
        // Check if already in focus mode - exit it
        if (box.classList.contains('mode-inactive')) {
            const closeBtn = box.querySelector('.popup-close-btn');
            if (closeBtn) {
                closeBtn.click(); // Trigger close button
            }
            return;
        }

        // Check for focusable elements
        const matchedElem = event.target.closest(model.get("_fsels"));
        if (matchedElem) { // Focus by JS to be able to have a close button etc
            box.blur(); // remove focus from box to avoid keyboard events there
            box.classList.add('mode-inactive');
            matchedElem.classList.add('mode-popup-active');
            
            const btn = document.createElement('button');
            btn.className = 'popup-close-btn';
            btn.title = 'Close Popup (Double-click)';
            btn.innerHTML = '<i class="fa fa-close"></i>';
            btn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                box.classList.remove('mode-inactive'); // remove focus active indication
                matchedElem.classList.remove('mode-popup-active');
                box.focus(); // return focus to box
                btn.remove(); // remove button
            };
            box.appendChild(btn);
        }
    });
}

function setColors(model, box) {
    let style = window.getComputedStyle(box);
    const colors = {}
    Object.entries(model.get("_colors")).forEach(([prop, cssVar]) => {
        colors[prop] = style.getPropertyValue(cssVar);
    });
    if (colors['accent']) { // Avoid sending empty data due to other closed displays
        model.set("_colors", colors);
        model.save_changes();
    };
}

function getSlideIndex(slide){
    return Array.from(
        slide.parentNode.querySelectorAll('.SlideArea')
    ).indexOf(slide);
}

function showJumpIndictor(model, box, originIndex, offset) {
    if (box._jumpIndicator) {
        clearTimeout(box._jumpIndicator.timerId);
        clearInterval(box._jumpIndicator.countdownInterval); // Clear countdown too
        box._jumpIndicator.remove();
    }
    
    let indicator = document.createElement('button');
    indicator.style.cssText = `
        position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%);cursor: pointer;backdrop-filter: blur(4px);
        font-size: 12px; z-index: 99; border:none;outline:none; text-shadow: 0px 1px var(--bg2-color);`;
    indicator.title = `Jumped ${offset > 0 ? 'forward' : 'backward'} by multiple slides, click to go back.`;
    box.appendChild(indicator);

    let countdown = 10;
    
    function updateCountdown() {
        countdown -= 1;
        if (countdown > 0 && box._jumpIndicator) {
            indicator.innerHTML = `<i class="fa fa-arrow${offset > 0 ? 'l' : 'r'}"></i> Back to Link 
            <span style="color: var(--pointer-color);margin-left:4px;text-shadow: 0.5px 1px var(--bg2-color);">${countdown}</span>`;
        } else {
            indicator.remove();
            box._jumpIndicator = null;
        }
    }

    function resetTimer() {
        clearTimeout(indicator.timerId);
        clearInterval(indicator.countdownInterval); // Clear old countdown
        countdown = 10; // Reset countdown
        indicator.innerHTML = `<i class="fa fa-arrow${offset > 0 ? 'l' : 'r'}"></i> Back to Link 
        <span style="color: var(--pointer-color);margin-left:4px;text-shadow: 0.5px 1px var(--bg2-color);">${countdown}</span>`;
        
        // Start new countdown
        indicator.countdownInterval = setInterval(updateCountdown, 1000);
        indicator.timerId = setTimeout(() => {
            clearInterval(indicator.countdownInterval);
            indicator.remove();
            box._jumpIndicator = null;
        }, 10000);
    }
    
    indicator.onmouseenter = resetTimer;
    indicator.originIndex = originIndex;
    
    indicator.onclick = function() {
        let currentIndex = getSlideIndex(box.querySelector('.SlideArea.ShowSlide'));
        if (currentIndex !== null) {
            let backOffset = indicator.originIndex - currentIndex;
            model.set("msg_topy", `SHIFT:${backOffset}`);
            model.save_changes();
        }
        clearInterval(indicator.countdownInterval); // Clear countdown on click
        clearTimeout(indicator.timerId);
        indicator.remove();
        box._jumpIndicator = null;
    };
    
    resetTimer(); // Start initial timer and countdown
    box._jumpIndicator = indicator;
}

function linkSwitchesSlide(model, box) {
    box.addEventListener('click', function (event) {
        const anchor = event.target.closest('.slide-link'); // Find the closest link with class 'slide-link
        if (!anchor || !box.contains(anchor)) return;   
        event.preventDefault(); 
        const href = anchor.getAttribute('href');
        const targetId = href.startsWith('#') ? href.slice(1) : null;
        const targetElement = targetId ? document.getElementById(targetId) : document.querySelector(href);  
        const originSlide = anchor.closest('.SlideArea');
        const targetSlide = targetElement?.closest('.SlideArea');   
        if (originSlide && targetSlide) {    
            const originIndex = getSlideIndex(originSlide);
            const targetIndex = getSlideIndex(targetSlide);   
            
            if (originIndex !== null && targetIndex !== null) {
                const offset = targetIndex - originIndex;
                model.set("msg_topy", `SHIFT:${offset}`); // Send message to shift slides
                model.save_changes();
                showJumpIndictor(model, box, originIndex, offset); // Show jump indicator to click back
                } else {
                alert(`Link '${anchor.textContent}' does not point to a valid slide`);
            }
        } else if (!originSlide || !targetSlide) {
            alert(`Link target not found or it was not set on a slide: '${anchor.textContent}'`);
        } 
    });
}

function markPrintable(el, className) {
  // First, remove the class from any previously marked elements
  document.querySelectorAll('.' + className).forEach(node => node.classList.remove(className));
  
  // Then walk up from the given element to <body>, adding the class
  while (el && el !== document.body) {
    el.classList.add(className);
    el = el.parentElement;
  }
}

function render({ model, el }) {
    let style = document.createElement('style');
    //  Trick to get main slide element is to wait for a loadable element
    style.onload = () => { 
        // Send a clean message after a second, without any error caused by other functions
        setTimeout(() => {
            model.set("msg_topy", "CleanView"); // after view, fix all others
            model.save_changes();
        }, 1000)

        let box = style.parentNode.parentNode;
        box.tabIndex = -1; // Need for event listeners, should be at top
        box.setAttribute("uid", model.get("_uid"));
        
        // Only for jupyter, voila, notebook, do as early as possible
        if (window.hasOwnProperty('_JUPYTERLAB')) {
            model.set("msg_topy","JUPYTER");
            model.save_changes();
        };

        box.onmouseenter = function(){
            if (!box.classList.contains('mode-inactive')){
                box.focus(); // focus only if not in inactive mode
            }
        };
        box.onmouseleave = function(){box.blur();};
        
        // Keyboard events
        keyboardEvents(box,model);

        // handle scale of slides size
        handleScale(box, model);

        // Remove other views without closing comm
        keepThisViewOnly(box); 

        // Link switches slides
        linkSwitchesSlide(model, box);

        // Handle box clicks for both focus and edge navigation
        handleBoxClicks(box, model);

        // Sends a message if fullscreen is changed by some other mechanism
        box.onfullscreenchange = ()=>{handleChangeFS(box,model)};

        // If voila, turn on full viewport
        let base_url = box.ownerDocument.body.getAttribute('data-base-url');
        if (base_url && base_url.includes("voila")) {
            box.classList.add("Voila-Child");
            box.ownerDocument.body.classList.add("Voila-App");
        };
        
        // Handle changes from Python side  
        model.on("change:msg_tojs", () => {
            let msg = model.get("msg_tojs");
            if (!msg) {return false}; // empty message, don't waste time
            handleMessage(model, msg, box);
        })

        // Handle notifications
        let toast = box.getElementsByClassName('Toast')[0]; // Define once
        toast.style = "top:-120%;transition: top 200ms"; // other props in CSS
        toast.timerId = null; // Need to auto remove after some time

        model.on("msg:custom", (msg) => {
            handleToastMessage(toast, msg);
        })

        // Reset size of drawing board instead of provided by widget
        let drawing = box.getElementsByClassName('Draw-Widget')[0];
        // Let all keys work here but don't go further up and avoid navigation of slides too.
        drawing.onkeydown = (e) => {e.stopPropagation();} 
        
        for (let c of drawing.childNodes) {
            c.style.width = '100%';
            c.style.height = '100%';
        }

        // Add a div to hold background image
        let bglayer = document.createElement('div');
        bglayer.className = 'BackLayer'; // other 
        box.insertBefore(bglayer, box.firstChild); // at back
        bglayer.style.zIndex = 0; // ensure at back further

        // Set background images if any left due to being loaded from python script
        box.querySelectorAll('.SlideArea').forEach(setBgImage); // only set which are not yet set
        setMainBgImage(box.querySelector('.ShowSlide'), box) // set background image if any on current slide
        
        // Add classes to mark ancestors for printing
        markPrintable(box, 'ipyslides-print-node');
    }  
    el.appendChild(style);
    model.set("msg_topy", "LOADED"); // to run onload functionality
    model.save_changes();
    
    // Clean up old slides if left over from previous session of kernel restart
    let slides = document.getElementsByClassName('SlidesWrapper');
    for (let slide of Array.from(slides)) {
        if (slide.classList.contains('jupyter-widgets-disconnected')) {slide.remove();};
    };
    return () => { 
        // clean up at removal time
	};
}

export default { render }