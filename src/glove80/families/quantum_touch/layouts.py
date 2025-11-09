"""Compose QuantumTouch layouts from declarative layer specs."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from glove80.layouts.common import compose_layout
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


class Family(LayoutFamily):
    name = "quantum_touch"

    def variants(self) -> Sequence[str]:
        return ["default"]

    def metadata_key(self) -> str:
        return "quantum_touch"

    def build(self, variant: str = "default") -> Dict:
        combos = materialize_sequence(COMBO_DATA["default"])
        listeners = materialize_sequence(INPUT_LISTENER_DATA["default"])
        macros = materialize_named_sequence(MACRO_DEFS, MACRO_ORDER)
        hold_taps = materialize_named_sequence(HOLD_TAP_DEFS, HOLD_TAP_ORDER)
        generated_layers = build_all_layers(variant)
        return compose_layout(
            COMMON_FIELDS,
            layer_names=LAYER_NAMES,
            macros=macros,
            hold_taps=hold_taps,
            combos=combos,
            input_listeners=listeners,
            generated_layers=generated_layers,
            metadata_key=self.metadata_key(),
            variant=variant,
        )


REGISTRY.register(Family())

__all__ = ["Family"]
