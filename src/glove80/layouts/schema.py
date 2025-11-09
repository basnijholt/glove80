"""Pydantic models for layout sections (incremental migration).

This module will gradually host strongly-typed models that mirror the JSON
shapes emitted by the builder. We introduce them model-by-model to keep
changes reviewable and tests green between commits.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# Avoid circular import at runtime; used for type checking only
try:  # pragma: no cover
    from glove80.base import LayerRef  # type: ignore
except Exception:  # pragma: no cover
    LayerRef = object  # type: ignore


class Macro(BaseModel):
    """Macro section entry.

    Matches the structure produced by MacroSpec.to_dict() today.
    Unknown keys are forbidden; field aliases match the JSON casing.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: Optional[str] = None
    bindings: List[Dict]
    params: List[str] = Field(default_factory=list)
    waitMs: Optional[int] = None
    tapMs: Optional[int] = None


class HoldTap(BaseModel):
    """Hold-tap behavior entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: Optional[str] = None
    bindings: List[str]
    tappingTermMs: Optional[int] = None
    flavor: Optional[str] = None
    quickTapMs: Optional[int] = None
    requirePriorIdleMs: Optional[int] = None
    holdTriggerOnRelease: Optional[bool] = None
    holdTriggerKeyPositions: Optional[List[int]] = None


__all__ = ["Macro", "HoldTap"]


class Combo(BaseModel):
    """Combo section entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: Optional[str] = None
    binding: Dict
    keyPositions: List[int]
    layers: List[Union[int, "LayerRef"]]
    timeoutMs: Optional[int] = None


__all__.append("Combo")


class InputProcessor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    params: List[Union[str, int, float, bool, dict, list]] = Field(default_factory=list)


class ListenerNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    layers: List[Union[int, LayerRef]]
    description: Optional[str] = None
    inputProcessors: List[InputProcessor] = Field(default_factory=list)


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

    model_config = ConfigDict(extra="allow", frozen=True)

    keyboard: str
    firmware_api_version: str
    locale: str
    unlisted: bool
    custom_defined_behaviors: str
    custom_devicetree: str
    config_parameters: List[Dict]
    layout_parameters: Dict


__all__.append("CommonFields")


class LayoutPayload(BaseModel):
    """Top-level layout payload shape (validated, still serialized as dict).

    We intentionally accept plain dicts for sections (macros, holdTaps, etc.)
    to keep the emission path lightweight while still validating presence and
    basic structure. Unknown extra keys are allowed for forward compatibility.
    """

    model_config = ConfigDict(extra="allow", frozen=True)

    # Common fields
    keyboard: str
    firmware_api_version: str
    locale: str
    unlisted: bool
    custom_defined_behaviors: str
    custom_devicetree: str
    config_parameters: List[Dict]
    layout_parameters: Dict

    # Sections
    layer_names: List[str]
    macros: List[Dict]
    holdTaps: List[Dict]
    combos: List[Dict]
    inputListeners: List[Dict]
    layers: List[List[Dict]]

    # Attached metadata (optional)
    title: Optional[str] = None
    uuid: Optional[str] = None
    parent_uuid: Optional[str] = None
    date: Optional[Any] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


__all__.append("LayoutPayload")
