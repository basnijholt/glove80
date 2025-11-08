"""Gaming layer generation."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from typing import Dict, List

Layer = List[Dict]


def _load_base_layer() -> Layer:
    data_path = resources.files("tailorkey_builder.data").joinpath("gaming_layer.json")
    with data_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data["Gaming"]


_BASE_GAMING_LAYER: Layer = _load_base_layer()


def build_gaming_layer(_variant: str) -> Layer:
    return deepcopy(_BASE_GAMING_LAYER)
