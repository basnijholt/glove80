"""Interactive key canvas backed by Textual widgets."""

from __future__ import annotations

from typing import Any, Sequence

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Static

from ..geometry import KEY_GRID_ROWS, Direction, move
from ..messages import FooterMessage, InspectorFocusRequested, SelectionChanged, StoreUpdated
from ..state import LayoutStore, SelectionState


class KeyCanvas(Widget):
    """80-key grid composed of individual `Button` widgets."""

    can_focus = True
    HAND_SPLIT_AFTER = 7
    MAX_LABEL_CHARS = 5
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

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="key-canvas")
        self.store = store
        self._selection = self.store.selection
        self._previous_selection: SelectionState | None = None
        self._caps: dict[int, KeyCap] = {}
        self._search_highlights: set[int] = set()

    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        self._caps.clear()
        with Vertical(id="key-grid"):
            for row in KEY_GRID_ROWS:
                with Horizontal(classes="key-row"):
                    for col_index, key_index in enumerate(row):
                        cap = KeyCap(canvas=self, index=key_index)
                        self._caps[key_index] = cap
                        yield cap
                        if col_index == self.HAND_SPLIT_AFTER:
                            yield Static("", classes="key-hand-gap")

    def on_mount(self) -> None:
        if self._selection.layer_index < 0 and self.store.layer_names:
            self._selection = self.store.set_selection(layer_index=0, key_index=0)
        self.call_after_refresh(self._refresh_caps)

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
        self._refresh_caps()

    def action_select_from_button(self, index: int) -> None:
        self._selection = self.store.set_selected_key(index)
        self._broadcast_selection()
        self._request_inspector_focus()
        self._refresh_caps()

    # ------------------------------------------------------------------
    def _move(self, direction: Direction) -> None:
        current = self._selection.key_index
        next_index = move(current, direction) if current >= 0 else 0
        if next_index is None:
            return
        self._selection = self.store.set_selected_key(next_index)
        self._broadcast_selection()
        self._refresh_caps()

    def _current_slots(self) -> tuple[dict[str, object], ...]:
        if self._selection.layer_index < 0:
            return ()
        return self.store.state.layers[self._selection.layer_index].slots

    def _slot_at(self, slots: Sequence[dict[str, object]], index: int) -> dict[str, object] | None:
        try:
            return slots[index]
        except (IndexError, TypeError):
            return None

    def _slot_behavior(self, slot: dict[str, object] | None) -> str:
        if not isinstance(slot, dict):
            return "--"
        return self._raw_label_for_value(str(slot.get("value", "")))

    def _slot_param(self, slot: dict[str, object] | None) -> str:
        if not isinstance(slot, dict):
            return "--"
        return self._first_param_value(slot.get("params")) or "--"

    def _slot_legend(self, slots: Sequence[dict[str, object]], index: int) -> str:
        slot = self._slot_at(slots, index)
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
        self._selection = self.store.selection
        self._refresh_caps()

    @on(SelectionChanged)
    def _handle_external_selection(self, event: SelectionChanged) -> None:
        if event.layer_index < 0 or event.key_index < 0:
            return
        self.apply_selection(layer_index=event.layer_index, key_index=event.key_index)

    def update_search_highlights(self, *, layer_index: int, indices: Sequence[int]) -> None:
        if layer_index != self.store.selection.layer_index:
            self._search_highlights.clear()
        else:
            self._search_highlights = set(indices)
        self._refresh_caps()

    def apply_selection(self, *, layer_index: int, key_index: int) -> None:
        if layer_index < 0 or key_index < 0:
            return
        self._selection = SelectionState(layer_index=layer_index, key_index=key_index)
        self._refresh_caps()

    # ------------------------------------------------------------------
    def selected_index_for_test(self) -> int:
        return self._selection.key_index

    def cap_lines_for_test(self, index: int) -> tuple[str, str, str]:
        cap = self._caps.get(index)
        if cap is None:
            return ("", "", "")
        return cap.snapshot_lines()

    def tooltip_for_test(self, index: int) -> str:
        cap = self._caps.get(index)
        if cap is None or cap.tooltip is None:
            return ""
        return str(cap.tooltip)

    def highlighted_indices_for_test(self) -> tuple[int, ...]:
        return tuple(sorted(self._search_highlights))

    def _refresh_caps(self) -> None:
        slots = self._current_slots()
        for index, cap in self._caps.items():
            slot = self._slot_at(slots, index)
            legend = self._slot_legend(slots, index)
            behavior = self._truncate_label(self._slot_behavior(slot))
            params = self._truncate_label(self._slot_param(slot))
            tooltip = self._detail_text(slot, index)
            cap.set_content(legend=legend, behavior=behavior, params=params, tooltip=tooltip)
            cap.set_selected(index == self._selection.key_index)
            cap.set_highlighted(index in self._search_highlights)

    def _detail_text(self, slot: dict[str, object] | None, index: int) -> str:
        if not isinstance(slot, dict):
            return f"Key #{index:02d}: (empty)"
        params_text = self._format_params_list(slot.get("params"))
        suffix = f" params: {params_text}" if params_text else ""
        return f"Key #{index:02d}: {slot.get('value', '(empty)')}" + suffix

    def _truncate_label(self, label: str) -> str:
        clean = " ".join(label.split()) or "--"
        if len(clean) > self.MAX_LABEL_CHARS:
            clean = f"{clean[: self.MAX_LABEL_CHARS - 1]}…"
        return clean.upper()

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
        self._refresh_caps()

    def _notify(self, message: str) -> None:
        try:
            self.app.notify(message)
        except Exception:  # pragma: no cover - Textual optional
            self.log.debug(message)


class KeyCap(Button):
    """Individual keycap with multi-line label."""

    can_focus = False

    def __init__(self, *, canvas: KeyCanvas, index: int) -> None:
        super().__init__("", id=f"key-{index}", classes="key-cap")
        self.canvas = canvas
        self.index = index
        self._lines: tuple[str, str, str] = ("", "", "")

    def set_content(
        self,
        *,
        legend: str,
        behavior: str,
        params: str,
        tooltip: str,
    ) -> None:
        self._lines = (legend, behavior, params)
        self.label = "\n".join(self._lines)
        self.tooltip = tooltip

    def set_selected(self, selected: bool) -> None:
        self.set_class(selected, "selected")

    def set_highlighted(self, highlighted: bool) -> None:
        self.set_class(highlighted, "highlighted")

    def snapshot_lines(self) -> tuple[str, str, str]:  # pragma: no cover - test helper
        return self._lines

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button is self:
            self.canvas.action_select_from_button(self.index)
            event.stop()
