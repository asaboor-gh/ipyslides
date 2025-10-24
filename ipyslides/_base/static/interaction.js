function showLaser(box, cursor){
    cursor.style.display = 'block'; // show in place
    function onMouseMove(e) {
        let bbox = box.getBoundingClientRect()
        cursor.style.display = "block"; // show everywhere by default
        if (e.pageX > (bbox.right - 35) || e.pageY > (bbox.bottom - 35)) {
            cursor.style.display = "none";
        };
        if (e.pageX < (bbox.left + 5) || e.pageY < (bbox.top + 5)) {
            cursor.style.display = "none"; // simulate exit near edges
        };
        cursor.style.left = (e.pageX - bbox.left + 20) + "px"; 
        cursor.style.top = (e.pageY - bbox.top + 20) + "px";
    };

    box.onmousemove = onMouseMove;
}

function hideLaser(box, cursor) {
    cursor.style.display = 'none'; // hide in place
    box.onmousemove = null;
}


function progress(numSlides,numFrames, index, fidx) {
    let unit = 100/((numSlides - 1) || 1); // avoid zero division error or None
    let pv = Math.round(unit * (index - (numFrames - fidx - 1)/numFrames) * 10000)/10000;
    let gradient = `linear-gradient(to right, var(--accent-color) 0%,  var(--accent-color) ${pv}%, var(--bg2-color) ${pv}%, var(--bg2-color) 100%)`;
    return gradient
}

