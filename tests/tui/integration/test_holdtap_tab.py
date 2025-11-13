from __future__ import annotations

import asyncio

from textual.widgets import Button, Input

from glove80.tui.app import Glove80TuiApp
from glove80.tui.messages import StoreUpdated
from glove80.tui.widgets.inspector import HoldTapTab


def test_holdtap_tab_create_rename_and_undo() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            holdtap_tab = pilot.app.screen.query_one("#holdtap-tab", HoldTapTab)

            name_input = holdtap_tab.query_one("#holdtap-name-input", Input)
            bindings_input = holdtap_tab.query_one("#holdtap-bindings-input", Input)
            tapping_input = holdtap_tab.query_one("#holdtap-tapping-input", Input)

            # Create hold tap
            name_input.value = "&hold_test"
            bindings_input.value = '["&kp","A"]'
            tapping_input.value = "175"
            holdtap_tab.query_one("#holdtap-add", Button).press()
            await pilot.pause()

            assert any(ht["name"] == "&hold_test" for ht in pilot.app.store.list_hold_taps())

            # Bind to key
            pilot.app.store.set_selection(layer_index=0, key_index=0)
            pilot.app.store.update_selected_key(value="&hold_test", params=[])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&hold_test"

            # Rename and verify ref updates
            name_input.value = "&hold_renamed"
            holdtap_tab.query_one("#holdtap-apply", Button).press()
            await pilot.pause()

            assert any(ht["name"] == "&hold_renamed" for ht in pilot.app.store.list_hold_taps())
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&hold_renamed"

            # Attempt delete while referenced (should block)
            holdtap_tab.query_one("#holdtap-delete", Button).press()
            await pilot.pause()
            assert any(ht["name"] == "&hold_renamed" for ht in pilot.app.store.list_hold_taps())

            # Unbind key
            pilot.app.store.set_selection(layer_index=0, key_index=0)
            pilot.app.store.update_selected_key(value="&kp", params=["TAB"])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            # Verify no references
            refs = pilot.app.store.find_hold_tap_references("&hold_renamed")
            assert not any(refs.values())

            # Reload hold tap and delete
            holdtap_tab._load_hold_tap(pilot.app.store.list_hold_taps()[0])
            holdtap_tab.query_one("#holdtap-delete", Button).press()
            await pilot.pause()
            assert all(ht["name"] != "&hold_renamed" for ht in pilot.app.store.list_hold_taps())

            # Undo delete
            await pilot.press("ctrl+z")
            await pilot.pause()
            assert any(ht["name"] == "&hold_renamed" for ht in pilot.app.store.list_hold_taps())

    asyncio.run(_run())
