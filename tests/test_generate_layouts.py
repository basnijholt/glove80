import json
from pathlib import Path

import pytest


import scripts.generate_tailorkey_layouts as generator


REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("variant", sorted(generator.load_metadata().keys()))
def test_generated_files_match_canonical_source(tmp_path, variant):
    """Each release JSON must match its canonical source exactly."""

    metadata = generator.load_metadata()
    meta = metadata[variant]

    source_path = REPO_ROOT / meta["source"]
    output_path = REPO_ROOT / meta["output"]

    # Ensure the generator rewrites the files before comparing.
    generator.generate_variant(variant, meta)

    with (
        source_path.open(encoding="utf-8") as src,
        output_path.open(encoding="utf-8") as dst,
    ):
        assert json.load(src) == json.load(dst)