function printSlides(box, model) {
    let slides = Array.from(box.getElementsByClassName('SlideArea')); 
    window._printOnlyObjs = [];
    const frameCounts = model.get('_nfs') || {}; // get frame counts per slid
    
    for (let n= 0; n < slides.length; n++) {
        let slide = slides[n];
        slide.style.setProperty('--slide-number', n); // set slide number for CSS

        if (slide.childNodes.length > 0) { // Need to have scroll positions on top for all slides
            slide.childNodes[0].scrollTop = 0; // scroll OutputArea to top
        }
        // Extract slide number from class (e.g., 'n25' -> 25)
        const slideNum = parseInt([...slide.classList].find(cls => /^n\d+$/.test(cls))?.slice(1)) || null;
        const numFrames = slideNum !== null ? (frameCounts[slideNum] || 1) : 1;

        slide.style.setProperty('--bar-bg-color', progress(slides.length, numFrames, n, 0));
        if (slide.classList.contains('Frames') && numFrames > 1) {
            for (let i = 1; i < numFrames; i++) { // single frame is already there
                let clone = slide.cloneNode(true); // deep clone
                clone.classList.remove('Frames'); // remove frames class to avoid infinite loop 
                clone.classList.add(`f${numFrames - i}`); // add frame index class: f1, f2, f3...
                clone.style.setProperty('--bar-bg-color', progress(slides.length, numFrames, n, numFrames - i));
                window._printOnlyObjs.push(clone);
                slide.parentNode.insertBefore(clone, slide.nextSibling);
            }
        }
    }
    // Clean up AFTER print dialog closes
    window.addEventListener('afterprint', function cleanup() {
        for (let frame of window._printOnlyObjs) {
            frame.remove();
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
    'z': 'ZOOM', // Enable zooming items
    's': 'TPAN', // Setting panel
    'k': 'KSC', // keyboard shortcuts
    'l': 'TLSR', // L toggle laser
    'e': 'EDIT', // Edit source cell
}

function keyboardEvents(box,model) {
    function keyOnSlides(e) {
        e.preventDefault(); // stop default actions
        e.stopPropagation(); // stop propagation to jupyterlab events and other views 
        if (e.target !== box){
            return true; // inside componets should work properly, avoid going outside
        }; 

        let key = e.key; // True unicode key
        let message = '';
        if ('123456789'.includes(key)) { // send to shift slides by numbers
            message = (e.ctrlKey ? "SHIFT:-" + key : "SHIFT:" + key);
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
        } else if (key === 'ArrowLeft' || (e.ctrlKey && key === ' ')) { // ^ + Space, <
            message = 'PREV';
        } else if (key === 'ArrowRight' || key === ' ') { // Space, >
            message = 'NEXT';
        } else if (key === '0') {
            message = (e.ctrlKey? "HOME": "END"); // Numbers don't change with control
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

function handleMessage(model, msg, box, cursor) {
    if (msg === "TFS") {
        if (document.fullscreenElement) {
            document.exitFullscreen(); // No box.fullscreen
        } else {
            box.requestFullscreen();
            box.focus(); // it gets unfocused, no idea why
        }
    } else if (msg === "TLSR") {
        if (box.onmousemove) {
            hideLaser(box,cursor);
        } else {
            showLaser(box, cursor);
        };
    
    } else if (msg === 'RESCALE') {
        setScale(box);
    } else if (msg === "SwitchView") {
        let slideNew = box.getElementsByClassName("ShowSlide")[0];
        slideNew.style.visibility = 'visible';

        let others = box.getElementsByClassName("HideSlide");
        for (let slide of others) {
            if (slide.style.visibility === 'visible') {
                slide.style.visibility = 'hidden';
            };
        }
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
    } else if (msg.includes("ToggleID:")) { // Toggle ID of slides
        const ids = msg.replace("ToggleID:","").split(",");
        const slides = box.getElementsByClassName('SlideArea');
        if (ids.length !== slides.length) {
            console.warn("Number of ids does not match number of slides, skipping setting ids");
            return false; // don't set ids if not match
        }
        for (let i = 0; i < slides.length; i++) {
            if (!ids[i]) {
                slides[i].removeAttribute('id'); // remove id if not set
            } else {
                slides[i].setAttribute('id', ids[i]); // set id if provided
            }
        }
        
    }
};

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

function setScale(box) {
    let sbox = box.getElementsByClassName('SlideBox')[0];
    let slide = box.getElementsByClassName('SlideArea')[0];
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
    
    box.style.setProperty('--contentScale',scale);
    box.style.setProperty('--paddingBottom',Number(23/scale) + "px");
}

function handleScale(box) {
    const resizeObs = new ResizeObserver((entry) => {
        setScale(box);
    });

    resizeObs.observe(box);
    setScale(box); // First time set
}

function setColors(model, box) {
    let style = window.getComputedStyle(box);
    const colors = {}
    for (let prop of ['accent', 'pointer', 'bg1', 'bg2', 'bg3', 'fg1', 'fg2', 'fg3']) {
        colors[prop] = style.getPropertyValue('--' + prop + '-color');
    }
    if (colors['accent']) { // Avoid sending empty data due to other closed displays
        model.set("_colors", colors);
        model.save_changes();
    };
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
            
            const getSlideIndex = (el) => {
                const className = [...el.classList].find(cls => /^n\d+$/.test(cls)); // regex to find class like n1, n2, etc.
                return className ? parseInt(className.slice(1), 10) : null;
            };    
            
            const originIndex = getSlideIndex(originSlide);
            const targetIndex = getSlideIndex(targetSlide);   
            
            if (originIndex !== null && targetIndex !== null) {
                const offset = targetIndex - originIndex;
                model.set("msg_topy", `SHIFT:${offset}`); // Send message to shift slides
                model.save_changes();
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
        
        // Laser pointer
        let cursor = box.getElementsByClassName('LaserPointer')[0];
        cursor.style = "position:absolute;display:none;"; // initial

        box.onmouseenter = function(){box.focus();};
        box.onmouseleave = function(){box.blur();};
        
        // Keyboard events
        keyboardEvents(box,model);

        // handle scale of slides size
        handleScale(box);

        // Remove other views without closing comm
        keepThisViewOnly(box); 

        // Link switches slides
        linkSwitchesSlide(model, box);

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
            handleMessage(model, msg, box, cursor);
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