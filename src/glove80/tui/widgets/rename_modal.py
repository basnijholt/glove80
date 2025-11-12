"""Modal screen for renaming layers."""

from __future__ import annotations

from typing import Optional

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class RenameLayerModal(ModalScreen[Optional[str]]):
    def __init__(self, *, current_name: str) -> None:
        super().__init__()
        self._current_name = current_name

    def compose(self):  # type: ignore[override]
        yield Vertical(
            Label("Rename layer", id="rename-title"),
            Input(value=self._current_name, id="rename-input"),
            Horizontal(
                Button.success("Save", id="rename-save"),
                Button("Cancel", id="rename-cancel"),
                id="rename-buttons",
            ),
            id="rename-container",
        )

    def on_mount(self) -> None:  # pragma: no cover - Textual wiring
        input_widget = self.query_one("#rename-input", Input)
        self.set_focus(input_widget)
        input_widget.cursor_position = len(input_widget.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:  # pragma: no cover - UI plumbing
        if event.button.id == "rename-save":
            self._submit_current_value()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:  # pragma: no cover - UI plumbing
        self.dismiss(event.value.strip() or None)

    def _submit_current_value(self) -> None:
        input_widget = self.query_one("#rename-input", Input)
        value = input_widget.value.strip()
        self.dismiss(value or None)
