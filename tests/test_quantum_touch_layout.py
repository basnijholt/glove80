from glove80.quantum_touch.layouts import build_layout
from tests.utils import load_variant_json


def test_quantum_touch_matches_original():
    expected = load_variant_json("default", layout="quantum_touch")
    built = build_layout("default")
    assert built == expected
