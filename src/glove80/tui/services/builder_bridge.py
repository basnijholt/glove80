"""Feature bundle bridge that mirrors LayoutBuilder helpers."""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, Literal, Mapping, Sequence, Tuple, cast

from glove80.features.cursor_mouse import cursor_components, mouse_components
from glove80.families.tailorkey.alpha_layouts import TAILORKEY_VARIANTS
from glove80.families.tailorkey.layers.hrm import build_hrm_layers
from glove80.layouts.components import LayoutFeatureComponents
from glove80.layouts.merge import merge_components

from ..state import LayoutStore


_LOGGER = logging.getLogger(__name__)
_TAILORKEY_VARIANTS = {name.lower() for name in TAILORKEY_VARIANTS}


@dataclass(frozen=True)
class FeatureInfo:
    """Metadata describing a catalogued feature bundle."""

    name: str
    label: str
    description: str
    provenance: str


@dataclass(frozen=True)
class FeatureDiff:
    """Lightweight diff summary for feature bundle previews."""

    feature: str
    label: str
    provenance: str
    description: str
    target_layer: str
    layers_added: tuple[str, ...]
    macros_added: tuple[str, ...]
    hold_taps_added: tuple[str, ...]
    combos_added: int
    listeners_added: int
    layer_order: tuple[str, ...]
    conflicts: tuple[str, ...] = ()

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


