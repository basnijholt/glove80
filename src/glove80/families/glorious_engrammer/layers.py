"""Layer builders for Glorious Engrammer."""

from __future__ import annotations

from typing import Dict

from glove80.base import LayerMap, LayerSpec, build_layer_from_spec
from glove80.layouts.layers import _rows_to_layer_spec

from .layer_rows import LayerRows, LAYER_ROWS


def _build_layer_specs(rows: Dict[str, LayerRows]) -> Dict[str, LayerSpec]:
    return {name: _rows_to_layer_spec(layer_rows) for name, layer_rows in rows.items()}


LAYER_SPECS = _build_layer_specs(LAYER_ROWS)


def build_all_layers(variant: str) -> LayerMap:  # noqa: ARG001
    """Return concrete layers for every Glorious Engrammer entry."""

    return {name: build_layer_from_spec(spec) for name, spec in LAYER_SPECS.items()}


__all__ = ["LAYER_SPECS", "build_all_layers"]
