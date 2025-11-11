from __future__ import annotations

import asyncio

from textual.pilot import Pilot

from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets.inspector import FeaturesTab


def _payload() -> dict[str, object]:
    slots = [{"value": "&kp", "params": [{"value": "A", "params": []}]} for _ in range(80)]
    return {
        "layer_names": ["Base"],
        "layers": [slots],
        "macros": [],
        "holdTaps": [],
        "combos": [],
        "inputListeners": [],
    }


def test_features_tab_preview_and_apply() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_payload(), initial_variant="windows")
        async with app.run_test() as pilot:  # type: Pilot
            features = pilot.app.query_one(FeaturesTab)

            features._preview_hrm()
            await pilot.pause()

            summary_text = features.current_summary
            assert "HRM →" in summary_text

            features._apply_hrm()
            await pilot.pause()

            assert "HRM_WinLinx" in pilot.app.store.layer_names

            await pilot.press("ctrl+z")
            await pilot.pause()
            assert "HRM_WinLinx" not in pilot.app.store.layer_names

    asyncio.run(_run())
