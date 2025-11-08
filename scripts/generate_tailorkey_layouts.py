#!/usr/bin/env python3
"""Regenerate the published TailorKey layouts from the canonical sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METADATA_PATH = ROOT / "sources" / "variant_metadata.json"

sys.path.insert(0, str(ROOT / "src"))

from tailorkey_builder.tailorkey.layouts import build_layout  # noqa: E402
from tailorkey_builder.metadata import (  # noqa: E402
    MetadataByVariant,
    VariantMetadata,
    load_metadata,
)


def write_layout(data: dict, destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        current = json.loads(destination.read_text(encoding="utf-8"))
        if current == data:
            return False
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def generate_variant(name: str, meta: VariantMetadata) -> None:
    destination = ROOT / meta["output"]
    layout = build_layout(name)

    for field in ("title", "uuid", "parent_uuid", "date", "notes", "tags"):
        if field in meta:
            layout[field] = meta[field]

    changed = write_layout(layout, destination)
    rel = destination.relative_to(ROOT)
    status = "updated" if changed else "unchanged"
    print(f"{name}: {rel} ({status})")


def main() -> None:
    metadata: MetadataByVariant = load_metadata(METADATA_PATH)
    for name, meta in metadata.items():
        generate_variant(name, meta)


if __name__ == "__main__":
    main()
