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
// I don't know why it does not work, specially in case of left, right
// function getBboxScreenPixels(box) {
//     let bbox = box.getBoundingClientRect();
//     let dpr = window.devicePixelRatio
//     let left = (window.screenX + bbox.left + window.outerWidth - window.innerWidth)*dpr
//     let top = (window.screenY + bbox.top + window.outerHeight - window.innerHeight)*dpr
//     let right = left + bbox.width*dpr 
//     let bottom = top + bbox.height*dpr
//     let out_str = "L:" + left + ",T:" + top + ",R:" + right + ",B:" + bottom
//     console.log(out_str) // Not giving correct values, take screenshot in javascript and send data to python I think, to work everywhere
// }

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
                console.log(bbox)
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


function keyboardEvents(box,model) {
        function keyOnSlides(e) {
            e.preventDefault();
            let key = e.keyCode;
            let message = '';
            if (key === 88 || key === 68) {
                alert("Pressing X or D,D may cut selected cell! Click outside slides to capture these keys!");
                e.stopPropagation(); // stop propagation to jupyterlab events
                return false;
            } else if (key===77){
                alert("Pressing M could change cell to Markdown and vanish away slides!");
                e.stopPropagation();   // M key
                return false;
            }  else if (key === 13 || key === 27) {
                e.stopPropagation();   // Don't let it pass over slides though, still can't hold Shift + Enter
                return true; // Enter key or Escape key should act properly
            } else if (key === 37 || (e.shiftKey && key === 32)) {
                message = 'PREV';
            } else if (key === 39 || key === 32) {
                message = 'NEXT';
            } else if (key === 83) {
                message = 'SCAP'; // S for screenshot
            } else if (key === 70) { 
                // Toggle Fullscreen with F but with click from button
                message = 'TFS'; 
            }  else if (key === 90) { 
                message = 'ZOOM'; // Z 
            } else if (key === 71) { 
                message = 'TPAN'; // G toggle panel
            } else if (key === 75) {
                message = 'KSC'; // K for keyboard shortcuts
            } else if (key === 76) {
                message = 'TLSR'; // L toggle laser
            } else if (key === 86) {
                message = 'TVP'; // V for toggle viewport, only in voila and LinkedOutputView
            }
        
            e.stopPropagation(); // stop propagation to jupyterlab events and other views 
            e.preventDefault(); // stop default actions
            model.set("msg_topy", message);
            model.save_changes();
        }
        
        box.onkeydown = keyOnSlides;
};

function handleMessage(msg, box, cursor) {
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
    } else if (msg.includes("PBW:")) {
        let w = msg.replace("PBW:","");
        let color = "var(--accent-color) 0%,  var(--accent-color) " + w + "%, var(--secondary-bg) " + w + "%, var(--secondary-bg) 100%";
        box.style.borderImage = "linear-gradient(to right," + color + ") 1 / 0  0 3px 0";
    } else if (msg.includes("THEME:")) {
        let theme = msg.replace("THEME:","");
        let container = box.getElementsByClassName("Draw-Widget")[0].getElementsByClassName("tl-container")[0];
        container.classList.remove((theme === "light") ? "tl-theme__dark" : "tl-theme__light")
        container.classList.add("tl-theme__" + theme) // worst way to do it, internal frames are changed with CSS
    }
};

function handleChangeFS(box,model){
    if (box === document.fullscreenElement) {
        console.log(box);
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


export function render({ model, el }) {
    let style = document.createElement('style');
    //  Trick to get main slide element is to wait for a loadable element
    style.onload = () => { 
        let box = style.parentNode.parentNode;
        box.tabIndex = -1; // Need for event listeners, should be at top
        // Laser pointer
        let cursor = box.getElementsByClassName('LaserPointer')[0];
        cursor.style = "position:absolute;display:none;"; // initial

        box.onmouseenter = function(){box.focus();};
        box.onmouseleave = function(){box.blur();};
        
        // Keyboard events
        keyboardEvents(box,model);
        
        // Touch Events are experimental
        touchSwiper(box, model);

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
            handleMessage(msg, box, cursor);
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
    }  
    el.appendChild(style);
    model.set("msg_topy", "LOADED"); // to run onload functionality
    model.save_changes();

    // Clean up old slides if left over from previous session of kernel restart
    let slides = document.getElementsByClassName('SlidesWrapper');
    for (let slide of Array.from(slides)) {
        if (slide.classList.contains('jupyter-widgets-disconnected')) {slide.remove();};
    };
}