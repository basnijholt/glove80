"""Compose QuantumTouch layouts from declarative layer specs."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from glove80.layouts.common import (
    _assemble_layers,
    _attach_variant_metadata,
    _resolve_referenced_fields,
    build_layout_payload,
)
from glove80.layouts.family import LayoutFamily, REGISTRY
from glove80.specs.primitives import materialize_named_sequence, materialize_sequence

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


def _base_layout_payload() -> Dict:
    combos = materialize_sequence(COMBO_DATA["default"])
    listeners = materialize_sequence(INPUT_LISTENER_DATA["default"])
    macros = materialize_named_sequence(MACRO_DEFS, MACRO_ORDER)
    hold_taps = materialize_named_sequence(HOLD_TAP_DEFS, HOLD_TAP_ORDER)
    return build_layout_payload(
        COMMON_FIELDS,
        layer_names=LAYER_NAMES,
        macros=macros,
        hold_taps=hold_taps,
        combos=combos,
        input_listeners=listeners,
    )


class Family(LayoutFamily):
    name = "quantum_touch"

    def variants(self) -> Sequence[str]:
        return ["default"]

    def metadata_key(self) -> str:
        return "quantum_touch"

    def build(self, variant: str = "default") -> Dict:
        layout = _base_layout_payload()
        layer_names = layout["layer_names"]
        _resolve_referenced_fields(layout, layer_names=layer_names)
        generated_layers = build_all_layers(variant)
        layout["layers"] = _assemble_layers(layer_names, generated_layers, variant=variant)
        _attach_variant_metadata(layout, variant=variant, layout_key=self.metadata_key())
        return layout


REGISTRY.register(Family())

__all__ = ["Family"]
