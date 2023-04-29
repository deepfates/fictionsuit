<script lang="ts">
    import Blue from "./blue.svelte";
    import Green from "./green.svelte";
    import Red from "./red.svelte";

    export let Color: "red" | "green" | "blue" = "red";

    let elementByColor: { [key: string]: any } = {
        "red": Red,
        "green": Green,
        "blue": Blue
    };
</script>

<svelte:component this={elementByColor[Color]} />
