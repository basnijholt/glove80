"""Schema-aware validation helpers for KeyInspector."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from importlib import resources
from typing import Any, Literal, Sequence

from glove80.keycodes import KeyOption, key_options_by_name

ParamKind = Literal["keycode", "layer", "integer", "string"]


@dataclass(frozen=True)
class BehaviorParamSpec:
    """Parameter metadata derived from `zmk.json`."""

    kind: ParamKind
    label: str | None = None
    minimum: int | None = None
    maximum: int | None = None


@dataclass(frozen=True)
class BehaviorSpec:
    code: str
    params: tuple[BehaviorParamSpec, ...]


@dataclass(frozen=True)
class ValidationIssue:
    field: Literal["value", "params"]
    message: str
    param_index: int | None = None


@dataclass(frozen=True)
class ValidationResult:
    value: str
    params: tuple[Any, ...]
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def first_issue(self, field: Literal["value", "params"]) -> ValidationIssue | None:
        for issue in self.issues:
            if issue.field == field:
                return issue
        return None


@dataclass(frozen=True)
class AutocompleteSuggestions:
    behaviors: tuple[str, ...]
    keycodes: tuple[str, ...]
    layers: tuple[str, ...]


class ValidationService:
    """Validates and normalizes KeySpec payloads for the Key Inspector."""

    def __init__(self, *, layer_names: Sequence[str] | None = None) -> None:
        self._layer_names: tuple[str, ...] = tuple(layer_names or ())
        self._behavior_map = _load_behaviors()
        self._keycodes = key_options_by_name()
        self._behavior_codes = tuple(sorted(self._behavior_map))
        self._keycode_aliases = tuple(sorted(self._keycodes))

    # ------------------------------------------------------------------
    def update_layers(self, layer_names: Sequence[str]) -> None:
        self._layer_names = tuple(layer_names)

    def validate(self, value: str, params: Sequence[Any]) -> ValidationResult:
        normalized_value = value.strip()
        issues: list[ValidationIssue] = []

        if not normalized_value:
            issues.append(ValidationIssue(field="value", message="Behavior is required"))
            return ValidationResult(normalized_value, tuple(), tuple(issues))

        behavior = self._behavior_map.get(normalized_value)
        if behavior is None:
            issues.append(ValidationIssue(field="value", message=f"Unknown behavior '{normalized_value}'"))
            return ValidationResult(normalized_value, tuple(), tuple(issues))

        normalized_params: list[Any] = []
        expected_params = behavior.params

        if len(params) < len(expected_params):
            issues.append(
                ValidationIssue(
                    field="params",
                    message=f"{normalized_value} expects {len(expected_params)} parameter(s)",
                )
            )
        elif len(params) > len(expected_params):
            issues.append(
                ValidationIssue(
                    field="params",
                    message=f"{normalized_value} accepts only {len(expected_params)} parameter(s)",
                )
            )

        for index, spec in enumerate(expected_params):
            try:
                raw_param = params[index]
            except IndexError:
                break
            converted, error = self._convert_param(raw_param, spec, index)
            if error:
                issues.append(error)
            normalized_params.append(converted)

        return ValidationResult(normalized_value, tuple(normalized_params), tuple(issues))

    # ------------------------------------------------------------------
    def suggest_behaviors(self, prefix: str, *, limit: int = 8) -> tuple[str, ...]:
        return _filter_prefix(self._behavior_codes, prefix, limit)

    def suggest_keycodes(self, prefix: str, *, limit: int = 8) -> tuple[str, ...]:
        return _filter_prefix(self._keycode_aliases, prefix, limit)

    def suggest_layers(self, prefix: str, *, limit: int = 8) -> tuple[str, ...]:
        return _filter_prefix(self._layer_names, prefix, limit)

    def suggestions(self, prefix: str) -> AutocompleteSuggestions:
        return AutocompleteSuggestions(
            behaviors=self.suggest_behaviors(prefix),
            keycodes=self.suggest_keycodes(prefix),
            layers=self.suggest_layers(prefix),
        )

    # ------------------------------------------------------------------
    def _convert_param(
        self,
        raw_param: Any,
        spec: BehaviorParamSpec,
        index: int,
    ) -> tuple[Any, ValidationIssue | None]:
        kind = spec.kind
        if kind == "keycode":
            token = _coerce_str(raw_param)
            if not token:
                return raw_param, ValidationIssue(
                    field="params",
                    message="Keycode parameter is required",
                    param_index=index,
                )
            option = self._keycodes.get(token) or self._keycodes.get(token.upper())
            if option is None:
                return raw_param, ValidationIssue(
                    field="params",
                    message=f"Unknown keycode '{token}'",
                    param_index=index,
                )
            canonical: KeyOption = option
            return {"value": canonical.canonical_name, "params": []}, None

        if kind == "layer":
            name = _extract_layer_name(raw_param)
            if name is None:
                return raw_param, ValidationIssue(
                    field="params",
                    message="Layer parameter must be a layer name",
                    param_index=index,
                )
            if name not in self._layer_names:
                return raw_param, ValidationIssue(
                    field="params",
                    message=f"Unknown layer '{name}'",
                    param_index=index,
                )
            return {"name": name}, None

        if kind == "integer":
            value, error = _coerce_int(raw_param, spec, index)
            if error:
                return raw_param, error
            return value, None

        # string-ish fallback
        return _coerce_str(raw_param), None


# ---------------------------------------------------------------------------
def _coerce_str(value: Any) -> str:
    if isinstance(value, dict) and "value" in value:
        inner = value["value"]
        if isinstance(inner, str):
            return inner
    if isinstance(value, str):
        return value
    return str(value)


def _extract_layer_name(value: Any) -> str | None:
    if isinstance(value, dict) and "name" in value:
        name = value["name"]
        if isinstance(name, str):
            return name
    if isinstance(value, str):
        return value
    return None


def _coerce_int(
    value: Any,
    spec: BehaviorParamSpec,
    index: int,
) -> tuple[int | None, ValidationIssue | None]:
    candidate: int | None
    if isinstance(value, int):
        candidate = value
    else:
        text = _coerce_str(value)
        try:
            candidate = int(text)
        except ValueError:
            return None, ValidationIssue(
                field="params",
                message=f"Parameter must be an integer (got '{text}')",
                param_index=index,
            )

    if candidate is None:
        return None, ValidationIssue(
            field="params",
            message="Integer parameter is required",
            param_index=index,
        )

    if spec.minimum is not None and candidate < spec.minimum:
        return None, ValidationIssue(
            field="params",
            message=f"Value must be >= {spec.minimum}",
            param_index=index,
        )
    if spec.maximum is not None and candidate > spec.maximum:
        return None, ValidationIssue(
            field="params",
            message=f"Value must be <= {spec.maximum}",
            param_index=index,
        )
    return candidate, None


def _filter_prefix(values: Sequence[str], prefix: str, limit: int) -> tuple[str, ...]:
    if not prefix:
        return tuple(values[:limit])
    lowered = prefix.lower()
    matches: list[str] = []
    for candidate in values:
        if candidate.lower().startswith(lowered):
            matches.append(candidate)
            if len(matches) >= limit:
                break
    return tuple(matches)


def _normalize_kind(raw: str | None) -> ParamKind:
    if raw in ("code", "keycode"):
        return "keycode"
    if raw == "layer":
        return "layer"
    if raw == "integer":
        return "integer"
    return "string"


def _normalize_param(entry: Any) -> BehaviorParamSpec:
    if isinstance(entry, str):
        return BehaviorParamSpec(kind=_normalize_kind(entry))
    if isinstance(entry, dict):
        kind = _normalize_kind(entry.get("type"))
        return BehaviorParamSpec(
            kind=kind,
            label=entry.get("name"),
            minimum=entry.get("min"),
            maximum=entry.get("max"),
        )
    return BehaviorParamSpec(kind="string")


@lru_cache(maxsize=1)
def _load_behaviors() -> dict[str, BehaviorSpec]:
    data = json.loads(resources.files("glove80.keycodes").joinpath("zmk.json").read_text(encoding="utf-8"))
    mapping: dict[str, BehaviorSpec] = {}
    for entry in data:
        code = entry.get("code")
        if not isinstance(code, str):
            continue
        specs = tuple(_normalize_param(param) for param in entry.get("params", []))
        mapping[code] = BehaviorSpec(code=code, params=specs)
    return mapping
