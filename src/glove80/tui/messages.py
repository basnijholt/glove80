"""Shared Textual messages for the TUI."""

from typing import Mapping, Sequence

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


class ValidationCompleted(Message):
    """Emit when a validation sweep completes."""

    def __init__(self, *, is_valid: bool, issue_count: int) -> None:
        super().__init__()
        self.is_valid = is_valid
        self.issue_count = issue_count


class SaveStateChanged(Message):
    """Emit when dirty/save state changes."""

    def __init__(
        self,
        *,
        is_dirty: bool,
        save_in_progress: bool,
        path: str | None = None,
        error: str | None = None,
    ) -> None:
        super().__init__()
        self.is_dirty = is_dirty
        self.save_in_progress = save_in_progress
        self.path = path
        self.error = error


class InspectorToggleRequested(Message):
    """Signal that the inspector drawer should toggle visibility."""


class JumpRequested(Message):
    """Request that the editor jump to a given target."""

    def __init__(
        self,
        *,
        layer_index: int,
        key_index: int,
        jump_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.layer_index = layer_index
        self.key_index = key_index
        self.jump_type = jump_type
        self.metadata = dict(metadata or {})


class SearchPanelClosed(Message):
    """Emitted when the search panel hides itself."""


class SearchHighlights(Message):
    """Publish highlight indices for the current layer."""

    def __init__(self, *, layer_index: int, indices: Sequence[int]) -> None:
        super().__init__()
        self.layer_index = layer_index
        self.indices = tuple(indices)


__all__ = [
    "StoreUpdated",
    "SelectionChanged",
    "InspectorFocusRequested",
    "InspectorToggleRequested",
    "FooterMessage",
    "ValidationCompleted",
    "SaveStateChanged",
    "JumpRequested",
    "SearchPanelClosed",
    "SearchHighlights",
]
