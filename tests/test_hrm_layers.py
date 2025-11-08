import json
from pathlib import Path

import pytest

from tailorkey_builder.layers.hrm import build_hrm_layers


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _canonical_layers(variant: str):
    data = json.loads((Path("sources/variants") / f"{variant}.json").read_text())
    layer_map = {}
    for idx, name in enumerate(data["layer_names"]):
        if name.startswith("HRM"):
            layer_map[name] = data["layers"][idx]
    return layer_map


@pytest.mark.parametrize("variant", VARIANTS)
def test_hrm_layers(variant):
    expected = _canonical_layers(variant)
    actual = build_hrm_layers(variant)
    assert actual.keys() == expected.keys()
    for name, layer in expected.items():
        assert actual[name] == layer
