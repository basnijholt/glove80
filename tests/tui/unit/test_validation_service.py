from __future__ import annotations

import pytest

from glove80.tui.services.validation import ValidationService


@pytest.fixture()
def service() -> ValidationService:
    return ValidationService(layer_names=("Base", "Lower"))


def test_unknown_behavior_fails(service: ValidationService) -> None:
    result = service.validate("&unknown", [])

    assert not result.is_valid
    assert result.first_issue("value") is not None


def test_missing_params_detected(service: ValidationService) -> None:
    result = service.validate("&kp", [])

    assert not result.is_valid
    issue = result.first_issue("params")
    assert issue is not None
    assert "expects" in issue.message


def test_extra_params_detected(service: ValidationService) -> None:
    result = service.validate("&kp", ["A", "B"])

    assert not result.is_valid
    issue = result.first_issue("params")
    assert issue and "only" in issue.message


def test_keycode_param_normalizes_to_canonical(service: ValidationService) -> None:
    result = service.validate("&kp", ["a"])

    assert result.is_valid
    assert result.params == ({"value": "A", "params": []},)


def test_keycode_param_rejects_unknown_names(service: ValidationService) -> None:
    result = service.validate("&kp", ["NOT_A_KEY"])

    assert not result.is_valid
    issue = result.first_issue("params")
    assert issue and "Unknown keycode" in issue.message


def test_layer_param_requires_known_layer(service: ValidationService) -> None:
    result = service.validate("&mo", ["DoesNotExist"])

    assert not result.is_valid
    issue = result.first_issue("params")
    assert issue and "Unknown layer" in issue.message


def test_layer_param_accepts_dict_payload(service: ValidationService) -> None:
    result = service.validate("&mo", [{"name": "Lower"}])

    assert result.is_valid
    assert result.params == ({"name": "Lower"},)


def test_integer_param_enforces_bounds(service: ValidationService) -> None:
    # macro tap time takes a single integer parameter with a minimum of 0
    result = service.validate("&macro_tap_time", ["-10"])

    assert not result.is_valid
    assert result.first_issue("params") is not None

    ok = service.validate("&macro_tap_time", ["250"])
    assert ok.is_valid
    assert ok.params == (250,)


def test_suggestions_are_filtered(service: ValidationService) -> None:
    behaviors = service.suggest_behaviors("&k")
    assert "&kp" in behaviors

    keycodes = service.suggest_keycodes("es")
    assert any(code.lower().startswith("es") for code in keycodes)

    layers = service.suggest_layers("ba")
    assert layers == ("Base",)
