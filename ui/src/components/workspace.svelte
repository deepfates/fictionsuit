<!-- A big empty canvas, with a dotted grid background. -->

<script>
    import FloatingPane from "./floating_pane.svelte";
    import PaneRow from "./pane_row.svelte";

    /**
     * @param {MouseEvent} event
     */
    function onMenuOpen(event) {
        if (event.button !== 2) return;

        showMenu = true;
        menuX = event.offsetX;
        menuY = event.offsetY;
        event.stopPropagation();
        event.preventDefault();
    }

    function addPane() {
        let pane = new FloatingPane({
            target: workspace,
            props: {
                title: "Menu",
                x: `${menuX}px`,
                y: `${menuY}px`
            }
        });

        showMenu = false;
    }

    function addRow() {
        let row = new PaneRow({
            target: workspace,
            props: {
                leftPercent: 50,
                rightPercent: 50
            }
        });

        showMenu = false;
    }

    /**
     * @type {HTMLDivElement}
     */
    let workspace;

    let showMenu = false;

    let menuX = 0, menuY = 0;
</script>

<div class=workspace
    bind:this={workspace}>
    <div class=backdrop 
        on:contextmenu={onMenuOpen}
        on:mousedown={() => {showMenu = false;}} />
    <slot></slot>
    {#if showMenu}
        <div class=menu-container style="left: {menuX - 100}px; top: {menuY - 100}px;">
            <button on:click={addPane} class=menu-center>Pane</button>
            <button on:click={addRow} class=menu-right>Row</button>
        </div>
    {/if}
</div>

<style>
    .workspace {
        margin: 0;
        border: 1px solid var(--pane-header);
        border-top: none;
        padding: 0;
        overflow: hidden;

        position: absolute;
        top: 0;
        left: 0;
        width: calc(100% - 2px);
        height: calc(100% - 1px);
    }

    .backdrop {
        position: absolute;
        width: 100%;
        height: 100%;
        
        background-size: 40px 40px;
        background-color: var(--workspace-background);
        background-image: radial-gradient(circle, var(--workspace-grid) 2px, rgba(0, 0, 0, 0) 1px);

        z-index: 0;
    }

    .menu-container {
        position: absolute;
        width: 200px;
        height: 200px;
        border-radius: 50%;
        z-index: 20;
        background-color: red;
    }

    .menu-center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100px;
        height: 100px;
        border: 0;
        border-radius: 50%;
        background-color: transparent;
        font: 1em monospace;
        z-index: 21;
    }

    .menu-center:hover {
        background-color: blue;
        border: 0;
    }
</style>