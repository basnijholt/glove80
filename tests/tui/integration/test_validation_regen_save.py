from __future__ import annotations

import asyncio
import json

from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets import FooterBar, KeyInspector, RegenPreviewModal
from glove80.tui.widgets.key_canvas import KeyCanvas
from textual.widgets import Button


def _sample_payload() -> dict[str, object]:
    from glove80.tui.state.store import DEFAULT_SAMPLE_LAYOUT

    return json.loads(json.dumps(DEFAULT_SAMPLE_LAYOUT))


async def _settle(pilot, cycles: int = 4) -> None:
    for _ in range(cycles):
        await pilot.pause()


async def _focus_first_key(pilot) -> KeyCanvas:
    canvas = pilot.app.screen.query_one(KeyCanvas)
    canvas.focus()
    await pilot.pause()
    return canvas


def test_validation_debounce_lifecycle(tmp_path) -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_sample_payload(), save_path=tmp_path / "layout.json")
        async with app.run_test() as pilot:
            await _focus_first_key(pilot)
            inspector = pilot.app.screen.query_one(KeyInspector)

            inspector.apply_value_for_test("", [])
            await _settle(pilot)
            footer = pilot.app.screen.query_one(FooterBar)
            assert "valid=✗" in footer.text_for_test()

            inspector.apply_value_for_test("&kp", ["Q"])
            await _settle(pilot)
            assert "valid=✓" in footer.text_for_test()

    asyncio.run(_run())


def test_regen_preview_apply_and_undo(tmp_path) -> None:
    async def _run() -> None:
        payload = _sample_payload()
        app = Glove80TuiApp(payload=payload, save_path=tmp_path / "layout.json")
        async with app.run_test() as pilot:
            app.store.rename_layer(old_name=app.store.layer_names[0], new_name="TempLayer")
            await _settle(pilot, cycles=2)

            await pilot.press("f6")
            await pilot.pause()
            assert isinstance(pilot.app.screen, RegenPreviewModal)
            modal = pilot.app.screen
            modal.query_one("#regen-accept", Button).press()
            await _settle(pilot, cycles=2)
            assert app.store.layer_names[0] == "Base"

            await pilot.press("ctrl+z")
            await _settle(pilot)
            assert app.store.layer_names[0] == "TempLayer"

    asyncio.run(_run())


def test_regen_preview_cancel(tmp_path) -> None:
    async def _run() -> None:
        payload = _sample_payload()
        app = Glove80TuiApp(payload=payload, save_path=tmp_path / "layout.json")
        async with app.run_test() as pilot:
            app.store.rename_layer(old_name=app.store.layer_names[0], new_name="CancelLayer")
            await _settle(pilot)

            await pilot.press("f6")
            await pilot.pause()
            assert isinstance(pilot.app.screen, RegenPreviewModal)
            modal = pilot.app.screen
            modal.query_one("#regen-cancel", Button).press()
            await _settle(pilot)
            assert app.store.layer_names[0] == "CancelLayer"

    asyncio.run(_run())


def test_save_requires_valid_layout(tmp_path) -> None:
    async def _run() -> None:
        save_path = tmp_path / "layout.json"
        app = Glove80TuiApp(payload=_sample_payload(), save_path=save_path)
        async with app.run_test() as pilot:
            await _focus_first_key(pilot)
            inspector = pilot.app.screen.query_one(KeyInspector)
            inspector.apply_value_for_test("", [])
            await _settle(pilot)

            await pilot.press("ctrl+s")
            await _settle(pilot)
            assert not save_path.exists()

            inspector.apply_value_for_test("&kp", ["R"])
            await _settle(pilot)
            await pilot.press("ctrl+s")
            await _settle(pilot)
            assert save_path.exists()

            footer = pilot.app.screen.query_one(FooterBar)
            assert "dirty=no" in footer.text_for_test()

    asyncio.run(_run())
