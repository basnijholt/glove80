"""Legacy spec helpers (materialization only).

This module previously defined lightweight dataclasses (e.g., MacroSpec,
HoldTapSpec) that were converted into Pydantic models at build time. The
codebase now constructs and passes the Pydantic models directly. We keep
only the materialization helpers for compatibility with any remaining
callers that pass a heterogeneous mix of items (models or plain dicts).
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence


def _materialize_item(item: Any) -> Any:
    if hasattr(item, "to_dict"):
        return item.to_dict()
    return deepcopy(item)


def materialize_sequence(items: Iterable[Any]) -> list[Any]:
    """Convert specs to pydantic models when possible (fallback to raw)."""
    result: list[Any] = []
    for item in items:
        if hasattr(item, "to_model"):
            result.append(item.to_model())
        elif hasattr(item, "to_dict"):
            result.append(_materialize_item(item))
        else:
            result.append(item)
    return result


def materialize_named_sequence(
    definitions: Mapping[str, Any],
    order: Sequence[str],
    overrides: Mapping[str, Any] | None = None,
) -> list[Any]:
    """Materialize a named sequence with optional overrides."""
    resolved: list[Any] = []
    overrides = overrides or {}
    for name in order:
        value = overrides.get(name, definitions.get(name))
        if value is None:
            msg = f"Unknown definition '{name}'"
            raise KeyError(msg)
        if hasattr(value, "to_model"):
            resolved.append(value.to_model())
        else:
            resolved.append(_materialize_item(value))
    return resolved
