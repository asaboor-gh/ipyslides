
function toIntOrNull(value) {
    const num = Number(value);
    return Number.isFinite(num) ? Math.trunc(num) : null;
}

function formatMainSlideNumber(index, page = undefined) {
    const base = index === 0 ? '' : `${index}`;
    return page !== undefined ? `${base}.${page}` : base;
}

function updateProgress(show, mainEnd, index, numFrames, fidx, isSupplemental) {
    if (!show) {
        return 'transparent';
    }
    if (isSupplemental) {
        return 'none';
    }
    let unit = 100/(mainEnd || 1); // avoid zero division when main end is title (0)
    let pv = Math.round(unit * (index - (numFrames - fidx - 1)/numFrames) * 10000)/10000;
    pv = Math.max(0, Math.min(100, pv));
    let gradient = `linear-gradient(to right, var(--accent-color) 0%,  var(--accent-color) ${pv}%, var(--bg2-color) ${pv}%, var(--bg2-color) 100%)`;
    return gradient;
}

// Function to fix IDs and references in cloned elements, especially for matplotlib SVGs
function fixIDsAndRefs(clone, cloneIndex = 0) {
  // Step 1: Collect all IDs in the clone
  const idElements = new Map();
  clone.querySelectorAll(':scope [id]').forEach(el => {
    idElements.set(el.id, el);
  });

  if (idElements.size === 0) return clone;

  // Step 2: Find which IDs are actually referenced within this clone
  const referencedIds = new Set();
  clone.querySelectorAll(':scope *').forEach(el => {
    for (const attr of el.getAttributeNames()) {
      if (attr === 'id') continue; // skip id attribute itself
      const val = el.getAttribute(attr);
      if (!val || !val.includes('#')) continue;

      // Check each known ID for a reference
      for (const id of idElements.keys()) {
        if (val.includes(`#${id}`)) {
          referencedIds.add(id);
        }
      }
    }
  });

  if (referencedIds.size === 0) return clone;

  // Step 3: Build ID map only for referenced IDs and rename them
  const idMap = {};
  referencedIds.forEach(oldId => {
    const newId = `${oldId}__${cloneIndex}`;
    idMap[oldId] = newId;
    idElements.get(oldId).id = newId;
  });

  // Step 4: Update references in attributes
  clone.querySelectorAll(':scope *').forEach(el => {
    for (const attr of el.getAttributeNames()) {
      if (attr === 'id') continue;
      const val = el.getAttribute(attr);
      if (!val || !val.includes('#')) continue;

      let newVal = val;
      for (const [oldId, newId] of Object.entries(idMap)) {
        newVal = newVal.replace(new RegExp(`#${oldId}(?![\\w-])`, 'g'), `#${newId}`);
      }
      if (newVal !== val) el.setAttribute(attr, newVal);
    }
  });

  return clone;
}

function tldrawLinks(node, model) { 
    node.querySelectorAll(':scope .link-button > .req-click').forEach(btn => {
        btn.classList.remove('req-click'); // remove class to avoid next time
        btn.onclick = () => { // set proper onclick
            model.set("msg_topy", "Draw:ON");
            model.save_changes();
        }
    })
}

function isGroupHeaderRow(rowEl) {
    return !!(rowEl && rowEl.querySelector('.group-header-content'));
}

