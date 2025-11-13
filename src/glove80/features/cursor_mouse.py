"""Cursor and mouse feature bundles shared by the TUI."""

from __future__ import annotations

import copy
from typing import Iterable, Sequence

from glove80.families.tailorkey.alpha_layouts import base_variant_for
from glove80.families.tailorkey.layers.cursor import build_cursor_layer
from glove80.families.tailorkey.layers.mouse import build_mouse_layers
from glove80.families.tailorkey.specs.macros import CURSOR_MACROS, CURSOR_MACROS_MAC
from glove80.layouts.components import LayoutFeatureComponents
from glove80.layouts.listeners import make_mouse_listeners


def cursor_components(variant: str) -> LayoutFeatureComponents:
    """Return the cursor-layer bundle for the requested variant."""

    base_variant = base_variant_for(variant)
    layer_name = "Cursor"
    layers = {layer_name: build_cursor_layer(variant)}

    macros: list = list(_clone_models(CURSOR_MACROS))
    if base_variant in {"mac", "bilateral_mac"}:
        macros.extend(_clone_models(CURSOR_MACROS_MAC))

    return LayoutFeatureComponents(layers=layers, macros=tuple(macros))


def mouse_components(variant: str) -> LayoutFeatureComponents:
    """Return the mouse-layer bundle (layers + listeners)."""

    layers = build_mouse_layers(variant)
    listeners = tuple(_clone_models(make_mouse_listeners()))
    return LayoutFeatureComponents(layers=layers, input_listeners=listeners)


def _clone_models(items: Iterable) -> Sequence:
    """Return deep copies of (pydantic) models for safe reuse."""

    clones: list = []
    for item in items:
        copy_fn = getattr(item, "model_copy", None)
        clones.append(copy_fn(deep=True) if callable(copy_fn) else copy.deepcopy(item))
    return clones


__all__ = ["cursor_components", "mouse_components"]
