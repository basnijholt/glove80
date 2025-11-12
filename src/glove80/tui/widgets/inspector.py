"""Key Inspector tab implementation for Milestone 3."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional, Sequence, Literal

from textual import on
from textual.containers import Vertical, VerticalScroll
from textual.suggester import Suggester
from textual.widgets import Button, Input, Label, ListItem, ListView, Static, TabbedContent, TabPane

from ..messages import FooterMessage, SelectionChanged, StoreUpdated
from ..state import (
    LayoutStore,
    SelectionState,
    MacroPayload,
    HoldTapPayload,
    ComboPayload,
    ListenerPayload,
)
from ..services import BuilderBridge, FeatureDiff, ValidationIssue, ValidationResult, ValidationService


class InspectorPanel(Vertical):
    """Wrapper that will eventually host multiple tabs."""

    def __init__(self, *, store: LayoutStore, variant: str) -> None:
        super().__init__(classes="inspector-panel")
        self.store = store
        self._variant = variant
        self.key_inspector = KeyInspector(store=store)
        self.macro_tab = MacroTab(store=store)
        self.hold_tap_tab = HoldTapTab(store=store)
        self.combo_tab = ComboTab(store=store)
        self.listener_tab = ListenerTab(store=store)
        self.features_tab = FeaturesTab(store=store, variant=variant)

    def compose(self):  # type: ignore[override]
        yield Static("Inspector", classes="inspector-heading")
        with TabbedContent(initial="tab-key", id="inspector-tabs"):
            with TabPane("Key", id="tab-key"):
                with VerticalScroll(classes="inspector-scroll"):
                    yield self.key_inspector
            with TabPane("Macros", id="tab-macros"):
                with VerticalScroll(classes="inspector-scroll"):
                    yield self.macro_tab
            with TabPane("Hold Taps", id="tab-holdtaps"):
                with VerticalScroll(classes="inspector-scroll"):
                    yield self.hold_tap_tab
            with TabPane("Combos", id="tab-combos"):
                with VerticalScroll(classes="inspector-scroll"):
                    yield self.combo_tab
            with TabPane("Listeners", id="tab-listeners"):
                with VerticalScroll(classes="inspector-scroll"):
                    yield self.listener_tab
            with TabPane("Features", id="tab-features"):
                with VerticalScroll(classes="inspector-scroll"):
                    yield self.features_tab


class InspectorDrawer(Vertical):
    """Collapsible wrapper around the inspector stack."""

    def __init__(self, *, store: LayoutStore, variant: str, expanded: bool = False) -> None:
        super().__init__(classes="inspector-drawer")
        self.panel = InspectorPanel(store=store, variant=variant)
        self._expanded = expanded

    def compose(self):  # type: ignore[override]
        yield self.panel

    def on_mount(self) -> None:
        self._sync_state()

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._sync_state()

    def expand(self) -> None:
        if not self._expanded:
            self._expanded = True
            self._sync_state()

    def collapse(self) -> None:
        if self._expanded:
            self._expanded = False
            self._sync_state()

    @property
    def expanded(self) -> bool:
        return self._expanded

    def _sync_state(self) -> None:
        self.set_class(not self._expanded, "collapsed")


class KeyInspector(Vertical):
    """Minimal form that edits a single key binding."""

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="key-inspector", id="key-inspector")
        self.store = store
        self.validator = ValidationService(layer_names=self.store.layer_names)
        self._selection: SelectionState | None = None
        self.value_input = Input(
            placeholder="&kp",
            id="key-value",
            suggester=_BehaviorSuggester(self.validator),
        )
        self.params_input = Input(
            placeholder="Param list (e.g., KC_A, Base)",
            id="key-params",
            suggester=_ParamSuggester(self.validator),
        )
        self.json_input = Input(
            placeholder='{"value": "&kp", "params": [{"value": "A", "params": []}]}',
            id="key-json",
        )
        self.value_error = Static("", classes="validation-hint hidden")
        self.params_error = Static("", classes="validation-hint hidden")

    def compose(self):  # type: ignore[override]
        yield Label("Key Behavior")
        yield self.value_input
        yield self.value_error
        yield Label("Params (comma separated)")
        yield self.params_input
        yield self.params_error
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
        self.validator.update_layers(self.store.layer_names)
        self._selection = SelectionState(layer_index=event.layer_index, key_index=event.key_index)
        self._load_from_store()

    @on(StoreUpdated)
    def _handle_store_updated(self, _: StoreUpdated) -> None:
        if self._selection is None:
            return
        self.validator.update_layers(self.store.layer_names)
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
        display_value, display_params = _display_tokens(slot)
        self.value_input.value = display_value
        self.params_input.value = ", ".join(display_params)
        self.json_input.value = json.dumps(slot, separators=(",", ":"))
        self._render_validation(ValidationResult(display_value, tuple(), tuple()))

    def _toggle_inputs(self, enabled: bool) -> None:
        self.value_input.disabled = not enabled
        self.params_input.disabled = not enabled
        self.json_input.disabled = not enabled

    def _apply_form(self) -> None:
        if self._selection is None:
            return
        value, inline = self._split_value_tokens()
        manual_params = [p.strip() for p in self.params_input.value.split(",") if p.strip()]
        combined_params: list[str] = [*inline, *manual_params]

        result = self.validator.validate(value, combined_params)
        self._render_validation(result)
        if not result.is_valid:
            return

        self.store.update_selected_key(value=result.value, params=list(result.params))
        self.post_message(StoreUpdated())
        self._load_from_store()

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
        result = self.validator.validate(value, list(params))
        self._render_validation(result)
        if not result.is_valid:
            return
        self.store.update_selected_key(value=result.value, params=list(result.params))
        self.post_message(StoreUpdated())
        self._load_from_store()

    # ------------------------------------------------------------------
    # Test helper -------------------------------------------------------
    def apply_value_for_test(self, value: str, params: Sequence[str] | None = None) -> None:
        self.value_input.value = value
        self.params_input.value = ", ".join(params or [])
        self._apply_form()

    # ------------------------------------------------------------------
    def _split_value_tokens(self) -> tuple[str, list[str]]:
        raw = self.value_input.value.strip()
        if not raw:
            return "", []
        tokens = raw.split()
        if tokens[0].startswith("&") and len(tokens) > 1:
            return tokens[0], tokens[1:]
        return raw, []

    def _render_validation(self, result: ValidationResult) -> None:
        self._set_field_state(self.value_input, self.value_error, result.first_issue("value"))
        self._set_field_state(self.params_input, self.params_error, result.first_issue("params"))

    @staticmethod
    def _set_field_state(widget: Input, label: Static, issue: ValidationIssue | None) -> None:
        if issue:
            widget.add_class("input-error")
            label.update(issue.message)
            label.remove_class("hidden")
        else:
            widget.remove_class("input-error")
            label.update("")
            label.add_class("hidden")


class FeaturesTab(Vertical):
    """Minimal feature toggle surface for HRM bundles."""

    def __init__(self, *, store: LayoutStore, variant: str) -> None:
        super().__init__(classes="features-tab", id="features-tab")
        self.store = store
        self.bridge = BuilderBridge(store=store, variant=variant)
        self._pending_request: tuple[str, Literal["before", "after"]] | None = None
        self._diff: FeatureDiff | None = None
        self._summary_text = "HRM preview pending."
        self._has_pending_changes = False
        self.summary = Static(self._summary_text, id="feature-summary")
        self.preview_button = Button("Preview HRM", id="preview-hrm")
        self.apply_button = Button("Apply HRM", id="apply-hrm", disabled=True)
        self.clear_button = Button("Clear", id="clear-hrm", disabled=True)

    @property
    def current_summary(self) -> str:
        return self._summary_text

    @property
    def has_pending_changes(self) -> bool:
        return self._has_pending_changes

    def on_mount(self) -> None:
        # Ensure our handles reference the mounted widgets.
        self.summary = self.query_one("#feature-summary", Static)
        self.preview_button = self.query_one("#preview-hrm", Button)
        self.apply_button = self.query_one("#apply-hrm", Button)
        self.clear_button = self.query_one("#clear-hrm", Button)

    def compose(self):  # type: ignore[override]
        yield Static("Features", classes="features-heading")
        yield self.preview_button
        yield self.summary
        yield self.apply_button
        yield self.clear_button

    @on(Button.Pressed)
    def _handle_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "preview-hrm":
            self._preview_hrm()
        elif event.button.id == "apply-hrm":
            self._apply_hrm()
        elif event.button.id == "clear-hrm":
            self._clear_preview()

    def _preview_hrm(self) -> None:
        target = self._resolve_target_layer()
        if target is None:
            self.app.notify("No layers available")
            return
        try:
            diff = self.bridge.preview_home_row_mods(target_layer=target)
        except ValueError as exc:
            self.app.notify(str(exc))
            return
        self._diff = diff
        self._pending_request = (target, "after")
        self._set_summary(f"HRM → {target}: {diff.summary()}")
        has_changes = bool(
            diff.layers_added or diff.macros_added or diff.hold_taps_added or diff.combos_added or diff.listeners_added
        )
        self._has_pending_changes = has_changes
        self.apply_button.disabled = not has_changes
        self.clear_button.disabled = False
        self.post_message(FooterMessage(f"HRM preview · anchor={target} · {diff.summary()}"))

    def _apply_hrm(self) -> None:
        if self._pending_request is None:
            return
        target, position = self._pending_request
        try:
            diff = self.bridge.apply_home_row_mods(target_layer=target, position=position)
        except ValueError as exc:
            self.app.notify(str(exc))
            return
        self.post_message(StoreUpdated())
        self._set_summary(f"HRM applied to {target}: {diff.summary()}")
        self.post_message(FooterMessage(f"HRM applied · anchor={target} · {diff.summary()}"))
        self.apply_button.disabled = True
        self.clear_button.disabled = True
        self._pending_request = None
        self._diff = None
        self._has_pending_changes = False

    def _clear_preview(self) -> None:
        self._pending_request = None
        self._diff = None
        self._set_summary("HRM preview pending.")
        self.apply_button.disabled = True
        self.clear_button.disabled = True
        self.post_message(FooterMessage("HRM preview cleared"))
        self._has_pending_changes = False

    def _resolve_target_layer(self) -> str | None:
        if self.store.selected_layer_name:
            return self.store.selected_layer_name
        if self.store.layer_names:
            return self.store.layer_names[0]
        return None

    def _set_summary(self, text: str) -> None:
        self._summary_text = text
        self.summary.update(text)


class MacroTab(Vertical):
    """Macro list and detail editor."""

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="macro-tab", id="macro-tab")
        self.store = store
        self._selected_name: Optional[str] = None
        self._list = ListView(id="macro-list")
        self.name_input = Input(placeholder="&macro_name", id="macro-name-input")
        self.desc_input = Input(placeholder="Description", id="macro-desc-input")
        self.bindings_input = Input(placeholder="Bindings JSON", id="macro-bindings-input")
        self.params_input = Input(placeholder="Params JSON", id="macro-params-input")
        self.wait_ms_input = Input(placeholder="waitMs", id="macro-wait-input", value="0")
        self.tap_ms_input = Input(placeholder="tapMs", id="macro-tap-input", value="0")
        self.add_button = Button("Add", id="macro-add")
        self.apply_button = Button("Apply", id="macro-apply", disabled=True)
        self.delete_button = Button("Delete", id="macro-delete", disabled=True)
        self.ref_label = Static("", classes="macro-refs", id="macro-ref-summary")

    def compose(self):  # type: ignore[override]
        yield Static("Macros", classes="macro-heading")
        yield self._list
        yield Label("Name")
        yield self.name_input
        yield Label("Description")
        yield self.desc_input
        yield Label("Bindings (JSON array)")
        yield self.bindings_input
        yield Label("Params (JSON array)")
        yield self.params_input
        yield Label("Wait (ms)")
        yield self.wait_ms_input
        yield Label("Tap (ms)")
        yield self.tap_ms_input
        yield self.ref_label
        yield self.add_button
        yield self.apply_button
        yield self.delete_button

    def on_mount(self) -> None:
        self._refresh_list()

    @on(StoreUpdated)
    def _handle_store_updated(self, _: StoreUpdated) -> None:
        self._refresh_list(preferred=self._selected_name)

    @on(ListView.Selected)
    def _handle_list_selected(self, event: ListView.Selected) -> None:
        if event.list_view is not self._list:
            return
        item = event.item
        if not isinstance(item, _MacroListItem):
            return
        self._load_macro(item.macro)
        event.stop()

    @on(Button.Pressed)
    def _handle_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "macro-add":
            self._create_macro()
        elif event.button.id == "macro-apply":
            self._apply_macro()
        elif event.button.id == "macro-delete":
            self._delete_macro()

    def _refresh_list(self, *, preferred: Optional[str] = None) -> None:
        self.call_after_refresh(self._rebuild_list, preferred)

    async def _rebuild_list(self, preferred: Optional[str]) -> None:
        await self._list.clear()
        macros = list(self.store.list_macros())
        names = [str(macro.get("name", "")) for macro in macros]
        target_name = preferred if preferred in names else (names[0] if names else None)
        items: list[ListItem] = []
        for macro in macros:
            refs = self.store.find_macro_references(macro.get("name", ""))
            items.append(_MacroListItem(macro, _reference_count(refs)))
        if items:
            await self._list.mount(*items)
            index = 0
            if target_name:
                for idx, macro_name in enumerate(names):
                    if macro_name == target_name:
                        index = idx
                        break
            self._list.index = index
            selected_item = items[index]
            if isinstance(selected_item, _MacroListItem):
                self._load_macro(selected_item.macro)
            else:
                self._clear_form()
        else:
            await self._list.mount(ListItem(Static("(no macros)", classes="macro-item")))
            self._clear_form()

    def _load_macro(self, macro: Optional[MacroPayload]) -> None:
        if not macro:
            self._clear_form()
            return
        self._selected_name = str(macro.get("name", ""))
        self.name_input.value = self._selected_name
        self.desc_input.value = str(macro.get("description", ""))
        self.bindings_input.value = json.dumps(macro.get("bindings", []))
        self.params_input.value = json.dumps(macro.get("params", []))
        self.wait_ms_input.value = str(macro.get("waitMs", 0))
        self.tap_ms_input.value = str(macro.get("tapMs", 0))
        refs = self.store.find_macro_references(self._selected_name)
        count = _reference_count(refs)
        if count:
            self.ref_label.update(f"Referenced {count} time(s)")
        else:
            self.ref_label.update("No references")
        self._toggle_form(True)
        self.delete_button.disabled = bool(count)

    def _clear_form(self) -> None:
        self._selected_name = None
        self.name_input.value = ""
        self.desc_input.value = ""
        self.bindings_input.value = ""
        self.params_input.value = ""
        self.wait_ms_input.value = "0"
        self.tap_ms_input.value = "0"
        self.ref_label.update("")
        self._toggle_form(False)

    def _toggle_form(self, enabled: bool) -> None:
        self.apply_button.disabled = not enabled
        self.delete_button.disabled = not enabled

    def _create_macro(self) -> None:
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        name = payload["name"]
        try:
            self.store.add_macro(payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Added macro {name}"))
        self._refresh_list(preferred=name)

    def _apply_macro(self) -> None:
        if self._selected_name is None:
            return
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        try:
            self.store.update_macro(name=self._selected_name, payload=payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Updated macro {payload['name']}"))
        self._selected_name = payload["name"]
        self._refresh_list(preferred=self._selected_name)

    def _delete_macro(self) -> None:
        if self._selected_name is None:
            return
        refs = self.store.find_macro_references(self._selected_name)
        if _reference_count(refs):
            self.post_message(FooterMessage("Cannot delete macro with references"))
            return
        try:
            self.store.delete_macro(name=self._selected_name)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Deleted macro {self._selected_name}"))
        self._clear_form()
        self._refresh_list()

    def _build_payload_from_inputs(self) -> Optional[Dict[str, Any]]:
        name = self.name_input.value.strip()
        if not name:
            self.post_message(FooterMessage("Name is required"))
            return None
        try:
            bindings = json.loads(self.bindings_input.value or "[]")
            params = json.loads(self.params_input.value or "[]")
            wait_ms = int(self.wait_ms_input.value or "0")
            tap_ms = int(self.tap_ms_input.value or "0")
        except (json.JSONDecodeError, ValueError) as exc:
            self.post_message(FooterMessage(f"Invalid macro data: {exc}"))
            return None
        payload: Dict[str, Any] = {
            "name": name,
            "description": self.desc_input.value.strip(),
            "bindings": bindings,
            "params": params,
            "waitMs": wait_ms,
            "tapMs": tap_ms,
        }
        return payload


class _MacroListItem(ListItem):
    def __init__(self, macro: MacroPayload, ref_count: int) -> None:
        name = str(macro.get("name", "?"))
        label = f"{name} [{ref_count}]"
        super().__init__(Static(label, classes="macro-item"))
        self.macro = macro


class _HoldTapListItem(ListItem):
    def __init__(self, hold_tap: HoldTapPayload, ref_count: int) -> None:
        label = f"{hold_tap.get('name', '?')} [{ref_count}]"
        super().__init__(Static(label, classes="macro-item"))
        self.hold_tap = hold_tap


class _ComboListItem(ListItem):
    def __init__(self, combo: ComboPayload, ref_count: int) -> None:
        label = f"{combo.get('name', '?')} [{ref_count}]"
        super().__init__(Static(label, classes="macro-item"))
        self.combo = combo


class _ListenerListItem(ListItem):
    def __init__(self, listener: ListenerPayload, ref_count: int) -> None:
        label = f"{listener.get('code', '?')} [{ref_count}]"
        super().__init__(Static(label, classes="macro-item"))
        self.listener = listener


class ComboTab(Vertical):
    """Combo list and detail editor mirroring Macro/HoldTap tabs."""

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="combo-tab", id="combo-tab")
        self.store = store
        self._selected_name: Optional[str] = None
        self._list = ListView(id="combo-list")
        self.name_input = Input(placeholder="&combo_name", id="combo-name-input")
        self.desc_input = Input(placeholder="Description", id="combo-desc-input")
        self.binding_input = Input(placeholder='{"value":"&kp","params":["ESC"]}', id="combo-binding-input")
        self.positions_input = Input(placeholder="keyPositions (e.g. 0, 1)", id="combo-positions-input")
        self.layers_input = Input(placeholder="layers (e.g. Base, Raise)", id="combo-layers-input")
        self.timeout_input = Input(placeholder="timeoutMs", id="combo-timeout-input")
        self.ref_label = Static("", classes="macro-refs", id="combo-ref-summary")
        self.add_button = Button("Add", id="combo-add")
        self.apply_button = Button("Apply", id="combo-apply", disabled=True)
        self.delete_button = Button("Delete", id="combo-delete", disabled=True)

    def compose(self):  # type: ignore[override]
        yield Static("Combos", classes="macro-heading")
        yield self._list
        yield Label("Name")
        yield self.name_input
        yield Label("Description")
        yield self.desc_input
        yield Label("Binding (JSON)")
        yield self.binding_input
        yield Label("Key Positions")
        yield self.positions_input
        yield Label("Layers")
        yield self.layers_input
        yield Label("Timeout (ms)")
        yield self.timeout_input
        yield self.ref_label
        yield self.add_button
        yield self.apply_button
        yield self.delete_button

    def on_mount(self) -> None:
        self._refresh_list()

    @on(StoreUpdated)
    def _handle_store_update(self, _: StoreUpdated) -> None:
        self._refresh_list(preferred=self._selected_name)

    @on(ListView.Selected)
    def _handle_list_select(self, event: ListView.Selected) -> None:
        if event.list_view is not self._list:
            return
        if isinstance(event.item, _ComboListItem):
            self._load_combo(event.item.combo)
            event.stop()

    @on(Button.Pressed)
    def _handle_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "combo-add":
            self._create_combo()
        elif event.button.id == "combo-apply":
            self._apply_combo()
        elif event.button.id == "combo-delete":
            self._delete_combo()

    def _refresh_list(self, *, preferred: Optional[str] = None) -> None:
        self.call_after_refresh(self._rebuild_list, preferred)

    async def _rebuild_list(self, preferred: Optional[str]) -> None:
        await self._list.clear()
        combos = list(self.store.list_combos())
        names = [str(entry.get("name", "")) for entry in combos]
        target = preferred if preferred in names else (names[0] if names else None)
        items: list[ListItem] = []
        for combo in combos:
            refs = self.store.find_combo_references(combo.get("name", ""))
            items.append(_ComboListItem(combo, _reference_count(refs)))
        if items:
            await self._list.mount(*items)
            index = 0
            if target:
                for idx, entry in enumerate(names):
                    if entry == target:
                        index = idx
                        break
            self._list.index = index
            selected = items[index]
            if isinstance(selected, _ComboListItem):
                self._load_combo(selected.combo)
        else:
            await self._list.mount(ListItem(Static("(no combos)", classes="macro-item")))
            self._clear_form()

    def _load_combo(self, combo: ComboPayload) -> None:
        self._selected_name = str(combo.get("name", ""))
        self.name_input.value = self._selected_name
        self.desc_input.value = str(combo.get("description", ""))
        self.binding_input.value = json.dumps(combo.get("binding", {}))
        self.positions_input.value = ", ".join(str(pos) for pos in combo.get("keyPositions", []))
        layers = combo.get("layers", [])
        if layers:
            rendered = []
            for entry in layers:
                if isinstance(entry, dict) and "name" in entry:
                    rendered.append(str(entry["name"]))
                else:
                    rendered.append(str(entry))
            self.layers_input.value = ", ".join(rendered)
        else:
            self.layers_input.value = ""
        timeout = combo.get("timeoutMs")
        self.timeout_input.value = str(timeout) if timeout is not None else ""
        refs = self.store.find_combo_references(self._selected_name)
        count = _reference_count(refs)
        self.ref_label.update(f"Referenced {count} time(s)" if count else "No references")
        self.apply_button.disabled = False
        self.delete_button.disabled = bool(count)

    def _clear_form(self) -> None:
        self._selected_name = None
        self.name_input.value = ""
        self.desc_input.value = ""
        self.binding_input.value = ""
        self.positions_input.value = ""
        self.layers_input.value = ""
        self.timeout_input.value = ""
        self.ref_label.update("")
        self.apply_button.disabled = True
        self.delete_button.disabled = True

    def _create_combo(self) -> None:
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        try:
            self.store.add_combo(payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self._selected_name = payload["name"]
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Added combo {payload['name']}"))
        self._refresh_list(preferred=self._selected_name)

    def _apply_combo(self) -> None:
        if self._selected_name is None:
            return
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        try:
            self.store.update_combo(name=self._selected_name, payload=payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Updated combo {payload['name']}"))
        self._selected_name = payload["name"]
        self._refresh_list(preferred=self._selected_name)

    def _delete_combo(self) -> None:
        if self._selected_name is None:
            return
        try:
            self.store.delete_combo(name=self._selected_name)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Deleted combo {self._selected_name}"))
        self._selected_name = None
        self._refresh_list()

    def _build_payload_from_inputs(self) -> Optional[Dict[str, Any]]:
        name = self.name_input.value.strip()
        if not name:
            self.post_message(FooterMessage("Name is required"))
            return None
        try:
            binding = json.loads(self.binding_input.value or "{}")
        except json.JSONDecodeError as exc:
            self.post_message(FooterMessage(f"Invalid binding JSON: {exc}"))
            return None
        positions = self.positions_input.value.strip()
        if not positions:
            self.post_message(FooterMessage("keyPositions are required"))
            return None
        payload: Dict[str, Any] = {
            "name": name,
            "description": self.desc_input.value.strip(),
            "binding": binding,
            "keyPositions": positions,
            "layers": self.layers_input.value.strip(),
        }
        timeout = self.timeout_input.value.strip()
        if timeout:
            try:
                payload["timeoutMs"] = int(timeout)
            except ValueError:
                self.post_message(FooterMessage("timeoutMs must be an integer"))
                return None
        return payload


class ListenerTab(Vertical):
    """Listener list and detail editor."""

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="listener-tab", id="listener-tab")
        self.store = store
        self._selected_code: Optional[str] = None
        self._list = ListView(id="listener-list")
        self.code_input = Input(placeholder="listener_code", id="listener-code-input")
        self.layers_input = Input(placeholder="layers (e.g. Base, Raise or JSON)", id="listener-layers-input")
        self.processors_input = Input(placeholder="inputProcessors JSON", id="listener-processors-input")
        self.nodes_input = Input(placeholder="nodes JSON", id="listener-nodes-input")
        self.ref_label = Static("", classes="macro-refs", id="listener-ref-summary")
        self.add_button = Button("Add", id="listener-add")
        self.apply_button = Button("Apply", id="listener-apply", disabled=True)
        self.delete_button = Button("Delete", id="listener-delete", disabled=True)

    def compose(self):  # type: ignore[override]
        yield Static("Listeners", classes="macro-heading")
        yield self._list
        yield Label("Code")
        yield self.code_input
        yield Label("Layers")
        yield self.layers_input
        yield Label("Input Processors (JSON array)")
        yield self.processors_input
        yield Label("Nodes (JSON array)")
        yield self.nodes_input
        yield self.ref_label
        yield self.add_button
        yield self.apply_button
        yield self.delete_button

    def on_mount(self) -> None:
        self._refresh_list()

    @on(StoreUpdated)
    def _handle_store_update(self, _: StoreUpdated) -> None:
        self._refresh_list(preferred=self._selected_code)

    @on(ListView.Selected)
    def _handle_list_select(self, event: ListView.Selected) -> None:
        if event.list_view is not self._list:
            return
        if isinstance(event.item, _ListenerListItem):
            self._load_listener(event.item.listener)
            event.stop()

    @on(Button.Pressed)
    def _handle_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "listener-add":
            self._create_listener()
        elif event.button.id == "listener-apply":
            self._apply_listener()
        elif event.button.id == "listener-delete":
            self._delete_listener()

    def _refresh_list(self, *, preferred: Optional[str] = None) -> None:
        self.call_after_refresh(self._rebuild_list, preferred)

    async def _rebuild_list(self, preferred: Optional[str]) -> None:
        await self._list.clear()
        listeners = list(self.store.list_listeners())
        codes = [str(entry.get("code", "")) for entry in listeners]
        target = preferred if preferred in codes else (codes[0] if codes else None)
        items: list[ListItem] = []
        for listener in listeners:
            refs = self.store.find_listener_references(listener.get("code", ""))
            items.append(_ListenerListItem(listener, _reference_count(refs)))
        if items:
            await self._list.mount(*items)
            index = 0
            if target:
                for idx, code in enumerate(codes):
                    if code == target:
                        index = idx
                        break
            self._list.index = index
            selected = items[index]
            if isinstance(selected, _ListenerListItem):
                self._load_listener(selected.listener)
        else:
            await self._list.mount(ListItem(Static("(no listeners)", classes="macro-item")))
            self._clear_form()

    def _load_listener(self, listener: ListenerPayload) -> None:
        self._selected_code = str(listener.get("code", ""))
        self.code_input.value = self._selected_code
        layers = listener.get("layers")
        self.layers_input.value = json.dumps(layers) if layers else ""
        self.processors_input.value = json.dumps(listener.get("inputProcessors", []))
        self.nodes_input.value = json.dumps(listener.get("nodes", []))
        refs = self.store.find_listener_references(self._selected_code)
        count = _reference_count(refs)
        self.ref_label.update(f"Referenced {count} time(s)" if count else "No references")
        self.apply_button.disabled = False
        self.delete_button.disabled = bool(count)

    def _clear_form(self) -> None:
        self._selected_code = None
        self.code_input.value = ""
        self.layers_input.value = ""
        self.processors_input.value = ""
        self.nodes_input.value = ""
        self.ref_label.update("")
        self.apply_button.disabled = True
        self.delete_button.disabled = True

    def _create_listener(self) -> None:
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        try:
            self.store.add_listener(payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self._selected_code = payload["code"]
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Added listener {payload['code']}"))
        self._refresh_list(preferred=self._selected_code)

    def _apply_listener(self) -> None:
        if self._selected_code is None:
            return
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        try:
            self.store.update_listener(code=self._selected_code, payload=payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self._selected_code = payload["code"]
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Updated listener {payload['code']}"))
        self._refresh_list(preferred=self._selected_code)

    def _delete_listener(self) -> None:
        if self._selected_code is None:
            return
        refs = self.store.find_listener_references(self._selected_code)
        if _reference_count(refs):
            self.post_message(FooterMessage("Cannot delete listener with references"))
            return
        try:
            self.store.delete_listener(code=self._selected_code)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        code = self._selected_code
        self._selected_code = None
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Deleted listener {code}"))
        self._refresh_list()

    def _build_payload_from_inputs(self) -> Optional[Dict[str, Any]]:
        code = self.code_input.value.strip()
        if not code:
            self.post_message(FooterMessage("Code is required"))
            return None
        try:
            processors_raw = self.processors_input.value.strip() or "[]"
            processors = json.loads(processors_raw)
            nodes_raw = self.nodes_input.value.strip() or "[]"
            nodes = json.loads(nodes_raw)
        except json.JSONDecodeError as exc:
            self.post_message(FooterMessage(f"Invalid JSON: {exc}"))
            return None
        if not isinstance(processors, list):
            self.post_message(FooterMessage("inputProcessors must be a JSON array"))
            return None
        if not isinstance(nodes, list):
            self.post_message(FooterMessage("nodes must be a JSON array"))
            return None
        payload: Dict[str, Any] = {
            "code": code,
            "inputProcessors": processors,
            "nodes": nodes,
        }
        layers_raw = self.layers_input.value.strip()
        if layers_raw:
            try:
                payload["layers"] = json.loads(layers_raw)
            except json.JSONDecodeError:
                payload["layers"] = layers_raw
        return payload


# ---------------------------------------------------------------------------
class HoldTapTab(Vertical):
    """Hold-tap list and detail editor."""

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="holdtap-tab", id="holdtap-tab")
        self.store = store
        self._selected_name: Optional[str] = None
        self._list = ListView(id="holdtap-list")
        self.name_input = Input(placeholder="&hold_name", id="holdtap-name-input")
        self.desc_input = Input(placeholder="Description", id="holdtap-desc-input")
        self.bindings_input = Input(placeholder='Bindings JSON (e.g. ["&kp","A"])', id="holdtap-bindings-input")
        self.flavor_input = Input(placeholder="flavor", id="holdtap-flavor-input")
        self.tapping_input = Input(placeholder="tappingTermMs", id="holdtap-tapping-input", value="200")
        self.quick_input = Input(placeholder="quickTapMs", id="holdtap-quick-input", value="0")
        self.idle_input = Input(placeholder="requirePriorIdleMs", id="holdtap-idle-input", value="0")
        self.trigger_positions_input = Input(
            placeholder="holdTriggerKeyPositions (e.g. 0, 5)", id="holdtap-trigger-input"
        )
        self.trigger_release_input = Input(
            placeholder="holdTriggerOnRelease (true/false)", id="holdtap-onrelease-input"
        )
        self.ref_label = Static("", classes="macro-refs", id="holdtap-ref-summary")
        self.add_button = Button("Add", id="holdtap-add")
        self.apply_button = Button("Apply", id="holdtap-apply", disabled=True)
        self.delete_button = Button("Delete", id="holdtap-delete", disabled=True)

    def compose(self):  # type: ignore[override]
        yield Static("Hold Taps", classes="macro-heading")
        yield self._list
        yield Label("Name")
        yield self.name_input
        yield Label("Description")
        yield self.desc_input
        yield Label("Bindings (JSON array)")
        yield self.bindings_input
        yield Label("Flavor")
        yield self.flavor_input
        yield Label("Tapping term (ms)")
        yield self.tapping_input
        yield Label("Quick tap (ms)")
        yield self.quick_input
        yield Label("Require prior idle (ms)")
        yield self.idle_input
        yield Label("holdTriggerKeyPositions")
        yield self.trigger_positions_input
        yield Label("holdTriggerOnRelease")
        yield self.trigger_release_input
        yield self.ref_label
        yield self.add_button
        yield self.apply_button
        yield self.delete_button

    def on_mount(self) -> None:
        self._refresh_list()

    @on(StoreUpdated)
    def _handle_store_update(self, _: StoreUpdated) -> None:
        self._refresh_list(preferred=self._selected_name)

    @on(ListView.Selected)
    def _handle_list_select(self, event: ListView.Selected) -> None:
        if event.list_view is not self._list:
            return
        if isinstance(event.item, _HoldTapListItem):
            self._load_hold_tap(event.item.hold_tap)
            event.stop()

    @on(Button.Pressed)
    def _handle_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "holdtap-add":
            self._create_hold_tap()
        elif event.button.id == "holdtap-apply":
            self._apply_hold_tap()
        elif event.button.id == "holdtap-delete":
            self._delete_hold_tap()

    def _refresh_list(self, *, preferred: Optional[str] = None) -> None:
        self.call_after_refresh(self._rebuild_list, preferred)

    async def _rebuild_list(self, preferred: Optional[str]) -> None:
        await self._list.clear()
        hold_taps = list(self.store.list_hold_taps())
        names = [str(entry.get("name", "")) for entry in hold_taps]
        target = preferred if preferred in names else (names[0] if names else None)
        items: list[ListItem] = []
        for hold in hold_taps:
            refs = self.store.find_hold_tap_references(hold.get("name", ""))
            items.append(_HoldTapListItem(hold, _reference_count(refs)))
        if items:
            await self._list.mount(*items)
            index = 0
            if target:
                for idx, entry in enumerate(names):
                    if entry == target:
                        index = idx
                        break
            self._list.index = index
            selected = items[index]
            if isinstance(selected, _HoldTapListItem):
                self._load_hold_tap(selected.hold_tap)
        else:
            await self._list.mount(ListItem(Static("(no hold taps)", classes="macro-item")))
            self._clear_form()

    def _load_hold_tap(self, hold_tap: HoldTapPayload) -> None:
        self._selected_name = str(hold_tap.get("name", ""))
        self.name_input.value = self._selected_name
        self.desc_input.value = str(hold_tap.get("description", ""))
        self.bindings_input.value = json.dumps(hold_tap.get("bindings", []))
        self.flavor_input.value = str(hold_tap.get("flavor", ""))
        self.tapping_input.value = str(hold_tap.get("tappingTermMs", ""))
        self.quick_input.value = str(hold_tap.get("quickTapMs", ""))
        self.idle_input.value = str(hold_tap.get("requirePriorIdleMs", ""))
        positions = hold_tap.get("holdTriggerKeyPositions")
        if positions:
            self.trigger_positions_input.value = ", ".join(str(pos) for pos in positions)
        else:
            self.trigger_positions_input.value = ""
        release = hold_tap.get("holdTriggerOnRelease")
        self.trigger_release_input.value = "true" if release else ""
        refs = self.store.find_hold_tap_references(self._selected_name)
        count = _reference_count(refs)
        self.ref_label.update(f"Referenced {count} time(s)" if count else "No references")
        self.apply_button.disabled = False
        self.delete_button.disabled = bool(count)

    def _clear_form(self) -> None:
        self._selected_name = None
        self.name_input.value = ""
        self.desc_input.value = ""
        self.bindings_input.value = ""
        self.flavor_input.value = ""
        self.tapping_input.value = "200"
        self.quick_input.value = "0"
        self.idle_input.value = "0"
        self.trigger_positions_input.value = ""
        self.trigger_release_input.value = ""
        self.ref_label.update("")
        self.apply_button.disabled = True
        self.delete_button.disabled = True

    def _create_hold_tap(self) -> None:
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        try:
            self.store.add_hold_tap(payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Added hold tap {payload['name']}"))
        self._refresh_list(preferred=payload["name"])

    def _apply_hold_tap(self) -> None:
        if self._selected_name is None:
            return
        payload = self._build_payload_from_inputs()
        if payload is None:
            return
        try:
            self.store.update_hold_tap(name=self._selected_name, payload=payload)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Updated hold tap {payload['name']}"))
        self._selected_name = payload["name"]
        self._refresh_list(preferred=self._selected_name)

    def _delete_hold_tap(self) -> None:
        if self._selected_name is None:
            return
        try:
            self.store.delete_hold_tap(name=self._selected_name)
        except ValueError as exc:
            self.post_message(FooterMessage(str(exc)))
            return
        self.post_message(StoreUpdated())
        self.post_message(FooterMessage(f"Deleted hold tap {self._selected_name}"))
        self._selected_name = None
        self._refresh_list()

    def _build_payload_from_inputs(self) -> Optional[Dict[str, Any]]:
        name = self.name_input.value.strip()
        if not name:
            self.post_message(FooterMessage("Name is required"))
            return None
        try:
            bindings = json.loads(self.bindings_input.value or "[]")
        except json.JSONDecodeError as exc:
            self.post_message(FooterMessage(f"Invalid bindings JSON: {exc}"))
            return None
        payload: Dict[str, Any] = {
            "name": name,
            "description": self.desc_input.value.strip(),
            "bindings": bindings,
        }
        for field, widget in (
            ("tappingTermMs", self.tapping_input),
            ("quickTapMs", self.quick_input),
            ("requirePriorIdleMs", self.idle_input),
        ):
            text = widget.value.strip()
            if text:
                try:
                    payload[field] = int(text)
                except ValueError:
                    self.post_message(FooterMessage(f"{field} must be an integer"))
                    return None
        flavor = self.flavor_input.value.strip()
        if flavor:
            payload["flavor"] = flavor
        triggers = self.trigger_positions_input.value.strip()
        if triggers:
            payload["holdTriggerKeyPositions"] = triggers
        on_release = self.trigger_release_input.value.strip().lower()
        if on_release in {"true", "1", "yes", "on"}:
            payload["holdTriggerOnRelease"] = True
        elif on_release in {"false", "0", "no", "off"}:
            payload["holdTriggerOnRelease"] = False
        return payload


# ---------------------------------------------------------------------------
def _display_tokens(slot: dict[str, object]) -> tuple[str, list[str]]:
    raw_value = str(slot.get("value", ""))
    params = slot.get("params", [])

    if (not params) and raw_value.startswith("&") and " " in raw_value:
        pieces = raw_value.split()
        return pieces[0], pieces[1:]

    tokens: list[str] = []
    if isinstance(params, Sequence) and not isinstance(params, (str, bytes)):
        for entry in params:
            if isinstance(entry, dict):
                if "value" in entry:
                    tokens.append(str(entry.get("value")))
                elif "name" in entry:
                    tokens.append(str(entry.get("name")))
                else:
                    tokens.append(json.dumps(entry))
            else:
                tokens.append(str(entry))
    return raw_value, tokens


def _reference_count(refs: Mapping[str, Sequence[Dict[str, Any]]]) -> int:
    return sum(len(entries) for entries in refs.values())


class _BehaviorSuggester(Suggester):
    def __init__(self, validator: ValidationService) -> None:
        super().__init__(use_cache=False)
        self._validator = validator

    async def get_suggestion(self, value: str) -> str | None:  # pragma: no cover - UI glue
        suggestions = self._validator.suggest_behaviors(value.strip(), limit=1)
        return suggestions[0] if suggestions else None


class _ParamSuggester(Suggester):
    def __init__(self, validator: ValidationService) -> None:
        super().__init__(use_cache=False)
        self._validator = validator

    async def get_suggestion(self, value: str) -> str | None:  # pragma: no cover - UI glue
        token = value.split(",")[-1].strip()
        if not token:
            return None
        keycode = self._validator.suggest_keycodes(token, limit=1)
        if keycode:
            return keycode[0]
        layer = self._validator.suggest_layers(token, limit=1)
        if layer:
            return layer[0]
        return None
