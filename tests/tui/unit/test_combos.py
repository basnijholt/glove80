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
        "holdTaps": [],
        "combos": [
            {
                "name": "&combo_home",
                "binding": {"value": "&kp", "params": ["ESC"]},
                "keyPositions": [0, 1],
                "layers": [{"name": "Base"}],
            }
        ],
        "inputListeners": [],
    }


def test_list_combos_returns_copy(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    combos = store.list_combos()
    combos[0]["name"] = "mutated"
    assert store.state.combos[0]["name"] == "&combo_home"


def test_add_combo(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.add_combo(
        {
            "name": "&combo_new",
            "binding": {"value": "&kp", "params": ["TAB"]},
            "keyPositions": [2, 3],
            "layers": [{"name": "Base"}],
        }
    )
    assert any(combo["name"] == "&combo_new" for combo in store.state.combos)
    store.undo()
    assert all(combo["name"] != "&combo_new" for combo in store.state.combos)


def test_add_combo_duplicate_name(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.add_combo(
            {
                "name": "&combo_home",
                "binding": {"value": "&kp"},
                "keyPositions": [4, 5],
                "layers": [{"name": "Base"}],
            }
        )


def test_add_combo_rejects_unknown_layer(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(ValueError):
        store.add_combo(
            {
                "name": "&combo_bad_layer",
                "binding": {"value": "&kp", "params": ["ESC"]},
                "keyPositions": [2, 4],
                "layers": [{"name": "Unknown"}],
            }
        )


def test_update_combo_rename_rewrites_references(sample_payload: dict[str, object]) -> None:
    payload = copy.deepcopy(sample_payload)
    payload["layers"][0][0] = {"value": "&combo_home", "params": []}
    store = LayoutStore.from_payload(payload)

    updated = {
        "name": "&combo_renamed",
        "binding": {"value": "&kp", "params": ["Q"]},
        "keyPositions": [0, 2],
        "layers": [{"name": "Base"}],
    }
    store.update_combo(name="&combo_home", payload=updated)

    assert store.state.combos[0]["name"] == "&combo_renamed"
    assert store.state.layers[0].slots[0]["value"] == "&combo_renamed"


def test_delete_combo_blocks_when_referenced(sample_payload: dict[str, object]) -> None:
    payload = copy.deepcopy(sample_payload)
    payload["layers"][0][1] = {"value": "&combo_home", "params": []}
    store = LayoutStore.from_payload(payload)

    with pytest.raises(ValueError):
        store.delete_combo(name="&combo_home")


def test_delete_combo_force_clears_references(sample_payload: dict[str, object]) -> None:
    payload = copy.deepcopy(sample_payload)
    payload["layers"][0][1] = {"value": "&combo_home", "params": []}
    store = LayoutStore.from_payload(payload)

    store.delete_combo(name="&combo_home", force=True)
    assert all(combo["name"] != "&combo_home" for combo in store.state.combos)
    store.undo()
    assert any(combo["name"] == "&combo_home" for combo in store.state.combos)


def test_find_combo_references(sample_payload: dict[str, object]) -> None:
    payload = copy.deepcopy(sample_payload)
    payload["layers"][0][2] = {"value": "&combo_home", "params": []}
    store = LayoutStore.from_payload(payload)

    refs = store.find_combo_references("&combo_home")
    assert refs["keys"]
