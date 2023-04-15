<!-- This wraps any element (or a group of elements), turning it into a handle for drag-and-drop operations. See floating_pane.svelte for usage examples. -->

<script>
    /**
     * @type {(arg0: number | string | null, arg1: number | string | null) => void}
     */
    export let onDrag;
    /**
     * @type {() => {x: number, y: number}}
     */
    export let getOffset;

    export let xEnabled = true;
    export let yEnabled = true;

    let drag_offset_x = 0;
    let drag_offset_y = 0;

    /**
     * @param {MouseEvent} event
     */
    function dragHandleMouseDown(event) {
        if (event.button !== 0) return; // Only left-clicks
        event.preventDefault()

        let offset = getOffset();
        drag_offset_x = event.clientX - offset.x;
        drag_offset_y = event.clientY - offset.y;

        document.addEventListener("mousemove", dragHandleMove);
        document.addEventListener("mouseup", dragHandleMouseUp);
    }

    /**
     * @param {MouseEvent} event
     */
    function dragHandleMove(event) {
        let x = event.clientX - drag_offset_x;
        let y = event.clientY - drag_offset_y;
        onDrag(xEnabled ? x : null, yEnabled ? y : null);
    }

    /**
     * @param {MouseEvent} event
     */
    function dragHandleMouseUp(event) {
        document.removeEventListener("mouseup", dragHandleMouseUp);
        document.removeEventListener("mousemove", dragHandleMove);
    }

</script>

<div on:mousedown={dragHandleMouseDown}>
    <slot/>
</div>
