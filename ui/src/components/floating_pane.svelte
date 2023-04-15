<!-- A window pane, containing anything or nothing. -->

<script context="module">
    /**
     * @type {({z_index: number, container: HTMLDivElement, onUpdate: (z_index: number) => void})[]}
     */
    export let instances = [];
</script>

<script>
    import { onMount } from "svelte";
    import { onDestroy } from "svelte";

    import DragHandle from "./drag_handle.svelte";
    import Emptiness from "./emptiness.svelte";

    export let width = 300;
    export let height = 200;
    
    export let x = `50% - ${width / 2}px`;
    export let y = `50% - ${height / 2}px`;
    
    export let title = "Untitled";
    export let scale = "1em";

    // The exported values are only used for initialization
    let w = 0;
    let h = 0;
    let z_index = 10;

    /**
     * @type {HTMLDivElement}
     */
    let container;

    let container_position = "";
    let container_size = "";
    let body_style = "";

    setPosition(x, y);
    resize(width, height);

    let title_style = ``;

    /**
     * 
     * @param {string | number | null} x
     * @param {string | number | null} y
     */
    function setPosition(x, y) {
        let left, top;
        
        if (typeof(x) === "number") {
            left = `calc(min(max(${x}px, 0%), 100% - ${w}px))`;
        } else {
            left = `calc(min(max(${x}, 0%), 100% - ${w}px))`;
        }
        if (typeof(y) === "number") {
            top = `calc(min(max(${y}px, 0%), 100% - ${h}px))`;
        } else {
            top = `calc(min(max(${y}, 0%), 100% - ${h}px))`;
        }

        container_position = `left: ${left}; top: ${top};`;
    }

    function getOffset() {
        return {
            x: container.offsetLeft,
            y: container.offsetTop
        }
    }

    function brOffset() {
        return {
            x: container.offsetLeft + w,
            y: container.offsetTop + h
        }
    }

    /**
     * 
     * @param {string | number | null} width
     * @param {string | number | null} height
     */
    function resize(width, height) {
        let left, top, wLimit, hLimit;
        if (container === undefined) {
            left = 0;
            top = 0;
            wLimit = null;
            hLimit = null;
        } else {
            left = container.offsetLeft;
            top = container.offsetTop;

            wLimit = container.parentElement?.clientWidth ?? null;
            hLimit = container.parentElement?.clientHeight ?? null;
        }

        if (width === null) {
            width = w + left;
        }
        if (height === null) {
            height = h + top;
        }
        
        if (typeof(width) !== "number" || typeof(height) !== "number") {
            return;
        }


        w = width - left;
        h = height - top;

        if (wLimit !== null) {
            w = Math.min(w, wLimit - left);
        }

        if (hLimit !== null) {
            h = Math.min(h, hLimit - top);
        }

        let width_style = `calc(max(${w}px, 5em))`;
        let height_style = `calc(max(${h}px, 3.5em))`;

        container_size = `width: ${width_style}; height: ${height_style};`;
        body_style = `height: calc(max(${h}px - 1.5em, 2em));`;
    }

    /**
     * 
     * @param {MouseEvent} event 
     */
    function takeFront(event) {
        let old_index = z_index;
        instances.forEach((pane, i) => {
            if (pane.container === container) {
                z_index = instances.length + 10;
                pane.z_index = z_index;
            } else if (pane.z_index >= old_index) {
                pane.z_index = pane.z_index - 1;
                pane.onUpdate(pane.z_index);
            }
        });
    }

    /**
     * 
     * @param {MouseEvent} event 
     */
    function headerMouseDown(event) {
        if (event.button === 1) {
            container.parentNode?.removeChild(container);
        }
    }

    let dh_offset = 15;
    let dh_separation = 20;
    let dh_height = 10;

    let bar0 = dh_offset;
    let bar1 = dh_offset + dh_separation + dh_height;
    let bar2 = dh_offset + 2 * (dh_separation + dh_height);

    onMount(() => {
        z_index = instances.length + 11;
        instances.push({z_index, container, onUpdate});
    });

    /**
     * @param {number} new_z_index
     */
    function onUpdate(new_z_index) {
        z_index = new_z_index;
    }

    onDestroy(() => {
        let index = instances.findIndex(pane => pane.container === container);
        if (index !== -1) {
            instances.splice(index, 1);
        }
    });
</script>

<div class=pane-container style="{container_position} {container_size} font-size: {scale}; z-index: {z_index}" bind:this={container} on:mousedown={takeFront}>
    <div class=relativizer>
        <DragHandle onDrag={setPosition} getOffset={getOffset}>
            <div class=pane-header
                on:mousedown={headerMouseDown}>
                <span class=pane-title style={title_style}>
                    {title}
                </span>
                <div class=drag-handle>
                    <div class=drag-handle-bar style="top: {bar0}%; height: {dh_height}%;"></div>
                    <div class=drag-handle-bar style="top: {bar1}%; height: {dh_height}%;"></div>
                    <div class=drag-handle-bar style="top: {bar2}%; height: {dh_height}%;"></div>
                </div>
            </div>
        </DragHandle>
        <div class=pane-body style={body_style}>
            <div class=pane-content>
                <slot>
                    <Emptiness />
                </slot>
            </div>
        </div>
    </div>
    <DragHandle onDrag={resize} getOffset={brOffset}>
        <div class="pane-resize-handle corner">
            
        </div>
    </DragHandle>
    <DragHandle onDrag={resize} getOffset={brOffset} yEnabled={false}>
        <div class="pane-resize-handle right">
            
        </div>
    </DragHandle>
    <DragHandle onDrag={resize} getOffset={brOffset} xEnabled={false}>
        <div class="pane-resize-handle bottom">
            
        </div>
    </DragHandle>
</div>

<style>
    .pane-container {
        position: absolute;
    }

    .relativizer {
        position: relative;
        width: 100%;
        height: 100%;
    }

    .pane-header {
        position: absolute;
        background-color: var(--pane-header);
        width: 100%; 
        height: 1.5em;
    }

    .pane-title {
        color: var(--pane-title);
        font: 1em monospace;
        position: absolute; 
        top: 0.22em; 
        left: 0.5em; 
        max-width: calc(100% - 2.5em); 
        overflow: hidden; 
        white-space: nowrap;
        user-select: none;
    }

    .pane-body {
        position: absolute;
        overflow: hidden;
        width: 100%;
        top: 1.5em;
    }

    .pane-content {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
    }

    .pane-resize-handle {
        position: absolute;
        user-select: none;
        z-index: 2;
    }
    
    .pane-resize-handle.corner {
        right: -0.5em;
        bottom: -0.5em;
        width: 1em;
        height: 1em;
        border-radius: 50%;
        cursor: nwse-resize;
    }

    .pane-resize-handle.right {
        right: -0.5em;
        bottom: 0.5em;
        width: 0.8em;
        height: calc(100% - 2em);
        border-radius: 30%;
        cursor: ew-resize;
    }

    .pane-resize-handle.bottom {
        right: 0.5em;
        bottom: -0.5em;
        width: calc(100% - 0.5em);
        height: 0.8em;
        border-radius: 30%;
        cursor: ns-resize;
    }

    .drag-handle {
        position: absolute;
        left: calc(100% - 1.5em);
        width: 1.5em;
        height: 1.5em;
        user-select: none;
        cursor: move;
    }

    .drag-handle-bar {
        position: absolute;
        background-color: var(--drag-handle);
        width: 80%;
        left: 10%;
        border-radius: 0.5em;
    }
</style>