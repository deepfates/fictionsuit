<script>
    /**
     * @type string value
     */
    export let value;
</script>

<div class=display-container>
    <pre class=display>{value}</pre>
</div>

<style>
    .display-container {
        margin: 0;
        padding: 0;

        position: relative;
        width: 100%;
        height: 100%;
        background-color: var(--ficscript-editor-background);
    }

    .display {
        position: absolute;
        padding: 0;
        margin: 0;
        top: 10px;
        left: 10px;
        width: calc(100% - 20px);
        height: calc(100% - 20px);
        color: white;
        font: 1em monospace;
        word-wrap: break-word;
        overflow: auto;
        white-space: pre-wrap;


        color: var(--ficscript-string);
        font-style: italic;
    }

    /* Identical to scrollbar styling of script_input.svelte. consider extracting to site.css */
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