from __future__ import annotations

from copy import deepcopy

import pytest

from glove80.tui.state.store import LayoutStore


def _slot(value: str) -> dict[str, object]:
    return {"value": value, "params": []}


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    layers = [[_slot("&kp A") for _ in range(80)], [_slot("&kp B") for _ in range(80)]]
    layers[0][0] = _slot("&hold_one")
    return {
        "layer_names": ["Base", "Lower"],
        "layers": layers,
        "macros": [
            {
                "name": "&macro_test",
                "description": "Test macro",
                "bindings": [
                    {"value": "&hold_one", "params": []},
                ],
                "params": [],
            }
        ],
        "holdTaps": [
            {
                "name": "&hold_one",
                "bindings": ["&kp", "A"],
                "flavor": "balanced",
                "tappingTermMs": 175,
            },
            {
                "name": "&hold_two",
                "bindings": ["&hold_one", "&kp"],
                "flavor": "tap-preferred",
            },
        ],
        "combos": [
            {
                "name": "combo_1",
                "binding": {"value": "&hold_one", "params": []},
                "keyPositions": [0, 1],
                "layers": [0],
            }
        ],
        "inputListeners": [
            {
                "code": "listener_0",
                "nodes": [
                    {
                        "code": "node",
                        "inputProcessors": [
                            {"code": "&hold_one", "params": []},
                        ],
                    }
                ],
                "inputProcessors": [
                    {"code": "&hold_one", "params": []},
                ],
            }
        ],
    }


def test_list_hold_taps_returns_copy(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    listing = store.list_hold_taps()
    assert len(listing) == 2
    listing[0]["name"] = "&mutated"
    assert store.state.hold_taps[0]["name"] == "&hold_one"


def test_add_hold_tap_appends_and_undo(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_hold_tap({"name": "&hold_new", "bindings": ["&kp", "B"], "flavor": "balanced"})
    assert store.state.hold_taps[-1]["name"] == "&hold_new"

    store.undo()
    assert all(hold["name"] != "&hold_new" for hold in store.state.hold_taps)


def test_add_hold_tap_duplicate_name_raises(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.add_hold_tap({"name": "&hold_one", "bindings": ["&kp", "C"], "flavor": "balanced"})


def test_update_hold_tap_replaces_payload(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    updated = deepcopy(store.state.hold_taps[0])
    updated["flavor"] = "tap-preferred"
    updated["tappingTermMs"] = 200
    store.update_hold_tap(name="&hold_one", payload=updated)

    hold_tap = store.state.hold_taps[0]
    assert hold_tap["flavor"] == "tap-preferred"
    assert hold_tap["tappingTermMs"] == 200


def test_update_hold_tap_rename_rewrites_references(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    updated = deepcopy(store.state.hold_taps[0])
    updated["name"] = "&hold_renamed"
    store.update_hold_tap(name="&hold_one", payload=updated)

    assert store.state.hold_taps[0]["name"] == "&hold_renamed"
    assert store.state.layers[0].slots[0]["value"] == "&hold_renamed"
    assert store.state.combos[0]["binding"]["value"] == "&hold_renamed"
    assert store.state.hold_taps[1]["bindings"][0] == "&hold_renamed"
    assert store.state.macros[0]["bindings"][0]["value"] == "&hold_renamed"


def test_delete_hold_tap_blocks_when_referenced(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.delete_hold_tap(name="&hold_one")


def test_delete_hold_tap_force_clears_references(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.delete_hold_tap(name="&hold_one", force=True)

    assert all(slot["value"] != "&hold_one" for slot in store.state.layers[0].slots)
    assert store.state.combos[0]["binding"]["value"] == ""
    assert store.state.hold_taps[0]["bindings"][0] == ""


def test_find_hold_tap_references_reports_locations(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    refs = store.find_hold_tap_references("&hold_one")
    assert refs["keys"][0]["layer_name"] == "Base"
    assert refs["combos"][0]["name"] == "combo_1"
    assert refs["hold_taps"][0]["name"] == "&hold_two"
    assert refs["macros"][0]["name"] == "&macro_test"


def test_hold_tap_operations_support_redo(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_hold_tap({"name": "&hold_three", "bindings": ["&kp", "Z"], "flavor": "balanced"})
    store.update_hold_tap(
        name="&hold_three",
        payload={
            "name": "&hold_three",
            "flavor": "tap-preferred",
            "bindings": ["&kp", "Z"],
        },
    )
    store.undo()
    store.undo()
    assert all(hold["name"] != "&hold_three" for hold in store.state.hold_taps)

    store.redo()
    store.redo()
    assert any(hold["name"] == "&hold_three" for hold in store.state.hold_taps)
