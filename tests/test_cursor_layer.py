import pytest

from tailorkey_builder.tailorkey.layers.cursor import build_cursor_layer
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
    name = "Cursor"
    idx = data["layer_names"].index(name)
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_cursor_layer_matches_canonical(variant):
    assert build_cursor_layer(variant) == _load_canonical_layer(variant)
