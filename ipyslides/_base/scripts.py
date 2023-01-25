
resize_js = "window.dispatchEvent(new Event('resize'));"

clear_disconnected_slides = """
let slides = document.getElementsByClassName('SlidesWrapper');
for (let slide of Array.from(slides)) {
    if (slide.classList.contains('jupyter-widgets-disconnected')) {slide.remove();};
};
"""

navigation_js = '''
function main(box){
    function resizeWindow() {
        window.dispatchEvent(new Event('resize')); // collapse/uncollapse/ and any time, very important, resize itself is not attribute, avoid that
    }; 
    resizeWindow(); // resize on first display
    // Only get buttons of first view, otherwise it will becomes multiclicks
    let arrows   = box.getElementsByClassName('Arrows'); // These are 2*instances
    let mplBtn   = box.getElementsByClassName('Zoom-Btn')[0];
    let winFs    = box.getElementsByClassName('FullWindow-Btn')[0];
    let fullSc   = box.getElementsByClassName('FullScreen-Btn')[0];
    let capSc    = box.getElementsByClassName('Screenshot-Btn')[0];
    let cursor   = box.getElementsByClassName('LaserPointer')[0];
    let panelBtn = box.getElementsByClassName('Settings-Btn')[0];
    let laserBtn = box.getElementsByClassName('Laser-Btn')[0];
    
    // Keyboard events
    function keyOnSlides(e) {
        e.preventDefault();
        resizeWindow(); // Resize before key press
        let key = e.keyCode;
        if (key === 37 || (e.shiftKey && key === 32)) { 
            arrows[0].click(); // Prev or Shift + Spacebar
        } else if (key === 39 || key === 32) { 
            arrows[1].click(); // Next or Spacebar
        } else if (key === 90) { 
            mplBtn.click(); // Z 
        } else if (key === 71) { 
            panelBtn.click(); // G
        } else if (key === 76) {
            laserBtn.click(); // L
        } else if (key === 88 || key === 68) {
            alert("Pressing X or D,D may cut selected cell! Click outside slides to capture these keys!");
            e.stopPropagation(); // stop propagation to jupyterlab events
            return false;
        } else if (key===77){
            alert("Pressing M could change cell to Markdown and vanish away slides!");
            e.stopPropagation();   // M key
        } else if (key === 87) { 
            winFs.click(); // Toggle Window with W 
            resizeWindow(); // Resize event after click
        } else if (key === 70) { 
            // F to enter fullscreen
            fullSc.click(); // Toggle Fullscreen with F
        } else if (key === 27) {  
            // Escape to exit fullscreen
            // document.getElementsByClassName('SlidesWrapper')[0].exitFullscreen();
            box.exitFullscreen();
        } else if (key === 13) {
            return true; // Enter key
        } else if (key === 83) {
            capSc.click();  // S for screenshot
        } else if (key === 80) {
            window.print(); // P for PDF print
        }; 
        resizeWindow(); // Resize after key press, good for F key
        e.stopPropagation(); // stop propagation to jupyterlab events and other views 
        e.preventDefault(); // stop default actions
    };
    
    box.tabIndex = -1; // Need for event listeners, should be at top
    box.onkeydown = keyOnSlides; // This is better than event listners as they register multiple times
    box.onmouseenter = function(){box.focus();};
    box.onmouseleave = function(){box.blur();};
    // Cursor pointer functions
    
    function onMouseMove(e) {
        let bbox = box.getBoundingClientRect()
        let _display = "display:block;"
        if (e.pageX > (bbox.right - 30) || e.pageY > (bbox.bottom - 30)) {
            _display = "display:none;"
        };
        cursor.setAttribute("style",_display + "left:"+ (e.pageX - bbox.left + 10) + "px; top: " + (e.pageY - bbox.top + 10) + "px;")
    };
    
    box.onmousemove = onMouseMove;
    box.onmouseleave = function (){cursor.setAttribute("style","display:none;");}
    box.onmouseenter = function (){cursor.setAttribute("style","display:block;");}
    
    let loc = window.location.toString()
    if (loc.includes("voila")) {
        winFs.click(); // Turn ON fullscreen for voila anywhare.
    };
    
};

// Touch Events are experimental
function touchSwiper(box){
    box.tabIndex = -1;
    let arrows = box.getElementsByClassName('Arrows');
    
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
                arrows[1].click(); // align-left Swipe to Next
            };

            if ((endX - startX) > 40 && startX < (bbox.left + 50)) {
                arrows[0].click(); // Right Swipe to Prev
            };
        }; 
    };
};
// Now execute function to work, handle browser refresh too
try {
    var waitLoading = setInterval(function() {
        let boxes = document.getElementsByClassName('SlidesWrapper');
        for (let box of Array.from(boxes)) {
            if (!box.classList.contains('EventsAdded')) { // Check if events are added or not
                main(box); // Refresh does not work in this case
                touchSwiper(box); // Touch events
                box.classList.add('EventsAdded');
            }
        }
        if (boxes.length >= 1) {
            clearInterval(waitLoading); // Stop checking after adding to all
        }
    }, 500); // check every 500ms, I do not need be hurry
    
} catch (error) {
   alert("Restart Kernel and run again for Keyboard Navigation to work. Avoid refreshing browser!") 
};
'''
