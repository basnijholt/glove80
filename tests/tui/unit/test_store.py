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

