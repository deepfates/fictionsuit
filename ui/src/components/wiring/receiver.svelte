<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { receivers } from "../../wiring";

    export let schemas: string[] = ["any"];

    export let onReceive: (message: Message) => void = m => { console.log(`Received message with schema ${m.schema}.`); };

    let id: string = "RECEIVER-" + crypto.randomUUID();

    let element: HTMLDivElement;

    onMount(() => {
        receivers[id] = { "signal": onReceive, "element": element, "schemas": schemas, "id": id };
    });

    onDestroy(() => {
        delete receivers[id];
    });
</script>

<div bind:this={element} class=container {...$$restProps}>
    <div {id} class=dish>
        <div class="receiver {schemas.join(' ')}" />
    </div>
</div>

<style>
    .container {
        background-color: blue;
        position: absolute;
        top: 1em;
        left: 0.5em;
        height: 1em;
        width: 1em;
        border-radius: 50%;
        z-index: 3;
    }

    .dish {
        background-color: transparent;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 3em;
        height: 3em;
        border-radius: 50%;
    }

    .receiver {
        background-color: blue;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 1em;
        height: 1em;
        border-radius: 50%;
        cursor: pointer;
        z-index: 100;
    }

    .receiver.any {
        background-color: var(--wire-any);
    }

    .receiver.command {
        background-color: var(--wire-command);
    }
</style>