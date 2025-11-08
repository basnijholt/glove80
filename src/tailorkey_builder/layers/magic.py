"""Magic layer generation."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from typing import Dict, List

Layer = List[Dict]


def _load_base_layer() -> Layer:
    data_path = resources.files("tailorkey_builder.data").joinpath("magic_layer.json")
    with data_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data["Magic"]


_BASE_MAGIC_LAYER: Layer = _load_base_layer()

_DUAL_PATCH = {
    11: {"value": "&to", "params": [{"value": 1, "params": []}]},
    12: {"value": "&to", "params": [{"value": 2, "params": []}]},
    15: {"value": "&to", "params": [{"value": 3, "params": []}]},
}


def _apply_patch(layer: Layer, patch: Dict[int, Dict]) -> None:
    for index, replacement in patch.items():
        layer[index] = deepcopy(replacement)


def build_magic_layer(variant: str) -> Layer:
    layer = deepcopy(_BASE_MAGIC_LAYER)
    if variant == "dual":
        _apply_patch(layer, _DUAL_PATCH)
    return layer
