from __future__ import annotations

import asyncio
import copy

from textual.geometry import Offset

from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets import KeyCanvas, LayerStrip


def _layer_with_label(label: str) -> list[dict[str, object]]:
    slot = {"value": "&kp", "params": [{"value": label, "params": []}]}
    return [copy.deepcopy(slot) for _ in range(80)]


def test_layer_strip_click_refreshes_canvas() -> None:
    payload = {
        "layer_names": ["Base", "Lower"],
        "layers": [
            _layer_with_label("BASE"),
            _layer_with_label("LOWR"),
        ],
        "macros": [],
        "holdTaps": [],
        "combos": [],
        "inputListeners": [],
    }

    async def _run() -> None:
        app = Glove80TuiApp(payload=payload)
        async with app.run_test() as pilot:
            await pilot.pause()
            canvas = pilot.app.screen.query_one(KeyCanvas)
            layer_strip = pilot.app.screen.query_one(LayerStrip)

            assert canvas.cap_lines_for_test(0)[0] == "BASE"

            layer_strip.render()
            lower_segment = next(seg for seg in layer_strip._segments if seg.index == 1)

            class _FakeMouseUp:
                def __init__(self, x: int) -> None:
                    self.button = 1
                    self._offset = Offset(x, 0)

                def get_content_offset(self, _widget):
                    return self._offset

            layer_strip.on_mouse_up(_FakeMouseUp(lower_segment.start + 1))
            await pilot.pause()

            assert pilot.app.store.selected_layer_name == "Lower"
            assert canvas.cap_lines_for_test(0)[0] == "LOWR"

    asyncio.run(_run())
