from __future__ import annotations

import copy

import pytest

from glove80.tui.state.store import LayoutStore


def _slot(value: str) -> dict[str, object]:
    return {"value": value, "params": []}


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    layers = [[_slot("&listener_primary") for _ in range(80)], [_slot("&kp B") for _ in range(80)]]
    return {
        "layer_names": ["Base", "Raise"],
        "layers": layers,
        "macros": [
            {
                "name": "&macro_listener",
                "bindings": [
                    {"value": "&listener_primary", "params": []},
                    {"value": "&kp", "params": []},
                ],
                "params": [],
            }
        ],
        "holdTaps": [
            {
                "name": "&hold_listener",
                "bindings": ["&listener_primary"],
            }
        ],
        "combos": [
            {
                "name": "combo_listener",
                "binding": {"value": "&listener_primary", "params": []},
                "keyPositions": [0, 1],
                "layers": [{"name": "Base"}],
            }
        ],
        "inputListeners": [
            {
                "code": "&listener_primary",
                "nodes": [
                    {
                        "code": "node_primary",
                        "layers": [0],
                        "inputProcessors": [{"code": "&kp", "params": []}],
                    }
                ],
                "inputProcessors": [{"code": "&kp", "params": []}],
            },
            {
                "code": "&listener_secondary",
                "nodes": [
                    {
                        "code": "node_secondary",
                        "layers": [1],
                        "inputProcessors": [{"code": "&listener_primary", "params": []}],
                    }
                ],
                "inputProcessors": [{"code": "&listener_primary", "params": []}],
            },
        ],
    }


def test_list_listeners_returns_copy(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    listing = store.list_listeners()
    listing[0]["code"] = "mutated"
    assert store.state.listeners[0]["code"] == "&listener_primary"


def test_add_listener(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_listener(
        {
            "code": "&listener_new",
            "nodes": [],
            "inputProcessors": [],
        }
    )
    assert any(listener["code"] == "&listener_new" for listener in store.state.listeners)
    store.undo()
    assert all(listener["code"] != "&listener_new" for listener in store.state.listeners)


def test_add_listener_duplicate_code(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.add_listener({"code": "&listener_primary", "nodes": [], "inputProcessors": []})


def test_update_listener_fields(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    updated = copy.deepcopy(store.state.listeners[0])
    updated["description"] = "Updated"
    updated["nodes"][0]["layers"] = [1]
    store.update_listener(code="&listener_primary", payload=updated)
    listener = store.state.listeners[0]
    assert listener["description"] == "Updated"
    assert listener["nodes"][0]["layers"] == [1]


def test_update_listener_rename_rewrites_references(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    updated = copy.deepcopy(store.state.listeners[0])
    updated["code"] = "&listener_renamed"
    store.update_listener(code="&listener_primary", payload=updated)

    assert store.state.listeners[0]["code"] == "&listener_renamed"
    assert store.state.layers[0].slots[0]["value"] == "&listener_renamed"
    assert store.state.macros[0]["bindings"][0]["value"] == "&listener_renamed"
    assert store.state.hold_taps[0]["bindings"][0] == "&listener_renamed"
    assert store.state.combos[0]["binding"]["value"] == "&listener_renamed"
    secondary = store.state.listeners[1]
    assert secondary["inputProcessors"][0]["code"] == "&listener_renamed"


def test_delete_listener_blocks_when_referenced(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.delete_listener(code="&listener_primary")


def test_delete_listener_force_clears_references(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.delete_listener(code="&listener_primary", force=True)

    assert all(slot["value"] != "&listener_primary" for slot in store.state.layers[0].slots)
    assert store.state.macros[0]["bindings"][0]["value"] == ""
    assert store.state.hold_taps[0]["bindings"][0] == ""
    assert store.state.combos[0]["binding"]["value"] == ""
    store.undo()
    assert any(listener["code"] == "&listener_primary" for listener in store.state.listeners)


def test_find_listener_references(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    refs = store.find_listener_references("&listener_primary")
    assert refs["keys"][0]["layer_name"] == "Base"
    assert refs["macros"][0]["name"] == "&macro_listener"
    assert refs["listeners"][0]["code"] == "&listener_secondary"


def test_listener_operations_support_redo(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_listener({"code": "&listener_temp", "nodes": [], "inputProcessors": []})
    store.update_listener(
        code="&listener_temp",
        payload={"code": "&listener_temp", "nodes": [], "inputProcessors": [{"code": "&kp", "params": []}]},
    )
    store.undo()
    store.undo()
    assert all(listener["code"] != "&listener_temp" for listener in store.state.listeners)

    store.redo()
    store.redo()
    assert any(listener["code"] == "&listener_temp" for listener in store.state.listeners)
