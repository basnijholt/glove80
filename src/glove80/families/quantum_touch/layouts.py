"""Compose QuantumTouch layouts from declarative layer specs."""

from __future__ import annotations

from typing import Dict, Sequence

from glove80.layouts import LayoutBuilder
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

        builder = LayoutBuilder(
            metadata_key=self.metadata_key(),
            variant=variant,
            common_fields=COMMON_FIELDS,
            layer_names=LAYER_NAMES,
        )
        builder.add_layers(generated_layers)
        builder.add_macros(macros)
        builder.add_hold_taps(hold_taps)
        builder.add_combos(combos)
        builder.add_input_listeners(listeners)
        return builder.build()


REGISTRY.register(Family())

__all__ = ["Family"]
