"""Shared key-grid helpers for the Textual TUI."""

from __future__ import annotations

from typing import Literal, Optional

Direction = Literal["left", "right", "up", "down"]

# Simple 5x16 grid (80 slots) – enough for deterministic navigation in Milestone 3.
KEY_GRID_ROWS: tuple[tuple[int, ...], ...] = (
    tuple(range(0, 16)),
    tuple(range(16, 32)),
    tuple(range(32, 48)),
    tuple(range(48, 64)),
    tuple(range(64, 80)),
)

INDEX_TO_POSITION = {
    index: (row, col) for row, row_values in enumerate(KEY_GRID_ROWS) for col, index in enumerate(row_values)
}
POSITION_TO_INDEX = {position: index for index, position in INDEX_TO_POSITION.items()}

MAX_ROW = len(KEY_GRID_ROWS) - 1
MAX_COL = len(KEY_GRID_ROWS[0]) - 1


def move(index: int, direction: Direction) -> Optional[int]:
    """Return the next key index when travelling in ``direction``.

    Movement clamps at grid edges to keep navigation predictable.
    """

    if index not in INDEX_TO_POSITION:
        return None
    row, col = INDEX_TO_POSITION[index]
    if direction == "left":
        col = max(0, col - 1)
    elif direction == "right":
        col = min(MAX_COL, col + 1)
    elif direction == "up":
        row = max(0, row - 1)
    elif direction == "down":
        row = min(MAX_ROW, row + 1)
    return POSITION_TO_INDEX.get((row, col))


__all__ = [
    "Direction",
    "KEY_GRID_ROWS",
    "INDEX_TO_POSITION",
    "move",
]
