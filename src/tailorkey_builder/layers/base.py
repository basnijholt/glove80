"""Shared helpers for layer generation."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from typing import Any, Dict, List

Layer = List[Dict[str, Any]]
LayerMap = Dict[str, Layer]


def load_layer_from_data(layer_name: str, *, filename: str | None = None) -> Layer:
    """Load a single layer definition from the data bundle."""

    file = filename or f"{layer_name.lower()}_layer.json"
    data_path = resources.files("tailorkey_builder.data").joinpath(file)
    with data_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data[layer_name]


def load_layers_map(filename: str) -> LayerMap:
    """Load a dict of layer_name -> layer data from the given JSON file."""

    data_path = resources.files("tailorkey_builder.data").joinpath(filename)
    with data_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def copy_layer(layer: Layer) -> Layer:
    return deepcopy(layer)


def copy_layers_map(layers: LayerMap) -> LayerMap:
    return {name: deepcopy(layer) for name, layer in layers.items()}


def apply_patch(layer: Layer, patch: Dict[int, Dict[str, Any]]) -> None:
    for index, replacement in patch.items():
        layer[index] = deepcopy(replacement)


def apply_patch_if(
    layer: Layer, condition: bool, patch: Dict[int, Dict[str, Any]]
) -> None:
    if condition:
        apply_patch(layer, patch)
