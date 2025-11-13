from __future__ import annotations

import asyncio

from copy import deepcopy

from textual.widgets import Button, Static

from glove80.tui.app import Glove80TuiApp
from glove80.tui.state.store import DEFAULT_SAMPLE_LAYOUT


def test_features_tab_preview_and_apply() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(
            payload=deepcopy(DEFAULT_SAMPLE_LAYOUT),
            initial_layout="tailorkey",
            initial_variant="windows",
        )
        async with app.run_test() as pilot:
            preview_button = pilot.app.screen.query_one("#preview-feature-hrm", Button)
            preview_button.press()
            await pilot.pause()

            summary = pilot.app.screen.query_one("#feature-summary-hrm", Static)
            assert "Home Row Mods" in str(summary.render())
            assert "Summary:" in str(summary.render())

            apply_button = pilot.app.screen.query_one("#apply-feature-hrm", Button)
            apply_button.press()
            await pilot.pause()
            assert "HRM_WinLinx" in pilot.app.store.layer_names

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert "HRM_WinLinx" not in pilot.app.store.layer_names

    asyncio.run(_run())
