<!-- Renderer for markdown code blocks -->

<script lang="ts">
    import ScriptDisplay from "../script_display.svelte";

    export let lang: string = "";
    export let text: string = "";

    let script: Script = {
        schema: "script",
        code: text,
        language: lang,
        source_file: ""
    };

    $: {
        script = {
            schema: "script",
            code: text,
            language: lang,
            source_file: ""
        };
    }
</script>

<ScriptDisplay message={script} />
