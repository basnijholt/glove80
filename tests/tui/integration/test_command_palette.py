from __future__ import annotations

import asyncio
from copy import deepcopy


from glove80.tui.app import Glove80TuiApp
from glove80.tui.screens.editor import EditorScreen
from glove80.tui.state.store import DEFAULT_SAMPLE_LAYOUT
from glove80.tui.widgets import CommandPaletteModal, KeyCanvas


def _payload() -> dict[str, object]:
    return deepcopy(DEFAULT_SAMPLE_LAYOUT)


async def _type_text(pilot, text: str) -> None:
    for char in text:
        await pilot.press(char)


def test_command_palette_executes_undo_and_restores_focus() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_payload())
        async with app.run_test() as pilot:
            await pilot.pause()
            canvas = pilot.app.screen.query_one(KeyCanvas)
            canvas.focus()
            await pilot.pause()

            original_name = app.store.layer_names[0]
            renamed = f"{original_name}_TMP"
            app.store.rename_layer(old_name=original_name, new_name=renamed)
            await pilot.pause()

            await pilot.press("ctrl+k")
            await pilot.pause()
            assert isinstance(pilot.app.screen, CommandPaletteModal)

            await _type_text(pilot, "undo")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            assert isinstance(pilot.app.screen, EditorScreen)
            assert original_name in app.store.layer_names
            assert renamed not in app.store.layer_names
            assert canvas.has_focus

    asyncio.run(_run())


def test_command_palette_escape_dismisses_modal() -> None:
    async def _run() -> None:
        app = Glove80TuiApp(payload=_payload())
        async with app.run_test() as pilot:
            await pilot.pause()
            canvas = pilot.app.screen.query_one(KeyCanvas)
            canvas.focus()
            await pilot.pause()

            await pilot.press("ctrl+k")
            await pilot.pause()
            assert isinstance(pilot.app.screen, CommandPaletteModal)

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(pilot.app.screen, EditorScreen)
            assert canvas.has_focus

    asyncio.run(_run())
