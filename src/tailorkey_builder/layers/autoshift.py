"""Autoshift layer generation."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from typing import Dict, List

Layer = List[Dict]


def _load_base_layer() -> Layer:
    data_path = resources.files("tailorkey_builder.data").joinpath("autoshift_layer.json")
    with data_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data["Autoshift"]


_BASE_AUTOSHIFT_LAYER: Layer = _load_base_layer()


def build_autoshift_layer(_variant: str) -> Layer:
    return deepcopy(_BASE_AUTOSHIFT_LAYER)
