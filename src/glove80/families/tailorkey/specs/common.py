"""Common metadata for TailorKey specs."""

from glove80.families.tailorkey.alpha_layouts import TAILORKEY_VARIANTS, base_variant_for
from glove80.layouts.common import build_common_fields

COMMON_FIELDS = build_common_fields(creator="moosy")

MOUSE_STACK = ["Mouse", "MouseSlow", "MouseFast", "MouseWarp"]
BILATERAL_FINGER_LAYERS = [
    "LeftIndex",
    "LeftMiddy",
    "LeftRingy",
    "LeftPinky",
    "RightIndex",
    "RightMiddy",
    "RightRingy",
    "RightPinky",
]


def _windows_layers() -> list[str]:
    return [
        "HRM_WinLinx",
        "Typing",
        "Autoshift",
        "Cursor",
        "Symbol",
        "Gaming",
        "Lower",
        *MOUSE_STACK,
        "Magic",
    ]


def _mac_layers() -> list[str]:
    layers = _windows_layers()
    layers[0] = "HRM_macOS"
    return layers


def _dual_layers() -> list[str]:
    return [
        "HRM_macOS",
        "HRM_WinLinx",
        "Typing",
        "Autoshift",
        "Cursor_macOS",
        "Cursor",
        "Symbol",
        *MOUSE_STACK,
        "Gaming",
        "Lower",
        "Magic",
    ]


def _bilateral_layers(hrm: str) -> list[str]:
    return [
        hrm,
        "Typing",
        "Autoshift",
        "Cursor",
        "Symbol",
        "Gaming",
        "Lower",
        *BILATERAL_FINGER_LAYERS,
        *MOUSE_STACK,
        "Magic",
    ]


LAYER_NAME_MAP = {
    "windows": _windows_layers(),
    "mac": _mac_layers(),
    "dual": _dual_layers(),
    "bilateral_windows": _bilateral_layers("HRM_WinLinx"),
    "bilateral_mac": _bilateral_layers("HRM_macOS"),
}

for variant in TAILORKEY_VARIANTS:
    if variant not in LAYER_NAME_MAP:
        base = base_variant_for(variant)
        LAYER_NAME_MAP[variant] = list(LAYER_NAME_MAP[base])


__all__ = ["COMMON_FIELDS", "LAYER_NAME_MAP"]
