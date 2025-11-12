from __future__ import annotations

import asyncio
import copy

from glove80.tui.app import Glove80TuiApp
from glove80.tui.state.store import DEFAULT_SAMPLE_LAYOUT
from glove80.tui.widgets import KeyCanvas


LONG_VALUE = "&macro_super_verbose_behavior_name"
LONG_PARAMS = [{"value": "ALPHA", "params": []}, {"value": "OMEGA", "params": []}]


def _payload_with_long_behavior() -> dict:
    payload = copy.deepcopy(DEFAULT_SAMPLE_LAYOUT)
    payload["layers"][0][0] = {"value": LONG_VALUE, "params": copy.deepcopy(LONG_PARAMS)}
    return payload


def test_key_canvas_truncates_and_reveals_detail() -> None:
    async def _run() -> None:
        payload = _payload_with_long_behavior()
        app = Glove80TuiApp(payload=payload)
        async with app.run_test() as pilot:
            canvas = pilot.app.screen.query_one(KeyCanvas)

            legend, _, _ = canvas.cap_lines_for_test(0)
            assert len(legend.strip()) <= KeyCanvas.MAX_LABEL_CHARS
            assert legend.strip().endswith("…")

            tooltip = canvas.tooltip_for_test(0)
            assert LONG_VALUE in tooltip
            assert "ALPHA" in tooltip and "OMEGA" in tooltip

            await pilot.click("#key-0")
            await pilot.pause()
            assert pilot.app.store.selection.key_index == 0

    asyncio.run(_run())


def test_key_canvas_keyboard_selection_updates_hud() -> None:
    async def _run() -> None:
        payload = _payload_with_long_behavior()
        app = Glove80TuiApp(payload=payload)
        async with app.run_test() as pilot:
            canvas = pilot.app.screen.query_one(KeyCanvas)
            canvas.focus()
            await pilot.pause()

            canvas.action_move_right()
            await pilot.pause()
            tooltip = canvas.tooltip_for_test(canvas.selected_index_for_test())
            assert LONG_VALUE not in tooltip

            canvas.action_move_left()
            await pilot.pause()
            tooltip = canvas.tooltip_for_test(canvas.selected_index_for_test())
            assert LONG_VALUE in tooltip
            assert "ALPHA" in tooltip and "OMEGA" in tooltip

    asyncio.run(_run())