function handleColsRows(outputs, frame) {
    // Fallback persistence: completed snapshots columns before current part keep only last row.
    if (frame.part !== undefined) {
        for (let j = 0; j < frame.part; j++) {
            if (!outputs[j]) continue;
            const writer = outputs[j].querySelector(':scope .columns.writer:first-of-type');
            if (!writer) continue;
            const cols = writer.querySelectorAll(':scope > div');
            for (const colDiv of cols) {
                if (!colDiv.classList.contains('snapshots-rows')) continue;
                const rowsRoot = colDiv.querySelector(':scope .jp-OutputArea');
                if (!rowsRoot) continue;
                const rows = rowsRoot.children;

                let lastVisible = -1;
                for (let r = rows.length - 1; r >= 0; r--) {
                    if (!isGroupHeaderRow(rows[r])) {
                        lastVisible = r;
                        break;
                    }
                }

                for (let r = 0; r < rows.length; r++) {
                    rows[r].classList.remove('print-collapsed');
                    if (isGroupHeaderRow(rows[r])) continue;
                    if (lastVisible >= 0 && r < lastVisible) {
                        rows[r].classList.add('print-collapsed');
                    }
                }
            }
        }
    }

    // Persistent snapshots: collapse non-last rows in columns we already exited.
    if (frame._snapshots_persist) {
        const persist = frame._snapshots_persist;
        const colsOutput = outputs[persist.idx];
        if (colsOutput) {
            const writer = colsOutput.querySelector(':scope .columns.writer:first-of-type');
            if (writer) {
                const cols = writer.querySelectorAll(':scope > div');
                for (const [c, lastRow] of Object.entries(persist._snapshots_last_rows)) {
                    const colDiv = cols[Number(c)];
                    if (!colDiv) continue;
                    if (!colDiv.classList.contains('snapshots-rows')) continue;
                    const rowsRoot = colDiv.querySelector(':scope .jp-OutputArea');
                    if (!rowsRoot) continue;
                    const rows = rowsRoot.children;
                    for (let r = 0; r < rows.length; r++) {
                        rows[r].classList.remove('print-collapsed');
                        if (isGroupHeaderRow(rows[r])) continue;
                        if (r <= lastRow) {
                            rows[r].classList.add('print-collapsed');
                        }
                    }
                }
            }
        }
    }
    if (frame.col !== undefined && outputs[frame.part]) {
        const writer = outputs[frame.part].querySelector(':scope .columns.writer:first-of-type');
        if (!writer) return;
        const snapshotsLastRows = frame._snapshots_last_rows || {};
        let cols = writer.querySelectorAll(':scope > div');
        for (let k = 0; k < cols.length; k++) {
            const isSnapshotsRows = cols[k].classList.contains('snapshots-rows');
            cols[k].classList.remove('print-invisible'); // reset first
            if (k > frame.col) {
                cols[k].classList.add('print-invisible');
            } else if (k < frame.col && isSnapshotsRows && snapshotsLastRows[k] !== undefined) {
                // snapshots: previous columns show only last row
                const rowsRoot = cols[k].querySelector(':scope .jp-OutputArea');
                if (!rowsRoot) { continue; }
                let rows = rowsRoot.children;
                for (let r = 0; r < rows.length; r++) {
                    rows[r].classList.remove('print-collapsed');
                    if (isGroupHeaderRow(rows[r])) continue;
                    if (r <= snapshotsLastRows[k]) {
                        rows[r].classList.add('print-collapsed');
                    }
                }
            } else if (k === frame.col) {
                if (frame.row !== undefined) {
                    // Handle incremental rows
                    const rowsRoot = cols[k].querySelector(':scope .jp-OutputArea');
                    if (!rowsRoot) { continue; }
                    let rows = rowsRoot.children;
                    for (let r = 0; r < rows.length; r++) {
                        rows[r].classList.remove('print-invisible');
                        rows[r].classList.remove('print-collapsed');
                        if (isGroupHeaderRow(rows[r])) continue;
                        if (r > frame.row) {
                            rows[r].classList.add('print-invisible');
                        } else if (isSnapshotsRows && snapshotsLastRows[k] !== undefined) {
                            // snapshots: collapse rows before current
                            const prevRow = frame.prev_row;
                            if (prevRow !== undefined && r <= prevRow) {
                                rows[r].classList.add('print-collapsed');
                            }
                        }
                    }
                } else if (isSnapshotsRows && snapshotsLastRows[k] !== undefined) {
                    // snapshots: current column fully visible, show only last row
                    const rowsRoot = cols[k].querySelector(':scope .jp-OutputArea');
                    if (!rowsRoot) { continue; }
                    let rows = rowsRoot.children;
                    for (let r = 0; r < rows.length; r++) {
                        rows[r].classList.remove('print-collapsed');
                        if (isGroupHeaderRow(rows[r])) continue;
                        if (r <= snapshotsLastRows[k]) {
                            rows[r].classList.add('print-collapsed');
                        }
                    }
                }
            }
        }
    }
}

