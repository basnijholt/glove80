from __future__ import annotations

import asyncio

from textual.pilot import Pilot

from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets.layer_sidebar import LayerSidebar


def test_sidebar_rename_updates_store():
    payload = {
        "layer_names": ["Base", "Lower", "Raise"],
        "layers": [
            [{"value": "&kp A", "params": []} for _ in range(80)],
            [{"value": "&kp B", "params": []} for _ in range(80)],
            [{"value": "&kp C", "params": []} for _ in range(80)],
        ],
        "combos": [
            {
                "name": "combo_1",
                "binding": {"value": "&mo", "params": [{"name": "Lower"}]},
                "keyPositions": [0, 1],
                "layers": [{"name": "Base"}],
            }
        ],
        "inputListeners": [],
    }

    async def _run() -> None:
        app = Glove80TuiApp(payload=payload)
        async with app.run_test() as pilot:  # type: Pilot
            sidebar = pilot.app.screen.query_one(LayerSidebar)
            await pilot.pause()
            sidebar.index = 0
            sidebar.rename_selected_for_test("Main")
            await pilot.pause()

            assert pilot.app.store.layer_names[0] == "Main"
            assert pilot.app.store.state.combos[0]["layers"] == [{"name": "Main"}]

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert pilot.app.store.layer_names[0] == "Base"

    asyncio.run(_run())
