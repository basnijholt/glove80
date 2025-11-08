"""Compose full TailorKey layouts from generated layers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence, cast

from ..base import resolve_layer_refs
from ..metadata import get_variant_metadata
from .layers import build_all_layers
from .specs import (
    COMBO_DATA,
    COMMON_FIELDS,
    HOLD_TAP_DEFS,
    HOLD_TAP_ORDER,
    INPUT_LISTENER_DATA,
    LAYER_NAME_MAP,
    MACRO_DEFS,
    MACRO_ORDER,
    MACRO_OVERRIDES,
)

META_FIELDS = ("title", "uuid", "parent_uuid", "date", "notes", "tags")


def _build_macros(variant: str) -> List[Dict[str, Any]]:
    order = _get_variant_section(MACRO_ORDER, variant, "macro order")
    overrides = MACRO_OVERRIDES.get(variant, {})
    macro_defs = cast(Mapping[str, Any], MACRO_DEFS)
    macros: List[Dict[str, Any]] = []
    for macro_name in order:
        macros.append(_materialize_named_entry(macro_defs, macro_name, overrides.get(macro_name)))
    return macros


def _build_hold_taps(variant: str) -> List[Dict[str, Any]]:
    order = _get_variant_section(HOLD_TAP_ORDER, variant, "hold-tap order")
    hold_tap_defs = cast(Mapping[str, Any], HOLD_TAP_DEFS)
    return [_materialize_named_entry(hold_tap_defs, name) for name in order]


def _materialize_named_entry(definitions: Mapping[str, Any], name: str, override: Any | None = None) -> Dict[str, Any]:
    data = override or definitions.get(name)
    if data is None:
        raise KeyError(f"Unknown definition '{name}'")
    if hasattr(data, "to_dict"):
        return data.to_dict()
    return deepcopy(data)


def _get_variant_section(sections: Mapping[str, Sequence[Any]], variant: str, label: str) -> List[Any]:
    try:
        return list(sections[variant])
    except KeyError as exc:
        raise KeyError(f"No {label} for variant '{variant}'") from exc


def _materialize_sequence(items: Sequence[Any]) -> List[Any]:
    result: List[Any] = []
    for item in items:
        if hasattr(item, "to_dict"):
            result.append(item.to_dict())
        else:
            result.append(deepcopy(item))
    return result


def _base_layout_payload(variant: str) -> Dict[str, Any]:
    layout = deepcopy(COMMON_FIELDS)
    layout["layer_names"] = deepcopy(_get_variant_section(LAYER_NAME_MAP, variant, "layer names"))
    layout["macros"] = _build_macros(variant)
    layout["holdTaps"] = _build_hold_taps(variant)
    layout["combos"] = _materialize_sequence(_get_variant_section(COMBO_DATA, variant, "combo definitions"))
    layout["inputListeners"] = _materialize_sequence(
        _get_variant_section(INPUT_LISTENER_DATA, variant, "input listeners")
    )
    return layout


def build_layout(variant: str) -> Dict:
    """Build the complete layout dictionary for the given variant."""

    layout = _base_layout_payload(variant)
    layer_names = layout["layer_names"]
    layer_indices = {name: idx for idx, name in enumerate(layer_names)}

    # Resolve any LayerRef placeholders (macros/combos/input listeners/etc).
    for field in ("macros", "holdTaps", "combos", "inputListeners"):
        layout[field] = resolve_layer_refs(layout[field], layer_indices)

    generated_layers = build_all_layers(variant)
    ordered_layers = []
    for name in layer_names:
        if name not in generated_layers:
            raise KeyError(f"No generated layer data for '{name}' in variant '{variant}'")
        ordered_layers.append(generated_layers[name])
    layout["layers"] = ordered_layers

    meta = get_variant_metadata(variant)
    for field in META_FIELDS:
        layout[field] = meta.get(field)

    return layout
