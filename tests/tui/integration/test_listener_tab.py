from __future__ import annotations

import asyncio

from textual.widgets import Button, Input

from glove80.tui.app import Glove80TuiApp
from glove80.tui.messages import StoreUpdated
from glove80.tui.widgets.inspector import ListenerTab


def test_listener_tab_create_bind_rename_delete_with_undo() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            listener_tab = pilot.app.screen.query_one("#listener-tab", ListenerTab)

            code_input = listener_tab.query_one("#listener-code-input", Input)
            layers_input = listener_tab.query_one("#listener-layers-input", Input)
            processors_input = listener_tab.query_one("#listener-processors-input", Input)
            nodes_input = listener_tab.query_one("#listener-nodes-input", Input)

            # Create a listener
            code_input.value = "listener_test"
            layers_input.value = '["Base"]'
            processors_input.value = '[{"code": "&kp", "params": []}]'
            nodes_input.value = (
                '[{"code": "node_test", "layers": [0], "inputProcessors": [{"code": "&kp", "params": []}]}]'
            )

            listener_tab.query_one("#listener-add", Button).press()
            await pilot.pause()

            assert any(listener["code"] == "listener_test" for listener in pilot.app.store.list_listeners())

            # Wait for the listener to be selected
            for _ in range(5):
                if listener_tab._selected_code == "listener_test":
                    break
                await pilot.pause()

            assert listener_tab._selected_code == "listener_test"

            # Bind the listener to a key
            pilot.app.store.set_selection(layer_index=0, key_index=0)
            pilot.app.store.update_selected_key(value="listener_test", params=[])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            assert pilot.app.store.state.layers[0].slots[0]["value"] == "listener_test"
            assert listener_tab._selected_code == "listener_test"

            # Rename the listener and verify references update
            code_input.value = "listener_renamed"
            listener_tab.query_one("#listener-apply", Button).press()
            await pilot.pause()

            assert any(listener["code"] == "listener_renamed" for listener in pilot.app.store.list_listeners())
            assert all(listener["code"] != "listener_test" for listener in pilot.app.store.list_listeners())
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "listener_renamed"

            # Attempt to delete while referenced (should be blocked)
            listener_tab.query_one("#listener-delete", Button).press()
            await pilot.pause()
            assert any(listener["code"] == "listener_renamed" for listener in pilot.app.store.list_listeners())

            # Unbind the listener
            pilot.app.store.update_selected_key(value="&kp", params=["TAB"])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            # Verify no references
            refs = pilot.app.store.find_listener_references("listener_renamed")
            assert not any(refs.values())

            # Load the listener and delete it
            listener_tab._load_listener(pilot.app.store.list_listeners()[-1])
            listener_tab.query_one("#listener-delete", Button).press()
            await pilot.pause()

            assert all(listener["code"] != "listener_renamed" for listener in pilot.app.store.list_listeners())

            # Undo the delete
            await pilot.press("ctrl+z")
            await pilot.pause()
            assert any(listener["code"] == "listener_renamed" for listener in pilot.app.store.list_listeners())

    asyncio.run(_run())
