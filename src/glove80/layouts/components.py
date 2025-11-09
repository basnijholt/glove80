"""Shared feature component dataclasses used by layout builders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Sequence

from glove80.base import LayerMap


@dataclass(frozen=True)
class LayoutFeatureComponents:
    """Small bundle of reusable layout pieces (macros, layers, etc.)."""

    macros: Sequence[Dict[str, Any]] = ()
    macro_overrides: Mapping[str, Dict[str, Any]] = field(default_factory=dict)
    hold_taps: Sequence[Dict[str, Any]] = ()
    combos: Sequence[Dict[str, Any]] = ()
    input_listeners: Sequence[Dict[str, Any]] = ()
    layers: LayerMap = field(default_factory=dict)


__all__ = ["LayoutFeatureComponents"]
