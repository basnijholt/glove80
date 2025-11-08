import pytest

from tailorkey_builder.tailorkey.layers.hrm import build_hrm_layers
from tests.utils import load_variant_json


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _canonical_layers(variant: str):
    data = load_variant_json(variant)
    layer_map = {}
    for idx, name in enumerate(data["layer_names"]):
        if name.startswith("HRM"):
            layer_map[name] = data["layers"][idx]
    return layer_map


@pytest.mark.parametrize("variant", VARIANTS)
def test_hrm_layers(variant):
    expected = _canonical_layers(variant)
    actual = build_hrm_layers(variant)
    assert actual.keys() == expected.keys()
    for name, layer in expected.items():
        assert actual[name] == layer
