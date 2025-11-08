"""Generate the Cursor layer across TailorKey variants."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from typing import Dict, List

Layer = List[Dict]


def _load_base_layer() -> Layer:
    data_path = resources.files("tailorkey_builder.data").joinpath("cursor_layer.json")
    with data_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data["Cursor"]


_BASE_CURSOR_LAYER: Layer = _load_base_layer()

_MAC_PATCH = {
    27: {'params': [{'params': [{'params': [], 'value': 'X'}], 'value': 'LG'}], 'value': '&kp'},
    28: {'params': [{'params': [{'params': [], 'value': 'X'}], 'value': 'LG'}], 'value': '&kp'},
    30: {'params': [{'params': [{'params': [], 'value': 'Z'}], 'value': 'LG'}], 'value': '&kp'},
    31: {'params': [{'params': [{'params': [{'params': [], 'value': 'Z'}], 'value': 'LS'}], 'value': 'LG'}], 'value': '&kp'},
    35: {'params': [{'params': [], 'value': 'LCTRL'}], 'value': '&kp'},
    37: {'params': [{'params': [], 'value': 'LGUI'}], 'value': '&kp'},
    39: {'params': [{'params': [{'params': [], 'value': 'C'}], 'value': 'LG'}], 'value': '&kp'},
    40: {'params': [{'params': [{'params': [], 'value': 'C'}], 'value': 'LG'}], 'value': '&kp'},
    46: {'params': [{'params': [{'params': [], 'value': 'L'}], 'value': 'LG'}], 'value': '&kp'},
    47: {'params': [{'params': [{'params': [], 'value': 'A'}], 'value': 'LG'}], 'value': '&kp'},
    48: {'params': [], 'value': '&cur_SELECT_LINE_macos_v1_TKZ'},
    49: {'params': [], 'value': '&cur_SELECT_WORD_macos_v1_TKZ'},
    50: {'params': [{'params': [{'params': [], 'value': 'F'}], 'value': 'LG'}], 'value': '&kp'},
    51: {'params': [{'params': [{'params': [], 'value': 'V'}], 'value': 'LG'}], 'value': '&kp'},
    52: {'params': [{'params': [], 'value': 'LGUI'}], 'value': '&mod_tab_v2_TKZ'},
    53: {'params': [{'params': [], 'value': 'LALT'}], 'value': '&mod_tab_v2_TKZ'},
    56: {'params': [], 'value': '&cur_EXTEND_LINE_macos_v1_TKZ'},
    57: {'params': [], 'value': '&cur_EXTEND_WORD_macos_v1_TKZ'},
    58: {'params': [{'params': [{'params': [], 'value': 'V'}], 'value': 'LG'}], 'value': '&kp'},
    63: {'params': [{'params': [{'params': [], 'value': 'L'}], 'value': 'LG'}], 'value': '&kp'},
    64: {'params': [{'params': [{'params': [], 'value': 'K'}], 'value': 'LG'}], 'value': '&kp'},
    65: {'params': [{'params': [{'params': [], 'value': 'Z'}], 'value': 'LG'}], 'value': '&kp'},
    66: {'params': [{'params': [{'params': [{'params': [], 'value': 'Z'}], 'value': 'LS'}], 'value': 'LG'}], 'value': '&kp'},
    67: {'params': [{'params': [{'params': [{'params': [], 'value': 'G'}], 'value': 'LS'}], 'value': 'LG'}], 'value': '&kp'},
    68: {'params': [{'params': [{'params': [], 'value': 'G'}], 'value': 'LG'}], 'value': '&kp'},
    71: {'params': [{'params': [{'params': [], 'value': 'F3'}], 'value': 'LG'}], 'value': '&kp'},
    72: {'params': [{'params': [{'params': [], 'value': 'A'}], 'value': 'LG'}], 'value': '&kp'},
    73: {'params': [], 'value': '&cur_SELECT_LINE_macos_v1_TKZ'},
    74: {'params': [], 'value': '&cur_SELECT_WORD_macos_v1_TKZ'},
    75: {'params': [{'params': [{'params': [], 'value': 'F'}], 'value': 'LG'}], 'value': '&kp'},
    76: {'params': [{'params': [{'params': [{'params': [], 'value': 'G'}], 'value': 'LS'}], 'value': 'LG'}], 'value': '&kp'},
    77: {'params': [{'params': [{'params': [], 'value': 'G'}], 'value': 'LG'}], 'value': '&kp'},
    79: {'params': [{'params': [{'params': [], 'value': 'K'}], 'value': 'LG'}], 'value': '&kp'},
}


def _apply_patch(layer: Layer, patch: Dict[int, Dict]) -> None:
    for index, replacement in patch.items():
        layer[index] = deepcopy(replacement)


def build_cursor_layer(variant: str) -> Layer:
    layer = deepcopy(_BASE_CURSOR_LAYER)
    if variant in {"mac", "bilateral_mac"}:
        _apply_patch(layer, _MAC_PATCH)
    return layer
