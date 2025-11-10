"""Helpers for applying reusable layout feature bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from glove80.layouts.components import LayoutFeatureComponents
from glove80.layouts.merge import merge_layers_with_order, merge_sections_except_layers

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableSequence


def _ensure_section(
    layout: Mapping[str, MutableSequence[Any]],
    key: str,
) -> MutableSequence[Any]:
    section = layout.get(key)
    if section is None:
        msg = f"Layout is missing '{key}' section"
        raise KeyError(msg)
    return section  # type: ignore[return-value]


def apply_feature(layout: dict, components: LayoutFeatureComponents) -> None:
    """Mutate *layout* in-place by appending the provided components."""

    def _to_dict(obj: Any) -> dict[str, Any]:
        if hasattr(obj, "model_dump"):
            return obj.model_dump(by_alias=True, exclude_none=True)
        return obj

    sections_view = {
        "macros": _ensure_section(layout, "macros"),
        "holdTaps": _ensure_section(layout, "holdTaps"),
        "combos": _ensure_section(layout, "combos"),
        "inputListeners": _ensure_section(layout, "inputListeners"),
    }
    merge_sections_except_layers(
        sections_view,
        components,
        normalize=_to_dict,
        macro_normalize=_to_dict,
    )

    layer_names: MutableSequence[str] = layout.setdefault("layer_names", [])  # type: ignore[assignment]
    ordered_layers: MutableSequence[Any] = layout.setdefault("layers", [])  # type: ignore[assignment]
    layers_by_name: dict[str, Any] = dict(zip(layer_names, ordered_layers, strict=False))

    merge_layers_with_order(
        layer_names,
        layers_by_name,
        components,
        layer_transform=_to_dict,
    )

    layout["layers"] = [layers_by_name[name] for name in layer_names]


__all__ = ["LayoutFeatureComponents", "apply_feature"]
