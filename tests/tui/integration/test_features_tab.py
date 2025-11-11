from __future__ import annotations

import asyncio

from textual.widgets import Button, Static

from glove80.tui.app import Glove80TuiApp


def test_features_tab_preview_and_apply() -> None:
    async def _run() -> None:
        app = Glove80TuiApp()
        async with app.run_test() as pilot:
            preview_button = pilot.app.screen.query_one("#preview-hrm", Button)
            preview_button.press()
            await pilot.pause()

            summary = pilot.app.screen.query_one("#feature-summary", Static)
            assert "HRM →" in str(summary.render())

            apply_button = pilot.app.screen.query_one("#apply-hrm", Button)
            apply_button.press()
            await pilot.pause()
            assert "HRM_WinLinx" in pilot.app.store.layer_names

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert "HRM_WinLinx" not in pilot.app.store.layer_names

    asyncio.run(_run())
