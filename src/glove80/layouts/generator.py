"""Helpers for regenerating release JSON artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from glove80.families import default  # noqa: F401  # ensure registration
from glove80.families import glorious_engrammer  # noqa: F401
from glove80.families import quantum_touch  # noqa: F401
from glove80.families import tailorkey  # noqa: F401
from glove80.layouts.family import REGISTRY, LayoutFamily
from glove80.metadata import MetadataByVariant, VariantMetadata, load_metadata

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

META_FIELDS = ("title", "uuid", "parent_uuid", "date", "notes", "tags")


@dataclass(frozen=True)
class GenerationResult:
    """Summary of a generated layout variant."""

    layout: str
    variant: str
    destination: Path
    changed: bool


def available_layouts() -> list[str]:
    """Return the sorted list of known layout families."""
    return sorted(registered.name for registered in REGISTRY.families())


def _normalize_layout_name(layout: str | None) -> Iterable[tuple[str, LayoutFamily]]:
    registered_families = list(REGISTRY.families())
    if layout is None:
        return [(registered.name, registered.family) for registered in registered_families]
    try:
        family = REGISTRY.get(layout)
        return [(layout, family)]
    except KeyError as exc:  # pragma: no cover
        msg = f"Unknown layout '{layout}'. Available: {available_layouts()}"
        raise KeyError(msg) from exc


def _iter_variants(
    layout: str,
    metadata: MetadataByVariant,
    variant: str | None = None,
) -> Iterator[tuple[str, VariantMetadata]]:
    if variant is None:
        yield from metadata.items()
        return
    try:
        yield variant, metadata[variant]
    except KeyError as exc:  # pragma: no cover
        msg = f"Unknown variant '{variant}' for layout '{layout}'. Available: {sorted(metadata)}"
        raise KeyError(msg) from exc


def _write_layout(data: dict[str, Any], destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        current = json.loads(destination.read_text(encoding="utf-8"))
        if current == data:
            return False
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def _augment_layout_with_metadata(layout: dict[str, Any], meta: VariantMetadata) -> None:
    meta_dict = cast("dict[str, Any]", meta)
    for field in META_FIELDS:
        if field in meta_dict:
            layout[field] = meta_dict[field]


def generate_layouts(
    *,
    layout: str | None = None,
    variant: str | None = None,
    metadata_path: Path | None = None,
    dry_run: bool = False,
) -> list[GenerationResult]:
    """Generate layouts and write (or check) their release artifacts."""
    results: list[GenerationResult] = []
    for layout_name, family in _normalize_layout_name(layout):
        metadata = load_metadata(layout=layout_name, path=metadata_path)
        for variant_name, meta in _iter_variants(layout_name, metadata, variant):
            destination = Path(meta["output"])
            layout_payload = family.build(variant_name)
            _augment_layout_with_metadata(layout_payload, meta)

            changed = False
            if dry_run:
                if destination.exists():
                    current = json.loads(destination.read_text(encoding="utf-8"))
                    changed = current != layout_payload
                else:
                    changed = True
            else:
                changed = _write_layout(layout_payload, destination)

            results.append(
                GenerationResult(
                    layout=layout_name,
                    variant=variant_name,
                    destination=destination,
                    changed=changed,
                ),
            )
    return results
