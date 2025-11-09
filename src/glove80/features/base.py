"""Helpers for applying reusable layout feature bundles."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableSequence

from glove80.layouts.components import LayoutFeatureComponents


def _ensure_section(
    layout: Mapping[str, MutableSequence[Dict[str, Any]]],
    key: str,
) -> MutableSequence[Dict[str, Any]]:
    section = layout.get(key)
    if section is None:
        raise KeyError(f"Layout is missing '{key}' section")
    return section  # type: ignore[return-value]


def apply_feature(layout: dict, components: LayoutFeatureComponents) -> None:
    """Mutate *layout* in-place by appending the provided components."""

    existing_macros = list(_ensure_section(layout, "macros"))
    macros_by_name = {macro.get("name"): macro for macro in existing_macros if "name" in macro}
    macro_order = [macro.get("name") for macro in existing_macros if "name" in macro]

    def _set_macro(macro_dict: Dict[str, Any]) -> None:
        name = macro_dict.get("name")
        if not isinstance(name, str):
            raise KeyError("Feature macros must include a 'name'")
        macros_by_name[name] = macro_dict
        if name not in macro_order:
            macro_order.append(name)

    for macro in components.macros:
        _set_macro(macro)
    for macro in components.macro_overrides.values():
        _set_macro(macro)

    layout["macros"] = [macros_by_name[name] for name in macro_order]

    _ensure_section(layout, "holdTaps").extend(components.hold_taps)
    _ensure_section(layout, "combos").extend(components.combos)
    _ensure_section(layout, "inputListeners").extend(components.input_listeners)

    layer_names: MutableSequence[str] = layout.setdefault("layer_names", [])  # type: ignore[assignment]
    ordered_layers: MutableSequence[Any] = layout.setdefault("layers", [])  # type: ignore[assignment]
    layers_by_name: Dict[str, Any] = {name: layer for name, layer in zip(layer_names, ordered_layers)}

    for name, layer in components.layers.items():
        if name not in layers_by_name:
            layer_names.append(name)
        layers_by_name[name] = layer

    layout["layers"] = [layers_by_name[name] for name in layer_names]


__all__ = ["apply_feature", "LayoutFeatureComponents"]
