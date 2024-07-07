// This needs more thoughts to send data properly

function setupNotesWindow(notes_win) {
    notes_win.resizeTo(screen.width/3,screen.height/3);
    notes_win.moveTo(0,0); // top left corner
    notes_win.document.title = 'IPySlides Notes';
    notes_win.document.body.style.background = 'var(--primary-bg)';
    notes_win.document.body.style.color = 'var(--primary-fg)';
    window.focus(); // Return focus to main window automatically
};


function setTime(notes_win){
    if (notes_win && !notes_win.closed) { // Close window by user is possible
        function pad(number) {return (number < 10) ? '0' + number : number}
        let date = new Date();
        let timer = notes_win.document.getElementById("timer");
        timer.innerText = "" + pad(date.getHours()) + ":" + pad(date.getMinutes())
    }
}

function setValue(notes_win, value) {
    let out = "<span style='position:fixed;right:4px;bottom:2px;'>🕑<b id='timer'>Time</b></span>" + value;
    notes_win.document.body.innerHTML = out
    setTime(notes_win); // show time immediately
}

var timerId;

function render({model, el}) {
    let notes_win = null; 
    clearInterval(timerId); // remove previous
    model.on("change:popup", () => {
        let popup = model.get("popup");
        if (popup) {
            notes_win = window.open("","__Notes_Window__","popup");
            setupNotesWindow(notes_win)
            setValue(notes_win, model.get("value"));
            timerId = setInterval(setTime, 5000, notes_win); // 5 seconds lag at max
        } else {
            if (notes_win) {
                notes_win.close();
                notes_win = null;
                clearInterval(timerId); // remove it
            };
        }
    })

    model.on("change:value", () => {
        setValue(notes_win, model.get("value")); 
    })
}

export default { render }