function printSlides(box, model) {
    let slides = Array.from(box.querySelectorAll(':scope .SlideBox >.SlideArea')); 

    // Defensive cleanup: VSCode/IDE print flows may skip afterprint and leave stale clones/classes.
    box.querySelectorAll(':scope .print-invisible').forEach(el => el.classList.remove('print-invisible'));
    box.querySelectorAll(':scope .print-collapsed').forEach(el => el.classList.remove('print-collapsed'));
    box.querySelectorAll(':scope .SlideArea.print-clone').forEach(el => el.remove());
    box.querySelectorAll(':scope > .print-cleanup-btn').forEach(btn => btn.remove());

    window._printOnlyObjs = [];
    const parts = model.get('_parts') || {}; // get part info for all slides
    const fkws = model.get('_fkws') || {}; // get footer kws
    const frameCounts = slides.map((slide) => {
        const slideNum = parseInt([...slide.classList].find(cls => /^n\d+$/.test(cls))?.slice(1)) || null;
        if (slideNum === null || !Array.isArray(parts[slideNum])) {
            return 1;
        }
        return parts[slideNum].length || 1;
    });
    const modelExtraStart = toIntOrNull(model.get('_extra_start'));
    const modelMainEnd = toIntOrNull(model.get('_main_end'));
    const classExtraStart = slides.findIndex(slide => slide.classList.contains('ExtraSlide'));
    const supplementalStart = modelExtraStart !== null
        ? modelExtraStart
        : (classExtraStart >= 0 ? classExtraStart : null);
    const mainEnd = modelMainEnd !== null
        ? modelMainEnd
        : (supplementalStart === null ? Math.max(slides.length - 1, 0) : Math.max(supplementalStart - 1, 0));

    function supplementalFrameIndex(slideIndex, fidx = 0) {
        if (supplementalStart === null || slideIndex < supplementalStart) {
            return null;
        }
        let count = 0;
        for (let i = supplementalStart; i < slideIndex; i++) {
            count += frameCounts[i] || 1;
        }
        return count + fidx + 1;
    }

    box.style.setProperty('--show-snumber', fkws.snum ? 'block' : 'none'); // show only if numbered
    box.style.setProperty('--printPadding', fkws.pad + 'px'); // set padding for print mode
    
    for (let n = 0; n < slides.length; n++) {
        let slide = slides[n];
        let outArea = slide.querySelector(':scope .jp-OutputArea');
        if (outArea) { outArea.scrollTop = 0; }

        // Extract slide number from class (e.g., 'n25' -> 25)
        const slideNum = parseInt([...slide.classList].find(cls => /^n\d+$/.test(cls))?.slice(1)) || null;
        const numFrames = frameCounts[n] || 1;
        const isSupplemental = supplementalStart !== null && n >= supplementalStart;

        slide.style.setProperty('--bar-bg-color', updateProgress(fkws.bar, mainEnd, n, numFrames, 0, isSupplemental));

        if (isSupplemental) {
            const sidx = supplementalFrameIndex(n, 0);
            slide.dataset.snum = sidx !== null ? `S.${sidx}` : '';
        } else {
            slide.dataset.snum = formatMainSlideNumber(n);
        }
        setBgImage(slide);

        if (slide.classList.contains('HasFrames') && numFrames > 1) {
            let lastInserted = slide;
            let clone = slide;
            const slideTemplate = slide.cloneNode(true); // immutable source for all cloned frames
            for (let i = 0; i < numFrames; i++) {
                if (i > 0) {
                    clone = slideTemplate.cloneNode(true);
                    clone.classList.remove('HasFrames');
                    clone.classList.add('HideSlide');
                    clone.classList.add('print-clone');
                    clone.querySelector(':scope .Slide-UID')?.remove();
                }

                const frame = (parts[slideNum] && parts[slideNum][i] !== undefined) ? parts[slideNum][i] : null;
                setBgImage(clone);

                // Ensure each frame starts from a clean print state.
                clone.querySelectorAll(':scope .print-invisible').forEach(el => el.classList.remove('print-invisible'));
                clone.querySelectorAll(':scope .print-collapsed').forEach(el => el.classList.remove('print-collapsed'));

                clone.style.setProperty('--bar-bg-color', updateProgress(fkws.bar, mainEnd, n, numFrames, i, isSupplemental));
                clone.style.transform = 'translateZ(0) scale(1)';

                if (frame) {
                    const outRoot = clone.querySelector(':scope .jp-OutputArea');
                    if (!outRoot) { continue; }
                    let outputs = Array.from(outRoot.children);
                    if (isSupplemental) {
                        const sidx = supplementalFrameIndex(n, i);
                        clone.dataset.snum = sidx !== null ? `S.${sidx}` : '';
                    } else {
                        clone.dataset.snum = frame.page !== undefined
                            ? formatMainSlideNumber(n, frame.page)
                            : formatMainSlideNumber(n);
                    }

                    for (let j = outputs.length - 1; j >= 0; j--) {
                        let inHead = (frame.head !== undefined && frame.head >= 0 && j <= frame.head);
                        let inContent = (j >= frame.start && j <= frame.end);
                        outputs[j].classList.remove('print-collapsed');
                        outputs[j].classList.remove('print-invisible');

                        if (!inHead && !inContent) {
                            if (outputs[j]) {
                                i > 0 ? outputs[j].remove() : outputs[j].classList.add('print-collapsed');
                            }
                        }
                    }

                    if (frame.part !== undefined) {
                        for (let j = frame.part + 1; j <= frame.end; j++) {
                            if (outputs[j]) {
                                outputs[j].classList.add('print-invisible');
                            }
                        }
                        handleColsRows(outputs, frame);
                    }
                }
                if (i > 0) {
                    clone = fixIDsAndRefs(clone, i);
                    window._printOnlyObjs.push(clone);
                    slide.parentNode.insertBefore(clone, lastInserted.nextSibling);
                    lastInserted = clone;
                }
            }
        }
    }

    // Clean up AFTER print dialog closes or user may click if print fails in soome IDEs like vscode
    function cleanupAfterPrint() {
        box.querySelectorAll(':scope .print-invisible').forEach(el => el.classList.remove('print-invisible'));
        box.querySelectorAll(':scope .print-collapsed').forEach(el => el.classList.remove('print-collapsed'));
        for (let obj of window._printOnlyObjs || []) {
            obj.remove(); // Remove cloned slides
        }
        box.querySelectorAll(':scope .SlideArea.print-clone').forEach(el => el.remove());
        delete window._printOnlyObjs;
        box.querySelectorAll(':scope > .print-cleanup-btn').forEach(btn => btn.remove());
    }
    // Add a manual cleanup button in case afterprint event does not fire
    let cleanupBtn = document.createElement('button');
    cleanupBtn.innerHTML = '<i class="fa fa-trash"></i> Cleanup Print Artifacts';
    cleanupBtn.className = 'jupyter-button print-cleanup-btn';
    cleanupBtn.style.cssText = `position:absolute;top:4px;right:4px;z-index:11;padding:4px 8px;font-size:16px;`;
    
    function afterPrintHandler() {
        cleanupAfterPrint();
        window.removeEventListener('afterprint', afterPrintHandler);
    }
    
    cleanupBtn.onclick = afterPrintHandler;
    window.addEventListener('afterprint', afterPrintHandler, { once: true }); 
    box.querySelectorAll(':scope .SlideArea').forEach(sa => { 
        void sa.offsetHeight; // force reflow of CSS
     }); 
    setTimeout(() => {   
        box.appendChild(cleanupBtn); // should not be visible immediately to distract user
        window.print();
    }, 1000); // slight delay to ensure rendering
}

const keyMessage = {
    's': 'menu:panel', // toggle side panel
    'k': 'menu:ksc', // keyboard shortcuts
    'e': 'menu:source', // Edit source cell
    'l': 'menu:laser', // toggle laser pointer
}

