"""QuantumTouch Mouse layer."""

from __future__ import annotations

from ...base import KeySpec, Layer, LayerSpec, build_layer_from_spec


MOUSE_LAYER_SPEC = LayerSpec(
    overrides={
        24: KeySpec("&msc", (KeySpec("SCRL_LEFT"),)),
        25: KeySpec("&mmv", (KeySpec("MOVE_UP"),)),
        26: KeySpec("&msc", (KeySpec("SCRL_RIGHT"),)),
        29: KeySpec("&msc", (KeySpec("SCRL_LEFT"),)),
        30: KeySpec("&msc", (KeySpec("SCRL_UP"),)),
        31: KeySpec("&msc", (KeySpec("SCRL_DOWN"),)),
        32: KeySpec("&msc", (KeySpec("SCRL_RIGHT"),)),
        35: KeySpec("&msc", (KeySpec("SCRL_UP"),)),
        36: KeySpec("&mmv", (KeySpec("MOVE_LEFT"),)),
        37: KeySpec("&mmv", (KeySpec("MOVE_DOWN"),)),
        38: KeySpec("&mmv", (KeySpec("MOVE_RIGHT"),)),
        41: KeySpec("&mo", (KeySpec(6),)),
        42: KeySpec("&mo", (KeySpec(5),)),
        43: KeySpec("&mo", (KeySpec(4),)),
        47: KeySpec("&msc", (KeySpec("SCRL_DOWN"),)),
        48: KeySpec("&mo", (KeySpec(4),)),
        49: KeySpec("&mo", (KeySpec(5),)),
        50: KeySpec("&mo", (KeySpec(6),)),
        52: KeySpec("&mkp", (KeySpec("MCLK"),)),
        54: KeySpec("&mkp", (KeySpec("MB5"),)),
        59: KeySpec("&mmv", (KeySpec("MOVE_LEFT"),)),
        60: KeySpec("&mmv", (KeySpec("MOVE_UP"),)),
        61: KeySpec("&mmv", (KeySpec("MOVE_DOWN"),)),
        62: KeySpec("&mmv", (KeySpec("MOVE_RIGHT"),)),
        69: KeySpec("&mkp", (KeySpec("LCLK"),)),
        70: KeySpec("&mkp", (KeySpec("RCLK"),)),
        71: KeySpec("&mkp", (KeySpec("MB4"),)),
        75: KeySpec("&mkp", (KeySpec("LCLK"),)),
        76: KeySpec("&mkp", (KeySpec("RCLK"),)),
        77: KeySpec("&mkp", (KeySpec("MCLK"),)),
        78: KeySpec("&mkp", (KeySpec("MB4"),)),
        79: KeySpec("&mkp", (KeySpec("MB5"),)),
    }
)


def build_mouse_layer(_variant: str) -> Layer:
    return build_layer_from_spec(MOUSE_LAYER_SPEC)
