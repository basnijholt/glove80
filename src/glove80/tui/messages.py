"""Shared Textual messages for the TUI."""

from textual.message import Message


class StoreUpdated(Message):
    """Broadcast when the layout store mutates."""

    pass

