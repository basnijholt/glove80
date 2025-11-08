"""Shared helpers for composing layout payloads."""

from __future__ import annotations

from typing import Iterable, Sequence

from ..base import Layer, LayerMap, resolve_layer_refs
from ..metadata import get_variant_metadata

META_FIELDS = ("title", "uuid", "parent_uuid", "date", "notes", "tags")
DEFAULT_REF_FIELDS = ("macros", "holdTaps", "combos", "inputListeners")


def resolve_referenced_fields(
    layout: dict,
    *,
    layer_names: Sequence[str],
    fields: Iterable[str] = DEFAULT_REF_FIELDS,
) -> None:
    """Resolve LayerRef placeholders for the requested fields."""

    layer_indices = {name: idx for idx, name in enumerate(layer_names)}
    for field in fields:
        layout[field] = resolve_layer_refs(layout[field], layer_indices)


def assemble_layers(layer_names: Sequence[str], generated_layers: LayerMap, *, variant: str) -> list[Layer]:
    """Return the ordered list of layers, erroring if any are missing."""

    ordered: list[Layer] = []
    for name in layer_names:
        try:
            ordered.append(generated_layers[name])
        except KeyError as exc:
            raise KeyError(f"No generated layer data for '{name}' in variant '{variant}'") from exc
    return ordered


def attach_variant_metadata(layout: dict, *, variant: str, layout_key: str) -> None:
    """Inject metadata fields into the layout payload."""

    meta = get_variant_metadata(variant, layout=layout_key)
    for field in META_FIELDS:
        layout[field] = meta.get(field)
