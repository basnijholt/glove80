"""Reusable spec dataclasses for macros, hold-taps, combos, and listeners."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from glove80.base import KeySpec, LayerRef
from glove80.layouts.schema import (
    Combo as ComboModel,
    InputProcessor as InputProcessorModel,
    ListenerNode as ListenerNodeModel,
    Macro as MacroModel,
    HoldTap as HoldTapModel,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence


def _serialize_simple(value: Any) -> Any:
    """Convert supported parameter types into JSON-friendly structures."""
    if isinstance(value, KeySpec):
        return value.to_dict()
    if isinstance(value, LayerRef):
        return value
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _serialize_simple(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_simple(item) for item in value]
    msg = f"Unsupported parameter type: {type(value)!r}"
    raise TypeError(msg)  # pragma: no cover


@dataclass(frozen=True)
class MacroSpec:
    """Structured representation of a macro definition."""

    name: str
    description: str
    bindings: Sequence[KeySpec]
    params: Sequence[str] = ()
    wait_ms: int | None = None
    tap_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        model = MacroModel(
            name=self.name,
            description=self.description,
            bindings=[binding.to_dict() for binding in self.bindings],
            params=list(self.params),
            waitMs=self.wait_ms,
            tapMs=self.tap_ms,
        )
        data = model.model_dump(by_alias=True, exclude_none=True)
        # Preserve KeySpec dicts (may contain LayerRef inside nested params)
        data["bindings"] = [binding.to_dict() for binding in self.bindings]
        return data


@dataclass(frozen=True)
class HoldTapSpec:
    """Declarative hold-tap definition."""

    name: str
    description: str
    bindings: Sequence[str]
    tapping_term_ms: int | None = None
    flavor: str | None = None
    quick_tap_ms: int | None = None
    require_prior_idle_ms: int | None = None
    hold_trigger_on_release: bool | None = None
    hold_trigger_key_positions: Sequence[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        model = HoldTapModel(
            name=self.name,
            description=self.description,
            bindings=list(self.bindings),
            tappingTermMs=self.tapping_term_ms,
            flavor=self.flavor,
            quickTapMs=self.quick_tap_ms,
            requirePriorIdleMs=self.require_prior_idle_ms,
            holdTriggerOnRelease=self.hold_trigger_on_release,
            holdTriggerKeyPositions=(
                list(self.hold_trigger_key_positions) if self.hold_trigger_key_positions else None
            ),
        )
        return model.model_dump(by_alias=True, exclude_none=True)


@dataclass(frozen=True)
class ComboSpec:
    """Combo definition for TailorKey/QuantumTouch layouts."""

    name: str
    description: str
    binding: KeySpec
    key_positions: Sequence[int]
    layers: Sequence[int | LayerRef]
    timeout_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        model = ComboModel(
            name=self.name,
            description=self.description,
            binding=self.binding.to_dict(),
            keyPositions=list(self.key_positions),
            layers=list(self.layers),
            timeoutMs=self.timeout_ms,
        )
        data = model.model_dump(by_alias=True, exclude_none=True)
        # Preserve original binding (may contain LayerRef inside nested KeySpecs)
        data["binding"] = self.binding.to_dict()
        # Preserve LayerRef objects for later resolution to indices
        data["layers"] = list(self.layers)
        return data


@dataclass(frozen=True)
class InputProcessorSpec:
    """Helper for mmv/msc processor blocks."""

    code: str
    params: Sequence[Any] = ()

    def to_dict(self) -> dict[str, Any]:
        model = InputProcessorModel(code=self.code, params=[_serialize_simple(param) for param in self.params])
        return model.model_dump(by_alias=True, exclude_none=True)


@dataclass(frozen=True)
class InputListenerNodeSpec:
    """Single listener node (layer binding plus processors)."""

    code: str
    layers: Sequence[int | LayerRef]
    description: str | None = None
    input_processors: Sequence[InputProcessorSpec] = ()

    def to_dict(self) -> dict[str, Any]:
        model = ListenerNodeModel(
            code=self.code,
            layers=list(self.layers),
            description=self.description,
            inputProcessors=[InputProcessorModel(**proc.to_dict()) for proc in self.input_processors],
        )
        data = model.model_dump(by_alias=True, exclude_none=True)
        data["layers"] = list(self.layers)
        return data


@dataclass(frozen=True)
class InputListenerSpec:
    """Top-level listener consisting of multiple nodes."""

    code: str
    nodes: Sequence[InputListenerNodeSpec]
    input_processors: Sequence[InputProcessorSpec] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "inputProcessors": [proc.to_dict() for proc in self.input_processors],
            "nodes": [node.to_dict() for node in self.nodes],
        }


def _materialize_item(item: Any) -> Any:
    if hasattr(item, "to_dict"):
        return item.to_dict()
    return deepcopy(item)


def materialize_sequence(items: Iterable[Any]) -> list[Any]:
    """Convert spec objects (with to_dict) into dictionaries."""
    return [_materialize_item(item) for item in items]


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
        resolved.append(_materialize_item(value))
    return resolved