function keyboardEvents(box,model) {
    function keyOnSlides(e) {
        e.preventDefault(); // stop default actions
        e.stopPropagation(); // stop propagation to jupyterlab events and other views 
        if (e.target !== box){
            return true; // inside componets should work properly, avoid going outside
        }; 

        // Block keyboard navigation for extra safety when in popup focus mode
        if (box.classList.contains('mode-inactive')) {
            return; // extra safety
        }

        let key = e.key; // True unicode key
        let message = '';
        if ('/*'.includes(key)) {
            message = "SHIFT:" + (key === '/' ? "-5" : "5"); // Shift slide by 5
        } else if (key === 'x' || key === 'd') {
            alert("Pressing X or D,D may cut selected cell! Click outside slides to capture these keys!");
            e.stopPropagation(); // stop propagation to jupyterlab events
            return false;
        } else if (key === 'm'){
            alert("Pressing M could change cell to Markdown and vanish away slides!");
            e.stopPropagation();   // M key
            return false;
        }  else if (key === 'Enter') { 
            e.stopPropagation();   // Don't let it pass over slides though, still can't hold Shift + Enter
            return true; // Enter key or Escape key should act properly
        } else if (key === 'f' || key === 'F11' && !e.ctrlKey) { // F11 for fullscreen toggle
            toggleFS(box);
            return false;
        } else if (key === 'Home') { // Jump to first slide
            message = 'FIRST';
        } else if (key === 'End') { // Jump to last main slide (before extra slides)
            message = 'LAST';
        } else if (key === 'ArrowLeft' || key === '-') { // -, <
            message = 'PREV';
        } else if (key === 'ArrowRight' || key === '+' || key === ' ') { // Space, +,  >
            message = 'NEXT';
        } else if (key in keyMessage && !e.ctrlKey){
            message = keyMessage[key];
        } else if (e.ctrlKey && key === 'p') { 
            message = 'PRINT'; // Ctrl + P for print
        }

        model.set("msg_topy", message);
        model.save_changes();
    }
    
    box.onkeydown = keyOnSlides;
};

function toggleFS(box) {
    if (document.fullscreenElement) {
        document.exitFullscreen(); // No box.fullscreen
    } else {
        box.requestFullscreen();
        box.focus(); // it gets unfocused, no idea why
    }
}

function handleMessage(model, msg, box) {
    if (msg === "TFS") {
        toggleFS(box);
    } else if (msg === 'RESCALE') {
        setScale(box, model);
    } else if (msg === "SwitchView") {
        let slideNew = box.querySelector(":scope .SlideArea.ShowSlide");
        slideNew.style.visibility = 'visible';
        slideNew.querySelector(':scope .jp-OutputArea').scrollTop = 0; // scroll reset is important
        // Set stagger delays for all anim-group children
        slideNew.querySelectorAll(':scope .anim-group').forEach(group => {
            const children = Array.from(group.children);
            const numChildren = children.length;
            if (numChildren === 0) return; // safety check

            children.forEach((child, index) => {
                // Linear time budget: 100ms per item
                // Sine curve applied to distribution within that budget
                const totalTime = (numChildren - 1) / 10; // Total time for all children
                const progress = index / (numChildren - 1 || 1); // 0 to 1
                const angle = progress * (Math.PI / 2); // Map to sine curve
                const sinValue = Math.sin(angle); // Apply sine easing
                const stagger = totalTime * sinValue; // Scale to actual time
                child.style.setProperty('--stagger', `${stagger.toFixed(3)}s`);
            });
        });
        
        setScale(box, model); // rescale on slide change if left over, useful in VSCode
        setBgImage(slideNew); // ensure background image is set if not yet
        setMainBgImage(slideNew, box) // set background image if any on current slide
        tldrawLinks(slideNew, model); // fix draw links for new slide

        let others = box.querySelectorAll(":scope .SlideArea.HideSlide");
        for (let slide of others) {
            if (slide.style.visibility === 'visible') {
                slide.style.visibility = 'hidden';
            };
            // Remove animation classes from all hidden slides to prevent reverse animation
            slide.querySelectorAll(':scope ._ips-content-animated').forEach(el => {
                el.classList.remove('_ips-content-animated');
            });
        }
    } else if (msg.includes("NAV:")) {
        console.log("Navigation message received:", msg);
        let slide = box.querySelector(":scope .SlideArea.ShowSlide");
        if (!slide) return;
        const inParts = msg.includes("/PARTS");

        if (msg.includes("NAV:LEFT")) {
            slide.querySelectorAll(':scope ._ips-content-animated').forEach(el => { 
                if (inParts) {
                    // In parts mode, only remove animation from elements which are invisible to avoid unnecessary re-animations
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') {
                        el.classList.remove('_ips-content-animated');
                    }
                } else {
                    el.classList.remove('_ips-content-animated'); // clear animations on going back to available again
                }
            });
        } else if (msg.includes("NAV:RIGHT")) {
            // Trigger animations AFTER a microtask to ensure DOM is fully updated
            let elem = msg.includes("/SELECTOR") 
                ? slide.querySelector(":scope " + msg.replace("NAV:RIGHT/SELECTOR:", "")) 
                : slide; // prefer specific selector if provided

            if (!elem) return; // safety check
            requestAnimationFrame(() => {
                requestAnimationFrame(() => { // Double RAF ensures layout is complete
                    elem.querySelectorAll(
                        ':scope [class*="anim-"]:not(.anim-group):not(._ips-content-animated), ' +
                        ':scope .anim-group > *:not(.jp-OutputArea):not(._ips-content-animated), ' +
                        ':scope .anim-group > .jp-OutputArea > .jp-OutputArea-child:not(._ips-content-animated)'
                    ).forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            el.classList.add('_ips-content-animated'); // triggers animation
                        }
                    });
                });
            });     
        }
    } else if (msg.includes("THEME:")) {
        let theme = msg.replace("THEME:","");

        if (theme.includes("jupyterlab")) {
            let jpTheme = document.body.getAttribute('data-jp-theme-name');
            jpTheme = (jpTheme?jpTheme:"").toLowerCase(); // handle custom themes name too by lowercase
            if (jpTheme.includes("dark")) {
                theme = "dark"; // update
            } else if (jpTheme.includes("light")) {
                theme = "light"; // update
            }
        }
        let container = box.querySelector(":scope .Draw-Widget").querySelector(":scope .tl-container");
        container.classList.remove((theme === "light") ? "tl-theme__dark" : "tl-theme__light")
        container.classList.add("tl-theme__" + theme) // worst way to do it, internal frames are changed with CSS
    } else if (msg === "CloseView") { // deletes node without closing comm to kernl
        if (box) { // may be nothing there left already
            box.remove();
        }
    } else if (msg === "SetColors") { // sent by export_html function only
        setColors(model, box);
    } else if (msg === "PRINT") {
        printSlides(box, model);
    } 
};


