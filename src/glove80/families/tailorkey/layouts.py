"""Compose full TailorKey layouts from generated layers."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

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
    LAYER_NAME_MAP,
    MACRO_DEFS,
    MACRO_ORDER,
    MACRO_OVERRIDES,
)


def _get_variant_section(sections: Mapping[str, Sequence[Any]], variant: str, label: str) -> List[Any]:
    try:
        return list(sections[variant])
    except KeyError as exc:  # pragma: no cover
        raise KeyError(f"No {label} for variant '{variant}'") from exc


def _build_macros(variant: str) -> List[Dict[str, Any]]:
    order = _get_variant_section(MACRO_ORDER, variant, "macro order")
    overrides = MACRO_OVERRIDES.get(variant)
    return materialize_named_sequence(MACRO_DEFS, order, overrides)


def _build_hold_taps(variant: str) -> List[Dict[str, Any]]:
    order = _get_variant_section(HOLD_TAP_ORDER, variant, "hold-tap order")
    return materialize_named_sequence(HOLD_TAP_DEFS, order)


def _layer_names(variant: str) -> List[str]:
    return list(_get_variant_section(LAYER_NAME_MAP, variant, "layer names"))


class Family(LayoutFamily):
    name = "tailorkey"

    def variants(self) -> Sequence[str]:
        return list(LAYER_NAME_MAP.keys())

    def metadata_key(self) -> str:
        return "tailorkey"

    def build(self, variant: str) -> Dict:
        combos = materialize_sequence(_get_variant_section(COMBO_DATA, variant, "combo definitions"))
        listeners = materialize_sequence(_get_variant_section(INPUT_LISTENER_DATA, variant, "input listeners"))
        generated_layers = build_all_layers(variant)
        layer_names = _layer_names(variant)

        builder = LayoutBuilder(
            metadata_key=self.metadata_key(),
            variant=variant,
            common_fields=COMMON_FIELDS,
            layer_names=layer_names,
        )
        builder.add_layers({name: generated_layers[name] for name in layer_names})
        builder.add_macros(_build_macros(variant))
        builder.add_hold_taps(_build_hold_taps(variant))
        builder.add_combos(combos)
        builder.add_input_listeners(listeners)
        return builder.build()


REGISTRY.register(Family())

__all__ = ["Family"]
