<script lang="ts">
    import { onMount } from "svelte";
    import DragHandle from "../general/drag_handle.svelte";
    import { transmitters, receivers } from "../../wiring";
    import { onDestroy } from "svelte";

    let dragging = false;
    let dragHandleBaseStyle = "width: 0.5em; height: 0.5em; border-radius: 50%; background-color: green; cursor: pointer; z-index: 3;"
    let dragHandleStyle = dragHandleBaseStyle;
    let fontsize: number = 1;

    let handleX = 0;
    let handleY = 0;
    let controlOffset = 0;

    let connections: {signal: (message: Message) => void, x: number, y: number, offset: number, element: HTMLElement }[] = [];

    export function send(message: Message) {
        for (let connection of connections) {
            connection.signal(message);
        }
    }

    function onDragStart() {

        dragging = true;
        let position = `bottom: 1.25em; right: 0.75em;`;
        dragHandleStyle = `${dragHandleBaseStyle} ${position} position: absolute;`

        getFontSize();
        
        handleX = 0;
        handleY = 0;

        controlOffset = 0.5 * Math.abs(handleX);
        if (controlOffset < 5) controlOffset = 5;
    }

    function onDragEnd() {
        dragging = false;

        let rect = container.getBoundingClientRect();

        let x = handleX + container.clientWidth + rect.left - 1 * fontsize;
        let y = handleY + container.clientHeight + rect.top - 1 * fontsize;

        let id = idAtLocation(x, y);

        if (id === null) return;
        if (receivers[id] === undefined) return;

        connections.push({...receivers[id], "x": handleX, "y": handleY, "offset": controlOffset})

        connections = connections;
    }

    export function updateWires() {
        connections = connections;
    }

    function svgPathVariables(receiver: HTMLElement) {
        let receiverRect = receiver.getBoundingClientRect();
        let containerRect = container.getBoundingClientRect();

        let x = receiverRect.left - container.clientWidth - containerRect.left + 1.5 * fontsize;
        let y = receiverRect.top - container.clientHeight - containerRect.top + 2 * fontsize;

        let offset = 0.5 * Math.abs(x);
        if (offset < 5) offset = 5;

        return {x, y, offset};
    }

    function onDrag(x: number | string | null, y: number | string | null) {
        let position = `left: calc(${x}px + 0.25em); top: calc(${y}px + 0.25em);`;
        dragHandleStyle = `${dragHandleBaseStyle} ${position} position: absolute;`

        if (typeof x !== "number") {
            x = 0;
        }
        if (typeof y !== "number") {
            y = 0;
        }

        handleX = x - container.clientWidth + 1.5 * fontsize;
        handleY = y - container.clientHeight + 2 * fontsize;

        controlOffset = 0.5 * Math.abs(handleX);
        if (controlOffset < 5) controlOffset = 5;
    }

    function getFontSize() {
        fontsize = parseFloat(getComputedStyle(container).fontSize);
    }

    function getOffset() {
        return {
            x: container.clientWidth - fontsize * 1.5,
            y: container.clientHeight - fontsize * 2
        }
    }

    let id: string = "TRANSMITTER-" + crypto.randomUUID();

    let container: HTMLElement;

    onMount(() => {
        transmitters[id] = { "element": container, "rerender": updateWires };
        getFontSize();
    });

    onDestroy(() => {
        delete transmitters[id];
    });

    function idAtLocation(x: number, y: number): string | null {
        var stack = [];
        var el;
        var result = null;
        do {
            el = document.elementFromPoint(x, y);
            if (el === null) {
                break;
            }
            if (el.id.startsWith("RECEIVER-")) {
                result = el.id;
                break;
            }
            stack.push(el);
            el.classList.add('pointerEventsNone');
        }while(el.tagName !== 'HTML');

        // clean up
        for(var i  = 0; i < stack.length; i += 1)
            stack[i].classList.remove('pointerEventsNone');

        return result;
    }

    let connectionDisplayData: { x: number, y: number, offset: number }[] = []

    $: {
        connectionDisplayData = [];
        for (let connection of connections) {
            connectionDisplayData.push(svgPathVariables(connection.element));
        }
    }
</script>

<div {id} style="position: relative; height: 100%; width: 100%;" bind:this={container}>
    <div class=transmitter {...$$restProps} style={dragging ? "" : "visibility: hidden;"} />

    {#if dragging}
        <svg xmlns="http://www.w3.org/2000/svg" style="overflow: visible; position: absolute; top: calc(100% - 1.5em); left: calc(100% - 1em); z-index: 3; pointer-events: none;">
            <path d="M {0} {0} C {controlOffset} {0}, {handleX - controlOffset} {handleY}, {handleX} {handleY}" stroke="green" stroke-width="4" fill="none" style="pointer-events: auto;" />
        </svg>
    {/if}

    {#each connectionDisplayData as connection}
        <svg xmlns="http://www.w3.org/2000/svg" style="overflow: visible; position: absolute; top: calc(100% - 1.5em); left: calc(100% - 1em); z-index: 3; pointer-events: none;">
            <path d="M {0} {0} C {connection.offset} {0}, {connection.x - connection.offset} {connection.y}, {connection.x} {connection.y}" stroke="blue" stroke-width="4" fill="none" style="pointer-events: auto;" />
        </svg>
    {/each}

    <DragHandle {onDragStart} {onDrag} {onDragEnd} {getOffset} style={dragging ? dragHandleStyle : ""}>
        <div class=transmitter {...$$restProps} style={dragging ? "visibility: hidden;" : ""}>
        </div>
    </DragHandle>
</div>

<style>
    .transmitter {
        background-color: red;
        position: absolute;
        bottom: 1em;
        right: 0.5em;
        height: 1em;
        width: 1em;
        border-radius: 50%;
        cursor: pointer;
        z-index: 3;
    }
</style>