function pickBackLayer(slide) {
    const outArea = slide.querySelector(':scope .jp-OutputArea');
    if (!outArea) return null;

    const targetLayer = outArea.querySelector(':scope .BackLayer.print-only');
    if (targetLayer) return targetLayer;
    return null;
}

function setBgImage(slide) {
    // Remove all previous BackLayer elements in SlideArea (direct children only)
    slide.querySelectorAll(':scope > .BackLayer').forEach(bg => bg.remove());

    // Find the new background image in the output area
    let bgImage = pickBackLayer(slide);
    if (bgImage) {
        // Clone the node to avoid moving it from output area
        let newBackLayer = bgImage.cloneNode(true);
        slide.insertBefore(newBackLayer, slide.firstChild); // Insert at the back
        // z-index:-1 paints behind normal-flow content (jp-OutputArea).
        // isolation:isolate scopes the z-index to this SlideArea stacking context so
        // the BackLayer is not pushed behind the SlideBox background.
        newBackLayer.style.zIndex = -1;
        slide.style.isolation = 'isolate';
    } else {
        slide.style.isolation = ''; // reset if no background on this slide
    }
}

function setMainBgImage(slide, target) {
    let bgImage = pickBackLayer(slide);
    let targetBg = target.querySelector(':scope .BackLayer'); // target backlayer
    if (!targetBg) return;
    if (bgImage) {
        targetBg.innerHTML = bgImage.innerHTML; // clone content
        // copy classes except print-only, so unique classes are preserved
        targetBg.className = Array.from(bgImage.classList).filter(c => c !== 'print-only').join(' ');
    } else {
        targetBg.innerHTML = ""; // clear if none
    }
}

const _viewCleanups = new Map(); // Store cleanup functions by box UID

function keepThisViewOnly(box){
    let uid = box.getAttribute("uid");
    let slides = document.querySelectorAll(`[uid='${uid}']`); // This avoids other notebooks Slides
    slides.forEach((slide) => {
        if (slide !== box) { // only keep this view
            // CRITICAL: Call cleanup before removing!
            const cleanup = _viewCleanups.get(slide);
            if (cleanup) cleanup(); // Remove listeners
            slide.remove(); // deletes node, but keeps comm live
        }
    })
}

function handleChangeFS(box,model){
    if (box === document.fullscreenElement) {
        model.set("msg_topy", "mode-fullscreen")
    } else {
        model.set("msg_topy", "!mode-fullscreen")
    };
    model.save_changes();
}

function handleContextMenu(box, model, event) {
    event.preventDefault(); // stop default actions
    event.stopPropagation(); // stop propagation to underlying slides
    // get relative coordinates to box in percents
    let rect = box.getBoundingClientRect();
    // Make context menu appear fully inside box
    let menuRect = box.querySelector(':scope > .CtxMenu').getBoundingClientRect();
    let wPerc = (menuRect.width / rect.width) * 100;
    let hPerc = (menuRect.height / rect.height) * 100;
    
    let xPerc = ((event.clientX - rect.left) / rect.width) * 100;
    let yPerc = ((event.clientY - rect.top) / rect.height) * 100;
    if (xPerc + wPerc > 100) xPerc = 100 - wPerc;
    if (yPerc + hPerc > 100) yPerc = 100 - hPerc - (16/rect.height*100); // a little above from bottom
    if (xPerc < 0) xPerc = 0; // still stays in bounds
    if (yPerc < 0) yPerc = 0; // still stays in bounds

    model.set("msg_topy", `CTX:${xPerc},${yPerc}`); // will parse on python side
    model.save_changes();
}

function showToast(box, msg) {
    box.querySelectorAll(':scope > .ToastMessage').forEach(t => t.remove());
    if (!msg.content || msg.content === "x") { return; } // empty message or x, do nothing

    let toast = document.createElement('div');
    toast.style.transform = 'translateZ(0)'; // force containing button inside as aboslute
    toast.innerHTML = `<div>${msg.content}</div>`; // to make div scrollable if needed
    toast.className = 'ToastMessage';
    let btn = document.createElement('button');
    btn.innerHTML = "<i class='fa fa-close'></i>";
    btn.onclick = () => {
        toast.style.right = '-420px'; // triggers animation on exit in CSS
        setTimeout(() => toast.remove(), 300); // remove after animation
        clearTimeout(toast.timerId); // clear timeout if any
    };
    toast.appendChild(btn);
    box.appendChild(toast);

    toast.style.right = '-420px'; // initial position, a litte more right than width
    setTimeout(() => {
        toast.style.right = '4px'; // triggers animation on enter in CSS
    }, 50); // slight delay to allow initial position to register
    toast.timerId = setTimeout(() => toast.remove(), msg.timeout || 3000); // default 3 seconds
}

