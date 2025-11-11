"""Key Inspector tab implementation for Milestone 3."""

from __future__ import annotations

import json
from typing import Sequence

from textual import on
from textual.containers import Vertical
from textual.widgets import Button, Input, Label, Static

from ..messages import SelectionChanged, StoreUpdated
from ..state import LayoutStore, SelectionState


class InspectorPanel(Vertical):
    """Wrapper that will eventually host multiple tabs."""

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="inspector-panel")
        self.store = store
        self.key_inspector = KeyInspector(store=store)

    def compose(self):  # type: ignore[override]
        yield Static("Inspector", classes="inspector-heading")
        yield self.key_inspector


class KeyInspector(Vertical):
    """Minimal form that edits a single key binding."""

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="key-inspector")
        self.store = store
        self._selection: SelectionState | None = None
        self.value_input = Input(placeholder="&kp A", id="key-value")
        self.params_input = Input(placeholder="comma separated params", id="key-params")
        self.json_input = Input(placeholder='{"value": "&kp A", "params": []}', id="key-json")

    def compose(self):  # type: ignore[override]
        yield Label("Key Behavior")
        yield self.value_input
        yield Label("Params (comma separated)")
        yield self.params_input
        yield Button("Apply", id="apply-form")
        yield Label("Raw JSON fallback")
        yield self.json_input
        yield Button("Apply JSON", id="apply-json")

    # ------------------------------------------------------------------
    def on_mount(self) -> None:
        if self.store.selection.layer_index >= 0:
            self._selection = self.store.selection
            self._load_from_store()
        else:
            self._toggle_inputs(False)

    def focus_value_field(self) -> None:
        self.value_input.focus()

    # ------------------------------------------------------------------
    @on(SelectionChanged)
    def _handle_selection_changed(self, event: SelectionChanged) -> None:
        if event.layer_index < 0 or event.key_index < 0:
            self._toggle_inputs(False)
            return
        self._selection = SelectionState(layer_index=event.layer_index, key_index=event.key_index)
        self._load_from_store()

    @on(StoreUpdated)
    def _handle_store_updated(self, _: StoreUpdated) -> None:
        if self._selection is None:
            return
        self._load_from_store()

    @on(Button.Pressed)
    def _handle_button(self, event: Button.Pressed) -> None:
        if event.button.id == "apply-form":
            self._apply_form()
        elif event.button.id == "apply-json":
            self._apply_json()

    # ------------------------------------------------------------------
    def _load_from_store(self) -> None:
        if self._selection is None:
            self._toggle_inputs(False)
            return
        try:
            slot = self.store.get_key(
                layer_index=self._selection.layer_index,
                key_index=self._selection.key_index,
            )
        except (IndexError, ValueError):
            self._toggle_inputs(False)
            return
        self._toggle_inputs(True)
        self.value_input.value = str(slot.get("value", ""))
        params = slot.get("params", [])
        if isinstance(params, Sequence) and not isinstance(params, (str, bytes)):
            self.params_input.value = ", ".join(str(p) for p in params)
        else:
            self.params_input.value = ""
        self.json_input.value = json.dumps(slot, separators=(",", ":"))

    def _toggle_inputs(self, enabled: bool) -> None:
        self.value_input.disabled = not enabled
        self.params_input.disabled = not enabled
        self.json_input.disabled = not enabled

    def _apply_form(self) -> None:
        if self._selection is None:
            return
        value = self.value_input.value.strip()
        params = [p.strip() for p in self.params_input.value.split(",") if p.strip()]
        try:
            self.store.update_selected_key(value=value, params=params)
        except ValueError as exc:  # pragma: no cover - error UI
            self.app.notify(str(exc))
            return
        self.post_message(StoreUpdated())

    def _apply_json(self) -> None:
        if self._selection is None:
            return
        raw = self.json_input.value.strip()
        if not raw:
            self.app.notify("JSON payload cannot be empty")
            return
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:  # pragma: no cover - error UI
            self.app.notify(f"Invalid JSON: {exc}")
            return
        value = str(payload.get("value", ""))
        params = payload.get("params", [])
        if not isinstance(params, Sequence) or isinstance(params, (str, bytes)):
            self.app.notify("'params' must be a list")
            return
        self.store.update_selected_key(value=value, params=list(params))
        self.post_message(StoreUpdated())

    # ------------------------------------------------------------------
    # Test helper -------------------------------------------------------
    def apply_value_for_test(self, value: str, params: Sequence[str] | None = None) -> None:
        self.value_input.value = value
        self.params_input.value = ", ".join(params or [])
        self._apply_form()
