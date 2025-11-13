from __future__ import annotations

import asyncio

from textual.widgets import Button, Input

from glove80.tui.app import Glove80TuiApp
from glove80.tui.messages import StoreUpdated
from glove80.tui.widgets.inspector import ComboTab


def test_combo_tab_create_bind_rename_delete_with_undo() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            combo_tab = pilot.app.screen.query_one("#combo-tab", ComboTab)

            name_input = combo_tab.query_one("#combo-name-input", Input)
            binding_input = combo_tab.query_one("#combo-binding-input", Input)
            positions_input = combo_tab.query_one("#combo-positions-input", Input)
            layers_input = combo_tab.query_one("#combo-layers-input", Input)
            timeout_input = combo_tab.query_one("#combo-timeout-input", Input)

            name_input.value = "&combo_test"
            binding_input.value = '{"value":"&kp","params":[{"value":"ESC","params":[]}]}'
            positions_input.value = "0, 1"
            layers_input.value = "Base"
            timeout_input.value = "75"

            combo_tab.query_one("#combo-add", Button).press()
            await pilot.pause()

            assert any(combo["name"] == "&combo_test" for combo in pilot.app.store.list_combos())

            for _ in range(5):
                if combo_tab._selected_name == "&combo_test":
                    break
                await pilot.pause()

            assert combo_tab._selected_name == "&combo_test"

            pilot.app.store.set_selection(layer_index=0, key_index=0)
            pilot.app.store.update_selected_key(value="&combo_test", params=[])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&combo_test"
            assert combo_tab._selected_name == "&combo_test"

            name_input.value = "&combo_renamed"
            combo_tab.query_one("#combo-apply", Button).press()
            await pilot.pause()

            assert any(combo["name"] == "&combo_renamed" for combo in pilot.app.store.list_combos())
            assert all(combo["name"] != "&combo_test" for combo in pilot.app.store.list_combos())
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&combo_renamed"

            combo_tab.query_one("#combo-delete", Button).press()
            await pilot.pause()
            assert any(combo["name"] == "&combo_renamed" for combo in pilot.app.store.list_combos())

            pilot.app.store.update_selected_key(value="&kp", params=["TAB"])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            refs = pilot.app.store.find_combo_references("&combo_renamed")
            assert not any(refs.values())

            combo_tab._load_combo(pilot.app.store.list_combos()[-1])
            combo_tab.query_one("#combo-delete", Button).press()
            await pilot.pause()

            assert all(combo["name"] != "&combo_renamed" for combo in pilot.app.store.list_combos())

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert any(combo["name"] == "&combo_renamed" for combo in pilot.app.store.list_combos())

    asyncio.run(_run())
