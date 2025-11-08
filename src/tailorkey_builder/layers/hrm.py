"""Home-row modifier layers."""

from __future__ import annotations

from typing import Any, Dict

from .base import Layer, LayerMap, apply_patch, copy_layer, load_layer_from_data


_BASE_HRM_LAYER: Layer = load_layer_from_data("HRM_WinLinx", filename="hrm_layer.json")

Patch = Dict[int, Dict[str, Any]]

_MAC_PATCH: Patch = {
    35: {
        "value": "&HRM_left_pinky_v1_TKZ",
        "params": [{"value": "LCTRL", "params": []}, {"value": "A", "params": []}],
    },
    37: {
        "value": "&HRM_left_middy_v1_TKZ",
        "params": [{"value": "LGUI", "params": []}, {"value": "D", "params": []}],
    },
    42: {
        "value": "&HRM_right_middy_v1_TKZ",
        "params": [{"value": "RGUI", "params": []}, {"value": "K", "params": []}],
    },
    44: {
        "value": "&HRM_right_pinky_v1_TKZ",
        "params": [{"value": "RCTRL", "params": []}, {"value": "SEMI", "params": []}],
    },
    53: {"value": "&kp", "params": [{"value": "LGUI", "params": []}]},
    55: {"value": "&kp", "params": [{"value": "LCTRL", "params": []}]},
    56: {"value": "&kp", "params": [{"value": "RGUI", "params": []}]},
}

_DUAL_PATCH: Patch = {
    69: {
        "value": "&thumb_v2_TKZ",
        "params": [{"value": 5, "params": []}, {"value": "BSPC", "params": []}],
    },
    74: {
        "value": "&space_v3_TKZ",
        "params": [{"value": 6, "params": []}, {"value": "SPACE", "params": []}],
    },
}

_DUAL_MAC_PATCH: Patch = {
    69: {
        "value": "&thumb_v2_TKZ",
        "params": [{"value": 4, "params": []}, {"value": "BSPC", "params": []}],
    },
    74: {
        "value": "&space_v3_TKZ",
        "params": [{"value": 6, "params": []}, {"value": "SPACE", "params": []}],
    },
}

_BILATERAL_WIN_PATCH: Patch = {
    35: {
        "value": "&HRM_left_pinky_v1B_TKZ",
        "params": [{"value": "LGUI", "params": []}, {"value": "A", "params": []}],
    },
    36: {
        "value": "&HRM_left_ring_v1B_TKZ",
        "params": [{"value": "LALT", "params": []}, {"value": "S", "params": []}],
    },
    37: {
        "value": "&HRM_left_middy_v1B_TKZ",
        "params": [{"value": "LCTRL", "params": []}, {"value": "D", "params": []}],
    },
    38: {
        "value": "&HRM_left_index_v1B_TKZ",
        "params": [{"value": "LSHFT", "params": []}, {"value": "F", "params": []}],
    },
    41: {
        "value": "&HRM_right_index_v1B_TKZ",
        "params": [{"value": "RSHFT", "params": []}, {"value": "J", "params": []}],
    },
    42: {
        "value": "&HRM_right_middy_v1B_TKZ",
        "params": [{"value": "RCTRL", "params": []}, {"value": "K", "params": []}],
    },
    43: {
        "value": "&HRM_right_ring_v1B_TKZ",
        "params": [{"value": "LALT", "params": []}, {"value": "L", "params": []}],
    },
    44: {
        "value": "&HRM_right_pinky_v1B_TKZ",
        "params": [{"value": "RGUI", "params": []}, {"value": "SEMI", "params": []}],
    },
    73: {
        "value": "&thumb_v2_TKZ",
        "params": [{"value": 15, "params": []}, {"value": "RET", "params": []}],
    },
}

_BILATERAL_MAC_PATCH: Patch = {
    35: {
        "value": "&HRM_left_pinky_v1B_TKZ",
        "params": [{"value": "LCTRL", "params": []}, {"value": "A", "params": []}],
    },
    36: {
        "value": "&HRM_left_ring_v1B_TKZ",
        "params": [{"value": "LALT", "params": []}, {"value": "S", "params": []}],
    },
    37: {
        "value": "&HRM_left_middy_v1B_TKZ",
        "params": [{"value": "LGUI", "params": []}, {"value": "D", "params": []}],
    },
    38: {
        "value": "&HRM_left_index_v1B_TKZ",
        "params": [{"value": "LSHFT", "params": []}, {"value": "F", "params": []}],
    },
    41: {
        "value": "&HRM_right_index_v1B_TKZ",
        "params": [{"value": "RSHFT", "params": []}, {"value": "J", "params": []}],
    },
    42: {
        "value": "&HRM_right_middy_v1B_TKZ",
        "params": [{"value": "RGUI", "params": []}, {"value": "K", "params": []}],
    },
    43: {
        "value": "&HRM_right_ring_v1B_TKZ",
        "params": [{"value": "LALT", "params": []}, {"value": "L", "params": []}],
    },
    44: {
        "value": "&HRM_right_pinky_v1B_TKZ",
        "params": [{"value": "RCTRL", "params": []}, {"value": "SEMI", "params": []}],
    },
    73: {
        "value": "&thumb_v2_TKZ",
        "params": [{"value": 15, "params": []}, {"value": "RET", "params": []}],
    },
}


def build_hrm_layers(variant: str) -> LayerMap:
    """Return the HRM layers needed for the variant."""

    layers: LayerMap = {}

    if variant == "windows":
        layers["HRM_WinLinx"] = copy_layer(_BASE_HRM_LAYER)
    elif variant == "mac":
        layer = copy_layer(_BASE_HRM_LAYER)
        apply_patch(layer, _MAC_PATCH)
        layers["HRM_macOS"] = layer
    elif variant == "dual":
        win_layer = copy_layer(_BASE_HRM_LAYER)
        apply_patch(win_layer, _DUAL_PATCH)
        layers["HRM_WinLinx"] = win_layer

        mac_layer = copy_layer(_BASE_HRM_LAYER)
        apply_patch(mac_layer, _MAC_PATCH)
        apply_patch(mac_layer, _DUAL_MAC_PATCH)
        layers["HRM_macOS"] = mac_layer
    elif variant == "bilateral_windows":
        layer = copy_layer(_BASE_HRM_LAYER)
        apply_patch(layer, _BILATERAL_WIN_PATCH)
        layers["HRM_WinLinx"] = layer
    elif variant == "bilateral_mac":
        layer = copy_layer(_BASE_HRM_LAYER)
        apply_patch(layer, _MAC_PATCH)
        apply_patch(layer, _BILATERAL_MAC_PATCH)
        layers["HRM_macOS"] = layer
    else:
        raise ValueError(f"Unsupported variant: {variant}")

    return layers
