from __future__ import annotations

import asyncio

from textual.pilot import Pilot

from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets.inspector import KeyInspector
from glove80.tui.widgets.key_canvas import KeyCanvas


def _sample_payload() -> dict[str, object]:
    return {
        "layer_names": ["Base", "Lower"],
        "layers": [
            [{"value": "&kp A", "params": []} for _ in range(80)],
            [{"value": "&kp B", "params": []} for _ in range(80)],
        ],
        "combos": [],
        "inputListeners": [],
    }


def test_key_canvas_moves_selection_and_focuses_inspector() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload())
        async with app.run_test() as pilot:  # type: Pilot
            canvas = pilot.app.query_one(KeyCanvas)
            inspector = pilot.app.query_one(KeyInspector)

            canvas.focus()
            await pilot.pause()
            canvas.action_move_right()
            canvas.action_move_down()
            await pilot.pause()

            assert pilot.app.store.selection.key_index == 17

            canvas.action_inspect()
            await pilot.pause()
            assert inspector.value_input.has_focus

    asyncio.run(_run())


def test_edit_key_value_round_trip() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload())
        async with app.run_test() as pilot:
            inspector = pilot.app.query_one(KeyInspector)
            await pilot.pause()

            inspector.apply_value_for_test("&kp TAB", [])
            await pilot.pause()
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&kp TAB"

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert pilot.app.store.state.layers[0].slots[0]["value"] == "&kp A"

    asyncio.run(_run())
