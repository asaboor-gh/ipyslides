// This needs more thoughts to send data properly

function setuNotesWindow(notes_win) {
    notes_win.resizeTo(screen.width/2,screen.height/2);
    notes_win.moveTo(0,0); // top left corner
    notes_win.document.title = 'Notes';
    notes_win.document.body.style.background = 'var(--primary-bg)';
    notes_win.document.body.style.color = 'var(--primary-fg)';
    window.focus(); // Return focus to main window automatically
};

function setContent(notes_win, value){
    if (notes_win && !notes_win.closed) { // Close window by user is possible
        function pad(number) {return (number < 10) ? '0' + number : number}
        let date = new Date();
        let out = value + "<hr/><b>⌛ " + pad(date.getHours()) + ":" + pad(date.getMinutes()) + "</b> (at lastest slide switch)";
        notes_win.document.body.innerHTML = out;
    }
}


export function render({model, el}) {
    let notes_win = null; 

    model.on("change:popup", () => {
        let popup = model.get("popup");
        if (popup) {
            notes_win = window.open("","__Notes_Window__","popup");
            setuNotesWindow(notes_win)
            setContent(notes_win, model.get("value"))
        } else {
            if (notes_win) {
                notes_win.close();
                notes_win = null;
            };
        }
    })

    model.on("change:value", () => {
        let value = model.get("value");
        setContent(notes_win, value);
    })
}