from __future__ import annotations

import asyncio

from textual.widgets import TabbedContent

from glove80.tui.app import Glove80TuiApp
from glove80.tui.widgets import InspectorOverlay, KeyCanvas, SearchPanel


def _search_payload() -> dict[str, object]:
    def _slot(value: str, param: str | None = None) -> dict[str, object]:
        params = []
        if param is not None:
            params = [{"value": param, "params": []}]
        return {"value": value, "params": params}

    base = [_slot("&kp", "A") for _ in range(80)]
    lower = [_slot("&kp", "B") for _ in range(80)]
    base[4] = _slot("&kp", "NAV")
    base[10] = _slot("MACRO_NAV")
    lower[3] = _slot("LISTENER_NAV")

    return {
        "layer_names": ["Base", "Lower"],
        "layers": [base, lower],
        "macros": [
            {
                "name": "MACRO_NAV",
                "description": "macro-only-desc",
                "bindings": [],
                "params": [],
                "waitMs": 0,
                "tapMs": 0,
            }
        ],
        "inputListeners": [
            {
                "code": "LISTENER_NAV",
                "description": "listener-only-desc",
                "layers": ["Base"],
                "inputProcessors": [],
                "nodes": [],
            }
        ],
        "combos": [],
    }


async def _type_text(pilot, text: str) -> None:
    for char in text:
        await pilot.press(char)


def test_search_panel_highlights_and_cycles_results() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_search_payload())
        async with app.run_test() as pilot:
            canvas = pilot.app.screen.query_one(KeyCanvas)
            await pilot.pause()

            await pilot.press("/")
            await pilot.pause()
            panel = pilot.app.screen.query_one(SearchPanel)
            assert panel.is_open

            await _type_text(pilot, "nav")
            await pilot.pause()
            highlights = canvas.highlighted_indices_for_test()
            assert highlights == (4, 10)

            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.store.selection.key_index == highlights[0]

            await pilot.press("f3")
            await pilot.pause()
            assert pilot.app.store.selection.key_index == highlights[1]

            await pilot.press("shift+f3")
            await pilot.pause()
            assert pilot.app.store.selection.key_index == highlights[0]

            await pilot.press("escape")
            await pilot.pause()
            assert not panel.is_open
            assert canvas.highlighted_indices_for_test() == ()
            assert canvas.has_focus

    asyncio.run(_run())


def test_search_panel_focuses_macro_and_listener_tabs() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_search_payload())
        async with app.run_test() as pilot:
            overlay = pilot.app.screen.query_one(InspectorOverlay)

            await pilot.press("/")
            await pilot.pause()
            await _type_text(pilot, "macro-only")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            assert overlay.visible
            tabs = overlay.panel.query_one("#inspector-tabs", TabbedContent)
            assert tabs.active == "tab-macros"

            await pilot.press("escape")  # close search panel
            await pilot.pause()

            await pilot.press("/")
            await pilot.pause()
            await _type_text(pilot, "listener-only")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            tabs = overlay.panel.query_one("#inspector-tabs", TabbedContent)
            assert tabs.active == "tab-listeners"

    asyncio.run(_run())
