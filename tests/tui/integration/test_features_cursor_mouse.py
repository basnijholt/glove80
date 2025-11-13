from __future__ import annotations

import asyncio

from copy import deepcopy

from textual.widgets import Button, Static

from glove80.tui.app import Glove80TuiApp
from glove80.tui.state.store import DEFAULT_SAMPLE_LAYOUT


def test_features_tab_cursor_preview_apply() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(
            payload=deepcopy(DEFAULT_SAMPLE_LAYOUT),
            initial_layout="tailorkey",
            initial_variant="windows",
        )
        async with app.run_test() as pilot:
            pilot.app.store.set_active_layer(0)
            preview = pilot.app.screen.query_one("#preview-feature-cursor", Button)
            preview.press()
            await pilot.pause()

            summary = pilot.app.screen.query_one("#feature-summary-cursor", Static)
            assert "Cursor Layer" in str(summary.render())

            apply = pilot.app.screen.query_one("#apply-feature-cursor", Button)
            apply.press()
            await pilot.pause()

            assert "Cursor" in pilot.app.store.layer_names

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert "Cursor" not in pilot.app.store.layer_names

    asyncio.run(_run())


def test_features_tab_mouse_preview_apply() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(
            payload=deepcopy(DEFAULT_SAMPLE_LAYOUT),
            initial_layout="tailorkey",
            initial_variant="windows",
        )
        async with app.run_test() as pilot:
            preview = pilot.app.screen.query_one("#preview-feature-mouse", Button)
            preview.press()
            await pilot.pause()

            summary = pilot.app.screen.query_one("#feature-summary-mouse", Static)
            assert "Mouse Layers" in str(summary.render())

            apply = pilot.app.screen.query_one("#apply-feature-mouse", Button)
            apply.press()
            await pilot.pause()

            names = set(pilot.app.store.layer_names)
            assert {"Mouse", "MouseSlow", "MouseFast", "MouseWarp"}.issubset(names)

    asyncio.run(_run())
