"""Modal command palette for the Glove80 TUI."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static

from ..services.command_registry import Command, CommandRegistry


class CommandPaletteModal(ModalScreen[Optional[str]]):
    """Minimal modal that filters commands and returns a command id."""

    BINDINGS = [
        Binding("escape", "close", "Close Palette", show=False),
        Binding("enter", "choose", "Run Command", show=False),
    ]

    def __init__(self, registry: CommandRegistry) -> None:
        super().__init__(classes="command-palette-modal")
        self._registry = registry
        self._results: list[Command] = list(registry.commands)
        self._input = Input(placeholder="Type a command…", id="command-palette-input")
        self._list = ListView(id="command-palette-list")
        self._status = Static("", id="command-palette-status")

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Vertical(
            Static("Command Palette", classes="command-palette-title"),
            self._input,
            self._status,
            self._list,
            id="command-palette-container",
        )

    async def on_mount(self) -> None:
        await self._refresh_list()
        self.call_after_refresh(lambda: self.set_focus(self._input))

    # ------------------------------------------------------------------
    def action_close(self) -> None:
        self.dismiss(None)

    def action_choose(self) -> None:
        command = self._selected_command
        if command is None:
            return
        self.dismiss(command.command_id)

    # ------------------------------------------------------------------
    @property
    def _selected_command(self) -> Command | None:
        if not self._results or not self._list.children:
            return None
        try:
            index = self._list.index
        except Exception:  # pragma: no cover - defensive
            return None
        if 0 <= index < len(self._results):
            return self._results[index]
        return None

    async def _refresh_list(self) -> None:
        self._results = self._registry.search(self._input.value)
        self._status.update(f"{len(self._results)} command(s)")
        await self._list.clear()
        if not self._results:
            await self._list.append(ListItem(Static("No commands", classes="command-empty")))
            self._list.index = 0
            return
        for command in self._results:
            label = f"{command.label} · {command.category}"
            if command.shortcut:
                label = f"{label} ({command.shortcut})"
            safe_id = command.command_id
            await self._list.append(ListItem(Static(label, classes="command-entry"), id=f"command-{safe_id}"))
        self._list.index = 0

    # ------------------------------------------------------------------
    async def on_input_changed(self, _: Input.Changed) -> None:  # type: ignore[override]
        await self._refresh_list()

    def on_input_submitted(self, _: Input.Submitted) -> None:  # type: ignore[override]
        self.action_choose()

    def on_list_view_highlighted(self, _: ListView.Highlighted) -> None:  # type: ignore[override]
        # keep status up to date
        command = self._selected_command
        if command is not None:
            self._status.update(f"{command.label} · {command.category}")

    def on_list_view_selected(self, _: ListView.Selected) -> None:  # type: ignore[override]
        self.action_choose()


__all__ = ["CommandPaletteModal"]