function setScale(box, model) {
    let sbox = box.querySelector(':scope .SlideBox');
    let slide = box.querySelector(':scope .SlideArea');
    if (!sbox || !slide) {
        return false; // not ready yet
    }
    
    let rectBox = sbox.getBoundingClientRect();
    let rectSlide = slide.getBoundingClientRect();

    let oldScale = box.style.getPropertyValue('--contentScale');
    
    if (!oldScale) {
        oldScale = 1; // default
    }
   
    let scaleH = oldScale*rectBox.height/rectSlide.height;
    let scaleW = oldScale*rectBox.width/rectSlide.width; 
    let scale = scaleH > scaleW ? scaleW : scaleH;
    
    if(!scale) { // Only set if there is one, don't set null
        return false; // This will ensure if Notebook is hidden, scale stays same
    }
    const pad = model.get('_fkws').pad || 23; // padding bottom, default 23px for footer space
    box.style.setProperty('--contentScale',scale);
    box.style.setProperty('--paddingBottom',Number(pad/scale) + "px");
}

function handleScale(box, model) {
    const resizeObs = new ResizeObserver((entry) => {
        setScale(box, model);
    });
    box._resObs = resizeObs; // need to cleanup later
    resizeObs.observe(box);
    setScale(box, model); // First time set
}

// Touch and Stylus are working perfect, mouse needs special handling to avoid hover effects and text selection
// Do not fall for mouse button combinations, they exclude touch pad users
function handlePointerSwipe(box, model) {
    let initialX = null;
    let initialY = null;
    let swiped = false;
    const THRESHOLD_SWIPE = 70;
    const THRESHOLD_Y_MAX = 30;

    // To ensure swipe works , added tocuh-action CSS to SlideBox and all children
    function setState(e, setValue) {
        swiped = false;
        // Avoid swipe when in inactive mode like popup focus should not trigger slide changes
        initialX = setValue && !box.classList.contains('mode-inactive') ? e.clientX : null;
        initialY = setValue && !box.classList.contains('mode-inactive') ? e.clientY : null;
        if (!setValue) box.classList.remove('mouse-swipe-active'); // reset on end
    }

    box.addEventListener('pointerdown', (e) => {
        // let interactive elements be not effected unintentionally
        if (e.target.closest(INTERACTIVE_SEL)) return;
        if (e.pointerType === 'mouse') { // only left mouse button be held down for swipe
            if (e.button !== 0 || !box.classList.contains('mouse-swipe-enabled')) return;
        }
        setState(e, true);
    }); // initialize coordinates
    box.addEventListener('pointermove', (e) => {
        if (initialX === null || swiped) return;
        const diffX = e.clientX - initialX;
        const diffY = e.clientY - initialY;

        // show overlay for mouse swipe, but only after 20% threshold to let clicks work
        // It is only needed for mouse, touch/stylus have no hover effects to worry about
        if (e.pointerType === 'mouse') { 
            if (Math.abs(diffX) > THRESHOLD_SWIPE/4 && !box.classList.contains('mouse-swipe-active')) { 
                box.classList.add('mouse-swipe-active'); // show overlay after 25% threshold
            } else if (box.classList.contains('mouse-swipe-active')) {
                box.classList.remove('mouse-swipe-active'); // reset if user wants to cancel in middle of swipe
            }
        }

        if (Math.abs(diffY) > THRESHOLD_Y_MAX) {
            setState(e, false); // reset swipe state
            return; // exit early, too much vertical movement
        }

        if (Math.abs(diffX) >= THRESHOLD_SWIPE) {
            model.set("msg_topy", diffX < 0 ? "NEXT" : "PREV");
            model.save_changes();
            swiped = true; // Only one navigation per gesture
        }
    });
    box.addEventListener('pointerup', (e) => { setState(e, false); });
    // left the area, cancel swipe
    box.addEventListener('pointercancel', (e) => { setState(e, false); });
}

// Avoid clicks passing through to underlying clickable elements // include vuetify/ipymaterialui sliders too
const INTERACTIVE_SEL = "a, button, input, select, textarea, area[href], summary, [contenteditable='true'], .widget-slider, .v-slider, .MuiSlider-root";  

function handleBoxClicks(box, model) {
    // Handle single clicks for navigation and blocking
    box.addEventListener('click', function(event) {
        // Handle footer area click to toggle context menu
        const ctxMenu = box.querySelector(':scope > .CtxMenu');
        const isCtxOpen = ctxMenu && ctxMenu.style.visibility === 'visible';
        if (isCtxOpen && !event.target.closest('.SlidesWrapper > .CtxMenu')) {
            model.set("msg_topy", "CCTX"); // close context menu
            model.save_changes(); // after that go on with other checks
        } else if (event.target.closest('.SlidesWrapper > .FooterBox')) {
            handleContextMenu(box, model, event); 
            return; // exit after handling footer click
        }
        
        // Then, check for interactive elements that should handle their own clicks
        if (event.target.closest(INTERACTIVE_SEL)) {
            event.stopPropagation(); // stop propagation to underlying slides
            return true; // let the click happen
        } 
        
        // Check if in focus mode, do not pass clicks to slides to avoid accidental slide changes
        if (event.target.closest('.mode-popup-active') || box.classList.contains('mode-inactive')) {
            event.stopPropagation(); // stop propagation to underlying slides
            event.preventDefault(); // stop default actions
            return; // Exit 
        }
    });

    // Handle double-click for entering focus mode
    box.addEventListener('dblclick', function(event) {
        // Check for interactive elements - they should handle their own double-clicks (text selection, etc.)
        if (event.target.closest(INTERACTIVE_SEL)) {
            return; // Let interactive elements handle their own double-clicks
        }
        
        // Check if already in focus mode - exit it
        if (box.classList.contains('mode-inactive')) {
            const closeBtn = box.querySelector(':scope .popup-close-btn');
            if (closeBtn) {
                closeBtn.click(); // Trigger close button
            }
            return false; // already in focus mode, exit
        }

        // Check for focusable elements
        const matchedElem = event.target.closest(model.get("_fsels"));
        if (matchedElem) { // Focus by JS to be able to have a close button etc
            event.preventDefault(); 
            event.stopPropagation();
            box.blur(); // remove focus from box to avoid keyboard events there
            matchedElem.classList.add('mode-popup-active');
            model.set("msg_topy", "mode-inactive");
            model.save_changes();
            
            const btn = document.createElement('button');
            btn.className = 'popup-close-btn';
            btn.title = 'Close Popup (Double-click)';
            btn.innerHTML = '<i class="fa fa-close"></i>';
            btn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                matchedElem.classList.remove('mode-popup-active');
                model.set("msg_topy", "!mode-inactive");
                model.save_changes();
                box.focus(); // return focus to box
                btn.remove(); // remove button
            };
            box.appendChild(btn);
        }
    });
}

