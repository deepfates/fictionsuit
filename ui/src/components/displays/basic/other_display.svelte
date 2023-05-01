<script lang="ts">
    import ScriptDisplay from "./script_display.svelte";

    export let message: Other;

    let asJson: Script;

    $: {
        if (message !== undefined) {
            asJson = { "schema": "script", "language": "javascript", "code": message.description, "source_file": "" };
        }
    }
</script>

<ScriptDisplay message={asJson} />

<style>
    .display-container {
        display: block;
        position: relative;
        margin: 0;
        padding: 0;
        border: 0;
        width: 100%;
        padding-bottom: 1em;
        background-color: var(--code-editor-background);
    }

    .display {
        position: relative;
        padding: 0;
        margin: 0;
        top: 0.5em;
        left: 0.5em;
        width: calc(100% - 1em);
        word-wrap: break-word;
        overflow: auto;
        white-space: pre-wrap;

        color: var(--ficscript-string);
        font-style: italic;
    }

    /* Identical to scrollbar styling of script_input.svelte. consider extracting to site.css */
    ::-webkit-scrollbar {
        width: 0.5em;
        position: absolute;
        right: 0.5em;
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