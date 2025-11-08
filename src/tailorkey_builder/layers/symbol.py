"\"\"Generate the Symbol layer across TailorKey variants.\"\"\""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from typing import Dict, List

Layer = List[Dict]


def _load_base_layer() -> Layer:
    data_path = resources.files("tailorkey_builder.data").joinpath("symbol_layer.json")
    with data_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data["Symbol"]


_BASE_SYMBOL_LAYER: Layer = _load_base_layer()


_MAC_PATCH = {
    30: {"value": "&sk", "params": [{"value": "RGUI", "params": []}]},
    32: {"value": "&sk", "params": [{"value": "RCTRL", "params": []}]},
}


def _apply_patch(layer: Layer, patch: Dict[int, Dict]) -> None:
    for index, replacement in patch.items():
        layer[index] = deepcopy(replacement)


def build_symbol_layer(variant: str) -> Layer:
    layer = deepcopy(_BASE_SYMBOL_LAYER)
    if variant in {"mac", "bilateral_mac"}:
        _apply_patch(layer, _MAC_PATCH)
    return layer
