import pytest

from tailorkey_builder.tailorkey.layers.symbol import build_symbol_layer
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
    idx = data["layer_names"].index("Symbol")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_symbol_layer_matches_canonical(variant):
    assert build_symbol_layer(variant) == _load_canonical_layer(variant)
