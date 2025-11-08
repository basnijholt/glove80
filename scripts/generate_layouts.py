#!/usr/bin/env python3
"""Regenerate every supported Glove80 layout from canonical sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from glove80.metadata import (  # noqa: E402
    MetadataByVariant,
    VariantMetadata,
    load_metadata as _load_metadata_from_pkg,
)
from glove80.quantum_touch.layouts import build_layout as build_quantum_touch_layout  # noqa: E402
from glove80.tailorkey.layouts import build_layout as build_tailorkey_layout  # noqa: E402

LayoutBuilder = Callable[[str], dict]

LAYOUT_BUILDERS: dict[str, LayoutBuilder] = {
    "tailorkey": build_tailorkey_layout,
    "quantum_touch": build_quantum_touch_layout,
}


def write_layout(data: dict, destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        current = json.loads(destination.read_text(encoding="utf-8"))
        if current == data:
            return False
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def generate_variant(layout_name: str, variant: str, meta: VariantMetadata, builder: LayoutBuilder) -> None:
    destination = ROOT / meta["output"]
    layout = builder(variant)

    for field in ("title", "uuid", "parent_uuid", "date", "notes", "tags"):
        if field in meta:
            layout[field] = meta[field]

    changed = write_layout(layout, destination)
    rel = destination.relative_to(ROOT)
    status = "updated" if changed else "unchanged"
    print(f"{layout_name}:{variant}: {rel} ({status})")


def load_layout_metadata(layout: str) -> MetadataByVariant:
    return _load_metadata_from_pkg(layout)


def load_metadata(layout: str = "tailorkey") -> MetadataByVariant:
    """Backward-compatible helper for tests (defaults to TailorKey metadata)."""

    return load_layout_metadata(layout)


def main() -> None:
    for layout_name, builder in LAYOUT_BUILDERS.items():
        metadata = load_layout_metadata(layout_name)
        for variant, meta in metadata.items():
            generate_variant(layout_name, variant, meta, builder)


if __name__ == "__main__":
    main()
