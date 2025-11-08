import json
from pathlib import Path

import pytest

from tailorkey_builder.layers.gaming import build_gaming_layer


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _canonical_layer(variant: str):
    data = json.loads((Path("sources/variants") / f"{variant}.json").read_text())
    idx = data["layer_names"].index("Gaming")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_gaming_layer(variant):
    assert build_gaming_layer(variant) == _canonical_layer(variant)
