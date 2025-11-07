function showLaser(box, cursor, model){
    cursor.style.display = 'block'; // show in place
    box.style.cursor = 'none'; // Hide default cursor on slide box
    function onMouseMove(e) {
        let bbox = box.getBoundingClientRect()
        cursor.style.display = "block"; // show everywhere by default
        if (e.pageX > (bbox.right - 16) || e.pageY > (bbox.bottom - 16)) {
            cursor.style.display = "none";
        };
        if (e.pageX < (bbox.left + 16) || e.pageY < (bbox.top + 16)) {
            cursor.style.display = "none"; // simulate exit near edges over padding
        };
        cursor.style.left = (e.pageX - bbox.left) + "px"; 
        cursor.style.top = (e.pageY - bbox.top) + "px";
        cursor.loc = {x: (e.pageX - bbox.left) / bbox.width, y: (e.pageY - bbox.top) / bbox.height };
    };

    box.onmousemove = onMouseMove;
    setXY(box, model, cursor, cursor.loc.x, cursor.loc.y); // make visible at current position before moving
}

function hideLaser(box, cursor) {
    cursor.style.display = 'none'; // hide in place
    box.style.cursor = ''; // Restore default cursor
    box.onmousemove = null;
}

function setXY(box, model, cursor, x, y) {
    if (!model.get('active')) {
        return; // avoid unseen moves if not active
    }
    // Clamp to 0-1 range
    if (x < 0) { x = 0; }
    if (x > 1) { x = 1; }
    if (y < 0) { y = 0; }
    if (y > 1) { y = 1; }   

    let bbox = box.getBoundingClientRect();
    let rx = bbox.width * x; // relative to box left
    let ry = bbox.height * y; // relative to box top

    // Hide if near edges in 16 px range
    if (rx < 16 || rx > (bbox.width - 16) || ry < 16 || ry > (bbox.height - 16)) {
        cursor.style.display = "none";
        box.style.cursor = ''; // show default cursor
    } else if (model.get('active')) { // only show if active
        cursor.style.display = "block";
        box.style.cursor = 'none'; // Hide default cursor
    }
    cursor.style.left = rx + "px"; // relative to box
    cursor.style.top  = ry + "px"; // relative to box
    // set model xy in 0-1 range
    cursor.loc = {x: rx/bbox.width, y: ry/bbox.height};
}

// dx, dy on buttons 1-9, 5 is center
const step = 0.025; // percent step to move
const dxy = {
    '1': [-step,  step], // ↙
    '2': [ 0,     step], // ↓
    '3': [ step,  step], // ↘
    '4': [-step,     0], // ←
    '6': [ step,     0], // →
    '7': [-step, -step], // ↖
    '8': [ 0,    -step], // ↑
    '9': [ step, -step], // ↗
}

function render({ model, el }) {
    el.loc = { x: 0.5, y: 0.5 }; // center by default
    let style = document.createElement('style');
    //  Trick to get main slide element is to wait for a loadable element
    style.onload = () => {
        el.classList.add('LaserPointer');
        el.style.cssText = `
            display: none;
            width: ${model.get('size')}px;
            height: ${model.get('size')}px;
        `; // Other styles are set in CSS
        let box = style.parentNode.parentNode; // slides

        model.on('change:active', () => {
            if (model.get('active')) {
                showLaser(box, el, model); // Activate laser pointer
            } else {
                hideLaser(box, el); // Deactivate laser pointer
            }
        });

        model.on('change:size', () => {
            el.style.width = `${model.get('size')}px`;
            el.style.height = `${model.get('size')}px`;
        });

        box.addEventListener('keydown', (e) => {
            e.preventDefault(); // stop default actions
            e.stopPropagation(); // stop propagation to jupyterlab events and other views 
            if (e.target !== box){
                return true; // inside componets should work properly, avoid going outside
            }; 
            let key = e.key; // True unicode key
            if (key === '5') {
                // center pointer
                setXY(box, model, el, 0.5, 0.5);
            } else if ('12346789'.includes(key)) {
                // move pointer in direction
                let [dx, dy] = dxy[key];
                setXY(box, model, el, el.loc.x + dx, el.loc.y + dy);
            } else {
                return true; // not handled
            }
        }); 
    };
    el.appendChild(style);
}

export default { render };