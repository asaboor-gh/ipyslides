let timeouts = new Set();

function render({ model, el }) {
    const container = document.createElement("div");
    container.classList.add("animation-slider");
    container.style.display = "flex";
    //container.style.flexWrap = "wrap";  // Allow wrapping for responsiveness
    container.style.alignItems = "flex-start";  // Align items to the top
    container.style.gap = "8px";  // Gap between the two main divs
    container.style.padding = "4px";  // Compact padding
    container.style.maxWidth = "200px";  // Limit container width for a clean layout
    container.style.flexDirection = "row";  // Align divs horizontally

    // Value and Buttons Container
    const valueButtonsContainer = document.createElement("div");
    valueButtonsContainer.style.display = "flex";
    valueButtonsContainer.style.alignItems = "center";
    valueButtonsContainer.style.gap = "4px";  // Small gap between elements

    // Value Element
    const valueLabel = document.createElement("span");
    valueLabel.textContent = model.get("description") + ":";  // Display "Value" label
    valueLabel.style.marginRight = "8px";  // Space between label and buttons

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

    // Go to First Frame Button
    const firstFrameButton = document.createElement("button");
    firstFrameButton.innerHTML = '<i class="fa fa-stop-circle"></i>';  // Icon for first frame
    firstFrameButton.title = "Go to First Frame";
    firstFrameButton.style.padding = "4px";
    firstFrameButton.style.border = "none";

    firstFrameButton.onclick = () => {
        slider.value = slider.min;  // Reset to first frame
        model.set("value", parseInt(slider.value, 10));
        model.save_changes();
    };

    // Loop Button
    const loopButton = document.createElement("button");
    loopButton.innerHTML = model.get("loop")
        ? '<i class="fa fa-toggle-on"></i>'  // Active loop state
        : '<i class="fa fa-toggle-off"></i>';  // Inactive loop state
    loopButton.title = "Toggle Looping";
    loopButton.style.padding = "4px";
    loopButton.style.border = "none";

    loopButton.onclick = () => {
        const currentLoop = model.get("loop");
        model.set("loop", !currentLoop);
        model.save_changes();
        loopButton.innerHTML = model.get("loop")
            ? '<i class="fa fa-toggle-on"></i>'  // Active
            : '<i class="fa fa-toggle-off"></i>';  // Inactive
    };

    valueButtonsContainer.appendChild(valueLabel);
    valueButtonsContainer.appendChild(playPauseButton);
    valueButtonsContainer.appendChild(firstFrameButton);
    valueButtonsContainer.appendChild(loopButton);

    // Slider and Value Container
    const sliderContainer = document.createElement("div");
    sliderContainer.style.display = "flex";
    sliderContainer.style.alignItems = "center";
    sliderContainer.style.gap = "8px";  // Compact spacing
    sliderContainer.style.flexGrow = "1";  // Take up remaining space

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
    const sliderValue = document.createElement("span");
    sliderValue.textContent = slider.value;  // Display slider value inline
    sliderValue.style.marginLeft = "8px";  // Space from slider for readability

    sliderContainer.appendChild(slider);
    sliderContainer.appendChild(sliderValue);

    // Append both containers to the main container
    container.appendChild(valueButtonsContainer);
    container.appendChild(sliderContainer);

    el.appendChild(container);

    // Animation logic
    let animationFrame;

    function animate() {
        if (model.get("playing")) {
            const currentValue = parseInt(slider.value, 10);
            if (currentValue < slider.max) {
                slider.value = currentValue + 1;
            } else if (model.get("loop")) {
                slider.value = slider.min;  // Restart if looping is enabled
            } else {
                model.set("playing", false);  // Stop if not looping
                model.save_changes();
                return;
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
    model.on("change:playing", () => {
        const isPlaying = model.get("playing");
        playPauseButton.innerHTML = isPlaying ? '<i class="fa fa-pause-circle"></i>' : '<i class="fa fa-play-circle"></i>';
        if (isPlaying) {
            animate();
        } else {
            clearTimeout(animationFrame);
        }
    });

    model.on("change:loop", () => {
        loopButton.innerHTML = model.get("loop")
            ? '<i class="fa fa-toggle-on"></i>'  // Active loop
            : '<i class="fa fa-toggle-off"></i>';  // Inactive loop
    });

    model.on("change:value", () => {
        slider.value = model.get("value");
        sliderValue.textContent = slider.value;
    });

    model.on("change:description", () => {
        valueLabel.textContent = model.get("description")+":";
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
    return () => { // clean up at removal time
		clearTimeout(animationFrame); // remove it to avoid multiplied signals
	};
}

export default { render };