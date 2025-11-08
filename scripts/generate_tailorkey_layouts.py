#!/usr/bin/env python3
"""Regenerate the published TailorKey layouts from the canonical sources."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METADATA_PATH = ROOT / "sources" / "variant_metadata.json"


def load_metadata() -> dict[str, dict]:
    with METADATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_layout(data: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def generate_variant(name: str, meta: dict) -> None:
    source_path = ROOT / meta["source"]
    destination = ROOT / meta["output"]

    with source_path.open(encoding="utf-8") as handle:
        layout = json.load(handle)

    for field in ("title", "uuid", "parent_uuid", "date", "notes", "tags"):
        if field in meta:
            layout[field] = meta[field]

    write_layout(layout, destination)
    rel = destination.relative_to(ROOT)
    print(f"Wrote {name}: {rel}")


def main() -> None:
    metadata = load_metadata()
    for name, meta in metadata.items():
        generate_variant(name, meta)


if __name__ == "__main__":
    main()
