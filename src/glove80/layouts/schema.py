"""Pydantic models for layout sections (incremental migration).

This module will gradually host strongly-typed models that mirror the JSON
shapes emitted by the builder. We introduce them model-by-model to keep
changes reviewable and tests green between commits.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from glove80.base import LayerRef


class Macro(BaseModel):
    """Macro section entry.

    Matches the structure produced by MacroSpec.to_dict() today.
    Unknown keys are forbidden; field aliases match the JSON casing.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: Optional[str] = None
    bindings: List[Dict[str, Any]]
    params: List[str] = Field(default_factory=list)
    waitMs: Optional[int] = None
    tapMs: Optional[int] = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not v or not v.startswith("&"):
            raise ValueError("macro name must start with '&'")
        return v

    @field_validator("bindings")
    @classmethod
    def _validate_bindings(cls, v: List[Any]) -> List[Any]:
        if not v:
            raise ValueError("bindings must be non-empty")
        return v


class HoldTap(BaseModel):
    """Hold-tap behavior entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: Optional[str] = None
    bindings: List[str]
    tappingTermMs: Optional[int] = None
    flavor: Optional[Literal["balanced", "tap-preferred", "hold-preferred"]] = None
    quickTapMs: Optional[int] = None
    requirePriorIdleMs: Optional[int] = None
    holdTriggerOnRelease: Optional[bool] = None
    holdTriggerKeyPositions: Optional[List[int]] = None

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "HoldTap":
        inst = super().model_validate(obj, *args, **kwargs)
        d = inst.model_dump()
        for k in ("tappingTermMs", "quickTapMs", "requirePriorIdleMs"):
            if d.get(k) is not None and d[k] < 0:
                raise ValueError(f"{k} must be non-negative")
        if d.get("holdTriggerKeyPositions"):
            for pos in d["holdTriggerKeyPositions"]:
                if not (0 <= pos <= 79):
                    raise ValueError("holdTriggerKeyPositions must be within 0..79")
        return inst


__all__ = ["Macro", "HoldTap"]


class Combo(BaseModel):
    """Combo section entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: Optional[str] = None
    binding: Dict[str, Any]
    keyPositions: List[int]
    layers: List[Union[int, "LayerRef"]]
    timeoutMs: Optional[int] = None

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "Combo":
        inst = super().model_validate(obj, *args, **kwargs)
        for pos in inst.keyPositions:
            if not (0 <= pos <= 79):
                raise ValueError("keyPositions must be within 0..79")
        if not inst.keyPositions:
            raise ValueError("keyPositions cannot be empty")
        return inst


__all__.append("Combo")


class InputProcessor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    params: List[Any] = Field(default_factory=list)

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "InputProcessor":
        inst = super().model_validate(obj, *args, **kwargs)
        if not inst.code:
            raise ValueError("processor code must be non-empty")
        return inst


class ListenerNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    layers: List[Union[int, LayerRef]]
    description: Optional[str] = None
    inputProcessors: List[InputProcessor] = Field(default_factory=list)

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "ListenerNode":
        inst = super().model_validate(obj, *args, **kwargs)
        if not inst.layers:
            raise ValueError("listener node layers cannot be empty")
        return inst


class InputListener(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    inputProcessors: List[InputProcessor] = Field(default_factory=list)
    nodes: List[ListenerNode]


__all__ += ["InputProcessor", "ListenerNode", "InputListener"]


class CommonFields(BaseModel):
    """Top-level, shared fields merged into every layout payload.

    We validate known keys while allowing extras so families can inject
    additional metadata (e.g., `creator`) without breaking validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    keyboard: str
    firmware_api_version: str
    locale: str
    unlisted: bool
    custom_defined_behaviors: str
    custom_devicetree: str
    config_parameters: List[Dict[str, Any]]
    layout_parameters: Dict[str, Any]
    creator: Optional[str] = None


__all__.append("CommonFields")


class LayoutPayload(BaseModel):
    """Top-level layout payload shape (validated, still serialized as dict).

    We intentionally accept plain dicts for sections (macros, holdTaps, etc.)
    to keep the emission path lightweight while still validating presence and
    basic structure. Unknown extra keys are allowed for forward compatibility.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Common fields
    keyboard: str
    firmware_api_version: str
    locale: str
    unlisted: bool
    custom_defined_behaviors: str
    custom_devicetree: str
    config_parameters: List[Dict[str, Any]]
    layout_parameters: Dict[str, Any]
    creator: Optional[str] = None

    # Sections
    layer_names: List[str]
    macros: List[Dict[str, Any]]
    holdTaps: List[Dict[str, Any]]
    combos: List[Dict[str, Any]]
    inputListeners: List[Dict[str, Any]]
    layers: List[List[Dict[str, Any]]]

    # Attached metadata (optional)
    title: Optional[str] = None
    uuid: Optional[str] = None
    parent_uuid: Optional[str] = None
    date: Optional[Any] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "LayoutPayload":
        inst = super().model_validate(obj, *args, **kwargs)
        # Length checks
        if len(inst.layer_names) != len(inst.layers):
            raise ValueError("layers length must match layer_names length")
        # Verify each layer has 80 entries
        for layer in inst.layers:
            if len(layer) != 80:
                raise ValueError("each layer must have exactly 80 key entries")
        return inst


__all__.append("LayoutPayload")
