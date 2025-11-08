import pytest

from tailorkey_builder.tailorkey.layers.bilateral import build_bilateral_training_layers
from tests.utils import load_variant_json


@pytest.mark.parametrize("variant", ["windows", "mac", "dual"])
def test_bilateral_layers_absent(variant):
    assert build_bilateral_training_layers(variant) == {}


@pytest.mark.parametrize("variant", ["bilateral_windows", "bilateral_mac"])
def test_bilateral_layers_match_canonical(variant):
    layers = build_bilateral_training_layers(variant)
    data = load_variant_json(variant)
    expected_names = [
        name
        for name in data["layer_names"]
        if name
        in {
            "LeftIndex",
            "LeftMiddy",
            "LeftRingy",
            "LeftPinky",
            "RightIndex",
            "RightMiddy",
            "RightRingy",
            "RightPinky",
        }
    ]
    assert set(layers.keys()) == set(expected_names)
    for name in expected_names:
        idx = data["layer_names"].index(name)
        assert layers[name] == data["layers"][idx]
