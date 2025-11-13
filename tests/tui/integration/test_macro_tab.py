from __future__ import annotations

import asyncio

from textual.widgets import Button, Input

from glove80.tui.app import Glove80TuiApp
from glove80.tui.messages import StoreUpdated
from glove80.tui.widgets.inspector import MacroTab


def test_macro_tab_create_rename_and_undo() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            macro_tab = pilot.app.screen.query_one("#macro-tab", MacroTab)

            name_input = macro_tab.query_one("#macro-name-input", Input)
            bindings_input = macro_tab.query_one("#macro-bindings-input", Input)
            params_input = macro_tab.query_one("#macro-params-input", Input)

            name_input.value = "&macro_test"
            bindings_input.value = "[]"
            params_input.value = "[]"
            macro_tab.query_one("#macro-add", Button).press()
            await pilot.pause()

            assert any(macro["name"] == "&macro_test" for macro in pilot.app.store.list_macros())

            pilot.app.store.update_selected_key(value="&macro_test", params=[])
            pilot.app.post_message(StoreUpdated())
            await pilot.pause()

            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&macro_test"

            name_input.value = "&macro_renamed"
            macro_tab.query_one("#macro-apply", Button).press()
            await pilot.pause()

            assert any(macro["name"] == "&macro_renamed" for macro in pilot.app.store.list_macros())
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&macro_renamed"

            await pilot.press("ctrl+z")
            await pilot.pause()

            assert any(macro["name"] == "&macro_test" for macro in pilot.app.store.list_macros())
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&macro_test"

    asyncio.run(_run())
