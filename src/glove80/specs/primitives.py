"""Reusable spec dataclasses for macros, hold-taps, combos, and listeners."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from glove80.base import KeySpec, LayerRef
from glove80.layouts.schema import (
    Combo as ComboModel,
    InputProcessor as InputProcessorModel,
    ListenerNode as ListenerNodeModel,
    Macro as MacroModel,
    HoldTap as HoldTapModel,
    InputListener as InputListenerModel,
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

    def to_model(self) -> MacroModel:
        return MacroModel(
            name=self.name,
            description=self.description,
            bindings=[binding.to_dict() for binding in self.bindings],
            params=list(self.params),
            waitMs=self.wait_ms,
            tapMs=self.tap_ms,
        )

    def to_dict(self) -> dict[str, Any]:
        model = self.to_model()
        data = model.model_dump(by_alias=True, exclude_none=True)
        data["bindings"] = [binding.to_dict() for binding in self.bindings]
        return data


@dataclass(frozen=True)
class HoldTapSpec:
    """Declarative hold-tap definition."""

    name: str
    description: str
    bindings: Sequence[str]
    tapping_term_ms: int | None = None
    flavor: Literal["balanced", "tap-preferred", "hold-preferred"] | None = None
    quick_tap_ms: int | None = None
    require_prior_idle_ms: int | None = None
    hold_trigger_on_release: bool | None = None
    hold_trigger_key_positions: Sequence[int] | None = None

    def to_model(self) -> HoldTapModel:
        return HoldTapModel(
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

    def to_dict(self) -> dict[str, Any]:
        return self.to_model().model_dump(by_alias=True, exclude_none=True)


@dataclass(frozen=True)
class ComboSpec:
    """Combo definition for TailorKey/QuantumTouch layouts."""

    name: str
    description: str
    binding: KeySpec
    key_positions: Sequence[int]
    layers: Sequence[int | LayerRef]
    timeout_ms: int | None = None

    def to_model(self) -> ComboModel:
        return ComboModel(
            name=self.name,
            description=self.description,
            binding=self.binding.to_dict(),
            keyPositions=list(self.key_positions),
            layers=list(self.layers),
            timeoutMs=self.timeout_ms,
        )

    def to_dict(self) -> dict[str, Any]:
        model = self.to_model()
        data = model.model_dump(by_alias=True, exclude_none=True)
        data["binding"] = self.binding.to_dict()
        data["layers"] = list(self.layers)
        return data


@dataclass(frozen=True)
class InputProcessorSpec:
    """Helper for mmv/msc processor blocks."""

    code: str
    params: Sequence[Any] = ()

    def to_model(self) -> InputProcessorModel:
        return InputProcessorModel(code=self.code, params=[_serialize_simple(param) for param in self.params])

    def to_dict(self) -> dict[str, Any]:
        return self.to_model().model_dump(by_alias=True, exclude_none=True)


@dataclass(frozen=True)
class InputListenerNodeSpec:
    """Single listener node (layer binding plus processors)."""

    code: str
    layers: Sequence[int | LayerRef]
    description: str | None = None
    input_processors: Sequence[InputProcessorSpec] = ()

    def to_model(self) -> ListenerNodeModel:
        return ListenerNodeModel(
            code=self.code,
            layers=list(self.layers),
            description=self.description,
            inputProcessors=[InputProcessorModel(**proc.to_dict()) for proc in self.input_processors],
        )

    def to_dict(self) -> dict[str, Any]:
        model = self.to_model()
        data = model.model_dump(by_alias=True, exclude_none=True)
        data["layers"] = list(self.layers)
        return data


@dataclass(frozen=True)
class InputListenerSpec:
    """Top-level listener consisting of multiple nodes."""

    code: str
    nodes: Sequence[InputListenerNodeSpec]
    input_processors: Sequence[InputProcessorSpec] = ()

    def to_model(self) -> InputListenerModel:
        return InputListenerModel(
            code=self.code,
            inputProcessors=[proc.to_model() for proc in self.input_processors],
            nodes=[node.to_model() for node in self.nodes],
        )

    def to_dict(self) -> dict[str, Any]:
        return self.to_model().model_dump(by_alias=True, exclude_none=True)


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
