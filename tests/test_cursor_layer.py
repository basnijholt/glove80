import json
from pathlib import Path

import pytest

from tailorkey_builder.layers.cursor import build_cursor_layer


VARIANTS = [
    "windows",
    "mac",
    "dual",
    "bilateral_windows",
    "bilateral_mac",
]


def _load_canonical_layer(variant: str):
    path = Path("sources/variants") / f"{variant}.json"
    data = json.loads(path.read_text())
    name = "Cursor"
    idx = data["layer_names"].index(name)
    return data["layers"][idx]


@pytest.mark.parametrize("variant", VARIANTS)
def test_cursor_layer_matches_canonical(variant):
    assert build_cursor_layer(variant) == _load_canonical_layer(variant)
