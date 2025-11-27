// Keep this simple and limited to mouse only
// I TRIED USING NUMPAD EVENTS BUT ADDITIONAL ISSUES
// ARISE LIKE ACTUAL CURSOR ON ANOTHER PLACE CAN DO
// TOTALLY UNINTENTIONAL CLICKS ETC.

function setPointLoc(e, cursor, rect) {
    cursor.style.display = "block";
    cursor.style.opacity = "1.0";
    cursor.style.scale = "1.0";

    const edgeThreshold = 8; // pixels from edge to start hiding
    const fadeThreshold = 16; // pixels from edge to start fading

    if (e.pageX > (rect.right - edgeThreshold)  || // right edge
        e.pageY > (rect.bottom - edgeThreshold) || // bottom edge
        e.pageX < (rect.left + edgeThreshold)   || // left edge
        e.pageY < (rect.top + edgeThreshold)       // top edge
    ) { cursor.style.display = "none"; };
    
    if (e.pageX > (rect.right - fadeThreshold)  || // right edge
        e.pageY > (rect.bottom - fadeThreshold) || // bottom edge
        e.pageX < (rect.left + fadeThreshold)   || // left edge
        e.pageY < (rect.top + fadeThreshold)       // top edge
    ) { 
        cursor.style.opacity = "0.5"; 
        cursor.style.scale = "0.5";
    };
    
    cursor.style.left = (e.pageX - rect.left) + "px"; 
    cursor.style.top = (e.pageY - rect.top) + "px";
}

function showLaser(box, cursor){
    cursor.style.display = 'block';
    box.style.cursor = 'none';

    let bbox = null; // we need to cache this for performance
    box._resetBBox = () => {bbox = null;} // in case of resize etc, null is faster than recomputing here
    
    box._mouseMove = function onMouseMove(e) {
        if (!bbox) {
            bbox = box.getBoundingClientRect()
        }; // get bounding box if not available
        setPointLoc(e, cursor, bbox);
    };

    box._pointerDown = function onPointerDown(e) {
        if (e.pointerType && e.pointerType !== 'mouse') {
            cursor.classList.add('Animated');
        } // set animation only for non-mouse pointers before setting location
        setPointLoc(e, cursor, box.getBoundingClientRect());
    };
    box._pointerUp = function onPointerUp(e) {
        setTimeout(() => {
            cursor.classList.remove('Animated'); // remove anyhow
        }, 800); // delay to allow for any last animation to finish
    };

    box.addEventListener('pointerdown', box._pointerDown);
    box.addEventListener('pointerup', box._pointerUp);
    box.addEventListener('pointermove', box._mouseMove);
    cursor.style.left = "50%"; // show in center even before mouse moves
    cursor.style.top = "50%";

    // Rest on resize etc
    window.addEventListener('resize', box._resetBBox);
    window.addEventListener('scroll', box._resetBBox);
    document.addEventListener('fullscreenchange', box._resetBBox);
}

function hideLaser(box, cursor) {
    cursor.style.display = 'none';
    box.style.cursor = '';
    box.removeEventListener('pointerdown', box._pointerDown);
    box.removeEventListener('pointerup', box._pointerUp);
    box.removeEventListener('pointermove', box._mouseMove);
    window.removeEventListener('resize', box._resetBBox);
    window.removeEventListener('scroll', box._resetBBox);
    document.removeEventListener('fullscreenchange', box._resetBBox);
}

function render({ model, el }) {
    let style = document.createElement('style');
    style.onload = () => {
        el.classList.add('LaserPointer');
        let box = style.parentNode.parentNode;
        hideLaser(box, el);

        model.on('change:active', () => {
            if (model.get('active')) {
                showLaser(box, el);
            } else {
                hideLaser(box, el);
            }
        });
    };
    el.appendChild(style);
}

export default { render };