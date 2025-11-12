"""Shared Textual messages for the TUI."""

from textual.message import Message


class StoreUpdated(Message):
    """Broadcast when the layout store mutates."""


class SelectionChanged(Message):
    """Published when a layer/key selection mutation occurs."""

    def __init__(self, *, layer_index: int, layer_name: str | None, key_index: int) -> None:
        super().__init__()
        self.layer_index = layer_index
        self.layer_name = layer_name
        self.key_index = key_index


class InspectorFocusRequested(Message):
    """Signal that the Inspector should focus the key editor."""

    def __init__(self, *, layer_index: int, key_index: int) -> None:
        super().__init__()
        self.layer_index = layer_index
        self.key_index = key_index


class FooterMessage(Message):
    """Informational footer update (status line)."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class InspectorToggleRequested(Message):
    """Signal that the inspector drawer should toggle visibility."""


__all__ = [
    "StoreUpdated",
    "SelectionChanged",
    "InspectorFocusRequested",
    "InspectorToggleRequested",
    "FooterMessage",
]
