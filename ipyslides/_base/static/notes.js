// This needs more thoughts to send data properly

function setupNotesWindow(notes_win) {
    notes_win.resizeTo(screen.width/3,screen.height/3);
    notes_win.moveTo(0,0); // top left corner
    notes_win.document.title = 'IPySlides Notes';
    notes_win.document.body.style.background = 'var(--bg1-color)';
    notes_win.document.body.style.color = 'var(--fg1-color)';
    
    window.focus(); // Return focus to main window automatically
};


function setTime(notes_win){
    if (notes_win && !notes_win.closed) { // Close window by user is possible
        function pad(number) {return (number < 10) ? '0' + number : number}
        let date = new Date();
        let timer = notes_win.document.getElementById("timer");
        if (timer) {
            timer.innerText = "" + pad(date.getHours()) + ":" + pad(date.getMinutes());
        }
    }
}

function startCountUp(notes_win) {
    if (!notes_win || notes_win.closed) return;
    
    // Clear previous interval if exists
    if (notes_win.__countUpIntervalId) {
        clearInterval(notes_win.__countUpIntervalId);
    }
    
    const countUp = notes_win.document.getElementById('countup');
    if (!countUp) return;
    
    const startTime = Date.now();
    
    const intervalId = setInterval(() => {
        if (!notes_win || notes_win.closed) {
            clearInterval(intervalId);
            return;
        }
        
        const elapsed = Date.now() - startTime;
        const totalSeconds = Math.floor(elapsed / 1000);
        
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const timeStr = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        // Change color and emoji based on elapsed time
        let timeColor, emoji;
        
        if (totalSeconds < 30) { // 0-30 seconds - green
            timeColor = '#44ff44';
            emoji = '⏱️';
        } else if (totalSeconds < 45) { // 30-45 seconds - light green
            timeColor = '#88ff88';
            emoji = '⏱️';
        } else if (totalSeconds < 60) { // 45-60 seconds - brown/orange
            timeColor = '#cc8800';
            emoji = '⏳';
        } else if (totalSeconds < 80) { // 60-80 seconds - yellow
            timeColor = '#ffcc00';
            emoji = '⏳';
        } else if (totalSeconds < 100) { // 80-100 seconds - orange
            timeColor = '#ff8800';
            emoji = '⌛';
        } else { // 100+ seconds - red
            timeColor = '#ff4444';
            emoji = '⌛';
        }
        
        countUp.innerHTML = `${emoji} <span style="color:${timeColor}">${timeStr}</span>`;
        
    }, 100); // Update every 100ms for smooth display
    
    notes_win.__countUpIntervalId = intervalId;
}


function setValue(notes_win, value) {
    let countUp = '<span id="countup" style="position:fixed;left:4px;bottom:2px;font-size:1.5em;font-weight:bold;">⏱️ 00:00</span>';
    let out = "<span style='position:fixed;right:4px;bottom:2px;'>🕑<b id='timer'>Time</b></span>" + countUp + value;
    notes_win.document.body.innerHTML = out;
    setTime(notes_win); // show time immediately
    
    // Start count-up timer
    startCountUp(notes_win);
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
            if (notes_win && !notes_win.closed) {
                setValue(notes_win, model.get("value"));
                timerId = setInterval(setTime, 5000, notes_win);
            }
        } else {
            if (notes_win) {
                notes_win.close();
                notes_win = null;
                clearInterval(timerId); // remove it
            };
        }
    })
    
    model.on("change:value", () => {
        if (notes_win && !notes_win.closed) { 
            setValue(notes_win, model.get("value"));
        }
    })
}

export default { render }