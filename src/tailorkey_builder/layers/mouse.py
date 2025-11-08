"""Generate the TailorKey mouse-oriented layers."""

from __future__ import annotations

from typing import Any, Dict

from .base import Layer, apply_patch, copy_layers_map, load_layers_map


_BASE_MOUSE_LAYERS: Dict[str, Layer] = load_layers_map("mouse_layers.json")

Patch = Dict[int, Dict[str, Any]]


_MAC_MOUSE_PATCH: Patch = {
    30: {"value": "&sk", "params": [{"value": "RGUI", "params": []}]},
    32: {"value": "&sk", "params": [{"value": "RCTRL", "params": []}]},
    55: {
        "value": "&kp",
        "params": [{"value": "LG", "params": [{"value": "X", "params": []}]}],
    },
    56: {
        "value": "&kp",
        "params": [{"value": "LG", "params": [{"value": "C", "params": []}]}],
    },
    57: {
        "value": "&kp",
        "params": [{"value": "LG", "params": [{"value": "V", "params": []}]}],
    },
}

_DUAL_MOUSE_PATCH: Patch = {
    55: {"value": "&none", "params": []},
    56: {"value": "&none", "params": []},
    57: {"value": "&none", "params": []},
}

_BILATERAL_MOUSE_PATCH: Patch = {
    41: {"value": "&mo", "params": [{"value": 17, "params": []}]},
    42: {"value": "&mo", "params": [{"value": 18, "params": []}]},
    43: {"value": "&mo", "params": [{"value": 16, "params": []}]},
    48: {"value": "&mo", "params": [{"value": 16, "params": []}]},
    49: {"value": "&mo", "params": [{"value": 18, "params": []}]},
    50: {"value": "&mo", "params": [{"value": 17, "params": []}]},
}


def build_mouse_layers(variant: str) -> Dict[str, Layer]:
    """Return the four mouse-related layers for the requested variant."""
    layers = copy_layers_map(_BASE_MOUSE_LAYERS)
    mouse = layers["Mouse"]

    if variant in {"mac", "bilateral_mac"}:
        apply_patch(mouse, _MAC_MOUSE_PATCH)

    if variant == "dual":
        apply_patch(mouse, _DUAL_MOUSE_PATCH)

    if variant in {"bilateral_windows", "bilateral_mac"}:
        apply_patch(mouse, _BILATERAL_MOUSE_PATCH)

    return layers
