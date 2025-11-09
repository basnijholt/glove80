"""Shared feature component dataclasses used by layout builders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from glove80.base import LayerMap


@dataclass(frozen=True)
class LayoutFeatureComponents:
    """Small bundle of reusable layout pieces (macros, layers, etc.)."""

    macros: Sequence[Any] = ()
    macro_overrides: Mapping[str, Any] = field(default_factory=dict)
    hold_taps: Sequence[Any] = ()
    combos: Sequence[Any] = ()
    input_listeners: Sequence[Any] = ()
    layers: LayerMap = field(default_factory=dict)


__all__ = ["LayoutFeatureComponents"]
