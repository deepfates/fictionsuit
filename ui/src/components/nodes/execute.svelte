<script lang="ts">
    import Receiver from "../wiring/receiver.svelte";
    import Transmitter from "../wiring/transmitter.svelte";

    let transmitter: Transmitter;

    function onReceive(message: Message) {
        if (message.schema !== "command") {
            transmitter.send({ schema: "failure", explanation: `Expected command, got ${message.schema}.` });
            return;
        }

        fetch("http://localhost:8000/fic",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    request_text: message.command,
                    user_name: "fic_api_node"
                })
            })
            .then(async response => {
                transmitter.send(await response.json());
            })
            .catch(error => {
                transmitter.send({ schema: "failure", explanation: "In ficsuit_session.svelte: " + error})
            });
    }
</script>


<div class="outer-container">
    <Receiver schemas={["command"]} {onReceive} />
    <div class="inner-container">
        <span>TODO: a field to let your choose the session id</span>
    </div>
    <Transmitter bind:this={transmitter} />
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
</style>