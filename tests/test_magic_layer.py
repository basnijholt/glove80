import json
from pathlib import Path

import pytest

from tailorkey_builder.layers.magic import build_magic_layer


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _canonical_layer(variant: str):
    data = json.loads((Path("sources/variants") / f"{variant}.json").read_text())
    idx = data["layer_names"].index("Magic")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_magic_layer(variant):
    assert build_magic_layer(variant) == _canonical_layer(variant)
