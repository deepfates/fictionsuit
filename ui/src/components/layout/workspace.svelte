<!-- A big empty canvas, with a dotted grid background. -->

<script lang="ts">
    import feather from "feather-icons";
    import FloatingPane from "./floating_pane.svelte";
    import PaneRow from "./pane_row.svelte";
    import RadialMenu from "../general/radial_menu.svelte";
    import { tick } from "svelte";
    import PaneColumn from "./pane_column.svelte";
    import Emptiness from "./emptiness.svelte";
    import FicsuitSession from "../ficsuit_session.svelte";
    import SimpleMenu from "../general/simple_menu.svelte";
    import Workspace from "./workspace.svelte";
    import Display from "../nodes/display.svelte";

    let hiddenElement: HTMLElement;

    function onMenuOpen(event: MouseEvent) {
        if (event.button !== 2) return;

        showLayoutMenu = false;
        showCreateMenu = false;

        if (event.shiftKey) {
            showLayoutMenu = true;
        }
        else {
            showCreateMenu = true;
        }
        menuX = event.offsetX;
        menuY = event.offsetY;
        event.stopPropagation();
        event.preventDefault();
    }

    function addPane() {
        let pane = new FloatingPane({
            target: workspace,
            props: {
                title: "",
                x: `${menuX}px`,
                y: `${menuY}px`
            }
        });

        showLayoutMenu = false;
        showCreateMenu = false;
    }

    function addDisplay() {
        let display = new Display({
            target: hiddenElement,
            props: {

            }
        });

        let pane = new FloatingPane({
            target: workspace,
            props: {
                title: "Display",
                x: `${menuX}px`,
                y: `${menuY}px`,
                content: hiddenElement.children[0] as HTMLElement
            }
        });

        showCreateMenu = false;
    }

    function addSession() {
        let session = new FicsuitSession({
            target: hiddenElement,
            props: {

            }
        });

        let pane = new FloatingPane({
            target: workspace,
            props: {
                title: "FictionSuit Session",
                x: `${menuX}px`,
                y: `${menuY}px`,
                width: 400,
                height: 500,
                content: hiddenElement.children[0] as HTMLElement
            }
        });

        showCreateMenu = false;
    }

    function addWorkspace() {
        let session = new Workspace({
            target: hiddenElement,
            props: {

            }
        });

        let pane = new FloatingPane({
            target: workspace,
            props: {
                title: "Workspace",
                x: `${menuX}px`,
                y: `${menuY}px`,
                content: hiddenElement.children[0] as HTMLElement
            }
        });

        showCreateMenu = false;
    }

    function addRight() {
        let parent = workspace.parentElement!;
        parent.removeChild(workspace);
        let row = new PaneRow({
            target: parent,
            props: {
                leftPercent: 50,
                rightPercent: 50,
                leftInit: workspace
            }
        });

        showLayoutMenu = false;
    }

    function addLeft() {
        let parent = workspace.parentElement!;
        parent.removeChild(workspace);
        let row = new PaneRow({
            target: parent,
            props: {
                leftPercent: 50,
                rightPercent: 50,
                rightInit: workspace
            }
        });

        showLayoutMenu = false;
    }

    function addTop() {
        let parent = workspace.parentElement!;
        parent.removeChild(workspace);
        let row = new PaneColumn({
            target: parent,
            props: {
                topPercent: 50,
                bottomPercent: 50,
                bottomInit: workspace
            }
        });

        showLayoutMenu = false;
    }

    function addBottom() {
        let parent = workspace.parentElement!;
        parent.removeChild(workspace);
        let row = new PaneColumn({
            target: parent,
            props: {
                topPercent: 50,
                bottomPercent: 50,
                topInit: workspace
            }
        });

        showLayoutMenu = false;
    }

    function remove() {
        let parent = workspace.parentElement!;
        parent.removeChild(workspace);
        let emptiness = new Emptiness({
            target: parent,
            props: {
            }
        });
    }

    let createMenuOptions = [
        { label: "FictionSuit Session", action: addSession },
        { label: "Workspace", action: addWorkspace },
        { label: "Empty Pane", action: addPane },
        { label: "Display", action: addDisplay },
    ]

    let workspace: HTMLDivElement;

    let showLayoutMenu = false;
    let showCreateMenu = false;

    let menuX = 0, menuY = 0;

    $: {
        if (showLayoutMenu) {
            tick().then(() => {
                feather.replace();
            });
        }
    }

    let id: string = "WORKSPACE-" + crypto.randomUUID();
</script>

<div class=workspace {id}
    bind:this={workspace}>
    <div class=backdrop 
        on:contextmenu={onMenuOpen}
        on:mousedown={() => {showLayoutMenu = false; showCreateMenu = false;}}
        data-panedrop={() => console.log('asdf')} />
    <slot></slot>
    {#if showLayoutMenu}
        <RadialMenu xPosition={menuX} yPosition={menuY}
            color=white
            background="#1b575760"
            background_hover="#1b5757A0"
            center={addPane}
            right={addRight}
            left={addLeft}
            top={addTop}
            bottom={addBottom}>
            <div slot="center" data-feather="credit-card" class="icon center" />
            <div slot="right" data-feather="plus" class="icon split-pane" />
            <div slot="left" data-feather="plus" class="icon split-pane" />
            <div slot="top" data-feather="plus" class="icon split-pane" />
            <div slot="bottom" data-feather="plus" class="icon split-pane" />
        </RadialMenu>
        <button class=delete on:click={remove}
            style="left: {menuX + 100}px; top: {menuY - 100}px;">
            <div data-feather="trash" class="trash-icon" />
        </button>
    {/if}
    {#if showCreateMenu}
        <SimpleMenu x={menuX} y={menuY}
            title="New"
            options={createMenuOptions} />
    {/if}

    <div class=hidden bind:this={hiddenElement} />
</div>

<style>
    .workspace {
        margin: 0;
        border: 1px solid var(--pane-header);
        border-top: none;
        padding: 0;

        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }

    .hidden {
        display: none;
    }

    .icon {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }

    .icon.center {
        transform: translate(-50%, -50%) scale(2);
    }

    .icon.split-pane {
        transform: translate(-50%, -50%) rotate(45deg) translate(0, -15%) scale(1.3);
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

    .delete {
        position: absolute;
        border: 0;
        padding: 0;
        margin: 0;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        z-index: 20;
        background-color: #FF000060;
        transform: translate(-50%, -50%);
    }

    .delete > .trash-icon {
        color: white;
    }

    .delete:hover {
        background-color: #FF0000EE;
    }
</style>