from __future__ import annotations

from copy import deepcopy

import pytest

from glove80.tui.state.store import LayoutStore


def _slot(value: str) -> dict[str, object]:
    return {"value": value, "params": []}


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    layers = [[_slot("&kp A") for _ in range(80)], [_slot("&kp B") for _ in range(80)]]
    layers[0][0] = _slot("&macro_one")
    return {
        "layer_names": ["Base", "Lower"],
        "layers": layers,
        "macros": [
            {
                "name": "&macro_one",
                "description": "First macro",
                "bindings": [
                    {"value": "&macro_press", "params": []},
                    {"value": "&kp", "params": [{"value": "A", "params": []}]},
                ],
                "params": [],
                "waitMs": 10,
                "tapMs": 5,
            },
            {
                "name": "&macro_two",
                "description": "Chained macro",
                "bindings": [
                    {"value": "&macro_one", "params": []},
                    {"value": "&kp", "params": [{"value": "B", "params": []}]},
                ],
                "params": [],
            },
        ],
        "holdTaps": [
            {
                "name": "&hold_test",
                "bindings": ["&macro_one", "&kp"],
                "flavor": "balanced",
            }
        ],
        "combos": [
            {
                "name": "combo_1",
                "binding": {"value": "&macro_one", "params": []},
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
                            {"code": "&macro_one", "params": []},
                        ],
                    }
                ],
                "inputProcessors": [
                    {"code": "&macro_one", "params": []},
                ],
            }
        ],
    }


def test_list_macros_returns_copy(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    listing = store.list_macros()
    assert len(listing) == 2
    listing[0]["name"] = "&mutated"
    assert store.state.macros[0]["name"] == "&macro_one"


def test_add_macro_appends_and_undo(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_macro({"name": "&macro_new", "bindings": [], "params": []})
    assert store.state.macros[-1]["name"] == "&macro_new"

    store.undo()
    assert all(macro["name"] != "&macro_new" for macro in store.state.macros)


def test_add_macro_duplicate_name_raises(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.add_macro({"name": "&macro_one", "bindings": [], "params": []})


def test_update_macro_replaces_payload(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    updated = deepcopy(store.state.macros[0])
    updated["description"] = "Updated"
    updated["waitMs"] = 99
    store.update_macro(name="&macro_one", payload=updated)

    macro = store.state.macros[0]
    assert macro["description"] == "Updated"
    assert macro["waitMs"] == 99


def test_update_macro_rename_rewrites_references(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    updated = deepcopy(store.state.macros[0])
    updated["name"] = "&macro_renamed"
    store.update_macro(name="&macro_one", payload=updated)

    assert store.state.macros[0]["name"] == "&macro_renamed"
    assert store.state.layers[0].slots[0]["value"] == "&macro_renamed"
    assert store.state.combos[0]["binding"]["value"] == "&macro_renamed"
    assert store.state.hold_taps[0]["bindings"][0] == "&macro_renamed"
    assert store.state.macros[1]["bindings"][0]["value"] == "&macro_renamed"


def test_delete_macro_blocks_when_referenced(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.delete_macro(name="&macro_one")


def test_delete_macro_force_clears_references(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.delete_macro(name="&macro_one", force=True)

    assert all(slot["value"] != "&macro_one" for slot in store.state.layers[0].slots)
    assert store.state.combos[0]["binding"]["value"] == ""
    assert store.state.hold_taps[0]["bindings"][0] == ""


def test_find_macro_references_reports_locations(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    refs = store.find_macro_references("&macro_one")
    assert refs["keys"][0]["layer_name"] == "Base"
    assert refs["combos"][0]["name"] == "combo_1"
    assert refs["hold_taps"][0]["name"] == "&hold_test"
    assert refs["macros"][0]["name"] == "&macro_two"


def test_macro_operations_support_redo(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_macro({"name": "&macro_three", "bindings": [], "params": []})
    store.update_macro(
        name="&macro_three",
        payload={"name": "&macro_three", "description": "tmp", "bindings": [], "params": []},
    )
    store.undo()
    store.undo()
    assert all(macro["name"] != "&macro_three" for macro in store.state.macros)

    store.redo()
    store.redo()
    assert any(macro["name"] == "&macro_three" for macro in store.state.macros)
