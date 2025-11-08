"""QuantumTouch LeftRing training layer."""

from __future__ import annotations

from ...base import KeySpec, Layer, LayerSpec, build_layer_from_spec


LEFT_RING_LAYER_SPEC = LayerSpec(
    overrides={
        0: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("F1"),)),
        1: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("F2"),)),
        2: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("F3"),)),
        3: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("F4"),)),
        4: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("F5"),)),
        10: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("EQUAL"),)),
        11: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("N1"),)),
        12: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("N2"),)),
        13: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("N3"),)),
        14: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("N4"),)),
        15: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("N5"),)),
        23: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("Q"),)),
        24: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("W"),)),
        25: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("E"),)),
        26: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("R"),)),
        27: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("T"),)),
        35: KeySpec("&BHRM_L_Ring_Pinky", (KeySpec("LCTRL"), KeySpec("A"))),
        36: KeySpec("&none"),
        37: KeySpec("&BHRM_L_Ring_Middle", (KeySpec("LGUI"), KeySpec("D"))),
        38: KeySpec("&BHRM_L_Ring_Index", (KeySpec("LSHFT"), KeySpec("F"))),
        39: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("G"),)),
        41: KeySpec("&kp", (KeySpec("J"),)),
        42: KeySpec("&kp", (KeySpec("K"),)),
        43: KeySpec("&kp", (KeySpec("L"),)),
        44: KeySpec("&kp", (KeySpec("SEMI"),)),
        47: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("Z"),)),
        48: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("X"),)),
        49: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("C"),)),
        50: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("V"),)),
        51: KeySpec("&BHRM_L_Ring_Tap", (KeySpec("B"),)),
    }
)


def build_left_ring_layer(_variant: str) -> Layer:
    return build_layer_from_spec(LEFT_RING_LAYER_SPEC)
