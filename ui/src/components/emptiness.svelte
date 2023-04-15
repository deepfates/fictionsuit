<script lang="ts">
    import Workspace from "./workspace.svelte";
    import PaneRow from "./pane_row.svelte";
    import PaneColumn from "./pane_column.svelte";
    import feather from "feather-icons";
    import { onMount } from "svelte";
    import { tick } from "svelte";

    function onMenuOpen(event: MouseEvent) {
        if (event.button !== 2) return;

        showMenu = true;
        menuX = event.offsetX;
        menuY = event.offsetY;
        event.stopPropagation();
        event.preventDefault();
    }

    function addWorkspace() {
        let workspace = new Workspace({
            target: emptiness.parentElement!,
            props: {
            }
        });

        emptiness.parentNode?.removeChild(emptiness);
        showMenu = false;
    }

    function addRow() {
        let row = new PaneRow({
            target: emptiness.parentElement!,
            props: {
                leftPercent: 50,
                rightPercent: 50
            }
        });

        emptiness.parentNode?.removeChild(emptiness);
        showMenu = false;
    }

    function addColumn() {
        let row = new PaneColumn({
        target: emptiness.parentElement!,
        props: {
            topPercent: 50,
            bottomPercent: 50
        }
    });

    emptiness.parentNode?.removeChild(emptiness);
    showMenu = false;
}

    let emptiness: HTMLDivElement;

    let showMenu = false;

    let menuX = 0, menuY = 0;

    $: {
        if (showMenu) {
            tick().then(() => {
                feather.replace();
            });
        }
    }
</script>

<div class=emptiness
    bind:this={emptiness}>
    <div class=backdrop
        on:contextmenu={onMenuOpen}
        on:mousedown={() => {showMenu = false;}} />
    <div class=nothing>
        nothing
    </div>
    {#if showMenu}
        <div class=menu-container
            style="left: {menuX - 100}px; top: {menuY - 100}px;">
            <button on:click={addWorkspace} class="menu-button center">
                <div data-feather=maximize style="" />
            </button>
            <button on:click={addRow} class="menu-button right">
                <div data-feather=columns style="transform: rotate(-45deg);" />
            </button>
            <button on:click={addRow} class="menu-button left">
                <div data-feather=sidebar style="transform: translate(-50%, -50%) rotate(-45deg) translate(15%, 0%); position: absolute;" />
                <div data-feather=sidebar style="transform: translate(-50%, -50%) rotate(135deg) translate(-15%, 0%); position: absolute;" />
            </button>
            <button on:click={addColumn} class="menu-button top">Column</button>
        </div>
    {/if}
</div>

<style>
    .emptiness {
        position: relative;
        width: 100%;
        height: 100%;
        z-index: 0;
    }

    .backdrop {
        position: absolute;
        width: 100%;
        height: 100%;
        background-color: var(--pane-backdrop);
        z-index: 0;
    }

    .nothing {
        position: absolute;
        top: calc(50% - 0.35em);
        left: 50%;
        transform: translate(-50%, -50%);
        white-space: pre;
        
        user-select: none;
        pointer-events: none;
        
        color: #446666;
        font: 0.9rem monospace;
    }

    .menu-container {
        position: absolute;
        width: 200px;
        height: 200px;
        border-radius: 50%;
        z-index: 20;
        overflow: hidden;
    }

    .menu-button {
        position: absolute;
        width: 100px;
        height: 100px;
        border: 0;
        color: white;
        background-color: transparent;
        font: 1em monospace;
        z-index: 21;
    }

    .menu-button.center {
        top: 50%;
        left: 50%;
        border-radius: 50%;
        transform: translate(-50%, -50%);
        background-color: rgba(255, 255, 255, 0.2);
        z-index: 23;
    }

    .menu-button.top {
        top: -25%;
        left: 50%;
        z-index: 22;
    }

    .menu-button.right {
        top: 0%;
        left: 50%;
        transform-origin: bottom left;
        transform: rotate(45deg) skewY(0deg);
        overflow: hidden;
        display: block;
    }

    .menu-button.right::before {
        content: "";
        position: absolute;
        bottom: -50%;
        left: -50%;
        width: 103%;
        height: 103%;
        border-radius: 100%;
        box-shadow: 0px 0px 0px 1000px rgba(255, 255, 255, 0.2);
        z-index: -1;
    }

    .menu-button.right:hover::before {
        box-shadow: 0px 0px 0px 1000px rgba(255, 255, 255, 0.4);
    }

    .menu-button.left {
        top: 0%;
        left: 50%;
        transform-origin: bottom left;
        transform: rotate(225deg);
        overflow: hidden;
        display: block;
    }

    .menu-button.left::before {
        content: "";
        position: absolute;
        bottom: -50%;
        left: -50%;
        width: 103%;
        height: 103%;
        border-radius: 100%;
        box-shadow: 0px 0px 0px 1000px rgba(255, 255, 255, 0.2);
        z-index: -1;
    }

    .menu-button.left:hover::before {
        box-shadow: 0px 0px 0px 1000px rgba(255, 255, 255, 0.4);
    }

    .menu-button.center:hover {
        background-color: rgba(255, 255, 255, 0.4);
        border: 0;
    }
</style>