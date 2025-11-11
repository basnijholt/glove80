from __future__ import annotations

import copy

import pytest

from glove80.tui.state.store import LayoutStore


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    return {
        "layer_names": ["Base", "Lower", "Raise"],
        "layers": [
            [{"value": "&kp A", "params": []} for _ in range(80)],
            [{"value": "&kp B", "params": []} for _ in range(80)],
            [{"value": "&kp C", "params": []} for _ in range(80)],
        ],
        "combos": [
            {
                "name": "combo_1",
                "binding": {"value": "&kp ESC", "params": []},
                "keyPositions": [0, 1],
                "layers": [{"name": "Base"}],
            }
        ],
        "inputListeners": [
            {
                "code": "listener",
                "layers": [{"name": "Raise"}],
                "nodes": [],
                "inputProcessors": [],
            }
        ],
    }


def test_rename_layer_updates_layerrefs(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.rename_layer(old_name="Base", new_name="Main")

    assert store.layer_names[0] == "Main"
    # Combo updated
    assert store.state.combos[0]["layers"] == [{"name": "Main"}]
    # Listener unaffected (different layer)
    assert store.state.listeners[0]["layers"] == [{"name": "Raise"}]

    store.undo()
    assert store.layer_names[0] == "Base"
    assert store.state.combos[0]["layers"] == [{"name": "Base"}]


def test_reorder_layer_preserves_refs(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.reorder_layer(source_index=2, dest_index=0)

    assert store.layer_names == ("Raise", "Base", "Lower")
    # Listener still points to Raise by name
    assert store.state.listeners[0]["layers"] == [{"name": "Raise"}]

    store.undo()
    assert store.layer_names == ("Base", "Lower", "Raise")


def test_duplicate_layer_inserts_copy(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.duplicate_layer(source_name="Lower", new_name="Lower Copy")

    assert "Lower Copy" in store.layer_names
    inserted_index = store.layer_names.index("Lower Copy")
    assert store.state.layers[inserted_index].slots == store.state.layers[1].slots

    store.undo()
    assert "Lower Copy" not in store.layer_names


def test_pickup_drop_moves_layer(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.pick_up_layer(name="Lower")
    store.drop_layer(target_index=0)

    assert store.layer_names == ("Lower", "Base", "Raise")

    store.undo()
    assert store.layer_names == ("Base", "Lower", "Raise")


def test_selection_defaults_and_updates(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)

    assert store.selection.layer_index == 0
    assert store.selection.key_index == 0

    updated = store.set_selection(layer_index=1, key_index=10)
    assert updated.layer_index == 1
    assert updated.key_index == 10


def test_update_selected_key_records_undo(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    store.set_selection(layer_index=0, key_index=0)

    store.update_selected_key(value="&kp TAB", params=["shift"])
    assert store.state.layers[0].slots[0]["value"] == "&kp TAB"
    assert store.state.layers[0].slots[0]["params"] == ["shift"]

    store.undo()
    assert store.state.layers[0].slots[0]["value"] == "&kp A"


def test_invalid_key_index_raises(sample_payload: dict[str, object]) -> None:
    store = LayoutStore.from_payload(sample_payload)
    with pytest.raises(IndexError):
        store.set_selection(layer_index=0, key_index=99)

    with pytest.raises(IndexError):
        store.set_selected_key(100)
