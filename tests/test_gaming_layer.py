import pytest

from tailorkey_builder.tailorkey.layers.gaming import build_gaming_layer
from tests.utils import load_variant_json


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _canonical_layer(variant: str):
    data = load_variant_json(variant)
    idx = data["layer_names"].index("Gaming")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_gaming_layer(variant):
    assert build_gaming_layer(variant) == _canonical_layer(variant)
