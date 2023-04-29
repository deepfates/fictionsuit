<script context="module">
    let last_user = 0;
</script>

<script lang="ts">
    import { onMount, tick } from "svelte";
    import ScriptInput from "./nodes/inputs/script_input.svelte";
    import PaneColumn from "./layout/pane_column.svelte";
    import MessageDisplay from "./displays/message_display.svelte";

    let nextCommand = "";

    let messages: Message[] = [];

    let innerContainer: HTMLDivElement;
    let scrollZone: HTMLDivElement;

    let scrollToBottom: boolean = true;

    last_user++;
    let session_name = `user_${last_user}`;

    onMount(async () => {
        onSubmit("motd", true);
    });

    function onSubmit(command: string, hide_command: boolean = false) {
        scrollToBottom = scrollZone.clientHeight + scrollZone.scrollTop === scrollZone.scrollHeight;
        if (!hide_command) {
            messages.push({ schema: "command", command: command });
            messages = messages;
            tick().then(() => {
                if (scrollToBottom) {
                    scrollZone.scrollTop = innerContainer.clientHeight - scrollZone.clientHeight;
                }
            });
        }
        fetch("http://localhost:8000/fic",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    request_text: command,
                    user_name: session_name
                })
            })
            .then(async response => {
                messages.push(await response.json());
            })
            .catch(error => {
                messages.push({ schema: "failure", explanation: "In ficsuit_session.svelte: " + error})
            })
            .finally(() => {
                messages = messages;
                tick().then(() => {
                    if (scrollToBottom) {
                        scrollZone.scrollTop = innerContainer.clientHeight - scrollZone.clientHeight;
                    }
                });
            });
    }
</script>

<PaneColumn topPercent={80} bottomPercent={20}>
    <div class=outer-container slot=top>
        <div class=scroll-zone bind:this={scrollZone}>
            <div class=inner-container bind:this={innerContainer}>
                {#each messages as message}
                    <MessageDisplay {message} />
                {/each}
            </div>
        </div>
    </div>
    <ScriptInput slot=bottom bind:code={nextCommand} onSubmit={onSubmit} />
</PaneColumn>

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

    .inner-container {
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