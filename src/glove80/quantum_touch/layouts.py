"""Compose QuantumTouch layouts from declarative layer specs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Sequence

from ..base import resolve_layer_refs
from ..metadata import get_variant_metadata
from .layers import build_all_layers
from .specs import (
    COMBO_DATA,
    COMMON_FIELDS,
    HOLD_TAP_DEFS,
    HOLD_TAP_ORDER,
    INPUT_LISTENER_DATA,
    LAYER_NAMES,
    MACRO_DEFS,
    MACRO_ORDER,
)

META_FIELDS = ("title", "uuid", "parent_uuid", "date", "notes", "tags")


def _materialize_named_sequence(defs: Dict[str, Any], order: Sequence[str]) -> list[Dict[str, Any]]:
    return [defs[name].to_dict() for name in order]


def _base_layout_payload() -> Dict:
    layout = deepcopy(COMMON_FIELDS)
    layout["layer_names"] = deepcopy(LAYER_NAMES)
    layout["macros"] = _materialize_named_sequence(MACRO_DEFS, MACRO_ORDER)
    layout["holdTaps"] = _materialize_named_sequence(HOLD_TAP_DEFS, HOLD_TAP_ORDER)
    layout["combos"] = [combo.to_dict() for combo in COMBO_DATA["default"]]
    layout["inputListeners"] = [listener.to_dict() for listener in INPUT_LISTENER_DATA["default"]]
    return layout


def build_layout(variant: str = "default") -> Dict:
    """Return the canonical QuantumTouch layout composed from code."""

    layout = _base_layout_payload()
    layer_names = layout["layer_names"]
    layer_indices = {name: idx for idx, name in enumerate(layer_names)}

    for field in ("macros", "holdTaps", "combos", "inputListeners"):
        layout[field] = resolve_layer_refs(layout[field], layer_indices)

    generated_layers = build_all_layers(variant)
    ordered_layers = []
    for name in layer_names:
        try:
            ordered_layers.append(generated_layers[name])
        except KeyError as exc:
            raise KeyError(f"No generated layer named '{name}' for variant '{variant}'") from exc

    layout["layers"] = ordered_layers
    meta = get_variant_metadata(variant, layout="quantum_touch")
    for field in META_FIELDS:
        layout[field] = meta.get(field)

    return layout
