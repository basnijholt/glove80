from __future__ import annotations

import asyncio


from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets import InspectorOverlay
from glove80.tui.widgets.inspector import KeyInspector
from glove80.tui.widgets.key_canvas import KeyCanvas


def _sample_payload() -> dict[str, object]:
    slots_a = [{"value": "&kp", "params": [{"value": "A", "params": []}]} for _ in range(80)]
    slots_b = [{"value": "&kp", "params": [{"value": "B", "params": []}]} for _ in range(80)]
    return {
        "layer_names": ["Base", "Lower"],
        "layers": [slots_a, slots_b],
        "combos": [],
        "inputListeners": [],
    }


def test_key_canvas_moves_selection_and_focuses_inspector() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload())
        async with app.run_test() as pilot:  # type: Pilot
            canvas = pilot.app.screen.query_one(KeyCanvas)
            overlay = pilot.app.screen.query_one(InspectorOverlay)

            canvas.focus()
            await pilot.pause()
            canvas.action_move_right()
            canvas.action_move_down()
            await pilot.pause()

            assert pilot.app.store.selection.key_index == 17

            canvas.action_inspect()
            await pilot.pause()
            assert overlay.visible
            assert overlay.panel.key_inspector.value_input.has_focus

    asyncio.run(_run())


def test_edit_key_value_round_trip() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload())
        async with app.run_test() as pilot:
            inspector = pilot.app.screen.query_one(KeyInspector)
            await pilot.pause()

            inspector.apply_value_for_test("&kp", ["TAB"])
            await pilot.pause()
            slot = pilot.app.store.state.layers[0].slots[0]
            assert slot["value"] == "&kp"
            assert slot["params"] == [{"value": "TAB", "params": []}]

            await pilot.press("ctrl+z")
            await pilot.pause()
            slot = pilot.app.store.state.layers[0].slots[0]
            assert slot["value"] == "&kp"
            assert slot["params"] == [{"value": "A", "params": []}]

    asyncio.run(_run())


def test_layer_switch_shortcuts_wrap() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload())
        async with app.run_test() as pilot:
            canvas = pilot.app.screen.query_one(KeyCanvas)
            canvas.focus()
            await pilot.pause()

            assert pilot.app.store.selection.layer_index == 0

            canvas.action_next_layer()
            await pilot.pause()
            assert pilot.app.store.selection.layer_index == 1

            canvas.action_next_layer()
            await pilot.pause()
            assert pilot.app.store.selection.layer_index == 0

            canvas.action_prev_layer()
            await pilot.pause()
            assert pilot.app.store.selection.layer_index == 1

    asyncio.run(_run())


def test_copy_shortcut_copies_between_layers() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload())
        async with app.run_test() as pilot:
            canvas = pilot.app.screen.query_one(KeyCanvas)
            canvas.focus()
            await pilot.pause()

            # ensure Lower slot differs from Base
            assert pilot.app.store.state.layers[1].slots[0]["params"][0]["value"] == "B"

            # switch to Lower (records previous Base selection)
            canvas.action_next_layer()
            await pilot.pause()
            assert pilot.app.store.selection.layer_index == 1

            canvas.action_copy_key()
            await pilot.pause()

            slot = pilot.app.store.state.layers[1].slots[0]
            assert slot["params"][0]["value"] == "A"

            await pilot.press("ctrl+z")
            await pilot.pause()

            slot = pilot.app.store.state.layers[1].slots[0]
            assert slot["params"][0]["value"] == "B"

    asyncio.run(_run())
