"""Magic layer generation."""

from __future__ import annotations

from typing import Any, Dict

from .base import Layer, apply_patch_if, copy_layer, load_layer_from_data


_BASE_MAGIC_LAYER: Layer = load_layer_from_data("Magic", filename="magic_layer.json")

Patch = Dict[int, Dict[str, Any]]

_DUAL_PATCH: Patch = {
    11: {"value": "&to", "params": [{"value": 1, "params": []}]},
    12: {"value": "&to", "params": [{"value": 2, "params": []}]},
    15: {"value": "&to", "params": [{"value": 3, "params": []}]},
}


def build_magic_layer(variant: str) -> Layer:
    layer = copy_layer(_BASE_MAGIC_LAYER)
    apply_patch_if(layer, variant == "dual", _DUAL_PATCH)
    return layer
