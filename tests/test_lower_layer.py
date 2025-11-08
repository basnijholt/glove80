import pytest

from tailorkey_builder.tailorkey.layers.lower import build_lower_layer
from tests.utils import load_variant_json


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _load_canonical_layer(variant: str):
    data = load_variant_json(variant)
    idx = data["layer_names"].index("Lower")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_lower_layer_matches_canonical(variant):
    assert build_lower_layer(variant) == _load_canonical_layer(variant)
