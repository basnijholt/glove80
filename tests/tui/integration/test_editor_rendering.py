from __future__ import annotations

import asyncio

from glove80.tui.app import Glove80TuiApp
from textual.widgets import Button

from glove80.tui.widgets import InspectorOverlay, KeyCanvas, LayerStrip, ProjectRibbon
from glove80.tui.widgets.inspector import KeyInspector
from textual.widgets import Static


def test_editor_renders_core_widgets() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            ribbon = pilot.app.screen.query_one(ProjectRibbon)
            canvas = pilot.app.screen.query_one(KeyCanvas)
            inspector = pilot.app.screen.query_one(KeyInspector)
            layer_strip = pilot.app.screen.query_one(LayerStrip)

            title = ribbon.query_one(".ribbon-title", Static)
            assert "Glove80" in str(title.render())
            assert canvas is not None
            assert inspector is not None
            assert "Base" in str(layer_strip.render())

    asyncio.run(_run())


def test_layer_switch_updates_store_selection() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            canvas = pilot.app.screen.query_one(KeyCanvas)
            canvas.action_next_layer()
            await pilot.pause()

            assert pilot.app.store.selected_layer_name == "Lower"

    asyncio.run(_run())


def test_inspector_overlay_toggles_and_resets_focus() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            overlay = pilot.app.screen.query_one(InspectorOverlay)

            assert not overlay.visible

            ribbon = pilot.app.screen.query_one(ProjectRibbon)
            ribbon.query_one("#toggle-inspector", Button).press()
            await pilot.pause()
            assert overlay.visible

            await pilot.press("escape")
            await pilot.pause()
            assert not overlay.visible

    asyncio.run(_run())