function setColors(model, box) {
    let style = window.getComputedStyle(box);
    const colors = {}
    Object.entries(model.get("_colors")).forEach(([prop, cssVar]) => {
        colors[prop] = style.getPropertyValue(cssVar);
    });
    if (colors['accent']) { // Avoid sending empty data due to other closed displays
        model.set("_colors", colors);
        model.save_changes();
    };
}

function getSlideIndex(slide){
    return Array.from(
        slide.parentNode.querySelectorAll(':scope > .SlideArea')
    ).indexOf(slide);
}

function showJumpIndictor(model, box, originIndex, offset) {
    if (box._jumpIndicator) {
        clearTimeout(box._jumpIndicator.timerId);
        clearInterval(box._jumpIndicator.countdownInterval); // Clear countdown too
        box._jumpIndicator.remove();
    }
    
    let indicator = document.createElement('button');
    indicator.style.cssText = `
        position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%);cursor: pointer;backdrop-filter: blur(4px);
        font-size: 12px; z-index: 9; border:none;outline:none; text-shadow: 0px 1px var(--bg2-color);`;
    indicator.title = `Jumped ${offset > 0 ? 'forward' : 'backward'} by multiple slides, click to go back.`;
    box.appendChild(indicator);

    let countdown = 10;
    
    function updateCountdown() {
        countdown -= 1;
        if (countdown > 0 && box._jumpIndicator) {
            indicator.innerHTML = `<i class="fa fa-arrow${offset > 0 ? 'l' : 'r'}"></i> Back to Link 
            <span style="color: var(--pointer-color);margin-left:4px;text-shadow: 0.5px 1px var(--bg2-color);">${countdown}</span>`;
        } else {
            indicator.remove();
            box._jumpIndicator = null;
        }
    }

    function resetTimer() {
        clearTimeout(indicator.timerId);
        clearInterval(indicator.countdownInterval); // Clear old countdown
        countdown = 10; // Reset countdown
        indicator.innerHTML = `<i class="fa fa-arrow${offset > 0 ? 'l' : 'r'}"></i> Back to Link 
        <span style="color: var(--pointer-color);margin-left:4px;text-shadow: 0.5px 1px var(--bg2-color);">${countdown}</span>`;
        
        // Start new countdown
        indicator.countdownInterval = setInterval(updateCountdown, 1000);
        indicator.timerId = setTimeout(() => {
            clearInterval(indicator.countdownInterval);
            indicator.remove();
            box._jumpIndicator = null;
        }, 10000);
    }
    
    indicator.onmouseenter = resetTimer;
    indicator.originIndex = originIndex;
    
    indicator.onclick = function() {
        let currentIndex = getSlideIndex(box.querySelector(':scope .SlideArea.ShowSlide'));
        if (currentIndex !== null) {
            let backOffset = indicator.originIndex - currentIndex;
            model.set("msg_topy", `SHIFT:${backOffset}`);
            model.save_changes();
        }
        clearInterval(indicator.countdownInterval); // Clear countdown on click
        clearTimeout(indicator.timerId);
        indicator.remove();
        box._jumpIndicator = null;
    };
    
    resetTimer(); // Start initial timer and countdown
    box._jumpIndicator = indicator;
}

function linkSwitchesSlide(model, box) {
    box.addEventListener('click', function (event) {
        const anchor = event.target.closest('.slide-link'); // Find the closest link with class 'slide-link
        if (!anchor || !box.contains(anchor)) return;   
        event.preventDefault(); 
        const href = anchor.getAttribute('href');
        const targetId = href.startsWith('#') ? href.slice(1) : null;
        const targetElement = targetId ? document.getElementById(targetId) : document.querySelector(href);  
        const originSlide = anchor.closest('.SlideArea');
        const targetSlide = targetElement?.closest('.SlideArea');   
        if (originSlide && targetSlide) {    
            const originIndex = getSlideIndex(originSlide);
            const targetIndex = getSlideIndex(targetSlide);   
            
            if (originIndex !== null && targetIndex !== null) {
                const offset = targetIndex - originIndex;
                model.set("msg_topy", `SHIFT:${offset}`); // Send message to shift slides
                model.save_changes();
                showJumpIndictor(model, box, originIndex, offset); // Show jump indicator to click back
                } else {
                alert(`Link '${anchor.textContent}' does not point to a valid slide`);
            }
        } else if (!originSlide || !targetSlide) {
            alert(`Link target not found or it was not set on a slide: '${anchor.textContent}'`);
        } 
    });
}

