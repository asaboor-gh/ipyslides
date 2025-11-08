// Keep this simple and limited to mouse only
// I TRIED USING NUMPAD EVENTS BUT ADDITIONAL ISSUES
// ARISE LIKE ACTUAL CURSOR ON ANOTHER PLACE CAN DO
// TOTALLY UNINTENTIONAL CLICKS ETC.

function showLaser(box, cursor){
    cursor.style.display = 'block';
    box.style.cursor = 'none';
    
    function onMouseMove(e) {
        let bbox = box.getBoundingClientRect()
        cursor.style.display = "block";
        if (e.pageX > (bbox.right - 16) || e.pageY > (bbox.bottom - 16)) {
            cursor.style.display = "none";
        };
        if (e.pageX < (bbox.left + 16) || e.pageY < (bbox.top + 16)) {
            cursor.style.display = "none";
        };
        cursor.style.left = (e.pageX - bbox.left) + "px"; 
        cursor.style.top = (e.pageY - bbox.top) + "px";
    };

    box.onmousemove = onMouseMove;
    cursor.style.left = "50%"; // show in center even before mouse moves
    cursor.style.top = "50%";
}

function hideLaser(box, cursor) {
    cursor.style.display = 'none';
    box.style.cursor = '';
    box.onmousemove = null;
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