import pytest

from tailorkey_builder.tailorkey.layers.magic import build_magic_layer
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
    idx = data["layer_names"].index("Magic")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_magic_layer(variant):
    assert build_magic_layer(variant) == _canonical_layer(variant)
