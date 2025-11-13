"""Modal that previews regen diffs before applying them."""

from __future__ import annotations

import json
from difflib import unified_diff
from typing import Mapping

from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Static


def _dump_payload(payload: Mapping[str, object]) -> list[str]:
    return json.dumps(payload, indent=2, sort_keys=True).splitlines()


def _build_diff(before: Mapping[str, object], after: Mapping[str, object]) -> str:
    before_lines = _dump_payload(before)
    after_lines = _dump_payload(after)
    diff = list(
        unified_diff(
            before_lines,
            after_lines,
            fromfile="current",
            tofile="regenerated",
            lineterm="",
        )
    )
    if not diff:
        return "[no changes]"
    return "\n".join(diff)


class DiffViewer(Static):
    """Simple Static wrapper that renders unified diff text."""

    def __init__(self, *, before: Mapping[str, object], after: Mapping[str, object]) -> None:
        super().__init__(_build_diff(before, after), classes="regen-diff")


class RegenPreviewModal(ModalScreen[bool]):
    """Modal prompting the user to accept a regenerated payload."""

    BINDINGS = [
        Binding("enter", "accept", "Accept Changes", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, before: Mapping[str, object], after: Mapping[str, object]) -> None:
        super().__init__(classes="regen-modal-screen")
        self._before = before
        self._after = after

    def compose(self):  # type: ignore[override]
        yield Vertical(
            Static("Regenerated Layout Changes", classes="regen-modal-title"),
            ScrollableContainer(
                DiffViewer(before=self._before, after=self._after),
                id="regen-diff-view",
            ),
            Horizontal(
                Button.success("Accept", id="regen-accept"),
                Button("Cancel", id="regen-cancel"),
                classes="regen-actions",
            ),
            id="regen-modal-container",
        )

    def action_accept(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "regen-accept":
            self.action_accept()
        elif event.button.id == "regen-cancel":
            self.action_cancel()


__all__ = ["RegenPreviewModal"]
