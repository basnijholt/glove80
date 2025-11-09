"""Compose full TailorKey layouts from generated layers."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

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


def _base_layout_payload(variant: str) -> Dict[str, Any]:
    combos = materialize_sequence(_get_variant_section(COMBO_DATA, variant, "combo definitions"))
    listeners = materialize_sequence(_get_variant_section(INPUT_LISTENER_DATA, variant, "input listeners"))
    return build_layout_payload(
        COMMON_FIELDS,
        layer_names=_layer_names(variant),
        macros=_build_macros(variant),
        hold_taps=_build_hold_taps(variant),
        combos=combos,
        input_listeners=listeners,
    )


class Family(LayoutFamily):
    name = "tailorkey"

    def variants(self) -> Sequence[str]:
        return list(LAYER_NAME_MAP.keys())

    def metadata_key(self) -> str:
        return "tailorkey"

    def build(self, variant: str) -> Dict:
        layout = _base_layout_payload(variant)
        layer_names = layout["layer_names"]
        _resolve_referenced_fields(layout, layer_names=layer_names)
        generated_layers = build_all_layers(variant)
        layout["layers"] = _assemble_layers(layer_names, generated_layers, variant=variant)
        _attach_variant_metadata(layout, variant=variant, layout_key=self.metadata_key())
        return layout


REGISTRY.register(Family())

__all__ = ["Family"]
