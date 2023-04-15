<script>
    import { onMount } from "svelte";
    import FloatingPane from "../components/floating_pane.svelte";
    import ScriptInput from "../components/inputs/script_input.svelte";
    import Workspace from "../components/workspace.svelte";
    import StringDisplay from "../components/displays/string_display.svelte";
    import Red from "../components/debug/red.svelte";
    import Blue from "../components/debug/blue.svelte";
    import PaneRow from "../components/pane_row.svelte";
    import PaneColumn from "../components/pane_column.svelte";
    import FicsuitSession from "../components/ficsuit_session.svelte";
    import Emptiness from "../components/emptiness.svelte";

    let test_code = `# Comment
. a := lorem ipsum dolor sit amet
. b = scope
. b . c = <foo++>
<chat> asdf
<user @ asdf> test 1 2 3
<temp @ asdf> 1.2
<system @ asdf> hello world
<assistant @ asdf> sorry but as an AI Language Model I am not allowed to do anything
`;


</script>

<div style="position: absolute; width: 100%; height: 100%;">
    <Emptiness />
</div>

<!--
<Workspace>


        <PaneRow leftPercent={30} rightPercent={70}>
            <FicsuitSession slot=left/>
            <Workspace slot=right>
                <FloatingPane title="Script 2" width={750} height={500} x=10px y=10px>
                    <ScriptInput code={test_code} />
                </FloatingPane>
                
                <FloatingPane title="Session" width={500} height={500}>
                    <FicsuitSession />
                </FloatingPane>
            </Workspace>
        </PaneRow>
    </Workspace>
-->
