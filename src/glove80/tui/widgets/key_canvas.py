"""Interactive key canvas widget for Milestone 3."""

from __future__ import annotations

from typing import Any, Sequence

from rich.text import Text
from textual import on
from textual.events import Leave, MouseEvent, MouseMove, MouseUp
from textual.binding import Binding
from textual.widget import Widget

from ..geometry import KEY_GRID_ROWS, Direction, move
from ..messages import FooterMessage, InspectorFocusRequested, SelectionChanged, StoreUpdated
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
        Binding("[", "prev_layer", "Prev Layer"),
        Binding("]", "next_layer", "Next Layer"),
        Binding(".", "copy_key", "Copy Key"),
    ]

    MAX_LABEL_CHARS = 5
    CELL_COL_WIDTH = MAX_LABEL_CHARS + 3  # brackets + space padding

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="key-canvas")
        self.store = store
        self._selection = self.store.selection
        self._previous_selection: SelectionState | None = None
        self._hover_index: int | None = None

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
                elif self._hover_index == idx:
                    style = "bold dark_cyan"
                else:
                    style = "grey70"
                text.append(f"[{legend}]", style=style)
                text.append(" ")
            text.append("\n")

        detail_lines = self._detail_lines(slots)
        if detail_lines:
            text.append("\n")
            for line in detail_lines:
                text.append(line, style="bold grey70")
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
        self._request_inspector_focus()

    def action_prev_layer(self) -> None:
        self._switch_layer(-1)

    def action_next_layer(self) -> None:
        self._switch_layer(1)

    def action_copy_key(self) -> None:
        if self._previous_selection is None or self._previous_selection.layer_index < 0:
            self._notify("Nothing to copy — visit a source layer first.")
            return
        if self._selection.layer_index < 0 or self._selection.key_index < 0:
            self._notify("No destination layer selected.")
            return
        if self._previous_selection.layer_index == self._selection.layer_index:
            self._notify("Select a different layer before copying.")
            return

        try:
            changed = self.store.copy_key_to_layer(
                source_layer_index=self._previous_selection.layer_index,
                target_layer_index=self._selection.layer_index,
                key_index=self._selection.key_index,
            )
        except IndexError as exc:
            self._notify(str(exc))
            return
        except ValueError as exc:  # pragma: no cover - defensive
            self._notify(str(exc))
            return

        if not changed:
            self._notify("Key already matches source binding.")
            return

        slot = self.store.state.layers[self._selection.layer_index].slots[self._selection.key_index]
        legend = self._slot_legend((slot,), 0) if slot else "--"
        self.post_message(StoreUpdated())
        message = (
            f"Copied key #{self._selection.key_index:02d}: {legend} → "
            f"{self.store.layer_names[self._selection.layer_index]}"
        )
        self.post_message(FooterMessage(message))
        self._notify(message)
        self.refresh()

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
        label = self._slot_label(slot)
        return self._truncate_label(label)

    def _slot_label(self, slot: dict[str, object] | None) -> str:
        if not isinstance(slot, dict):
            return "--"
        value = str(slot.get("value", ""))
        if value == "&kp":
            param_value = self._first_param_value(slot.get("params"))
            if param_value:
                return param_value
        return self._raw_label_for_value(value)

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

    def on_mouse_move(self, event: MouseMove) -> None:  # pragma: no cover - UI interaction
        index = self._index_from_event(event)
        if index is None:
            return
        if self._hover_index != index:
            self._hover_index = index
            self.refresh()

    def on_mouse_up(self, event: MouseUp) -> None:  # pragma: no cover - UI interaction
        if event.button != 1:
            return
        index = self._index_from_event(event)
        if index is None:
            return
        self._selection = self.store.set_selected_key(index)
        self._broadcast_selection()
        self._request_inspector_focus()
        self.refresh()

    def on_leave(self, _: Leave) -> None:  # pragma: no cover - UI interaction
        if self._hover_index is not None:
            self._hover_index = None
            self.refresh()

    # ------------------------------------------------------------------
    # Test helpers ------------------------------------------------------
    def selected_index_for_test(self) -> int:
        return self._selection.key_index

    # ------------------------------------------------------------------
    # Internal helpers
    def _truncate_label(self, label: str) -> str:
        clean = " ".join(label.split()) or "--"
        if len(clean) > self.MAX_LABEL_CHARS:
            clean = f"{clean[: self.MAX_LABEL_CHARS - 1]}…"
        return clean.upper().center(self.MAX_LABEL_CHARS)

    def _request_inspector_focus(self) -> None:
        if self._selection.layer_index < 0 or self._selection.key_index < 0:
            return
        self.post_message(
            InspectorFocusRequested(
                layer_index=self._selection.layer_index,
                key_index=self._selection.key_index,
            )
        )

    def _raw_label_for_value(self, value: str) -> str:
        if not value:
            return "--"
        if value.startswith("&"):
            return value[1:]
        return value

    def _first_param_value(self, params: Any) -> str:
        if not params:
            return ""
        if isinstance(params, (list, tuple)):
            for item in params:
                candidate = self._first_param_value(item)
                if candidate:
                    return candidate
            return ""
        if isinstance(params, dict):
            value = params.get("value") or params.get("name")
            if isinstance(value, str):
                return value
            if value is not None:
                return str(value)
            nested = params.get("params")
            return self._first_param_value(nested)
        return str(params)

    def _detail_lines(self, slots: Sequence[dict[str, object]]) -> list[str]:
        lines: list[str] = []
        if self._hover_index is not None:
            lines.extend(self._detail_lines_for_slot(slots, self._hover_index, prefix="Hover"))
        if self._selection.key_index >= 0:
            prefix = "Focus" if self.has_focus else "Selected"
            lines.extend(self._detail_lines_for_slot(slots, self._selection.key_index, prefix=prefix))
        return lines

    def _detail_lines_for_slot(self, slots: Sequence[dict[str, object]], index: int, *, prefix: str) -> list[str]:
        try:
            slot = slots[index]
        except (IndexError, TypeError):
            return [f"{prefix}: Key #{index:02d} (empty)"]
        if not isinstance(slot, dict):
            return [f"{prefix}: Key #{index:02d} (empty)"]

        lines = [f"{prefix}: Key #{index:02d} {slot.get('value', '(empty)') or '(empty)'}"]
        params_text = self._format_params_list(slot.get("params"))
        if params_text:
            lines.append(f"    params: {params_text}")
        return lines

    def _format_params_list(self, params: Any) -> str:
        if not params:
            return ""
        if isinstance(params, (list, tuple)):
            values = [self._format_param_item(item) for item in params]
        else:
            values = [self._format_param_item(params)]
        return ", ".join(v for v in values if v)

    def _format_param_item(self, item: Any) -> str:
        if isinstance(item, dict):
            value = item.get("value") or item.get("name")
            nested = item.get("params")
            base = str(value) if value is not None else str(item)
            if nested:
                nested_values = ", ".join(self._format_param_item(sub) for sub in self._ensure_iterable(nested))
                return f"{base}({nested_values})"
            return base
        if isinstance(item, (list, tuple)):
            return ", ".join(self._format_param_item(sub_item) for sub_item in item)
        return str(item)

    def _ensure_iterable(self, value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return [value]

    def _index_from_coordinates(self, x: int, y: int) -> int | None:
        if x < 0 or y < 0:
            return None
        row_count = len(KEY_GRID_ROWS)
        if y >= row_count:
            return None
        col = x // self.CELL_COL_WIDTH
        if col >= len(KEY_GRID_ROWS[0]):
            return None
        return KEY_GRID_ROWS[y][col]

    def _index_from_event(self, event: MouseEvent) -> int | None:
        offset = event.get_content_offset(self)
        if offset is None:
            return None
        return self._index_from_coordinates(offset.x, offset.y)

    def _switch_layer(self, delta: int) -> None:
        layer_names = self.store.layer_names
        if not layer_names:
            return
        current = self._selection.layer_index if self._selection.layer_index >= 0 else 0
        next_index = (current + delta) % len(layer_names)
        if next_index == current:
            return
        self._previous_selection = self._selection
        self._selection = self.store.set_active_layer(next_index)
        self._broadcast_selection()
        self.post_message(FooterMessage(f"Active layer → {layer_names[next_index]}"))
        self._notify(f"Layer switched to {layer_names[next_index]}")
        self.refresh()

    def _notify(self, message: str) -> None:
        try:
            self.app.notify(message)
        except Exception:  # pragma: no cover - Textual optional
            self.log.debug(message)
