"""
Helpers for loading TailorKey variant metadata.

This keeps JSON parsing in one place (with types) so both the generator and the
library can share it safely.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_LAYOUT = "tailorkey"
LAYOUT_METADATA_PATHS: Dict[str, Path] = {
    "tailorkey": REPO_ROOT / "layouts" / "tailorkey" / "metadata" / "metadata.json",
    "quantum_touch": REPO_ROOT / "layouts" / "quantum_touch" / "metadata" / "metadata.json",
}


class VariantMetadata(TypedDict):
    output: str
    title: str
    uuid: str
    parent_uuid: str
    date: int
    tags: List[str]
    notes: str


MetadataByVariant = Dict[str, VariantMetadata]


def _metadata_path_for(layout: str, override: Path | None) -> Path:
    if override is not None:
        return override
    try:
        return LAYOUT_METADATA_PATHS[layout]
    except KeyError as exc:
        raise KeyError(f"Unknown layout '{layout}'. Available: {sorted(LAYOUT_METADATA_PATHS)}") from exc


@lru_cache()
def _load_metadata_cached(layout: str, metadata_path: str) -> MetadataByVariant:
    with Path(metadata_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_metadata(layout: str = DEFAULT_LAYOUT, path: Path | None = None) -> MetadataByVariant:
    """Load (and cache) the metadata file as typed objects."""

    metadata_path = _metadata_path_for(layout, path)
    return _load_metadata_cached(layout, str(metadata_path))


def get_variant_metadata(
    name: str,
    *,
    layout: str = DEFAULT_LAYOUT,
    path: Path | None = None,
) -> VariantMetadata:
    """Return the metadata entry for a particular variant."""

    metadata = load_metadata(layout, path)
    try:
        return metadata[name]
    except KeyError as exc:
        raise KeyError(f"Unknown variant '{name}' for layout '{layout}'. Available: {sorted(metadata)}") from exc
