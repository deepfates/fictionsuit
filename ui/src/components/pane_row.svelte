<script>
    import { onMount } from "svelte";
    import DragHandle from "./drag_handle.svelte";
    import Emptiness from "./emptiness.svelte";

    export let dividers = true;

    export let leftPercent = 50;
    export let centerPercent = 0;
    export let rightPercent = 50;

    /**
     * @type {HTMLDivElement}
     */
    let container;

    onMount(() => {
        if ($$slots.center && (leftPercent === 50 && centerPercent === 0 && rightPercent === 50)) {
            leftPercent = 33;
            centerPercent = 32;
            rightPercent = 33;
        }
    });

    /**
     * @param {string | number | null} x
     * @param {string | number | null} y
     */
    function onDragA(x, y) {
        if (x === null || typeof(x) !== "number") return;
        let width = container.clientWidth;
        if ($$slots.center) {
            leftPercent = x / width * 100;
            if (leftPercent > 97.9 - rightPercent) {
                leftPercent = 97.9 - rightPercent;
            }
            if (leftPercent < 0.1) {
                leftPercent = 0.1;
            }
            centerPercent = 98 - leftPercent - rightPercent; // 2% for the 2 dividers
        } else { 
            leftPercent = x / width * 100;
            rightPercent = 99 - leftPercent; // 1% for the divider
        }
    }

    /**
     * @param {string | number | null} x
     * @param {string | number | null} y
    */
    function onDragB(x, y) {
        if (x === null || typeof(x) !== "number") return;
        let width = container.clientWidth;
        rightPercent = (width - x) / width * 100;
        if (rightPercent > 97.9 - leftPercent) {
            rightPercent = 97.9 - leftPercent;
        }
        if (rightPercent < 0.1) {
            rightPercent = 0.1;
        }
        centerPercent = 98 - leftPercent - rightPercent; // 2% for the 2 dividers

    }

    function getOffsetA() {
        return {
            x: container.offsetLeft + container.clientWidth * leftPercent / 100,
            y: 0, // don't care
        };
    }

    function getOffsetB() {
        return {
            x: container.offsetLeft + container.clientWidth * (leftPercent + centerPercent + 2) / 100,
            y: 0, // don't care
        };
    }
</script>

<div class="row-container" bind:this={container}>
    <div class="pane-container"
        style="flex: 1 1 {leftPercent}%">
        <slot name="left" >
            <Emptiness />
        </slot>
    </div>
    {#if dividers}
        <div class="pane-divider">
            <DragHandle onDrag={onDragA} getOffset={getOffsetA} >
                <div class="pane-resize" />
            </DragHandle>
        </div>
    {/if}
    {#if $$slots.center}
        <div class="pane-container"
            style="flex: 1 1 {centerPercent}%">
            <slot name="center" />
        </div>
        {#if dividers}
            <div class="pane-divider">
                <DragHandle onDrag={onDragB} getOffset={getOffsetB} >
                    <div class="pane-resize" />
                </DragHandle>
            </div>
        {/if}
    {/if}
    <div class="pane-container"
        style="flex: 1 1 {rightPercent}%">
        <slot name="right">
            <Emptiness />
        </slot>
    </div>
</div>

<style>
    .row-container {
        position: relative;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        align-items: stretch;
        justify-content: flex-start;
    }

    .pane-container {
        position: relative;
        overflow: hidden;
        left: 0;
        top: 0;
        right: 0;
        bottom: 0;
    }

    .pane-divider {
        position: relative;
        flex: 1 1 calc(min(1%, 1px));
        top: 0;
        bottom: 0;
        background-color: var(--pane-divider);
        overflow: visible;
        z-index: 1;
    }

    .pane-resize {
        position: absolute;
        height: 100%;
        left: calc(50% - 0.5em);
        width: 1em;
        border-radius: 40%;
        cursor: col-resize;
    }
</style>