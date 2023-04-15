<script context="module">
    let last_user = 0;
</script>

<script>
    import { onMount } from "svelte";
    import StringDisplay from "./displays/string_display.svelte";
    import ScriptInput from "./inputs/script_input.svelte";
    import PaneColumn from "./pane_column.svelte";
    import Red from "./debug/red.svelte";

    let command = "";
    let last_command = "help";
    let result = "";

    last_user++;
    let session_name = `user_${last_user}`;

    onMount(async () => {
        let response = await fetch("http://localhost:8000/fic", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                request_text: last_command,
                user_name: session_name
            })
        });

        let json = await response.json();

        if (json.string !== undefined) {
            result = json.string;
        }
    });

    /**
     * @param {string} command
     */
    function onSubmit(command) {
        result = "[processing]";
        last_command = command;
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
            .then(response => response.json())
            .then(json => {
                if (json.string !== undefined) {
                    result = json.string;
                    return;
                }
                if (json.error !== undefined) {
                    result = "Error: " + json.error;
                    return;
                }
                if (json.object !== undefined) {
                    result = json.object;
                    return;
                }
                console.log(json);
            });
    }
</script>

<PaneColumn topPercent={20} middlePercent={10} bottomPercent={68}>
    <ScriptInput slot=top bind:code={command} onSubmit={onSubmit} />
    <StringDisplay slot=middle value="> {last_command}"/>
    <StringDisplay slot=bottom value={result} />
</PaneColumn>