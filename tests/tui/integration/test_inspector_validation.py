from __future__ import annotations

import asyncio


from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets.inspector import KeyInspector


def _sample_payload() -> dict[str, object]:
    slots = [{"value": "&kp", "params": [{"value": "A", "params": []}]} for _ in range(80)]
    return {
        "layer_names": ["Base"],
        "layers": [slots],
        "combos": [],
        "inputListeners": [],
    }


def test_key_inspector_validation_flow() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload())
        async with app.run_test() as pilot:  # type: Pilot
            inspector = pilot.app.screen.query_one(KeyInspector)
            await pilot.pause()

            inspector.apply_value_for_test("&unknown", [])
            await pilot.pause()

            slot = pilot.app.store.state.layers[0].slots[0]
            assert slot["params"][0]["value"] == "A"
            assert inspector.value_input.has_class("input-error")

            inspector.apply_value_for_test("&kp", ["TAB"])
            await pilot.pause()

            slot = pilot.app.store.state.layers[0].slots[0]
            assert slot["value"] == "&kp"
            assert slot["params"] == [{"value": "TAB", "params": []}]
            assert not inspector.value_input.has_class("input-error")

            await pilot.press("ctrl+z")
            await pilot.pause()

            slot = pilot.app.store.state.layers[0].slots[0]
            assert slot["params"] == [{"value": "A", "params": []}]

    asyncio.run(_run())
