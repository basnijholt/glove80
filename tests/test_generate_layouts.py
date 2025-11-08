import json
from pathlib import Path

import pytest

from glove80.metadata import load_metadata
from glove80.tailorkey.layouts import build_layout


REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("variant", sorted(load_metadata(layout="tailorkey").keys()))
def test_generated_files_match_canonical_source(tmp_path, variant):
    """Each release JSON must match its canonical source exactly."""

    metadata = load_metadata(layout="tailorkey")
    meta = metadata[variant]

    source_path = REPO_ROOT / meta["output"]
    expected = json.loads(source_path.read_text())

    built = build_layout(variant)
    assert built == expected
