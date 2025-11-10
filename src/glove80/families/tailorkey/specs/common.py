"""Common metadata for TailorKey specs."""

from glove80.families.tailorkey.alpha_layouts import TAILORKEY_VARIANTS, base_variant_for
from glove80.layouts.common import build_common_fields

COMMON_FIELDS = build_common_fields(creator="moosy")

_WINDOWS_ORDER = [
    "HRM_WinLinx",
    "Typing",
    "Autoshift",
    "Cursor",
    "Symbol",
    "Gaming",
    "Lower",
    "Mouse",
    "MouseSlow",
    "MouseFast",
    "MouseWarp",
    "Magic",
]


def _mac_order() -> list[str]:
    order = list(_WINDOWS_ORDER)
    order[0] = "HRM_macOS"
    return order


def _dual_order() -> list[str]:
    return [
        "HRM_macOS",
        "HRM_WinLinx",
        "Typing",
        "Autoshift",
        "Cursor_macOS",
        "Cursor",
        "Symbol",
        "Mouse",
        "MouseSlow",
        "MouseFast",
        "MouseWarp",
        "Gaming",
        "Lower",
        "Magic",
    ]


_BILATERAL_FINGERS = [
    "LeftIndex",
    "LeftMiddy",
    "LeftRingy",
    "LeftPinky",
    "RightIndex",
    "RightMiddy",
    "RightRingy",
    "RightPinky",
]


def _bilateral_order(*, mac: bool) -> list[str]:
    order = [
        "HRM_macOS" if mac else "HRM_WinLinx",
        "Typing",
        "Autoshift",
        "Cursor",
        "Symbol",
        "Gaming",
        "Lower",
    ]
    order.extend(_BILATERAL_FINGERS)
    order.extend(["Mouse", "MouseSlow", "MouseFast", "MouseWarp", "Magic"])
    return order


LAYER_NAME_MAP = {
    "windows": list(_WINDOWS_ORDER),
    "mac": _mac_order(),
    "dual": _dual_order(),
    "bilateral_windows": _bilateral_order(mac=False),
    "bilateral_mac": _bilateral_order(mac=True),
}

for variant in TAILORKEY_VARIANTS:
    if variant not in LAYER_NAME_MAP:
        base = base_variant_for(variant)
        LAYER_NAME_MAP[variant] = list(LAYER_NAME_MAP[base])


__all__ = ["COMMON_FIELDS", "LAYER_NAME_MAP"]
