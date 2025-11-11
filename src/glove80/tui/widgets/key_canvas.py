"""Interactive key canvas widget for Milestone 3."""

from __future__ import annotations

from typing import Sequence

from rich.text import Text
from textual import on
from textual.binding import Binding
from textual.widget import Widget

from ..geometry import KEY_GRID_ROWS, Direction, move
from ..messages import InspectorFocusRequested, SelectionChanged, StoreUpdated
from ..state import LayoutStore, SelectionState


class KeyCanvas(Widget):
    """Minimal 80-key grid with keyboard navigation."""

    can_focus = True
    BINDINGS = [
        Binding("left", "move_left", "←", show=False),
        Binding("right", "move_right", "→", show=False),
        Binding("up", "move_up", "↑", show=False),
        Binding("down", "move_down", "↓", show=False),
        Binding("h", "move_left", show=False),
        Binding("l", "move_right", show=False),
        Binding("k", "move_up", show=False),
        Binding("j", "move_down", show=False),
        Binding("enter", "inspect", "Inspect"),
    ]

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="key-canvas")
        self.store = store
        self._selection = self.store.selection

    # ------------------------------------------------------------------
    # Textual lifecycle
    def on_mount(self) -> None:
        if self._selection.layer_index < 0 and self.store.layer_names:
            self._selection = self.store.set_selection(layer_index=0, key_index=0)

    def render(self) -> Text:
        slots = self._current_slots()
        text = Text()
        for row in KEY_GRID_ROWS:
            for idx in row:
                legend = self._slot_legend(slots, idx)
                if self._selection.key_index == idx:
                    style = "bold white on dark_cyan"
                else:
                    style = "grey70"
                text.append(f"[{legend:^4}]", style=style)
                text.append(" ")
            text.append("\n")
        return text

    # ------------------------------------------------------------------
    # Actions
    def action_move_left(self) -> None:
        self._move("left")

    def action_move_right(self) -> None:
        self._move("right")

    def action_move_up(self) -> None:
        self._move("up")

    def action_move_down(self) -> None:
        self._move("down")

    def action_inspect(self) -> None:
        if self._selection.layer_index < 0:
            return
        self.post_message(
            InspectorFocusRequested(
                layer_index=self._selection.layer_index,
                key_index=self._selection.key_index,
            )
        )

    # ------------------------------------------------------------------
    def _move(self, direction: Direction) -> None:
        current = self._selection.key_index
        next_index = move(current, direction) if current >= 0 else 0
        if next_index is None:
            return
        self._selection = self.store.set_selected_key(next_index)
        self._broadcast_selection()
        self.refresh()

    def _current_slots(self) -> tuple[dict[str, object], ...]:
        if self._selection.layer_index < 0:
            return ()
        return self.store.state.layers[self._selection.layer_index].slots

    def _slot_legend(self, slots: Sequence[dict[str, object]], index: int) -> str:
        try:
            slot = slots[index]
        except (IndexError, TypeError):
            return "--"
        value = slot.get("value", "") if isinstance(slot, dict) else ""
        if not value:
            return "--"
        value_str = str(value)
        if value_str.startswith("&kp "):
            parts = value_str.split(" ", 1)
            if len(parts) > 1:
                return parts[1][:3].upper()
        if value_str.startswith("&"):
            return value_str[1:4].upper()
        return value_str[:4].upper()

    def _broadcast_selection(self) -> None:
        self.post_message(
            SelectionChanged(
                layer_index=self._selection.layer_index,
                layer_name=self.store.selected_layer_name,
                key_index=self._selection.key_index,
            )
        )

    # ------------------------------------------------------------------
    @on(StoreUpdated)
    def _handle_store_updated(self, _: StoreUpdated) -> None:
        self.refresh()

    @on(SelectionChanged)
    def _handle_external_selection(self, event: SelectionChanged) -> None:
        if event.layer_index < 0 or event.key_index < 0:
            return
        self._selection = SelectionState(layer_index=event.layer_index, key_index=event.key_index)
        self.refresh()

    # ------------------------------------------------------------------
    # Test helpers ------------------------------------------------------
    def selected_index_for_test(self) -> int:
        return self._selection.key_index
