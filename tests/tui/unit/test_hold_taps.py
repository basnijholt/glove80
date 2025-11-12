from __future__ import annotations

import copy

import pytest

from glove80.tui.state.store import LayoutStore


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    return {
        "layer_names": ["Base", "Raise"],
        "layers": [
            [{"value": "&kp A", "params": []} for _ in range(80)],
            [{"value": "&kp B", "params": []} for _ in range(80)],
        ],
        "macros": [],
        "holdTaps": [
            {
                "name": "&hold_primary",
                "bindings": ["&kp", "A"],
                "tappingTermMs": 200,
            }
        ],
        "combos": [],
        "inputListeners": [],
    }


def test_list_hold_taps_returns_copy(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    entries = store.list_hold_taps()
    assert len(entries) == 1
    entries[0]["name"] = "mutated"
    assert store.state.hold_taps[0]["name"] == "&hold_primary"


def test_add_hold_tap(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_hold_tap(
        {
            "name": "&hold_secondary",
            "bindings": ["&kp", "B"],
            "tappingTermMs": 150,
            "holdTriggerKeyPositions": [0, 1],
        }
    )
    assert any(ht["name"] == "&hold_secondary" for ht in store.state.hold_taps)

    store.undo()
    assert all(ht["name"] != "&hold_secondary" for ht in store.state.hold_taps)


def test_add_hold_tap_duplicate_name_raises(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.add_hold_tap(
            {
                "name": "&hold_primary",
                "bindings": ["&kp"],
            }
        )


def test_update_hold_tap_rename_rewrites_references(sample_payload: dict[str, object]) -> None:
    payload = copy.deepcopy(sample_payload)
    payload["layers"][0][0] = {"value": "&hold_primary", "params": []}
    store = LayoutStore.from_payload(payload)

    updated = {
        "name": "&hold_renamed",
        "bindings": ["&kp", "C"],
        "tappingTermMs": 180,
    }
    store.update_hold_tap(name="&hold_primary", payload=updated)

    assert store.state.hold_taps[0]["name"] == "&hold_renamed"
    assert store.state.layers[0].slots[0]["value"] == "&hold_renamed"


def test_delete_hold_tap_blocks_when_referenced(sample_payload: dict[str, object]) -> None:
    payload = copy.deepcopy(sample_payload)
    payload["layers"][0][1] = {"value": "&hold_primary", "params": []}
    store = LayoutStore.from_payload(payload)

    with pytest.raises(ValueError):
        store.delete_hold_tap(name="&hold_primary")


def test_delete_hold_tap_after_unbinding(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.delete_hold_tap(name="&hold_primary", force=True)
    assert not store.state.hold_taps
    store.undo()
    assert store.state.hold_taps


def test_find_hold_tap_references(sample_payload: dict[str, object]) -> None:
    payload = copy.deepcopy(sample_payload)
    payload["layers"][0][2] = {"value": "&hold_primary", "params": []}
    payload["macros"].append(
        {
            "name": "&macro_uses_hold",
            "bindings": ["&hold_primary"],
            "params": [],
        }
    )
    store = LayoutStore.from_payload(payload)

    refs = store.find_hold_tap_references("&hold_primary")
    assert refs["keys"]
    assert refs["macros"]
