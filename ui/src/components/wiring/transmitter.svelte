<script lang="ts">
    import { onMount } from "svelte";
    import DragHandle from "../general/drag_handle.svelte";
    import { transmitters, receivers } from "../../wiring";
    import { onDestroy } from "svelte";

    export let schemas: string[] = ["any"];

    let dragging = false;
    let dragHandleBaseStyle = "width: 0.5em; height: 0.5em; border-radius: 50%; background-color: green; cursor: pointer; z-index: 3;"
    let dragHandleStyle = dragHandleBaseStyle;
    let fontsize: number = 1;

    let handleX = 0;
    let handleY = 0;
    let controlOffset = 0;

    let connections: {signal: (message: Message) => void, x: number, y: number, offset: number, element: HTMLElement, id: string }[] = [];

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
        if (controlOffset < 0) controlOffset = 0;
    }

    function onDragEnd() {
        dragging = false;

        let rect = container.getBoundingClientRect();

        let x = handleX + container.clientWidth + rect.left - 1 * fontsize;
        let y = handleY + container.clientHeight + rect.top - 1 * fontsize;

        let id = idAtLocation(x, y);

        if (id === null) return;
        if (receivers[id] === undefined) return;

        let acceptedSchemas = receivers[id].schemas;
        if (!acceptedSchemas.includes("any")) {
            console.log(schemas, acceptedSchemas)
            if (!schemas.every(schema => acceptedSchemas.includes(schema))) return;
        }

        connections.push({...receivers[id], "x": handleX, "y": handleY, "offset": controlOffset})

        connections = connections;
    }

    export function updateWires() {
        connections = connections;
    }

    function svgPathVariables(receiver: HTMLElement, id: string) {
        let receiverRect = receiver.getBoundingClientRect();
        let containerRect = container.getBoundingClientRect();

        let x = receiverRect.left - container.clientWidth - containerRect.left + 1.5 * fontsize;
        let y = receiverRect.top - container.clientHeight - containerRect.top + 2 * fontsize;

        let offset = 0.5 * Math.abs(x);
        if (offset < 120) offset = 120;

        return {x, y, offset, id};
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
        if (controlOffset < 0) controlOffset = 0;
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
        transmitters[id] = { "element": container, "rerender": updateWires, "connections": connections };
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

    function onPathClick(id: string) {
        let index = connections.findIndex((connection) => connection.id === id);
        if (index === -1) {
            // Impossible -- unless something has gone horribly wrong
            return;
        }

        connections.splice(index, 1);
        connections = connections;
    }

    let connectionDisplayData: { x: number, y: number, offset: number, id: string }[] = []

    $: {
        connectionDisplayData = [];
        for (let connection of connections) {
            connectionDisplayData.push(svgPathVariables(connection.element, connection.id));
        }
    }
</script>

<div {id} style="position: relative; height: 100%; width: 100%;" bind:this={container}>
    <div class="transmitter {schemas.join(' ')}" {...$$restProps} style={dragging ? "" : "visibility: hidden;"} />

    {#if dragging}
        <svg xmlns="http://www.w3.org/2000/svg" style="overflow: visible; position: absolute; top: calc(100% - 1.5em); left: calc(100% - 1em); z-index: 3; pointer-events: none;">
            <path d="M {0} {0} C {controlOffset} {0}, {handleX - controlOffset} {handleY}, {handleX} {handleY}" class="connection {schemas.join(' ')}" stroke-width="4" fill="none" style="pointer-events: auto;" />
        </svg>
    {/if}

    {#each connectionDisplayData as connection}
        <svg xmlns="http://www.w3.org/2000/svg" style="overflow: visible; position: absolute; top: calc(100% - 1.5em); left: calc(100% - 1em); z-index: 3; pointer-events: none;">
            <path d="M {0} {0} C {connection.offset} {0}, {connection.x - connection.offset} {connection.y}, {connection.x} {connection.y}" class="connection {schemas.join(' ')}" stroke-width="4" fill="none" style="pointer-events: auto;" />
            <path d="M {0} {0} C {connection.offset} {0}, {connection.x - connection.offset} {connection.y}, {connection.x} {connection.y}" class="connection-selector" stroke-width="10" fill="none" style="pointer-events: auto;" on:mousedown={(event) => {if (event.button===1) {onPathClick(connection.id)}}} />
        </svg>
    {/each}

    <DragHandle {onDragStart} {onDrag} {onDragEnd} {getOffset} style={dragging ? dragHandleStyle : ""}>
        <div class="transmitter {schemas.join(' ')}" {...$$restProps} style={dragging ? "visibility: hidden;" : ""}>
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
        z-index: 100;
    }

    .transmitter.any {
        background-color: var(--wire-any);
    }

    .transmitter.command {
        background-color: var(--wire-command);
    }

    .connection {
        stroke: red;
        z-index: -10;
    }

    .connection.any {
        stroke: var(--wire-any);
    }

    .connection.command {
        stroke: var(--wire-command);
    }

    .connection-selector {
        stroke: transparent;
    }

    .connection-selector:hover {
        stroke: #FFF5;
    }
</style>