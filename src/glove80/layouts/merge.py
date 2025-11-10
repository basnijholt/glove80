"""Shared merge helpers for layout sections and feature components."""

from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, MutableMapping, MutableSequence, Sequence, cast

from glove80.layouts.components import LayoutFeatureComponents


Normalizer = Callable[[Any], Any] | None


def unique_sequence(values: Iterable[str]) -> list[str]:
    """Return the input sequence without duplicates while preserving order."""

    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def macro_name(macro: Any) -> str:
    """Best-effort accessor for a macro object's ``name`` attribute."""

    if hasattr(macro, "name") and not isinstance(macro, dict):
        name = getattr(macro, "name")
    else:
        try:
            from collections.abc import Mapping as _Mapping

            if isinstance(macro, _Mapping):
                name = macro["name"]
            else:
                name = cast("Any", macro)["name"]
        except Exception as exc:  # pragma: no cover - defensive guard
            msg = "Macro definitions must include a 'name'"
            raise KeyError(msg) from exc
    if not isinstance(name, str):  # pragma: no cover - sanity guard
        msg = "Macro name must be a string"
        raise TypeError(msg)
    return name


def merge_sections_except_layers(
    layout_like: MutableMapping[str, MutableSequence[Any]],
    components: LayoutFeatureComponents,
    *,
    normalize: Normalizer = None,
    macro_normalize: Normalizer = None,
) -> None:
    """Merge macros/hold-taps/combos/listeners from ``components`` into ``layout_like``."""

    macros_section = _get_section(layout_like, "macros")
    merge_macros_in_place(macros_section, components.macros, components.macros_by_name, transform=macro_normalize)

    for field_name, values in (
        ("holdTaps", components.hold_taps),
        ("combos", components.combos),
        ("inputListeners", components.input_listeners),
    ):
        if not values:
            continue
        section = _get_section(layout_like, field_name)
        if normalize is None:
            section.extend(values)
        else:
            section.extend(normalize(value) for value in values)


def merge_layers_with_order(
    layer_names: MutableSequence[str],
    layers_by_name: MutableMapping[str, Any],
    components: LayoutFeatureComponents,
    *,
    insert_after: str | None = None,
    insert_before: str | None = None,
    explicit_order: Sequence[str] | None = None,
    layer_transform: Normalizer = None,
) -> tuple[MutableSequence[str], MutableMapping[str, Any]]:
    """Merge layers while keeping the target order list consistent."""

    if not components.layers:
        return layer_names, layers_by_name

    desired_order = list(explicit_order or components.layers.keys())
    missing = [name for name in desired_order if name not in components.layers]
    if missing:
        msg = f"Layer '{missing[0]}' missing from provided component mapping"
        raise KeyError(msg)

    for name in desired_order:
        layer_data = components.layers[name]
        if layer_transform is not None:
            layer_data = layer_transform(layer_data)
        layers_by_name[name] = layer_data

    insert_layer_names(layer_names, desired_order, after=insert_after, before=insert_before)
    return layer_names, layers_by_name


def insert_layer_names(
    current_order: MutableSequence[str],
    names: Sequence[str],
    *,
    after: str | None = None,
    before: str | None = None,
) -> None:
    """Insert *names* into *current_order* honoring before/after anchors."""

    sanitized = unique_sequence(names)
    if not sanitized:
        return
    if after is not None and before is not None:
        msg = "Specify only one of 'after' or 'before'"
        raise ValueError(msg)

    if after is None and before is None:
        for name in sanitized:
            if name not in current_order:
                current_order.append(name)
        return

    filtered = [name for name in current_order if name not in sanitized]

    if before is not None:
        try:
            anchor_index = filtered.index(before)
        except ValueError as exc:
            msg = f"Layer '{before}' is not present in the order"
            raise ValueError(msg) from exc
        updated = (
            filtered[:anchor_index] + [name for name in sanitized if name not in filtered] + filtered[anchor_index:]
        )
        current_order[:] = updated
        return

    if after is not None:
        try:
            anchor_index = filtered.index(after)
        except ValueError as exc:
            msg = f"Layer '{after}' is not present in the order"
            raise ValueError(msg) from exc
        updated = (
            filtered[: anchor_index + 1]
            + [name for name in sanitized if name not in filtered]
            + filtered[anchor_index + 1 :]
        )
        current_order[:] = updated


def merge_macros_in_place(
    existing: MutableSequence[Any],
    appended: Sequence[Any],
    overrides: Mapping[str, Any] | None,
    *,
    transform: Normalizer,
) -> None:
    """Deduplicate macros while preserving existing order semantics."""

    catalog: dict[str, Any] = {}
    order: list[str] = []

    def _index(macro_obj: Any, *, explicit_name: str | None = None) -> None:
        macro_data = transform(macro_obj) if transform is not None else macro_obj
        name = explicit_name or macro_name(macro_data)
        macro_data = _ensure_macro_name(macro_data, name)
        if name not in order:
            order.append(name)
        catalog[name] = macro_data

    for macro in list(existing):
        _index(macro)
    for macro in appended or ():
        _index(macro)
    if overrides:
        for name, macro in overrides.items():
            if not isinstance(name, str):
                msg = "Override macro keys must be strings"
                raise TypeError(msg)
            _index(macro, explicit_name=name)

    existing[:] = [catalog[name] for name in order]


def _ensure_macro_name(macro: Any, name: str) -> Any:
    if hasattr(macro, "name") and not isinstance(macro, dict):
        current = getattr(macro, "name")
        if current == name:
            return macro
        if hasattr(macro, "model_copy"):
            return macro.model_copy(update={"name": name})
    if isinstance(macro, dict):
        if macro.get("name") == name:
            return macro
        updated = dict(macro)
        updated.setdefault("name", name)
        return updated
    if hasattr(macro, "model_copy"):
        return macro.model_copy(update={"name": name})
    if hasattr(macro, "copy"):
        try:
            cloned = macro.copy()
        except Exception:  # pragma: no cover - fallback path
            cloned = None
        if isinstance(cloned, dict):
            cloned.setdefault("name", name)
            return cloned
    raise KeyError("Feature macros must include a 'name'")


def _get_section(
    layout_like: MutableMapping[str, MutableSequence[Any]],
    key: str,
) -> MutableSequence[Any]:
    try:
        return layout_like[key]
    except KeyError as exc:  # pragma: no cover - consumer contracts ensure sections exist
        msg = f"Layout is missing '{key}' section"
        raise KeyError(msg) from exc


__all__ = [
    "insert_layer_names",
    "macro_name",
    "merge_layers_with_order",
    "merge_macros_in_place",
    "merge_sections_except_layers",
    "unique_sequence",
]
