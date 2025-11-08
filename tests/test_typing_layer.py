import pytest

from tailorkey_builder.tailorkey.layers.typing import build_typing_layer
from tests.utils import load_variant_json


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _load_layer(variant: str):
    data = load_variant_json(variant)
    idx = data["layer_names"].index("Typing")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_typing_layer(variant):
    assert build_typing_layer(variant) == _load_layer(variant)
