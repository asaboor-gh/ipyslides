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

function touchSwiper(box, model){
    let startX = 0;
    let endX = 0;
    let startY = 0;
    let endY = 0;
    
    box.addEventListener('touchstart', function (event) {
        startX = event.changedTouches[0].screenX;
        startY = event.changedTouches[0].screenY;
    }, false);

    box.addEventListener('touchend', function (event) {
        endX = event.changedTouches[0].screenX;
        endY = event.changedTouches[0].screenY;
        handleGesture();
    }, false);

    function handleGesture() {
        let bbox = box.getBoundingClientRect(); // Swipe only from edges
        if (Math.abs(endY - startY) < 20) {
            // Y axis is not important but we should avoid X component of touch for a long y-scroll
            if ((endX - startX) < -40 && startX > (bbox.right - 50)) {
                model.set("msg_topy", "NEXT"); // align-left Swipe to Next
            };

            if ((endX - startX) > 40 && startX < (bbox.left + 50)) {
                model.set("msg_topy", "PREV"); // Right Swipe to Prev
            };
            model.save_changes();
        }; 
    };
};

const keyMessage = {
    's': 'SCAP', // Screenshot
    'f': 'TFS', // Toggle Fullscreen with F but with click from button
    'z': 'ZOOM', // Enable zooming items
    'g': 'TPAN', // Setting panel
    'k': 'KSC', // keyboard shortcuts
    'l': 'TLSR', // L toggle laser
    'v': 'TVP', // V for toggle viewport, only in voila and LinkedOutputView
    'e': 'EDIT', // Edit source cell
}


function keyboardEvents(box,model) {
    function keyOnSlides(e) {
        e.preventDefault();
        let key = e.key; // True unicode key
        let message = '';
        if ('123456789'.includes(key)) { // send to shift slides by numbers
            message = (e.ctrlKey? "SHIFT:-" + key: "SHIFT:" + key);
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
        } else if (key in keyMessage){
            message = keyMessage[key];
        }
    
        e.stopPropagation(); // stop propagation to jupyterlab events and other views 
        e.preventDefault(); // stop default actions
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
    } else if (msg.includes("SYNC:")) {
        let sync = msg.replace("SYNC:","");
        if (sync.includes("ON:")) {
            clearInterval(model.syncIntervalID); // Remove previous one to avoid multiple calls

            let interval = Number(sync.replace("ON:",""));
            model.syncIntervalID = setInterval(() => {
                model.send({sync:true})
            }, interval)
        } else if (sync === "OFF") {
            clearInterval(model.syncIntervalID);
        }

    } else if (msg === "CloseView") { // deletes node without closing comm to kernl
        if (box) { // may be nothing there left already
            box.remove();
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
        btn.innerHTML = "✕";
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
    box.style.setProperty('--paddingBottom',Number(28/scale) + "px");
}

function handleScale(box) {
    const resizeObs = new ResizeObserver((entry) => {
        setScale(box);
    });

    resizeObs.observe(box);
    setScale(box); // First time set
}

export function render({ model, el }) {
    model.syncIntervalID = null; // Need for Markdown Sync
    let style = document.createElement('style');
    //  Trick to get main slide element is to wait for a loadable element
    style.onload = () => { 
        let box = style.parentNode.parentNode;
        box.tabIndex = -1; // Need for event listeners, should be at top
        box.setAttribute("uid", model.get("_uid"));
        
        // Laser pointer
        let cursor = box.getElementsByClassName('LaserPointer')[0];
        cursor.style = "position:absolute;display:none;"; // initial

        box.onmouseenter = function(){box.focus();};
        box.onmouseleave = function(){box.blur();};
        
        // Keyboard events
        keyboardEvents(box,model);
        
        // Touch Events are experimental
        touchSwiper(box, model);

        // handle scale of slides size
        handleScale(box);

        // Remove other views without closing comm
        keepThisViewOnly(box); 

        // Sends a message if fullscreen is changed by some other mechanism
        box.onfullscreenchange = ()=>{handleChangeFS(box,model)};

        // If voila, turn on full viewport
        let loc = window.location.toString()
        if (loc.includes("voila")) {
            model.set("msg_topy", "TVP");
            model.save_changes();
        } else {
            model.set("msg_topy", "NOVP");
            model.save_changes();
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
        // Remove menu active class for initial user intros, but with python
        setTimeout(() => {
            model.set("msg_topy", "RACTIVE"); 
            model.save_changes();
        }, 10000); // Remove after 10 seconds
    }  
    el.appendChild(style);
    model.set("msg_topy", "LOADED"); // to run onload functionality
    model.save_changes();

    // Clean up old slides if left over from previous session of kernel restart
    let slides = document.getElementsByClassName('SlidesWrapper');
    for (let slide of Array.from(slides)) {
        if (slide.classList.contains('jupyter-widgets-disconnected')) {slide.remove();};
    };
    return () => { // clean up at removal time
		clearInterval(model.syncIntervalID); // remove it to avoid conflict
	};
}