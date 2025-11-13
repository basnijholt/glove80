from __future__ import annotations

import asyncio

from textual.widgets import Button, Input

from glove80.tui.app import Glove80TuiApp
from glove80.tui.messages import StoreUpdated
from glove80.tui.widgets.inspector import HoldTapTab


def test_hold_tap_tab_create_rename_delete() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            hold_tab = pilot.app.screen.query_one("#holdtap-tab", HoldTapTab)

            name_input = hold_tab.query_one("#holdtap-name-input", Input)
            bindings_input = hold_tab.query_one("#holdtap-bindings-input", Input)
            tapping_input = hold_tab.query_one("#holdtap-tapping-input", Input)

            name_input.value = "&hold_test"
            bindings_input.value = '["&kp","A"]'
            tapping_input.value = "175"
            hold_tab.query_one("#holdtap-add", Button).press()
            await pilot.pause()

            assert any(ht["name"] == "&hold_test" for ht in pilot.app.store.list_hold_taps())

            pilot.app.store.set_selection(layer_index=0, key_index=0)
            pilot.app.store.update_selected_key(value="&hold_test", params=[])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            name_input.value = "&hold_renamed"
            hold_tab.query_one("#holdtap-apply", Button).press()
            await pilot.pause()

            assert any(ht["name"] == "&hold_renamed" for ht in pilot.app.store.list_hold_taps())
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&hold_renamed"

            # Delete while referenced should be blocked
            hold_tab.query_one("#holdtap-delete", Button).press()
            await pilot.pause()
            assert any(ht["name"] == "&hold_renamed" for ht in pilot.app.store.list_hold_taps())

            pilot.app.store.set_selection(layer_index=0, key_index=0)
            pilot.app.store.update_selected_key(value="&kp", params=["TAB"])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            refs = pilot.app.store.find_hold_tap_references("&hold_renamed")
            assert not any(refs.values())
            hold_tab._load_hold_tap(pilot.app.store.list_hold_taps()[0])

            hold_tab.query_one("#holdtap-delete", Button).press()
            await pilot.pause()
            assert all(ht["name"] != "&hold_renamed" for ht in pilot.app.store.list_hold_taps())

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert any(ht["name"] == "&hold_renamed" for ht in pilot.app.store.list_hold_taps())

    asyncio.run(_run())
