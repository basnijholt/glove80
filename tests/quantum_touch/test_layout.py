from glove80.quantum_touch.layouts import build_layout


def test_quantum_touch_matches_original(load_quantum_touch_variant):
    expected = load_quantum_touch_variant("default")
    built = build_layout("default")
    assert built == expected
