"""Horizontal layer strip widget."""

from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text
from textual import on
from textual.binding import Binding
from textual.widget import Widget

from ..messages import SelectionChanged, StoreUpdated
from ..state import LayoutStore


@dataclass
class _Segment:
    index: int
    start: int
    end: int


class LayerStrip(Widget):
    """Click-friendly layer pills spanning the footer."""

    BINDINGS = [
        Binding("left", "prev_layer", show=False),
        Binding("right", "next_layer", show=False),
    ]

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="layer-strip")
        self.store = store
        self._segments: list[_Segment] = []

    # ------------------------------------------------------------------
    def render(self) -> Text:  # pragma: no cover - exercised via integration tests
        text = Text()
        self._segments.clear()
        cursor = 0
        active = self.store.selection.layer_index if self.store.selection.layer_index >= 0 else -1
        for idx, name in enumerate(self.store.layer_names):
            pill = self._format_pill(name, is_active=idx == active)
            text.append(pill, style="bold" if idx == active else "")
            self._segments.append(_Segment(index=idx, start=cursor, end=cursor + len(pill)))
            cursor += len(pill)
            spacer = "  "
            text.append(spacer)
            cursor += len(spacer)
        text.append("   + Layer ▾    Inspector ▸")
        return text

    def _format_pill(self, name: str, *, is_active: bool) -> str:
        marker = "*" if is_active else " "
        return f"[ {name}{marker} ]"

    # ------------------------------------------------------------------
    def action_prev_layer(self) -> None:
        if not self.store.layer_names:
            return
        current = self.store.selection.layer_index if self.store.selection.layer_index >= 0 else 0
        self._activate((current - 1) % len(self.store.layer_names))

    def action_next_layer(self) -> None:
        if not self.store.layer_names:
            return
        current = self.store.selection.layer_index if self.store.selection.layer_index >= 0 else 0
        self._activate((current + 1) % len(self.store.layer_names))

    def on_mouse_up(self, event):  # type: ignore[override]
        if event.button != 1 or not self._segments:
            return
        offset = event.get_content_offset(self)
        if offset is None:
            return
        for segment in self._segments:
            if segment.start <= offset.x < segment.end:
                self._activate(segment.index)
                break

    def _activate(self, index: int) -> None:
        if not self.store.layer_names:
            return
        index = index % len(self.store.layer_names)
        self.store.set_active_layer(index)
        self.post_message(StoreUpdated())
        self.refresh()

    # ------------------------------------------------------------------
    @on(SelectionChanged)
    def _handle_selection(self, _: SelectionChanged) -> None:
        self.refresh()

    @on(StoreUpdated)
    def _handle_store(self, _: StoreUpdated) -> None:
        self.refresh()
