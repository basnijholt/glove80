import json
from pathlib import Path

import pytest

from tailorkey_builder.tailorkey.layouts import build_layout

import scripts.generate_tailorkey_layouts as generator


REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("variant", sorted(generator.load_metadata().keys()))
def test_generated_files_match_canonical_source(tmp_path, variant):
    """Each release JSON must match its canonical source exactly."""

    metadata = generator.load_metadata()
    meta = metadata[variant]

    source_path = REPO_ROOT / meta["output"]
    expected = json.loads(source_path.read_text())

    built = build_layout(variant)
    assert built == expected
