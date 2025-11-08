"""Compose QuantumTouch layouts from declarative layer specs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Sequence

from ..layouts.common import (
    assemble_layers,
    attach_variant_metadata,
    resolve_referenced_fields,
)
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
    resolve_referenced_fields(layout, layer_names=layer_names)
    generated_layers = build_all_layers(variant)
    layout["layers"] = assemble_layers(layer_names, generated_layers, variant=variant)
    attach_variant_metadata(layout, variant=variant, layout_key="quantum_touch")

    return layout
