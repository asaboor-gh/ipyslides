function setLabel(model, el) {
    let lab = model.get("description");
    el.textContent = lab;  // Display "Value" label
    el.style.display = lab ? "" : "none";  // Hide label if no description is provided
}

let timeouts = new Set();

function render({ model, el }) {
    const container = document.createElement("div");
    container.classList.add("animation-slider", "jupyter-widgets", "widget-inline-hbox", "widget-slider","widget-hslider");  // Use the same style as other widgets
    container.style.alignItems = "center";  // Center elements vertically
    container.style.gap = "4px";  // Small gap between elements
    container.style.width = "auto";  // Allow container to grow dynamically
    container.style.maxWidth = "var(--jp-widgets-inline-width)";
    container.style.overflowX = "auto";  // Allow horizontal scrolling if needed
    container.style.overflowY = "hidden";  // Hide vertical scrolling when scaling buttons

    // Value Element
    const valueLabel = document.createElement("label");
    valueLabel.textContent = '';
    valueLabel.classList.add("widget-label");  // Use the same style as other labels
    valueLabel.title = null;  // Remove tooltip
    setLabel(model, valueLabel);  // Display "Value" label first time

    // Play/Pause Button
    const playPauseButton = document.createElement("button");
    playPauseButton.innerHTML = '<i class="fa fa-play-circle"></i>';  // Initial Play icon
    playPauseButton.title = "Play/Pause Animation";  // Tooltip
    playPauseButton.style.padding = "4px";  // Compact button size
    playPauseButton.style.border = "none";  // Sleek button design

    playPauseButton.onclick = () => {
        const isPlaying = model.get("playing");
        model.set("playing", !isPlaying);
        model.save_changes();
    };

    // Loop Button
    const loopButton = document.createElement("button");
    loopButton.innerHTML = model.get("loop")
        ? '<i class="fa fa-rotate-left"></i>'  // Active loop state
        : '<i class="fa fa-rotate-left inactive"></i>';  // Inactive loop state
    loopButton.title = "Toggle Looping";
    loopButton.style.padding = "4px";
    loopButton.style.border = "none";

    loopButton.onclick = () => {
        const currentLoop = model.get("loop");
        model.set("loop", !currentLoop);
        model.save_changes();
        loopButton.innerHTML = model.get("loop")
            ? '<i class="fa fa-rotate-left"></i>'  // Active
            : '<i class="fa fa-rotate-left inactive"></i>';  // Inactive
    };

    container.appendChild(valueLabel);
    container.appendChild(playPauseButton);
    container.appendChild(loopButton);

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = 0;
    slider.max = model.get("nframes") - 1;
    slider.value = model.get("value");
    slider.style.flexGrow = "1";  // Allow slider to grow dynamically
    slider.style.minWidth = "50px";  // Minimum slider width

    slider.oninput = () => {
        sliderValue.textContent = slider.value;  // Update displayed value 
        if (model.get("continuous_update")) {
            model.set("value", parseInt(slider.value, 10));
            model.save_changes();
        };
    };

    slider.onchange = () => {
        if (!model.get("continuous_update")) {
            model.set("value", parseInt(slider.value, 10));
            model.save_changes();
        }
    };

    // Attach keydown listener directly to the slider
    slider.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") {
            // Move slider left
            slider.value = Math.max(slider.min, parseInt(slider.value, 10) - 1);
            model.set("value", parseInt(slider.value, 10));
            model.save_changes();
        } else if (event.key === "ArrowRight") {
            // Move slider right
            slider.value = Math.min(slider.max, parseInt(slider.value, 10) + 1);
            model.set("value", parseInt(slider.value, 10));
            model.save_changes();
        }
    });

    // Slider Value
    const sliderValue = document.createElement("div");
    sliderValue.classList.add("widget-readout");  // Use the same style as other readouts
    sliderValue.textContent = slider.value;  // Display slider value inline
    sliderValue.style.width = `${model.get("nframes").toString().length + 1}ch`;  // Adjust width based on number of frames
    sliderValue.style.minWidth = `${model.get("nframes").toString().length}ch`;  // Minimum width based on number of frames
    sliderValue.style.maxWidth = "unset";  // ovveride large space in jupyter

    container.appendChild(slider);
    container.appendChild(sliderValue);
    el.appendChild(container);

    // Animation logic
    let animationFrame;
    let direction = 1; // 1 for forward, -1 for backward

    function animate() {
        if (model.get("playing")) {
            const currentValue = parseInt(slider.value, 10);
            
            if (model.get("cyclic") && model.get("loop")) { // Cyclic mode only with loop
                // Reverse direction at endpoints
                if (currentValue >= slider.max) {
                    direction = -1;
                } else if (currentValue <= slider.min) {
                    direction = 1;
                }
                slider.value = currentValue + direction;
            } else {
                // Original behavior
                if (currentValue < slider.max) {
                    slider.value = currentValue + 1;
                } else if (model.get("loop")) {
                    slider.value = slider.min;  // Restart if looping is enabled
                } else {
                    model.set("playing", false);  // Stop if not looping
                    model.save_changes();
                    return;
                }
            }

            for (let timeout of timeouts) {
                clearTimeout(timeout); // remove all prevous to avoid multiplied signals
                timeouts.delete(timeout);
            };

            model.set("value", parseInt(slider.value, 10));
            sliderValue.textContent = slider.value;
            model.save_changes();

            animationFrame = setTimeout(animate, model.get("interval"));
            timeouts.add(animationFrame); // add new timeout to the set
        }
    }

    // Listeners for model changes

    model.on("change:cyclic", () => {
        direction = 1; // Reset direction when cyclic mode changes, will fix in animate itself
    });

    model.on("change:playing", () => {
        const isPlaying = model.get("playing");
        playPauseButton.innerHTML = isPlaying ? '<i class="fa fa-pause-circle"></i>' : '<i class="fa fa-play-circle"></i>';
        if (isPlaying) {
            if (slider.value === slider.max) { // Restart if at the end, without need of extra button
                slider.value = slider.min;
                model.set("value", parseInt(slider.value, 10));
                model.save_changes();
            }
            animationFrame = setTimeout(animate, model.get("interval"));
            timeouts.add(animationFrame); // add new timeout to the set
        } else {
            clearTimeout(animationFrame);
        }
    });

    model.on("change:loop", () => {
        loopButton.innerHTML = model.get("loop")
            ? '<i class="fa fa-rotate-left"></i>'  // Active loop
            : '<i class="fa fa-rotate-left inactive"></i>';  // Inactive loop
    });

    model.on("change:value", () => {
        slider.value = model.get("value");
        sliderValue.textContent = slider.value;
    });

    model.on("change:description", () => {
        setLabel(model, valueLabel);  // Display "Value" label
    });

    model.on("change:nframes", () => {
        slider.max = model.get("nframes") - 1;
        sliderValue.style.width = `${model.get("nframes").toString().length * 1.2}em`;
    });

    model.on("change:interval", () => {
        clearTimeout(animationFrame);
        if (model.get("playing")) {
            animate();
        }
    });

    model.on("msg:custom", (msg) => {
        if (msg && 'do' in msg) {
            if (msg.do === 'focus') { // focus slider to be controlled by keyboard
                slider.focus();
            } else if (msg.do === 'blur') {
                slider.blur();
            }
        }
    });
    return () => { // clean up at removal time
		clearTimeout(animationFrame); // remove it to avoid multiplied signals
	};
}

export default { render };