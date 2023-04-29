<script lang="ts">
    import Receiver from "../wiring/receiver.svelte";
    import MessageDisplay from "../displays/message_display.svelte";

    let messages: Message[] = [];

    let innerContainer: HTMLDivElement;
    let scrollZone: HTMLDivElement;

    function onReceive(m: Message) {
        messages.push(m);
        messages = messages;
    }
</script>


<div class="outer-container">
    <Receiver {onReceive} />
    <div class=inner-container>
        <div class=scroll-zone bind:this={scrollZone}>
            <div class=innest-container bind:this={innerContainer}>
                {#each messages as message}
                    <MessageDisplay {message} />
                {/each}
            </div>
        </div>
    </div>
    <!--<Transmitter bind:this={transmitter} />-->
</div>


<style>
    .outer-container {
        position: absolute;
        margin: 0;
        padding: 0;
        border: 0;
        width: 100%;
        height: 100%;
        background-color: var(--pane-backdrop);
    }

    .inner-container {
        position: absolute;
        margin: 0;
        padding: 0;
        border: 0;
        top: 0.5em;
        left: 2em;
        width: calc(100% - 3em - 4px);
        height: calc(100% - 1em);
        background-color: var(--pane-backdrop);
    }

    .scroll-zone {
        position: absolute;
        width: calc(100% - 1.5em);
        height: calc(100% - 2em);
        scroll-snap-type: y mandatory;
        scroll-snap-align: end;
        left: 1em;
        top: 1em;
        overflow-y: auto;
    }

    .innest-container {
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        min-height: 100%;
    }

    ::-webkit-scrollbar {
        width: 10px;
        position: absolute;
        right: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #344;
        cursor: pointer !important;
    }

    ::-webkit-scrollbar-thumb {
        background: #788;
        cursor: pointer !important;
    }

    ::-webkit-scrollbar-track:hover, ::-webkit-scrollbar-thumb:hover {
        cursor: pointer !important;
        user-select: none;
    }
</style>