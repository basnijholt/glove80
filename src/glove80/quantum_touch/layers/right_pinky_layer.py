"""QuantumTouch RightPinky training layer."""

from __future__ import annotations

from ...base import KeySpec, Layer, LayerSpec, build_layer_from_spec


RIGHT_PINKY_LAYER_SPEC = LayerSpec(
    overrides={
        5: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("F6"),)),
        6: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("F7"),)),
        7: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("F8"),)),
        8: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("F9"),)),
        9: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("F10"),)),
        16: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("N6"),)),
        17: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("N7"),)),
        18: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("N8"),)),
        19: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("N9"),)),
        20: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("N0"),)),
        21: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("MINUS"),)),
        28: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("Y"),)),
        29: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("U"),)),
        30: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("I"),)),
        31: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("O"),)),
        32: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("P"),)),
        33: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("BSLH"),)),
        35: KeySpec("&kp", (KeySpec("A"),)),
        36: KeySpec("&kp", (KeySpec("S"),)),
        37: KeySpec("&kp", (KeySpec("D"),)),
        38: KeySpec("&kp", (KeySpec("F"),)),
        40: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("H"),)),
        41: KeySpec("&BHRM_R_Pinky_Index", (KeySpec("RSHFT"), KeySpec("J"))),
        42: KeySpec("&BHRM_R_Pinky_Middle", (KeySpec("RGUI"), KeySpec("K"))),
        43: KeySpec("&BHRM_R_Pinky_Ring", (KeySpec("LALT"), KeySpec("L"))),
        44: KeySpec("&none"),
        45: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("SQT"),)),
        58: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("N"),)),
        59: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("M"),)),
        60: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("COMMA"),)),
        61: KeySpec("&BHRM_R_Pinky_Tap", (KeySpec("DOT"),)),
    }
)


def build_right_pinky_layer(_variant: str) -> Layer:
    return build_layer_from_spec(RIGHT_PINKY_LAYER_SPEC)
