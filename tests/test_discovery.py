from __future__ import annotations

from glove80.layouts.generator import available_layouts
from glove80.metadata import LAYOUT_METADATA_PACKAGES


def test_generator_imports_all_metadata_packages() -> None:
    """Discovery derives from LAYOUT_METADATA_PACKAGES values."""
    discovered = set(available_layouts())
    expected = set(LAYOUT_METADATA_PACKAGES.keys())
    assert expected.issubset(discovered)