function markPrintable(el, className) {
  // First, remove the class from any previously marked elements
  document.querySelectorAll('.' + className).forEach(node => node.classList.remove(className));
  
  // Then walk up from the given element to <body>, adding the class
  while (el && el !== document.body) {
    el.classList.add(className);
    el = el.parentElement;
  }
}

function displaySplash(box) {
    box.classList.add('ips-loading');
    setTimeout(() => {
        window.dispatchEvent(new Event('resize')); // another resize after load
        box.classList.remove('ips-loading');
    }, 1000); // slight delay to ensure smooth transition
}

function render({ model, el }) {
    // Store listener references for cleanup
    const listeners = { msgToJs: null, msgCustom: null};

    let style = document.createElement('style');
    //  Trick to get main slide element is to wait for a loadable element
    style.onload = () => { 
        
        let box = style.parentNode.parentNode;
        displaySplash(box);
        box.tabIndex = -1; // Need for event listeners, should be at top
        box.setAttribute("uid", model.get("_uid"));
        // JupyterLab/Notebook specific attribute to suppress shortcuts when focused
        box.setAttribute("data-lm-suppress-shortcuts", "true"); // how we can know this hack works forever?
        
        // Only for jupyter, voila, notebook, do as early as possible
        if (window.hasOwnProperty('_JUPYTERLAB')) {
            model.set("msg_topy","JUPYTER");
            model.save_changes();
        };

        box.onmouseenter = function(){
            if (!box.classList.contains('mode-inactive')){
                box.focus(); // focus only if not in inactive mode
            }
        };
        box.onmouseleave = function(){box.blur();};
        
        // Keyboard events
        keyboardEvents(box,model);

        // handle scale of slides size
        handleScale(box, model);

        // Remove other views without closing comm
        keepThisViewOnly(box); 

        // Link switches slides
        linkSwitchesSlide(model, box);

        // Handle box clicks for both focus and edge navigation
        handleBoxClicks(box, model);

        // Handle swipe events for navigation
        handlePointerSwipe(box, model);

        // Sends a message if fullscreen is changed by some other mechanism
        box.onfullscreenchange = ()=>{handleChangeFS(box,model)};

        // Capture context menu to avoid passing to underlying elements
        box.addEventListener('contextmenu', function(event) {
            if (event.shiftKey) {return true}; // allow Shift + Right click for normal context menu
            handleContextMenu(box, model, event);
        });

        // If voila, turn on full viewport
        let base_url = box.ownerDocument.body.getAttribute('data-base-url');
        if (base_url && base_url.includes("voila")) {
            box.classList.add("Voila-Child");
            box.ownerDocument.body.classList.add("Voila-App");
        };
        
        // Handle changes from Python side  
        listeners.msgToJs = () => {
            let msg = model.get("msg_tojs");
            if (!msg) {return false}; // empty message, don't waste time
            if (document.hasFocus() && !document.hidden) { // only if document is in view of user
                handleMessage(model, msg, box);
            } // sometimes print and other command make issue in other tabs since notebook is a widget with synced state
        };
        model.on("change:msg_tojs", listeners.msgToJs);

        // Handle notifications
        listeners.msgCustom = (msg) => {
            if (document.hasFocus() && !document.hidden) { // only if document is in view of user
                showToast(box, msg);
            }
        };
        model.on("msg:custom", listeners.msgCustom);

        // Reset size of drawing board instead of provided by widget
        let drawing = box.querySelector(':scope .Draw-Widget');
        // Let all keys work here but don't go further up and avoid navigation of slides too.
        drawing.onkeydown = (e) => {e.stopPropagation();} 
        drawing.oncontextmenu = (e) => {e.stopPropagation();} // avoid context menu passing up
        
        for (let c of drawing.childNodes) {
            c.style.width = '100%';
            c.style.height = '100%';
        }

        // Add a div to hold background image
        let bglayer = document.createElement('div');
        bglayer.className = 'BackLayer'; // other 
        box.insertBefore(bglayer, box.firstChild); // at back
        bglayer.style.zIndex = 0; // ensure at back further

        // Set background images if any left due to being loaded from python script
        box.querySelectorAll(':scope .SlideArea').forEach((slide) => {setBgImage(slide);}); // only set which are not yet set
        setMainBgImage(box.querySelector(':scope .ShowSlide'), box) // set background image if any on current slide
        tldrawLinks(box, model); // fix draw links for all slides
        
        // Add classes to mark ancestors for printing
        markPrintable(box, 'ipyslides-print-node');

        // Store cleanup function (it removes itself from map when called)
        _viewCleanups.set(box, () => {
            console.log("Cleaning up view:", box.getAttribute("uid"));
            if (listeners.msgToJs) model.off("change:msg_tojs", listeners.msgToJs);
            if (listeners.msgCustom) model.off("msg:custom", listeners.msgCustom);
            if (box._resObs) {
                box._resObs.disconnect();
                delete box._resObs;
            }
            _viewCleanups.delete(box); // Remove from map at end
        });
    }  
    el.appendChild(style);
    model.set("msg_topy", "LOADED"); // to run onload functionality
    model.save_changes();
    
    // Clean up old slides if left over from previous session of kernel restart
    let slides = document.querySelectorAll('.SlidesWrapper');
    for (let slide of Array.from(slides)) {
        if (slide.classList.contains('jupyter-widgets-disconnected')) {
            const cleanup = _viewCleanups.get(slide);
            if (cleanup) cleanup(); // Clean up before removing
            slide.remove();
        };
    };
    // Return cleanup function (called by widget framework when view is properly destroyed)
    return () => { 
        console.log("Widget framework cleanup called");
        const cleanup = _viewCleanups.get(style.parentNode?.parentNode);
        if (cleanup) cleanup();
    };
}

export default { render }