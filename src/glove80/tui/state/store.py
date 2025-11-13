"""State management for the Glove80 TUI (Milestone 2)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


LayerPayload = List[Dict[str, Any]]
ComboPayload = Dict[str, Any]
ListenerPayload = Dict[str, Any]
MacroPayload = Dict[str, Any]
HoldTapPayload = Dict[str, Any]


def _ensure_tuple(items: Iterable[Any]) -> Tuple[Any, ...]:
    return tuple(items)


@dataclass(frozen=True)
class LayerRecord:
    name: str
    slots: Tuple[Dict[str, Any], ...]


@dataclass(frozen=True)
class LayoutState:
    layer_names: Tuple[str, ...]
    layers: Tuple[LayerRecord, ...]
    macros: Tuple[MacroPayload, ...]
    hold_taps: Tuple[HoldTapPayload, ...]
    combos: Tuple[ComboPayload, ...]
    listeners: Tuple[ListenerPayload, ...]

    @staticmethod
    def from_payload(payload: Mapping[str, Any]) -> LayoutState:
        layer_names = tuple(payload.get("layer_names", []))
        layer_records = []
        for name, slots in zip(layer_names, payload.get("layers", [])):
            layer_records.append(LayerRecord(name=name, slots=_ensure_tuple(deepcopy(slots))))
        macros = tuple(deepcopy(payload.get("macros", [])))
        hold_taps = tuple(deepcopy(payload.get("holdTaps", [])))
        combos = tuple(deepcopy(payload.get("combos", [])))
        listeners = tuple(deepcopy(payload.get("inputListeners", [])))
        return LayoutState(
            layer_names=tuple(layer_names),
            layers=tuple(layer_records),
            macros=macros,
            hold_taps=hold_taps,
            combos=combos,
            listeners=listeners,
        )


@dataclass(frozen=True)
class SelectionState:
    """Tracks the active layer/key pair for the UI."""

    layer_index: int
    key_index: int


class LayoutStore:
    """Mutable state container with undo/redo support."""

    def __init__(self, state: LayoutState) -> None:
        self._state = state
        self._undo_stack: List[LayoutState] = []
        self._redo_stack: List[LayoutState] = []
        self._clipboard: Optional[LayerRecord] = None
        self._selection = SelectionState(layer_index=0 if state.layers else -1, key_index=0 if state.layers else -1)
        self._clamp_selection()

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> LayoutStore:
        return cls(LayoutState.from_payload(payload))

    # ------------------------------------------------------------------
    # Properties
    @property
    def state(self) -> LayoutState:
        return self._state

    @property
    def layer_names(self) -> Tuple[str, ...]:
        return self._state.layer_names

    @property
    def selection(self) -> SelectionState:
        return self._selection

    @property
    def selected_layer_name(self) -> Optional[str]:
        if self._selection.layer_index < 0:
            return None
        if self._selection.layer_index >= len(self._state.layer_names):
            return None
        return self._state.layer_names[self._selection.layer_index]

    # ------------------------------------------------------------------
    # Public API
    def rename_layer(self, *, old_name: str, new_name: str) -> None:
        if old_name == new_name:
            return
        if old_name not in self._state.layer_names:
            raise ValueError(f"Unknown layer '{old_name}'")
        if new_name in self._state.layer_names:
            raise ValueError(f"Layer '{new_name}' already exists")
        rename_map = {old_name: new_name}
        self._record_snapshot()
        layer_names = tuple(new_name if name == old_name else name for name in self._state.layer_names)
        layers = []
        for record in self._state.layers:
            updated = record
            if record.name == old_name:
                updated = replace(record, name=new_name)
            updated_slots = tuple(_rewrite_layer_refs(slot, rename_map) for slot in updated.slots)
            updated = replace(updated, slots=updated_slots)
            layers.append(updated)
        macros = tuple(_rewrite_layer_refs(macro, rename_map) for macro in self._state.macros)
        hold_taps = tuple(_rewrite_layer_refs(hold, rename_map) for hold in self._state.hold_taps)
        combos = tuple(_rewrite_layer_refs(combo, rename_map) for combo in self._state.combos)
        listeners = tuple(_rewrite_layer_refs(listener, rename_map) for listener in self._state.listeners)
        self._state = LayoutState(
            layer_names=layer_names,
            layers=tuple(layers),
            macros=macros,
            hold_taps=hold_taps,
            combos=combos,
            listeners=listeners,
        )
        self._redo_stack.clear()

    def reorder_layer(self, *, source_index: int, dest_index: int) -> None:
        size = len(self._state.layer_names)
        if not (0 <= source_index < size and 0 <= dest_index < size):
            raise IndexError("Layer index out of range")
        if source_index == dest_index:
            return
        self._record_snapshot()
        names = list(self._state.layer_names)
        record = names.pop(source_index)
        names.insert(dest_index, record)
        layers = list(self._state.layers)
        layer_record = layers.pop(source_index)
        layers.insert(dest_index, layer_record)
        self._state = LayoutState(
            layer_names=tuple(names),
            layers=tuple(layers),
            macros=self._state.macros,
            hold_taps=self._state.hold_taps,
            combos=self._state.combos,
            listeners=self._state.listeners,
        )
        self._redo_stack.clear()

    def duplicate_layer(self, *, source_name: str, new_name: Optional[str] = None, insert_after: bool = True) -> None:
        if source_name not in self._state.layer_names:
            raise ValueError(f"Unknown layer '{source_name}'")
        new_name = new_name or _increment_name(source_name, set(self._state.layer_names))
        if new_name in self._state.layer_names:
            raise ValueError(f"Layer '{new_name}' already exists")
        self._record_snapshot()
        index = self._state.layer_names.index(source_name)
        insert_index = index + 1 if insert_after else index
        layer_names = list(self._state.layer_names)
        layer_names.insert(insert_index, new_name)
        layers = list(self._state.layers)
        source_layer = layers[index]
        layers.insert(insert_index, LayerRecord(name=new_name, slots=tuple(deepcopy(source_layer.slots))))
        self._state = LayoutState(
            layer_names=tuple(layer_names),
            layers=tuple(layers),
            macros=self._state.macros,
            hold_taps=self._state.hold_taps,
            combos=self._state.combos,
            listeners=self._state.listeners,
        )
        self._redo_stack.clear()

    def pick_up_layer(self, *, name: str) -> None:
        if name not in self._state.layer_names:
            raise ValueError(f"Unknown layer '{name}'")
        index = self._state.layer_names.index(name)
        self._clipboard = self._state.layers[index]

    def drop_layer(self, *, target_index: int) -> None:
        if self._clipboard is None:
            return
        size = len(self._state.layer_names)
        if not (0 <= target_index <= size):
            raise IndexError("Layer index out of range")
        self._record_snapshot()
        names = list(self._state.layer_names)
        layers = list(self._state.layers)
        if self._clipboard.name in names:
            orig_index = names.index(self._clipboard.name)
            names.pop(orig_index)
            layers.pop(orig_index)
            if orig_index < target_index:
                target_index -= 1
        names.insert(target_index, self._clipboard.name)
        layers.insert(target_index, self._clipboard)
        self._state = LayoutState(
            layer_names=tuple(names),
            layers=tuple(layers),
            macros=self._state.macros,
            hold_taps=self._state.hold_taps,
            combos=self._state.combos,
            listeners=self._state.listeners,
        )
        self._redo_stack.clear()

    # ------------------------------------------------------------------
    # Selection helpers
    def set_selection(self, *, layer_index: int, key_index: int) -> SelectionState:
        self._selection = SelectionState(
            layer_index=self._validate_layer_index(layer_index),
            key_index=self._validate_key_index(layer_index, key_index),
        )
        return self._selection

    def set_active_layer(self, layer_index: int) -> SelectionState:
        if not self._state.layers:
            self._selection = SelectionState(layer_index=-1, key_index=-1)
            return self._selection
        valid_layer = self._validate_layer_index(layer_index)
        key_index = self._selection.key_index if self._selection.layer_index >= 0 else 0
        key_index = self._validate_key_index(valid_layer, key_index)
        self._selection = SelectionState(layer_index=valid_layer, key_index=key_index)
        return self._selection

    def set_selected_key(self, key_index: int) -> SelectionState:
        if not self._state.layers:
            self._selection = SelectionState(layer_index=-1, key_index=-1)
            return self._selection
        layer_index = self._selection.layer_index if self._selection.layer_index >= 0 else 0
        layer_index = self._validate_layer_index(layer_index)
        self._selection = SelectionState(
            layer_index=layer_index,
            key_index=self._validate_key_index(layer_index, key_index),
        )
        return self._selection

    def copy_key_to_layer(
        self,
        *,
        source_layer_index: int,
        target_layer_index: int,
        key_index: int,
    ) -> bool:
        """Copy the key binding from one layer to another.

        Returns True if a mutation occurred.
        """

        if not self._state.layers:
            raise ValueError("No layers available")

        source_layer_index = self._validate_layer_index(source_layer_index)
        target_layer_index = self._validate_layer_index(target_layer_index)
        if source_layer_index == target_layer_index:
            return False

        source_key_index = self._validate_key_index(source_layer_index, key_index)
        target_key_index = self._validate_key_index(target_layer_index, key_index)

        source_slot = self._state.layers[source_layer_index].slots[source_key_index]
        target_slot = self._state.layers[target_layer_index].slots[target_key_index]
        if source_slot == target_slot:
            return False

        self._record_snapshot()
        layers = list(self._state.layers)
        target_layer = layers[target_layer_index]
        slots = list(target_layer.slots)
        slots[target_key_index] = deepcopy(source_slot)
        layers[target_layer_index] = replace(target_layer, slots=tuple(slots))
        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=tuple(layers),
            macros=self._state.macros,
            hold_taps=self._state.hold_taps,
            combos=self._state.combos,
            listeners=self._state.listeners,
        )
        self._redo_stack.clear()
        return True

    def get_key(self, *, layer_index: Optional[int] = None, key_index: Optional[int] = None) -> Dict[str, Any]:
        if not self._state.layers:
            raise ValueError("No layers available")
        resolved_layer = layer_index if layer_index is not None else self._selection.layer_index
        resolved_key = key_index if key_index is not None else self._selection.key_index
        resolved_layer = self._validate_layer_index(resolved_layer)
        resolved_key = self._validate_key_index(resolved_layer, resolved_key)
        slot = self._state.layers[resolved_layer].slots[resolved_key]
        return deepcopy(slot)

    def update_key(
        self,
        *,
        layer_index: int,
        key_index: int,
        value: str,
        params: Sequence[Any],
    ) -> None:
        if not value:
            raise ValueError("Key value cannot be empty")
        layer_index = self._validate_layer_index(layer_index)
        key_index = self._validate_key_index(layer_index, key_index)
        self._record_snapshot()
        layers = list(self._state.layers)
        target = layers[layer_index]
        slots = list(target.slots)
        slots[key_index] = {"value": value, "params": list(params)}
        layers[layer_index] = replace(target, slots=tuple(deepcopy(slot) for slot in slots))
        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=tuple(layers),
            macros=self._state.macros,
            hold_taps=self._state.hold_taps,
            combos=self._state.combos,
            listeners=self._state.listeners,
        )
        self._redo_stack.clear()

    def update_selected_key(self, *, value: str, params: Sequence[Any]) -> None:
        if self._selection.layer_index < 0 or self._selection.key_index < 0:
            raise ValueError("No key selected")
        self.update_key(
            layer_index=self._selection.layer_index,
            key_index=self._selection.key_index,
            value=value,
            params=params,
        )

    # ------------------------------------------------------------------
    # Macro management API
    def list_macros(self) -> Tuple[MacroPayload, ...]:
        """Return a deep copy of the current macro payloads."""

        return tuple(deepcopy(macro) for macro in self._state.macros)

    def find_macro_references(self, name: str) -> Dict[str, Tuple[Dict[str, Any], ...]]:
        """Locate every reference to *name* across the layout."""

        references: Dict[str, List[Dict[str, Any]]] = {
            "keys": [],
            "hold_taps": [],
            "combos": [],
            "listeners": [],
            "macros": [],
        }

        for layer_index, record in enumerate(self._state.layers):
            for key_index, slot in enumerate(record.slots):
                if slot.get("value") == name:
                    references["keys"].append(
                        {
                            "layer_index": layer_index,
                            "layer_name": record.name,
                            "key_index": key_index,
                        }
                    )

        for index, hold in enumerate(self._state.hold_taps):
            if _contains_string(hold, name):
                references["hold_taps"].append({"index": index, "name": hold.get("name")})

        for index, combo in enumerate(self._state.combos):
            binding = combo.get("binding")
            if _contains_string(binding, name):
                references["combos"].append({"index": index, "name": combo.get("name")})

        for index, listener in enumerate(self._state.listeners):
            if _contains_string(listener, name):
                references["listeners"].append({"index": index, "code": listener.get("code")})

        for index, macro in enumerate(self._state.macros):
            if macro.get("name") == name:
                continue
            if _contains_string(macro, name):
                references["macros"].append({"index": index, "name": macro.get("name")})

        return {key: tuple(entries) for key, entries in references.items()}

    def add_macro(self, macro: Mapping[str, Any]) -> None:
        normalized = _normalize_macro_payload(macro)
        name = normalized["name"]
        self._ensure_macro_name_available(name)
        self._record_snapshot()
        macros = list(self._state.macros)
        macros.append(normalized)
        self._state = replace(self._state, macros=tuple(macros))
        self._redo_stack.clear()

    def update_macro(self, *, name: str, payload: Mapping[str, Any]) -> None:
        index = self._macro_index(name)
        normalized = _normalize_macro_payload(payload)
        new_name = normalized["name"]
        rename_map: Dict[str, str] = {}
        if new_name != name:
            self._ensure_macro_name_available(new_name)
            rename_map = {name: new_name}

        self._record_snapshot()
        macros = list(self._state.macros)
        macros[index] = normalized
        if rename_map:
            macros = [
                normalized if idx == index else _replace_strings(macro, rename_map) for idx, macro in enumerate(macros)
            ]
        layers = self._rewrite_layers_with_macros(rename_map) if rename_map else self._state.layers
        combos = (
            self._rewrite_sequence_with_macros(self._state.combos, rename_map) if rename_map else self._state.combos
        )
        hold_taps = (
            self._rewrite_sequence_with_macros(self._state.hold_taps, rename_map)
            if rename_map
            else self._state.hold_taps
        )
        listeners = (
            self._rewrite_sequence_with_macros(self._state.listeners, rename_map)
            if rename_map
            else self._state.listeners
        )
        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=tuple(macros),
            hold_taps=hold_taps,
            combos=combos,
            listeners=listeners,
        )
        self._redo_stack.clear()

    def delete_macro(self, *, name: str, force: bool = False) -> None:
        index = self._macro_index(name)
        references = self.find_macro_references(name)
        has_refs = any(references[key] for key in ("keys", "hold_taps", "combos", "listeners", "macros"))
        if has_refs and not force:
            raise ValueError(f"Macro '{name}' is referenced and cannot be deleted")

        self._record_snapshot()
        macros = list(self._state.macros)
        macros.pop(index)
        if has_refs:
            cleanup_map = {name: ""}
            layers = self._rewrite_layers_with_macros(cleanup_map)
            combos = self._rewrite_sequence_with_macros(self._state.combos, cleanup_map)
            hold_taps = self._rewrite_sequence_with_macros(self._state.hold_taps, cleanup_map)
            listeners = self._rewrite_sequence_with_macros(self._state.listeners, cleanup_map)
            macros = [_replace_strings(macro, cleanup_map) if macro.get("name") != name else macro for macro in macros]
        else:
            layers = self._state.layers
            combos = self._state.combos
            hold_taps = self._state.hold_taps
            listeners = self._state.listeners

        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=tuple(macros),
            hold_taps=hold_taps,
            combos=combos,
            listeners=listeners,
        )
        self._redo_stack.clear()

    # ------------------------------------------------------------------
    # Hold-tap management API
    def list_hold_taps(self) -> Tuple[HoldTapPayload, ...]:
        return tuple(deepcopy(hold) for hold in self._state.hold_taps)

    def find_hold_tap_references(self, name: str) -> Dict[str, Tuple[Dict[str, Any], ...]]:
        references: Dict[str, List[Dict[str, Any]]] = {
            "keys": [],
            "macros": [],
            "hold_taps": [],
            "combos": [],
            "listeners": [],
        }

        for layer_index, record in enumerate(self._state.layers):
            for key_index, slot in enumerate(record.slots):
                if slot.get("value") == name:
                    references["keys"].append(
                        {
                            "layer_index": layer_index,
                            "layer_name": record.name,
                            "key_index": key_index,
                        }
                    )

        for index, macro in enumerate(self._state.macros):
            if _contains_string(macro, name):
                references["macros"].append({"index": index, "name": macro.get("name")})

        for index, hold in enumerate(self._state.hold_taps):
            if hold.get("name") == name:
                continue
            if _contains_string(hold, name):
                references["hold_taps"].append({"index": index, "name": hold.get("name")})

        for index, combo in enumerate(self._state.combos):
            if _contains_string(combo, name):
                references["combos"].append({"index": index, "name": combo.get("name")})

        for index, listener in enumerate(self._state.listeners):
            if _contains_string(listener, name):
                references["listeners"].append({"index": index, "code": listener.get("code")})

        return {key: tuple(entries) for key, entries in references.items()}

    def add_hold_tap(self, hold_tap: Mapping[str, Any]) -> None:
        normalized = _normalize_hold_tap_payload(hold_tap)
        name = normalized["name"]
        self._ensure_hold_tap_name_available(name)
        self._record_snapshot()
        hold_taps = list(self._state.hold_taps)
        hold_taps.append(normalized)
        self._state = replace(self._state, hold_taps=tuple(hold_taps))
        self._redo_stack.clear()

    def update_hold_tap(self, *, name: str, payload: Mapping[str, Any]) -> None:
        index = self._hold_tap_index(name)
        normalized = _normalize_hold_tap_payload(payload)
        new_name = normalized["name"]
        rename_map: Dict[str, str] = {}
        if new_name != name:
            self._ensure_hold_tap_name_available(new_name)
            rename_map = {name: new_name}

        self._record_snapshot()
        hold_taps = list(self._state.hold_taps)
        hold_taps[index] = normalized
        if rename_map:
            hold_taps = [
                normalized if idx == index else _replace_strings(hold, rename_map) for idx, hold in enumerate(hold_taps)
            ]

        layers = self._rewrite_layers_with_macros(rename_map) if rename_map else self._state.layers
        macros = (
            self._rewrite_sequence_with_macros(self._state.macros, rename_map) if rename_map else self._state.macros
        )
        combos = (
            self._rewrite_sequence_with_macros(self._state.combos, rename_map) if rename_map else self._state.combos
        )
        listeners = (
            self._rewrite_sequence_with_macros(self._state.listeners, rename_map)
            if rename_map
            else self._state.listeners
        )

        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=macros,
            hold_taps=tuple(hold_taps),
            combos=combos,
            listeners=listeners,
        )
        self._redo_stack.clear()

    def rename_hold_tap(self, *, old_name: str, new_name: str) -> None:
        normalized_new = new_name if new_name.startswith("&") else f"&{new_name}"
        index = self._hold_tap_index(old_name)
        existing = deepcopy(self._state.hold_taps[index])
        existing["name"] = normalized_new
        self.update_hold_tap(name=old_name, payload=existing)

    def delete_hold_tap(self, *, name: str, force: bool = False) -> None:
        index = self._hold_tap_index(name)
        references = self.find_hold_tap_references(name)
        has_refs = any(references[key] for key in references)
        if has_refs and not force:
            raise ValueError(f"HoldTap '{name}' is referenced and cannot be deleted")

        self._record_snapshot()
        hold_taps = list(self._state.hold_taps)
        hold_taps.pop(index)
        if has_refs:
            cleanup_map = {name: ""}
            layers = self._rewrite_layers_with_macros(cleanup_map)
            macros = self._rewrite_sequence_with_macros(self._state.macros, cleanup_map)
            combos = self._rewrite_sequence_with_macros(self._state.combos, cleanup_map)
            listeners = self._rewrite_sequence_with_macros(self._state.listeners, cleanup_map)
            hold_taps = [
                _replace_strings(hold, cleanup_map) if hold.get("name") != name else hold for hold in hold_taps
            ]
        else:
            layers = self._state.layers
            macros = self._state.macros
            combos = self._state.combos
            listeners = self._state.listeners

        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=macros,
            hold_taps=tuple(hold_taps),
            combos=combos,
            listeners=listeners,
        )
        self._redo_stack.clear()

    # ------------------------------------------------------------------
    # Combo management API
    def list_combos(self) -> Tuple[ComboPayload, ...]:
        return tuple(deepcopy(combo) for combo in self._state.combos)

    def find_combo_references(self, name: str) -> Dict[str, Tuple[Dict[str, Any], ...]]:
        references: Dict[str, List[Dict[str, Any]]] = {
            "keys": [],
            "macros": [],
            "hold_taps": [],
            "combos": [],
            "listeners": [],
        }

        for layer_index, record in enumerate(self._state.layers):
            for key_index, slot in enumerate(record.slots):
                if slot.get("value") == name:
                    references["keys"].append(
                        {
                            "layer_index": layer_index,
                            "layer_name": record.name,
                            "key_index": key_index,
                        }
                    )

        for index, macro in enumerate(self._state.macros):
            if _contains_string(macro, name):
                references["macros"].append({"index": index, "name": macro.get("name")})

        for index, hold in enumerate(self._state.hold_taps):
            if _contains_string(hold, name):
                references["hold_taps"].append({"index": index, "name": hold.get("name")})

        for index, combo in enumerate(self._state.combos):
            if combo.get("name") == name:
                continue
            if _contains_string(combo, name):
                references["combos"].append({"index": index, "name": combo.get("name")})

        for index, listener in enumerate(self._state.listeners):
            if _contains_string(listener, name):
                references["listeners"].append({"index": index, "code": listener.get("code")})

        return {key: tuple(entries) for key, entries in references.items()}

    def add_combo(self, combo: Mapping[str, Any]) -> None:
        normalized = _normalize_combo_payload(combo)
        self._assert_combo_layers_valid(normalized.get("layers", ()))
        name = normalized["name"]
        self._ensure_combo_name_available(name)
        self._record_snapshot()
        combos = list(self._state.combos)
        combos.append(normalized)
        self._state = replace(self._state, combos=tuple(combos))
        self._redo_stack.clear()

    def update_combo(self, *, name: str, payload: Mapping[str, Any]) -> None:
        index = self._combo_index(name)
        normalized = _normalize_combo_payload(payload)
        self._assert_combo_layers_valid(normalized.get("layers", ()))
        new_name = normalized["name"]
        rename_map: Dict[str, str] = {}
        if new_name != name:
            self._ensure_combo_name_available(new_name)
            rename_map = {name: new_name}

        self._record_snapshot()
        combos = list(self._state.combos)
        combos[index] = normalized
        if rename_map:
            combos = [
                normalized if idx == index else _replace_strings(combo, rename_map) for idx, combo in enumerate(combos)
            ]

        layers = self._rewrite_layers_with_macros(rename_map) if rename_map else self._state.layers
        macros = (
            self._rewrite_sequence_with_macros(self._state.macros, rename_map) if rename_map else self._state.macros
        )
        hold_taps = (
            self._rewrite_sequence_with_macros(self._state.hold_taps, rename_map)
            if rename_map
            else self._state.hold_taps
        )
        listeners = (
            self._rewrite_sequence_with_macros(self._state.listeners, rename_map)
            if rename_map
            else self._state.listeners
        )

        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=macros,
            hold_taps=hold_taps,
            combos=tuple(combos),
            listeners=listeners,
        )
        self._redo_stack.clear()

    def rename_combo(self, *, old_name: str, new_name: str) -> None:
        normalized_new = new_name if new_name.startswith("&") else f"&{new_name}"
        combo = deepcopy(self._state.combos[self._combo_index(old_name)])
        combo["name"] = normalized_new
        self.update_combo(name=old_name, payload=combo)

    def delete_combo(self, *, name: str, force: bool = False) -> None:
        index = self._combo_index(name)
        references = self.find_combo_references(name)
        has_refs = any(references[key] for key in references)
        if has_refs and not force:
            raise ValueError(f"Combo '{name}' is referenced and cannot be deleted")

        self._record_snapshot()
        combos = list(self._state.combos)
        combos.pop(index)
        if has_refs:
            cleanup_map = {name: ""}
            layers = self._rewrite_layers_with_macros(cleanup_map)
            macros = self._rewrite_sequence_with_macros(self._state.macros, cleanup_map)
            hold_taps = self._rewrite_sequence_with_macros(self._state.hold_taps, cleanup_map)
            listeners = self._rewrite_sequence_with_macros(self._state.listeners, cleanup_map)
            combos = [_replace_strings(combo, cleanup_map) if combo.get("name") != name else combo for combo in combos]
        else:
            layers = self._state.layers
            macros = self._state.macros
            hold_taps = self._state.hold_taps
            listeners = self._state.listeners

        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=macros,
            hold_taps=hold_taps,
            combos=tuple(combos),
            listeners=listeners,
        )
        self._redo_stack.clear()

    # ------------------------------------------------------------------
    # Listener management API
    def list_listeners(self) -> Tuple[ListenerPayload, ...]:
        return tuple(deepcopy(listener) for listener in self._state.listeners)

    def find_listener_references(self, code: str) -> Dict[str, Tuple[Dict[str, Any], ...]]:
        references: Dict[str, List[Dict[str, Any]]] = {
            "keys": [],
            "macros": [],
            "hold_taps": [],
            "combos": [],
            "listeners": [],
        }

        for layer_index, record in enumerate(self._state.layers):
            for key_index, slot in enumerate(record.slots):
                if slot.get("value") == code:
                    references["keys"].append(
                        {
                            "layer_index": layer_index,
                            "layer_name": record.name,
                            "key_index": key_index,
                        }
                    )

        for index, macro in enumerate(self._state.macros):
            if _contains_string(macro, code):
                references["macros"].append({"index": index, "name": macro.get("name")})

        for index, hold in enumerate(self._state.hold_taps):
            if _contains_string(hold, code):
                references["hold_taps"].append({"index": index, "name": hold.get("name")})

        for index, combo in enumerate(self._state.combos):
            if _contains_string(combo, code):
                references["combos"].append({"index": index, "name": combo.get("name")})

        for index, listener in enumerate(self._state.listeners):
            listener_code = str(listener.get("code", ""))
            if listener_code == code:
                continue
            if _contains_string(listener, code):
                references["listeners"].append({"index": index, "code": listener_code})

        return {key: tuple(entries) for key, entries in references.items()}

    def add_listener(self, payload: Mapping[str, Any]) -> None:
        normalized = _normalize_listener_payload(payload)
        self._assert_listener_layers_valid(normalized)
        code = normalized["code"]
        self._ensure_listener_code_available(code)
        self._record_snapshot()
        listeners = list(self._state.listeners)
        listeners.append(normalized)
        self._state = replace(self._state, listeners=tuple(listeners))
        self._redo_stack.clear()

    def update_listener(self, *, code: str, payload: Mapping[str, Any]) -> None:
        index = self._listener_index(code)
        normalized = _normalize_listener_payload(payload)
        self._assert_listener_layers_valid(normalized)
        new_code = normalized["code"]
        rename_map: Dict[str, str] = {}
        if new_code != code:
            self._ensure_listener_code_available(new_code)
            rename_map = {code: new_code}

        self._record_snapshot()
        listeners = list(self._state.listeners)
        listeners[index] = normalized
        if rename_map:
            listeners = [
                normalized if idx == index else _replace_strings(listener, rename_map)
                for idx, listener in enumerate(listeners)
            ]

        layers = self._rewrite_layers_with_macros(rename_map) if rename_map else self._state.layers
        macros = (
            self._rewrite_sequence_with_macros(self._state.macros, rename_map) if rename_map else self._state.macros
        )
        hold_taps = (
            self._rewrite_sequence_with_macros(self._state.hold_taps, rename_map)
            if rename_map
            else self._state.hold_taps
        )
        combos = (
            self._rewrite_sequence_with_macros(self._state.combos, rename_map) if rename_map else self._state.combos
        )

        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=macros,
            hold_taps=hold_taps,
            combos=combos,
            listeners=tuple(listeners),
        )
        self._redo_stack.clear()

    def rename_listener(self, *, old_code: str, new_code: str) -> None:
        listener = deepcopy(self._state.listeners[self._listener_index(old_code)])
        listener["code"] = str(new_code).strip()
        self.update_listener(code=old_code, payload=listener)

    def delete_listener(self, *, code: str, force: bool = False) -> None:
        index = self._listener_index(code)
        references = self.find_listener_references(code)
        has_refs = any(references[key] for key in references)
        if has_refs and not force:
            raise ValueError(f"Listener '{code}' is referenced and cannot be deleted")

        self._record_snapshot()
        listeners = list(self._state.listeners)
        listeners.pop(index)
        if has_refs:
            cleanup_map = {code: ""}
            layers = self._rewrite_layers_with_macros(cleanup_map)
            macros = self._rewrite_sequence_with_macros(self._state.macros, cleanup_map)
            hold_taps = self._rewrite_sequence_with_macros(self._state.hold_taps, cleanup_map)
            combos = self._rewrite_sequence_with_macros(self._state.combos, cleanup_map)
            listeners = [_replace_strings(listener, cleanup_map) for listener in listeners]
        else:
            layers = self._state.layers
            macros = self._state.macros
            hold_taps = self._state.hold_taps
            combos = self._state.combos

        self._state = LayoutState(
            layer_names=self._state.layer_names,
            layers=layers,
            macros=macros,
            hold_taps=hold_taps,
            combos=combos,
            listeners=tuple(listeners),
        )
        self._redo_stack.clear()

    def export_payload(self) -> Dict[str, Any]:
        """Return a deep-copied payload representing the current state."""

        layers = [[deepcopy(slot) for slot in record.slots] for record in self._state.layers]
        return {
            "layer_names": list(self._state.layer_names),
            "layers": layers,
            "macros": [deepcopy(macro) for macro in self._state.macros],
            "holdTaps": [deepcopy(hold) for hold in self._state.hold_taps],
            "combos": [deepcopy(combo) for combo in self._state.combos],
            "inputListeners": [deepcopy(listener) for listener in self._state.listeners],
        }

    def replace_payload(self, payload: Mapping[str, Any]) -> None:
        """Replace the current layout with *payload* (undoable)."""

        self._record_snapshot()
        self._state = LayoutState.from_payload(payload)
        self._redo_stack.clear()
        self._clamp_selection()

    # ------------------------------------------------------------------
    # Undo / Redo
    def undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self._state)
        self._state = self._undo_stack.pop()
        self._clamp_selection()

    def redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self._state)
        self._state = self._redo_stack.pop()
        self._clamp_selection()

    # ------------------------------------------------------------------
    def _record_snapshot(self) -> None:
        self._undo_stack.append(self._state)

    def _validate_layer_index(self, layer_index: int) -> int:
        if not (0 <= layer_index < len(self._state.layers)):
            raise IndexError("Layer index out of range")
        return layer_index

    def _validate_key_index(self, layer_index: int, key_index: int) -> int:
        slot_count = len(self._state.layers[layer_index].slots)
        if not (0 <= key_index < slot_count):
            raise IndexError("Key index out of range")
        return key_index

    def _clamp_selection(self) -> None:
        if not self._state.layers:
            self._selection = SelectionState(layer_index=-1, key_index=-1)
            return
        layer_index = self._selection.layer_index
        if not (0 <= layer_index < len(self._state.layers)):
            layer_index = 0
        key_index = self._selection.key_index
        slot_count = len(self._state.layers[layer_index].slots)
        if not (0 <= key_index < slot_count):
            key_index = 0
        self._selection = SelectionState(layer_index=layer_index, key_index=key_index)

    def _ensure_macro_name_available(self, name: str) -> None:
        if any(macro.get("name") == name for macro in self._state.macros):
            raise ValueError(f"Macro '{name}' already exists")

    def _macro_index(self, name: str) -> int:
        for index, macro in enumerate(self._state.macros):
            if macro.get("name") == name:
                return index
        raise ValueError(f"Macro '{name}' not found")

    def _ensure_hold_tap_name_available(self, name: str) -> None:
        if any(hold.get("name") == name for hold in self._state.hold_taps):
            raise ValueError(f"HoldTap '{name}' already exists")

    def _hold_tap_index(self, name: str) -> int:
        normalized = name if name.startswith("&") else f"&{name}"
        for index, hold_tap in enumerate(self._state.hold_taps):
            if hold_tap.get("name") == normalized:
                return index
        raise ValueError(f"HoldTap '{normalized}' not found")

    def _ensure_combo_name_available(self, name: str) -> None:
        normalized = self._normalize_combo_name(name)
        for combo in self._state.combos:
            existing = self._normalize_combo_name(combo.get("name", ""))
            if existing and existing == normalized:
                raise ValueError(f"Combo '{name}' already exists")

    def _combo_index(self, name: str) -> int:
        literal = str(name).strip()
        normalized = self._normalize_combo_name(literal)
        for index, combo in enumerate(self._state.combos):
            current = str(combo.get("name", ""))
            if current == literal or self._normalize_combo_name(current) == normalized:
                return index
        target = literal or normalized
        raise ValueError(f"Combo '{target}' not found")

    @staticmethod
    def _normalize_combo_name(name: Any) -> str:
        text = str(name).strip()
        if not text:
            return ""
        return text if text.startswith("&") else f"&{text}"

    def _assert_combo_layers_valid(self, layers: Sequence[Any]) -> None:
        if not layers:
            return
        total_layers = len(self._state.layer_names)
        if total_layers == 0:
            raise ValueError("No layers defined for combo assignment")
        valid_names = set(self._state.layer_names)
        for entry in layers:
            if isinstance(entry, Mapping):
                if "name" in entry:
                    ref = str(entry["name"])
                    if ref not in valid_names:
                        raise ValueError(f"Unknown layer '{ref}' referenced by combo")
                elif "index" in entry:
                    idx = int(entry["index"])
                    if not (0 <= idx < total_layers):
                        raise ValueError(f"Layer index {idx} out of range")
                else:
                    raise ValueError("Combo layer mapping must include 'name' or 'index'")
            elif isinstance(entry, int):
                if not (0 <= entry < total_layers):
                    raise ValueError(f"Layer index {entry} out of range")
            else:
                raise ValueError("Combo layers must be layer names or indices")

    def _ensure_listener_code_available(self, code: str) -> None:
        normalized = self._normalize_listener_code(code)
        for listener in self._state.listeners:
            existing = self._normalize_listener_code(listener.get("code", ""))
            if existing and existing == normalized:
                raise ValueError(f"Listener '{code}' already exists")

    def _listener_index(self, code: str) -> int:
        literal = str(code).strip()
        normalized = self._normalize_listener_code(literal)
        for index, listener in enumerate(self._state.listeners):
            current = str(listener.get("code", ""))
            if current == literal or self._normalize_listener_code(current) == normalized:
                return index
        target = literal or normalized
        raise ValueError(f"Listener '{target}' not found")

    @staticmethod
    def _normalize_listener_code(code: Any) -> str:
        return str(code).strip()

    def _assert_listener_layers_valid(self, listener: Mapping[str, Any]) -> None:
        total_layers = len(self._state.layer_names)
        if total_layers == 0:
            if listener.get("layers") or any(node.get("layers") for node in listener.get("nodes", [])):
                raise ValueError("No layers defined for listener assignment")
            return
        valid_names = set(self._state.layer_names)

        def _check_layers(layers: Any) -> None:
            if not layers:
                return
            for entry in layers:
                if isinstance(entry, Mapping):
                    if "name" in entry:
                        ref = str(entry["name"])
                        if ref not in valid_names:
                            raise ValueError(f"Unknown layer '{ref}' referenced by listener")
                    elif "index" in entry:
                        idx = int(entry["index"])
                        if not (0 <= idx < total_layers):
                            raise ValueError(f"Layer index {idx} out of range")
                    else:
                        raise ValueError("Listener layer mapping must include 'name' or 'index'")
                elif isinstance(entry, int):
                    if not (0 <= entry < total_layers):
                        raise ValueError(f"Layer index {entry} out of range")
                elif isinstance(entry, str):
                    if entry not in valid_names:
                        raise ValueError(f"Unknown layer '{entry}' referenced by listener")
                else:
                    raise ValueError("Listener layers must be layer names or indices")

        if "layers" in listener:
            _check_layers(listener.get("layers"))
        for node in listener.get("nodes", []):
            _check_layers(node.get("layers"))

    def _rewrite_layers_with_macros(self, rename_map: Mapping[str, str]) -> Tuple[LayerRecord, ...]:
        if not rename_map:
            return self._state.layers
        records: List[LayerRecord] = []
        for record in self._state.layers:
            slots = tuple(_replace_strings(slot, rename_map) for slot in record.slots)
            records.append(replace(record, slots=slots))
        return tuple(records)

    def _rewrite_sequence_with_macros(
        self,
        items: Tuple[Dict[str, Any], ...],
        rename_map: Mapping[str, str],
    ) -> Tuple[Dict[str, Any], ...]:
        if not rename_map:
            return items
        return tuple(_replace_strings(item, rename_map) for item in items)


def _increment_name(base: str, existing: Iterable[str]) -> str:
    counter = 2
    candidate = f"{base} Copy"
    while candidate in existing:
        candidate = f"{base} ({counter})"
        counter += 1
    return candidate


def _rewrite_layer_refs(data: Any, rename_map: Mapping[str, str]) -> Any:
    if isinstance(data, dict):
        if set(data.keys()) == {"name"}:
            name = data["name"]
            if name in rename_map:
                updated = dict(data)
                updated["name"] = rename_map[name]
                return updated
            return data
        return {k: _rewrite_layer_refs(v, rename_map) for k, v in data.items()}
    if isinstance(data, list):
        return [_rewrite_layer_refs(item, rename_map) for item in data]
    if isinstance(data, tuple):
        return tuple(_rewrite_layer_refs(item, rename_map) for item in data)
    return data


def _normalize_macro_payload(macro: Mapping[str, Any]) -> MacroPayload:
    if "name" not in macro:
        raise ValueError("Macro payload must include 'name'")
    name = str(macro["name"]).strip()
    if not name:
        raise ValueError("Macro name cannot be empty")
    if not name.startswith("&"):
        raise ValueError("Macro name must start with '&'")
    normalized: Dict[str, Any] = deepcopy(dict(macro))
    normalized["name"] = name
    normalized.setdefault("bindings", [])
    normalized.setdefault("params", [])
    return normalized


def _normalize_hold_tap_payload(payload: Mapping[str, Any]) -> HoldTapPayload:
    normalized: Dict[str, Any] = {}
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("HoldTap name cannot be empty")
    if not name.startswith("&"):
        name = f"&{name}"
    normalized["name"] = name
    description = payload.get("description")
    if description:
        normalized["description"] = str(description)
    bindings = payload.get("bindings", [])
    if not isinstance(bindings, Sequence) or isinstance(bindings, (str, bytes)):
        raise ValueError("HoldTap bindings must be a list")
    normalized["bindings"] = list(bindings)

    for field in ("tappingTermMs", "quickTapMs", "requirePriorIdleMs"):
        value = payload.get(field)
        if value is None or value == "":
            continue
        int_value = int(value)
        if int_value < 0:
            raise ValueError(f"{field} must be ≥ 0")
        normalized[field] = int_value

    flavor = payload.get("flavor")
    if flavor:
        normalized["flavor"] = str(flavor)

    hold_trigger_on_release = payload.get("holdTriggerOnRelease")
    if hold_trigger_on_release not in (None, ""):
        normalized["holdTriggerOnRelease"] = bool(hold_trigger_on_release)

    positions = payload.get("holdTriggerKeyPositions")
    if positions not in (None, ""):
        normalized["holdTriggerKeyPositions"] = _normalize_hold_trigger_positions(positions)

    return normalized


def _normalize_hold_trigger_positions(value: Any) -> List[int]:
    positions: List[int] = []
    if isinstance(value, str):
        tokens = [token.strip() for token in value.replace("[", "").replace("]", "").split(",") if token.strip()]
        for token in tokens:
            positions.append(int(token))
    elif isinstance(value, Iterable):
        for item in value:
            positions.append(int(item))
    else:
        raise ValueError("holdTriggerKeyPositions must be iterable or comma-delimited string")

    deduped = sorted(set(positions))
    for pos in deduped:
        if pos < 0 or pos >= 80:
            raise ValueError("holdTriggerKeyPositions must be between 0 and 79")
    return deduped


def _normalize_combo_payload(payload: Mapping[str, Any]) -> ComboPayload:
    normalized: Dict[str, Any] = {}
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("Combo name cannot be empty")
    if not name.startswith("&"):
        name = f"&{name}"
    normalized["name"] = name

    description = payload.get("description")
    if description:
        normalized["description"] = str(description)

    binding = payload.get("binding")
    if not isinstance(binding, Mapping):
        raise ValueError("Combo binding must be an object")
    if "value" not in binding:
        raise ValueError("Combo binding requires a 'value'")
    normalized["binding"] = {
        "value": str(binding["value"]),
        "params": list(binding.get("params", [])),
    }

    key_positions = _normalize_key_positions(payload.get("keyPositions"))
    normalized["keyPositions"] = key_positions

    layers = payload.get("layers")
    if layers is None:
        normalized["layers"] = []
    else:
        normalized["layers"] = _normalize_combo_layers(layers)

    timeout = payload.get("timeoutMs")
    if timeout not in (None, ""):
        try:
            timeout_int = int(str(timeout))
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError("timeoutMs must be an integer") from exc
        if timeout_int < 0:
            raise ValueError("timeoutMs must be ≥ 0")
        normalized["timeoutMs"] = timeout_int

    return normalized


def _normalize_key_positions(value: Any) -> List[int]:
    if value is None:
        raise ValueError("keyPositions are required")
    positions: List[int] = []
    if isinstance(value, str):
        tokens = [token.strip() for token in value.replace("[", "").replace("]", "").split(",") if token.strip()]
        for token in tokens:
            positions.append(int(token))
    elif isinstance(value, Iterable):
        for item in value:
            positions.append(int(item))
    else:
        raise ValueError("keyPositions must be iterable or comma-delimited string")
    if not positions:
        raise ValueError("keyPositions must contain at least one entry")
    deduped = sorted(set(positions))
    for pos in deduped:
        if pos < 0 or pos >= 80:
            raise ValueError("keyPositions must be between 0 and 79")
    return deduped


def _normalize_combo_layers(value: Any) -> List[Any]:
    layers: List[Any] = []
    if isinstance(value, str):
        tokens = [token.strip() for token in value.split(",") if token.strip()]
        for token in tokens:
            layers.append({"name": token} if not token.isdigit() else int(token))
    elif isinstance(value, Iterable):
        for entry in value:
            if isinstance(entry, Mapping):
                layers.append(dict(entry))
            elif isinstance(entry, str) and entry.isdigit():
                layers.append(int(entry))
            else:
                layers.append({"name": str(entry)})
    else:
        raise ValueError("layers must be iterable or comma-delimited string")
    return layers


def _normalize_listener_payload(payload: Mapping[str, Any]) -> ListenerPayload:
    normalized: Dict[str, Any] = dict(payload)
    code = str(payload.get("code", "")).strip()
    if not code:
        raise ValueError("Listener code cannot be empty")
    normalized["code"] = code
    normalized["inputProcessors"] = _normalize_listener_processors(payload.get("inputProcessors", []))
    normalized["nodes"] = _normalize_listener_nodes(payload.get("nodes", []))
    if "layers" in normalized:
        normalized["layers"] = _normalize_listener_layers(normalized["layers"])
    return normalized


def _normalize_listener_processors(value: Any) -> List[Dict[str, Any]]:
    if value in (None, ""):
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("Listener processors must be provided as a list")
    processors: List[Dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            raise ValueError("Each listener processor must be an object")
        code = str(entry.get("code", "")).strip()
        if not code:
            raise ValueError("Listener processor requires a 'code'")
        processor = dict(entry)
        processor["code"] = code
        params = entry.get("params", [])
        if params in (None, ""):
            processor["params"] = []
        elif isinstance(params, Sequence) and not isinstance(params, (str, bytes)):
            processor["params"] = list(params)
        else:
            raise ValueError("Listener processor 'params' must be a list")
        processors.append(processor)
    return processors


def _normalize_listener_nodes(value: Any) -> List[Dict[str, Any]]:
    if value in (None, ""):
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("Listener nodes must be provided as a list")
    nodes: List[Dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            raise ValueError("Each listener node must be an object")
        code = str(entry.get("code", "")).strip()
        if not code:
            raise ValueError("Listener node requires a 'code'")
        node = dict(entry)
        node["code"] = code
        node["inputProcessors"] = _normalize_listener_processors(entry.get("inputProcessors", []))
        if "layers" in node:
            node["layers"] = _normalize_listener_layers(node["layers"])
        nodes.append(node)
    return nodes


def _normalize_listener_layers(value: Any) -> List[Any]:
    if value in (None, ""):
        return []
    layers: List[Any] = []
    if isinstance(value, str):
        tokens = [token.strip() for token in value.split(",") if token.strip()]
        for token in tokens:
            layers.append(_normalize_single_layer_reference(token))
        return layers
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        raise ValueError("Listener layers must be iterable or comma-delimited string")
    for entry in value:
        layers.append(_normalize_single_layer_reference(entry))
    return layers


def _normalize_single_layer_reference(entry: Any) -> Any:
    if isinstance(entry, Mapping):
        if "name" in entry:
            return {"name": str(entry["name"])}
        if "index" in entry:
            return {"index": int(entry["index"])}
        raise ValueError("Layer mapping must include 'name' or 'index'")
    if isinstance(entry, int):
        return entry
    if isinstance(entry, str):
        token = entry.strip()
        if not token:
            raise ValueError("Layer reference cannot be empty")
        if token.isdigit():
            return int(token)
        return {"name": token}
    raise ValueError("Unsupported layer reference type")


def _contains_string(data: Any, target: str) -> bool:
    if isinstance(data, str):
        return data == target
    if isinstance(data, Mapping):
        return any(_contains_string(value, target) for value in data.values())
    if isinstance(data, (list, tuple)):
        return any(_contains_string(item, target) for item in data)
    return False


def _replace_strings(data: Any, replacements: Mapping[str, str]) -> Any:
    if not replacements:
        return data
    if isinstance(data, str):
        return replacements.get(data, data)
    if isinstance(data, Mapping):
        return {k: _replace_strings(v, replacements) for k, v in data.items()}
    if isinstance(data, list):
        return [_replace_strings(item, replacements) for item in data]
    if isinstance(data, tuple):
        return tuple(_replace_strings(item, replacements) for item in data)
    return data


# Convenience payload for bootstrapping the app
def _sample_layer_slots(binding: str) -> List[Dict[str, Any]]:
    tokens = binding.split()
    if tokens and tokens[0].startswith("&") and len(tokens) > 1:
        value = tokens[0]
        param_template = [{"value": tokens[1], "params": []}]
    else:
        value = binding
        param_template = []

    slots: List[Dict[str, Any]] = []
    for _ in range(80):
        slots.append({"value": value, "params": list(param_template)})
    return slots


DEFAULT_SAMPLE_LAYOUT: Dict[str, Any] = {
    "layer_names": ["Base", "Lower", "Raise"],
    "layers": [_sample_layer_slots("&kp A"), _sample_layer_slots("&kp B"), _sample_layer_slots("&kp C")],
    "macros": [],
    "holdTaps": [],
    "combos": [
        {
            "name": "LayerToggle",
            "binding": {"value": "&mo", "params": [{"name": "Lower"}]},
            "keyPositions": [0, 1],
            "layers": [{"name": "Base"}],
        }
    ],
    "inputListeners": [
        {
            "code": "listener_0",
            "layers": [{"name": "Raise"}],
            "nodes": [],
            "inputProcessors": [],
        }
    ],
}
