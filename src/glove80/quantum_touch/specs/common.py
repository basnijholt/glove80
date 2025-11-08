"""Common metadata for QuantumTouch layouts."""

COMMON_FIELDS = {
    "keyboard": "glove80",
    "firmware_api_version": "1",
    "locale": "en-US",
    "unlisted": False,
    "creator": "basnijholt",
    "custom_defined_behaviors": '// "Meh" key to define custom commands in e.g., VSCode\n'
    "// NOTE: Using right-side keys because of Keyd remaps in Linux\n"
    "#define MEH_KEY RA(RC(RIGHT_SHIFT))\n"
    "\n"
    "behaviors {\n"
    "    // Shift + Backspace for Delete\n"
    "    bspc_del: backspace_delete {\n"
    '        compatible = "zmk,behavior-mod-morph";\n'
    "        #binding-cells = <0>;\n"
    "        bindings = <&kp BACKSPACE>, <&kp DELETE>;\n"
    "        mods = <(MOD_LSFT|MOD_RSFT)>;\n"
    "        keep-mods = <0>;\n"
    "    };\n"
    "\n"
    "    // Double tap to toggle caps word\n"
    "    td_caps_lshift: tap_dance_caps_lshift {\n"
    '        compatible = "zmk,behavior-tap-dance";\n'
    "        #binding-cells = <0>;\n"
    "        tapping-term-ms = <200>;\n"
    "        bindings = <&kp LSHIFT>, <&caps_word>;\n"
    "    };\n"
    "    td_caps_rshift: tap_dance_caps_rshift {\n"
    '        compatible = "zmk,behavior-tap-dance";\n'
    "        #binding-cells = <0>;\n"
    "        tapping-term-ms = <200>;\n"
    "        bindings = <&kp RSHIFT>, <&caps_word>;\n"
    "    };\n"
    "    // (Sticky) Double tap to toggle caps word\n"
    "    td_caps_lshift_sk: tap_dance_caps_lshift_sk {\n"
    '        compatible = "zmk,behavior-tap-dance";\n'
    "        #binding-cells = <0>;\n"
    "        tapping-term-ms = <200>;\n"
    "        bindings = <&sk LSHIFT>, <&caps_word>;\n"
    "    };\n"
    "    td_caps_rshift_sk: tap_dance_caps_rshift_sk {\n"
    '        compatible = "zmk,behavior-tap-dance";\n'
    "        #binding-cells = <0>;\n"
    "        tapping-term-ms = <200>;\n"
    "        bindings = <&sk RSHIFT>, <&caps_word>;\n"
    "    };\n"
    "\n"
    "    // Double tap Command for Enter\n"
    "    td_lgui_enter: td_lgui_enter {\n"
    '        compatible = "zmk,behavior-tap-dance";\n'
    "        #binding-cells = <0>;\n"
    "        tapping-term-ms = <200>;\n"
    "        bindings = <&kp LGUI>, <&kp ENTER>;\n"
    "    };\n"
    "    // (Sticky) Double tap Command for Enter\n"
    "    td_lgui_enter_sk: td_lgui_enter_sk {\n"
    '        compatible = "zmk,behavior-tap-dance";\n'
    "        #binding-cells = <0>;\n"
    "        tapping-term-ms = <200>;\n"
    "        bindings = <&sk LGUI>, <&kp ENTER>;\n"
    "    };\n"
    "\n"
    "    behavior_caps_word {\n"
    "        continue-list = <\n"
    "            UNDERSCORE\n"
    "            BACKSPACE DELETE\n"
    "            N1 N2 N3 N4 N5 N6 N7 N8 N9 N0\n"
    "            LSHFT RSHFT\n"
    "        >;\n"
    "        mods = <(MOD_LSFT | MOD_RSFT)>;\n"
    "    };\n"
    "\n"
    "    // Mac-style word navigation with Alt (Option)\n"
    "    alt_left_word: alt_left_word {\n"
    '        compatible = "zmk,behavior-mod-morph";\n'
    "        #binding-cells = <0>;\n"
    "        bindings = <&kp LC(LEFT)>, <&kp LEFT>;\n"
    "        mods = <(MOD_LSFT|MOD_LCTL)>;\n"
    "        keep-mods = <(MOD_LSFT|MOD_LCTL)>;\n"
    "    };\n"
    "\n"
    "    alt_right_word: alt_right_word {\n"
    '        compatible = "zmk,behavior-mod-morph";\n'
    "        #binding-cells = <0>;\n"
    "        bindings = <&kp LC(RIGHT)>, <&kp RIGHT>;\n"
    "        mods = <(MOD_LSFT|MOD_LCTL)>;\n"
    "        keep-mods = <(MOD_LSFT|MOD_LCTL)>;\n"
    "    };\n"
    "\n"
    "    // Mac-style Shift + Backspace for Delete\n"
    "    alt_bspc_del_morph: alt_bspc_del_morph {\n"
    '        compatible = "zmk,behavior-mod-morph";\n'
    "        #binding-cells = <0>;\n"
    "        bindings = <&kp LC(BSPC)>, <&kp LC(DEL)>;\n"
    "        mods = <(MOD_LSFT|MOD_RSFT)>;\n"
    "    };\n"
    "\n"
    "    cmd_bspc_del_morph: cmd_bspc_del_morph {\n"
    '        compatible = "zmk,behavior-mod-morph";\n'
    "        #binding-cells = <0>;\n"
    "        bindings = <&cmd_backspace>, <&cmd_delete>;\n"
    "        mods = <(MOD_LSFT|MOD_RSFT)>;\n"
    "    };\n"
    "\n"
    "};\n"
    "\n"
    "macros {\n"
    "\n"
    "    // Delete line left (Cmd+Backspace)\n"
    "    cmd_backspace: cmd_backspace {\n"
    '        label = "&CMD_BACKSPACE";\n'
    '        compatible = "zmk,behavior-macro";\n'
    "        #binding-cells = <0>;\n"
    "        bindings = <&macro_press &kp LSHFT>, <&macro_tap &kp HOME>, <&macro_release &kp LSHFT>, <&macro_tap &kp BSPC>;\n"
    "    };\n"
    "\n"
    "    // Delete line right (Cmd+Delete)\n"
    "    cmd_delete: cmd_delete {\n"
    '        label = "&CMD_DELETE";\n'
    '        compatible = "zmk,behavior-macro";\n'
    "        #binding-cells = <0>;\n"
    "        bindings = <&macro_press &kp LSHFT>, <&macro_tap &kp END>, <&macro_release &kp LSHFT>, <&macro_tap &kp DEL>;\n"
    "    };\n"
    "};",
    "custom_devicetree": '&mt {\n    flavor = "tap-preferred";\n    tapping-term-ms = <220>;\n};',
    "config_parameters": [
        {"paramName": "BLE_BAS", "value": "y"},
        {"paramName": "HID_POINTING", "value": "y"},
        {"paramName": "EXPERIMENTAL_RGB_UNDERGLOW_AUTO_OFF_USB", "value": "y"},
    ],
    "layout_parameters": {},
}

LAYER_NAMES = [
    "Base",
    "HRM",
    "Original",
    "Lower",
    "Mouse",
    "MouseSlow",
    "MouseFast",
    "MouseWarp",
    "Magic",
    "LeftIndex",
    "LeftMiddle",
    "LeftRing",
    "LeftPinky",
    "RightIndex",
    "RightMiddle",
    "RightRing",
    "RightPinky",
]

__all__ = ["COMMON_FIELDS", "LAYER_NAMES"]
