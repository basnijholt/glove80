"""Shared helpers for layer generation."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from importlib import resources
from typing import Any, Dict, List, Sequence

Layer = List[Dict[str, Any]]
LayerMap = Dict[str, Layer]


@dataclass(frozen=True)
class KeySpec:
    """Declarative spec for a single key in a layer."""

    value: Any
    params: Sequence[Any] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "params": [_coerce_param(param) for param in self.params],
        }


@dataclass(frozen=True)
class LayerSpec:
    """Sparse layer representation."""

    overrides: Dict[int, KeySpec]
    length: int = 80
    default: KeySpec = KeySpec("&trans")

    def to_layer(self) -> Layer:
        layer = [self.default.to_dict() for _ in range(self.length)]
        for index, spec in self.overrides.items():
            layer[index] = spec.to_dict()
        return layer


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


def apply_patch(layer: Layer, patch: PatchSpec) -> None:
    for index, spec in patch.items():
        layer[index] = spec.to_dict()


def apply_patch_if(layer: Layer, condition: bool, patch: PatchSpec) -> None:
    if condition:
        apply_patch(layer, patch)


def build_layer_from_spec(spec: LayerSpec) -> Layer:
    return spec.to_layer()


def _coerce_param(param: Any) -> Dict[str, Any]:
    if isinstance(param, KeySpec):
        return param.to_dict()
    if isinstance(param, dict):
        return deepcopy(param)
    if isinstance(param, (str, int)):
        return {"value": param, "params": []}
    raise TypeError(f"Unsupported param type: {type(param)!r}")


PatchSpec = Dict[int, KeySpec]
