<script lang="ts">
    import { onMount } from "svelte";
    import TextDisplay from "./basic/text_display.svelte";
    import FailureDisplay from "./basic/failure_display.svelte";
    import ScriptDisplay from "./basic/script_display.svelte";
    import OtherDisplay from "./basic/other_display.svelte";
    import NothingDisplay from "./basic/nothing_display.svelte";

    export let message: Message = { schema: "nothing" };
    export let height: string | null = null;

    export let context = "command_response";

    const displays: {[key: string]: any} = {
        "text": TextDisplay,
        "script": ScriptDisplay,
        "command": ScriptDisplay,
        "failure": FailureDisplay,
        "other": OtherDisplay,
        "nothing": NothingDisplay
    }

    let props = {
        message: message,
        context: context
    }

    let component: any = null;

    onMount(() => {
        component = displays[message.schema];
        props = {
            message: message,
            context: context
        }
    });

    $: {
        if (message !== undefined) {
            component = displays[message.schema];
            props = {
                message: message,
                context: context
            }
        }
    }

    let commandStyle = "";

    $: {
        if (height !== null) {
            commandStyle = `height: ${height};`;
        }
    }

</script>

<div class=command style={commandStyle}>
    <svelte:component this={component} {...props} />
</div>


<style>
    .command {
        position: relative;
        border: 2px solid var(--pane-divider);
        width: calc(100% - 0.5em - 4px);
        margin-bottom: 0.25em;
        border-radius: 0.5em;
        overflow: hidden;
        color: red;
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