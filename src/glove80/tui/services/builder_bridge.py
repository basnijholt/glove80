"""Feature bundle bridge that mirrors LayoutBuilder helpers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, Literal, Mapping, Sequence

from glove80.families.tailorkey.layers.hrm import build_hrm_layers
from glove80.layouts.components import LayoutFeatureComponents
from glove80.layouts.merge import merge_components

from ..state import LayoutStore


@dataclass(frozen=True)
class FeatureDiff:
    """Lightweight diff summary for feature bundle previews."""

    feature: str
    target_layer: str
    layers_added: tuple[str, ...]
    macros_added: tuple[str, ...]
    hold_taps_added: tuple[str, ...]
    combos_added: int
    listeners_added: int
    layer_order: tuple[str, ...]

    def summary(self) -> str:
        parts: list[str] = []
        if self.layers_added:
            parts.append(f"+{len(self.layers_added)}L")
        if self.macros_added:
            parts.append(f"+{len(self.macros_added)}M")
        if self.hold_taps_added:
            parts.append(f"+{len(self.hold_taps_added)}HT")
        if self.combos_added:
            parts.append(f"+{self.combos_added}C")
        if self.listeners_added:
            parts.append(f"+{self.listeners_added}IL")
        return " ".join(parts) if parts else "No changes"


class BuilderBridge:
    """Wraps LayoutBuilder feature helpers for use inside the TUI."""

    def __init__(
        self,
        *,
        store: LayoutStore,
        variant: str = "windows",
    ) -> None:
        self.store = store
        self.variant = variant or "windows"

    # ------------------------------------------------------------------
    # Public API
    def preview_home_row_mods(
        self,
        *,
        target_layer: str,
        position: Literal["before", "after"] = "after",
    ) -> FeatureDiff:
        payload = self.store.export_payload()
        _, diff = self._apply_home_row_mods(
            payload,
            target_layer=target_layer,
            position=position,
            dry_run=True,
        )
        return diff

    def apply_home_row_mods(
        self,
        *,
        target_layer: str,
        position: Literal["before", "after"] = "after",
    ) -> FeatureDiff:
        payload = self.store.export_payload()
        mutated, diff = self._apply_home_row_mods(
            payload,
            target_layer=target_layer,
            position=position,
            dry_run=False,
        )
        if diff.layers_added or diff.macros_added or diff.hold_taps_added or diff.combos_added or diff.listeners_added:
            self.store.replace_payload(mutated)
        return diff

    # ------------------------------------------------------------------
    # Internals
    def _apply_home_row_mods(
        self,
        payload: Mapping[str, object],
        *,
        target_layer: str,
        position: Literal["before", "after"],
        dry_run: bool,
    ) -> tuple[Dict[str, object], FeatureDiff]:
        components = self._home_row_components()
        if not components.layers:
            msg = "Home-row components are unavailable for this variant"
            raise ValueError(msg)

        layout = deepcopy(payload)
        merge_components(layout, components)

        component_names = list(components.layers.keys())
        self._reorder_layers(layout, component_names, target_layer=target_layer, position=position)

        diff = self._build_diff(payload, layout, component_names, target_layer=target_layer)
        return (payload if dry_run else layout, diff)

    def _home_row_components(self) -> LayoutFeatureComponents:
        layers = build_hrm_layers(self.variant)
        return LayoutFeatureComponents(layers=layers)

    @staticmethod
    def _reorder_layers(
        layout: Dict[str, object],
        component_names: Sequence[str],
        *,
        target_layer: str,
        position: Literal["before", "after"],
    ) -> None:
        layer_names = list(layout.get("layer_names", []))
        if target_layer not in layer_names:
            raise ValueError(f"Unknown target layer '{target_layer}'")

        sanitized = [name for name in layer_names if name not in component_names]
        if target_layer not in sanitized:
            raise ValueError(f"Target layer '{target_layer}' removed during preprocessing")

        anchor_index = sanitized.index(target_layer)
        insert_index = anchor_index + (1 if position == "after" else 0)
        updated_order = sanitized[:insert_index] + list(component_names) + sanitized[insert_index:]
        layers_by_name = dict(zip(layer_names, layout.get("layers", []), strict=False))
        layout["layer_names"] = updated_order
        layout["layers"] = [layers_by_name[name] for name in updated_order]

    @staticmethod
    def _build_diff(
        original: Mapping[str, object],
        mutated: Mapping[str, object],
        component_names: Sequence[str],
        *,
        target_layer: str,
    ) -> FeatureDiff:
        orig_macro_names = _names(original.get("macros", []))
        new_macro_names = _names(mutated.get("macros", []))
        orig_hold_names = _names(original.get("holdTaps", []))
        new_hold_names = _names(mutated.get("holdTaps", []))

        orig_combos = len(original.get("combos", []) or [])
        new_combos = len(mutated.get("combos", []) or [])
        orig_listeners = len(original.get("inputListeners", []) or [])
        new_listeners = len(mutated.get("inputListeners", []) or [])

        return FeatureDiff(
            feature="hrm",
            target_layer=target_layer,
            layers_added=tuple(name for name in component_names if name not in original.get("layer_names", [])),
            macros_added=tuple(name for name in new_macro_names if name not in orig_macro_names),
            hold_taps_added=tuple(name for name in new_hold_names if name not in orig_hold_names),
            combos_added=new_combos - orig_combos,
            listeners_added=new_listeners - orig_listeners,
            layer_order=tuple(mutated.get("layer_names", [])),
        )


def _names(items: Iterable[object]) -> set[str]:
    names: set[str] = set()
    for item in items:
        if isinstance(item, Mapping):
            value = item.get("name")
            if isinstance(value, str):
                names.add(value)
    return names


__all__ = ["BuilderBridge", "FeatureDiff"]
