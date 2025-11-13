"""Footer/status bar that mirrors selection state."""

from __future__ import annotations

from textual import on
from textual.widgets import Static

from ..messages import (
    FooterMessage,
    SaveStateChanged,
    SelectionChanged,
    ValidationCompleted,
)


class FooterBar(Static):
    """Lightweight status line that surfaces selection + dirty state."""

    def __init__(self) -> None:
        super().__init__(classes="footer-bar")
        self._layer_name = "—"
        self._key_index: int | None = None
        self._dirty = False
        self._saving = False
        self._validation_issue_count: int | None = None
        self._message = ""
        self._latest_text = ""

    def on_mount(self) -> None:
        self._render_status()

    def _render_status(self) -> None:
        key_fragment = "--" if self._key_index is None else f"#{self._key_index:02d}"
        dirty_fragment = "yes" if self._dirty else "no"
        save_fragment = "*" if self._saving else ""
        if self._validation_issue_count is None:
            validation_fragment = "?"
        elif self._validation_issue_count == 0:
            validation_fragment = "✓"
        else:
            validation_fragment = f"✗{self._validation_issue_count}"
        message_fragment = f" · {self._message}" if self._message else ""
        text = (
            f"Layer: {self._layer_name} · Key: {key_fragment} "
            f"· dirty={dirty_fragment}{save_fragment} · valid={validation_fragment}{message_fragment}"
        )
        self._latest_text = text
        self.update(text)

    @on(SelectionChanged)
    def _handle_selection(self, event: SelectionChanged) -> None:
        self._layer_name = event.layer_name or "—"
        self._key_index = event.key_index
        self._render_status()

    @on(FooterMessage)
    def _handle_footer_message(self, event: FooterMessage) -> None:
        self._message = event.text
        self._render_status()

    @on(SaveStateChanged)
    def _handle_save_state(self, event: SaveStateChanged) -> None:
        self._dirty = event.is_dirty
        self._saving = event.save_in_progress
        self._render_status()

    @on(ValidationCompleted)
    def _handle_validation_completed(self, event: ValidationCompleted) -> None:
        self._validation_issue_count = event.issue_count
        self._render_status()

    # ------------------------------------------------------------------
    def text_for_test(self) -> str:
        return self._latest_text

    def set_validation_issue_count(self, issue_count: int) -> None:
        self._validation_issue_count = issue_count
        self._render_status()
