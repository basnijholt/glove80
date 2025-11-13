from __future__ import annotations

import copy

import pytest

from glove80.layouts.builder import LayoutBuilder
from glove80.layouts.common import BASE_COMMON_FIELDS
from glove80.layouts.components import LayoutFeatureComponents

from glove80.tui.services import BuilderBridge
from glove80.tui.state import LayoutStore


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    slots_a = [{"value": "&kp", "params": [{"value": "A", "params": []}]} for _ in range(80)]
    slots_b = [{"value": "&kp", "params": [{"value": "B", "params": []}]} for _ in range(80)]
    return {
        "layer_names": ["Base", "Lower"],
        "layers": [slots_a, slots_b],
        "macros": [],
        "holdTaps": [],
        "combos": [],
        "inputListeners": [],
    }


def test_preview_reports_layers_without_mutation(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    bridge = BuilderBridge(store=store, variant="windows")

    diff = bridge.preview_home_row_mods(target_layer="Base")

    assert diff.layers_added == ("HRM_WinLinx",)
    assert store.layer_names == tuple(sample_payload["layer_names"])  # no mutation


def test_apply_matches_layoutbuilder_output(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    bridge = BuilderBridge(store=store, variant="windows")

    bridge.apply_home_row_mods(target_layer="Base")
    updated = store.export_payload()

    expected = _build_with_layoutbuilder(sample_payload, target_layer="Base")

    assert updated["layer_names"] == expected["layer_names"]
    assert updated["layers"] == expected["layers"]


def test_apply_is_undoable(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    bridge = BuilderBridge(store=store, variant="windows")

    bridge.apply_home_row_mods(target_layer="Base")
    store.undo()

    assert store.export_payload() == {
        "layer_names": sample_payload["layer_names"],
        "layers": copy.deepcopy(sample_payload["layers"]),
        "macros": [],
        "holdTaps": [],
        "combos": [],
        "inputListeners": [],
    }


def _build_with_layoutbuilder(payload: dict[str, object], target_layer: str) -> dict[str, object]:
    builder = LayoutBuilder(
        metadata_key="tailorkey",
        variant="windows",
        common_fields=dict(BASE_COMMON_FIELDS),
        layer_names=payload["layer_names"],
        home_row_provider=lambda _variant: LayoutFeatureComponents(layers=_hrm_layer_map()),
    )
    layer_map = dict(zip(payload["layer_names"], payload["layers"], strict=False))
    builder.add_layers(layer_map)
    builder.add_combos(payload.get("combos", []))
    builder.add_input_listeners(payload.get("inputListeners", []))
    builder.add_home_row_mods(target_layer=target_layer)
    return builder.build()


def _hrm_layer_map() -> dict[str, object]:  # pragma: no cover - helper for builder
    # Lazily import inside helper to keep test import surface minimal.
    from glove80.families.tailorkey.layers.hrm import build_hrm_layers

    return build_hrm_layers("windows")


def test_preview_cursor_adds_layer_without_mutation(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    bridge = BuilderBridge(store=store, variant="windows")

    diff = bridge.preview_feature("cursor", target_layer="Base")

    assert "Cursor" not in store.layer_names
    assert diff.layers_added == ("Cursor",)


def test_apply_cursor_is_undoable(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    bridge = BuilderBridge(store=store, variant="windows")

    bridge.apply_feature("cursor", target_layer="Base")
    assert "Cursor" in store.layer_names

    store.undo()
    assert "Cursor" not in store.layer_names


def test_apply_mouse_layers_adds_stack(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    bridge = BuilderBridge(store=store, variant="windows")

    diff = bridge.apply_feature("mouse", target_layer="Base")

    expected_layers = {"Mouse", "MouseSlow", "MouseFast", "MouseWarp"}
    assert expected_layers.issubset(set(store.layer_names))
    assert diff.listeners_added >= 2


def test_preview_cursor_conflict_raises(sample_payload: dict[str, object]) -> None:
    sample_payload["layer_names"].append("Cursor")
    sample_payload["layers"].append(sample_payload["layers"][0])
    store = LayoutStore.from_payload(sample_payload)
    bridge = BuilderBridge(store=store, variant="windows")

    with pytest.raises(ValueError):
        bridge.preview_feature("cursor", target_layer="Base")
