import json
from pathlib import Path

import pytest

from tailorkey_builder.layers.autoshift import build_autoshift_layer


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _canonical_layer(variant: str):
    data = json.loads((Path("sources/variants") / f"{variant}.json").read_text())
    idx = data["layer_names"].index("Autoshift")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_autoshift_layer(variant):
    assert build_autoshift_layer(variant) == _canonical_layer(variant)
