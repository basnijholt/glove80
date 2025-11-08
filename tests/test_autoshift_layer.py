import pytest

from tailorkey_builder.tailorkey.layers.autoshift import build_autoshift_layer
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
    idx = data["layer_names"].index("Autoshift")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_autoshift_layer(variant):
    assert build_autoshift_layer(variant) == _canonical_layer(variant)
