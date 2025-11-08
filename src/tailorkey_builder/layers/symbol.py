"""Generate the Symbol layer across TailorKey variants."""

from __future__ import annotations

from typing import Any, Dict

from .base import Layer, apply_patch_if, copy_layer, load_layer_from_data


_BASE_SYMBOL_LAYER: Layer = load_layer_from_data("Symbol", filename="symbol_layer.json")


Patch = Dict[int, Dict[str, Any]]

_MAC_PATCH: Patch = {
    30: {"value": "&sk", "params": [{"value": "RGUI", "params": []}]},
    32: {"value": "&sk", "params": [{"value": "RCTRL", "params": []}]},
}


def build_symbol_layer(variant: str) -> Layer:
    layer = copy_layer(_BASE_SYMBOL_LAYER)
    apply_patch_if(layer, variant in {"mac", "bilateral_mac"}, _MAC_PATCH)
    return layer