_FEATURE_CATALOG: tuple[FeatureInfo, ...] = (
    FeatureInfo(
        name="hrm",
        label="Home Row Mods",
        description="Adds TailorKey home-row mod layers for the active layout.",
        provenance="TailorKey",
    ),
    FeatureInfo(
        name="cursor",
        label="Cursor Layer",
        description="Adds the TailorKey cursor layer and supporting macros.",
        provenance="TailorKey",
    ),
    FeatureInfo(
        name="mouse",
        label="Mouse Layers",
        description="Adds mouse layers plus movement/scroll listeners.",
        provenance="TailorKey",
    ),
)
_FEATURE_BY_NAME = {info.name: info for info in _FEATURE_CATALOG}


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
        self._warned_variant_fallback = False

    def list_available_features(self) -> tuple[FeatureInfo, ...]:
        return _FEATURE_CATALOG

    def preview_feature(
        self,
        name: str,
        *,
        target_layer: str,
        position: Literal["before", "after"] = "after",
    ) -> FeatureDiff:
        info = _FEATURE_BY_NAME[name]
        payload = self.store.export_payload()
        components = self._components_for_feature(info)
        _, diff = self._merge_feature(
            payload,
            info,
            components,
            target_layer=target_layer,
            position=position,
            dry_run=True,
        )
        return diff

    def apply_feature(
        self,
        name: str,
        *,
        target_layer: str,
        position: Literal["before", "after"] = "after",
    ) -> FeatureDiff:
        info = _FEATURE_BY_NAME[name]
        payload = self.store.export_payload()
        components = self._components_for_feature(info)
        mutated, diff = self._merge_feature(
            payload,
            info,
            components,
            target_layer=target_layer,
            position=position,
            dry_run=False,
        )
        if diff.summary() != "No changes":
            self.store.replace_payload(mutated)
        return diff

    def preview_home_row_mods(
        self,
        *,
        target_layer: str,
        position: Literal["before", "after"] = "after",
    ) -> FeatureDiff:
        return self.preview_feature("hrm", target_layer=target_layer, position=position)

    def apply_home_row_mods(
        self,
        *,
        target_layer: str,
        position: Literal["before", "after"] = "after",
    ) -> FeatureDiff:
        return self.apply_feature("hrm", target_layer=target_layer, position=position)

    def _merge_feature(
        self,
        payload: Dict[str, object],
        info: FeatureInfo,
        components: LayoutFeatureComponents,
        *,
        target_layer: str,
        position: Literal["before", "after"],
        dry_run: bool,
    ) -> tuple[Dict[str, object], FeatureDiff]:
        conflicts = self._detect_conflicts(payload, components)
        if conflicts:
            formatted = ", ".join(conflicts)
            raise ValueError(f"Feature '{info.label}' cannot be applied because {formatted} already exist")

        layout = deepcopy(payload)
        merge_components(layout, components)

        component_names = list(components.layers.keys())
        if component_names:
            self._reorder_layers(
                layout,
                component_names,
                target_layer=target_layer,
                position=position,
            )

        diff = self._build_diff(
            payload,
            layout,
            component_names,
            info=info,
            target_layer=target_layer,
        )
        return (payload if dry_run else layout, diff)

    def _components_for_feature(self, info: FeatureInfo) -> LayoutFeatureComponents:
        if info.name == "hrm":
            return self._home_row_components()
        if info.name == "cursor":
            return cursor_components(self.variant)
        if info.name == "mouse":
            return mouse_components(self.variant)
        msg = f"Unknown feature '{info.name}'"
        raise ValueError(msg)

    def _home_row_components(self) -> LayoutFeatureComponents:
        normalized, fallback = _normalize_tailorkey_variant(self.variant)
        if fallback and not self._warned_variant_fallback:
            _LOGGER.warning(
                "HRM preview variant '%s' is not a TailorKey variant; using '%s' instead",
                self.variant,
                normalized,
            )
            self._warned_variant_fallback = True
        layers = build_hrm_layers(normalized)
        return LayoutFeatureComponents(layers=layers)

    @staticmethod
    def _reorder_layers(
        layout: Dict[str, object],
        component_names: Sequence[str],
        *,
        target_layer: str,
        position: Literal["before", "after"],
    ) -> None:
        layer_names = list(_string_sequence(layout.get("layer_names")))
        if target_layer not in layer_names:
            raise ValueError(f"Unknown target layer '{target_layer}'")

        sanitized = [name for name in layer_names if name not in component_names]
        if target_layer not in sanitized:
            raise ValueError(f"Target layer '{target_layer}' removed during preprocessing")

        anchor_index = sanitized.index(target_layer)
        insert_index = anchor_index + (1 if position == "after" else 0)
        updated_order = sanitized[:insert_index] + list(component_names) + sanitized[insert_index:]
        layer_entries = list(cast(Sequence[object], layout.get("layers", [])))
        layers_by_name = dict(zip(layer_names, layer_entries, strict=False))
        layout["layer_names"] = updated_order
        layout["layers"] = [layers_by_name[name] for name in updated_order]

    def _build_diff(
        self,
        original: Mapping[str, object],
        mutated: Mapping[str, object],
        component_names: Sequence[str],
        *,
        info: FeatureInfo,
        target_layer: str,
    ) -> FeatureDiff:
        orig_macro_names = _names(_sequence_of_mappings(original.get("macros")))
        new_macro_names = _names(_sequence_of_mappings(mutated.get("macros")))
        orig_hold_names = _names(_sequence_of_mappings(original.get("holdTaps")))
        new_hold_names = _names(_sequence_of_mappings(mutated.get("holdTaps")))

        orig_combos = len(_sequence_of_mappings(original.get("combos")))
        new_combos = len(_sequence_of_mappings(mutated.get("combos")))
        orig_listeners = len(_sequence_of_mappings(original.get("inputListeners")))
        new_listeners = len(_sequence_of_mappings(mutated.get("inputListeners")))

        return FeatureDiff(
            feature=info.name,
            label=info.label,
            provenance=info.provenance,
            description=info.description,
            target_layer=target_layer,
            layers_added=tuple(
                name for name in component_names if name not in _string_sequence(original.get("layer_names"))
            ),
            macros_added=tuple(name for name in new_macro_names if name not in orig_macro_names),
            hold_taps_added=tuple(name for name in new_hold_names if name not in orig_hold_names),
            combos_added=new_combos - orig_combos,
            listeners_added=new_listeners - orig_listeners,
            layer_order=_string_sequence(mutated.get("layer_names")),
        )

    @staticmethod
    def _detect_conflicts(
        original: Mapping[str, object],
        components: LayoutFeatureComponents,
    ) -> tuple[str, ...]:
        conflicts: list[str] = []

        existing_layers = set(_string_sequence(original.get("layer_names")))
        for name in components.layers.keys():
            if name in existing_layers:
                conflicts.append(f"layer '{name}'")

        existing_macros = _names(_sequence_of_mappings(original.get("macros")))
        for macro in components.macros:
            macro_name = getattr(macro, "name", None)
            if macro_name and macro_name in existing_macros:
                conflicts.append(f"macro '{macro_name}'")

        if components.macros_by_name:
            for macro_name in components.macros_by_name.keys():
                if macro_name in existing_macros:
                    conflicts.append(f"macro '{macro_name}'")

        return tuple(conflicts)


def _names(items: Iterable[Mapping[str, object]]) -> set[str]:
    names: set[str] = set()
    for item in items:
        value = item.get("name")
        if isinstance(value, str):
            names.add(value)
    return names


def _sequence_of_mappings(value: object | None) -> Tuple[Mapping[str, object], ...]:
    if isinstance(value, Sequence):
        collected: list[Mapping[str, object]] = []
        for entry in value:
            if isinstance(entry, Mapping):
                collected.append(entry)
        return tuple(collected)
    return ()


def _string_sequence(value: object | None) -> Tuple[str, ...]:
    if isinstance(value, Sequence):
        return tuple(entry for entry in value if isinstance(entry, str))
    return ()


def _normalize_tailorkey_variant(candidate: str | None) -> tuple[str, bool]:
    """Map arbitrary variant names to a TailorKey-safe value."""

    name = (candidate or "windows").strip().lower()
    if name in _TAILORKEY_VARIANTS:
        return name, False
    return "windows", True


__all__ = ["BuilderBridge", "FeatureDiff", "FeatureInfo"]
