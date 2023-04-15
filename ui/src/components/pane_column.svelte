<script>
    import { onMount } from "svelte";
    import DragHandle from "./drag_handle.svelte";
    import Emptiness from "./emptiness.svelte";

    export let dividers = true;

    export let topPercent = 50;
    export let middlePercent = 0;
    export let bottomPercent = 50;

    /**
     * @type {HTMLDivElement}
     */
    let container;

    onMount(() => {
        if ($$slots.middle && (topPercent === 50 && middlePercent === 0 && bottomPercent === 50)) {
            topPercent = 33;
            middlePercent = 32;
            bottomPercent = 33;
        }
    });

    /**
     * @param {string | number | null} x
     * @param {string | number | null} y
     */
    function onDragA(x, y) {
        if (y === null || typeof(y) !== "number") return;
        let height = container.clientHeight;
        if ($$slots.middle) {
            topPercent = y / height * 100;
            if (topPercent > 97.9 - bottomPercent) {
                topPercent = 97.9 - bottomPercent;
            }
            if (topPercent < 0.1) {
                topPercent = 0.1;
            }
            middlePercent = 98 - topPercent - bottomPercent; // 2% for the 2 dividers
        } else { 
            topPercent = y / height * 100;
            bottomPercent = 99 - topPercent; // 1% for the divider
        }
    }

    /**
     * @param {string | number | null} x
     * @param {string | number | null} y
    */
    function onDragB(x, y) {
        if (y === null || typeof(y) !== "number") return;
        let height = container.clientHeight;
        bottomPercent = (height - y) / height * 100;
        if (bottomPercent > 97.9 - topPercent) {
            bottomPercent = 97.9 - topPercent;
        }
        if (bottomPercent < 0.1) {
            bottomPercent = 0.1;
        }
        middlePercent = 98 - topPercent - bottomPercent; // 2% for the 2 dividers

    }

    function getOffsetA() {
        return {
            x: 0, // don't care
            y: container.offsetTop + container.clientHeight * topPercent / 100
        };
    }

    function getOffsetB() {
        return {
            x: 0, // don't care
            y: container.offsetTop + container.clientHeight * (topPercent + middlePercent + 2) / 100
        };
    }
</script>

<div class="column-container" bind:this={container}>
    <div class="pane-container"
        style="flex: 1 1 {topPercent}%">
        <slot name="top">
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
    {#if $$slots.middle}
        <div class="pane-container"
            style="flex: 1 1 {middlePercent}%">
            <slot name="middle" />
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
        style="flex: 1 1 {bottomPercent}%">
        <slot name="bottom">
            <Emptiness />
        </slot>
    </div>
</div>

<style>
    .column-container {
        position: relative;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
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
        width: 100%;
        top: calc(50% - 0.5em);
        height: 1em;
        border-radius: 40%;
        cursor: row-resize;
    }
</style>