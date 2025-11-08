import json
from pathlib import Path

import pytest

from tailorkey_builder.layers.typing import build_typing_layer


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _load_layer(variant: str):
    data = json.loads((Path("sources/variants") / f"{variant}.json").read_text())
    idx = data["layer_names"].index("Typing")
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_typing_layer(variant):
    assert build_typing_layer(variant) == _load_layer(variant)
