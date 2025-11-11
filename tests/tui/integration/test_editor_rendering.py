from __future__ import annotations

import asyncio

from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets import KeyCanvas, LayerSidebar, ProjectRibbon
from glove80.tui.widgets.inspector import KeyInspector


def test_editor_renders_core_widgets() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            ribbon = pilot.app.screen.query_one(ProjectRibbon)
            sidebar = pilot.app.screen.query_one(LayerSidebar)
            canvas = pilot.app.screen.query_one(KeyCanvas)
            inspector = pilot.app.screen.query_one(KeyInspector)

            assert "Glove80" in str(ribbon.render())
            assert sidebar.children, "Sidebar should list layers"
            assert canvas is not None
            assert inspector is not None

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
