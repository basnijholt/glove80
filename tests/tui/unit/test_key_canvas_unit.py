from __future__ import annotations

from glove80.tui.state.store import DEFAULT_SAMPLE_LAYOUT, LayoutStore
from glove80.tui.widgets.key_canvas import KeyCanvas


def _make_canvas() -> KeyCanvas:
    store = LayoutStore.from_payload(DEFAULT_SAMPLE_LAYOUT)
    return KeyCanvas(store=store)


def test_slot_labels_are_capped_at_five_chars() -> None:
    canvas = _make_canvas()
    slot = {"value": "&macro_super_long_name"}
    legend = canvas._slot_legend((slot,), 0)
    assert len(legend.strip()) <= KeyCanvas.MAX_LABEL_CHARS
    assert legend.strip().endswith("…")


def test_slot_labels_strip_control_characters() -> None:
    canvas = _make_canvas()
    slot = {"value": "line1\nline2"}
    legend = canvas._slot_legend((slot,), 0)
    assert "\n" not in legend
    assert legend.strip().startswith("LINE")
    assert legend.strip().endswith("…")


def test_kp_slot_prefers_param_value() -> None:
    canvas = _make_canvas()
    slot = {"value": "&kp", "params": [{"value": "A", "params": []}]}
    legend = canvas._slot_legend((slot,), 0)
    assert legend.strip() == "A"


def test_detail_text_includes_params() -> None:
    canvas = _make_canvas()
    slot = {"value": "&kp", "params": ["A"]}
    detail_text = canvas._detail_text(slot, 0)
    assert detail_text.startswith("Key #00: &kp")
    assert "params: A" in detail_text
