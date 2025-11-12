"""Utilities to capture the live Textual screen as plain text."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import io

from rich.console import Console

if TYPE_CHECKING:
    from glove80.tui.app import Glove80TuiApp


def capture_snapshot(app: Glove80TuiApp) -> str:
    """Render the current screen buffer to text."""

    header = _header_lines(app)
    store_summary = _store_lines(app)

    try:
        frame_text = _render_screen_to_text(app)
    except Exception as exc:  # pragma: no cover - defensive
        frame_text = f"(Unable to render snapshot: {exc})"

    sections: list[str] = []
    if header:
        sections.append("\n".join(header))
    if store_summary:
        sections.append("\n".join(store_summary))
    sections.append(frame_text.rstrip())
    return "\n\n".join(section for section in sections if section)


def save_snapshot(app: Glove80TuiApp, filepath: str | Path) -> None:
    """Capture and write the snapshot to disk."""

    Path(filepath).write_text(capture_snapshot(app))


def _render_screen_to_text(app: Glove80TuiApp) -> str:
    size = getattr(app, "size", None)
    width = getattr(size, "width", 80) or 80
    height = getattr(size, "height", 25) or 25
    console = Console(
        width=width,
        height=height,
        file=io.StringIO(),
        force_terminal=True,
        color_system="truecolor",
        record=True,
        legacy_windows=False,
        safe_box=False,
    )
    renderable = app.screen._compositor.render_update(  # type: ignore[attr-defined]
        full=True,
        screen_stack=app._background_screens,  # type: ignore[attr-defined]
        simplify=False,
    )
    console.print(renderable)
    return console.export_text(clear=True)


def _header_lines(app: Glove80TuiApp) -> list[str]:
    size = getattr(app, "size", None)
    width = getattr(size, "width", 80) or 80
    height = getattr(size, "height", 25) or 25
    screen_name = app.screen.__class__.__name__ if getattr(app, "screen", None) else "?"
    title = getattr(app, "title", "") or "Glove80"
    border = "=" * width
    return [
        border,
        title.center(width),
        f"Screen: {screen_name}",
        f"Size: {width}x{height}",
        border,
    ]


def _store_lines(app: Glove80TuiApp) -> list[str]:
    store = getattr(app, "store", None)
    if store is None:
        return []
    layer_name = _value_or_call(getattr(store, "selected_layer_name", None)) or "—"
    selection = getattr(store, "selection", None)
    key_index = getattr(selection, "key_index", "—")
    return [
        "Store State:",
        f"  Active Layer: {layer_name}",
        f"  Key Index: {key_index}",
    ]


def _value_or_call(value: Any) -> Any:
    return value() if callable(value) else value


__all__ = ["capture_snapshot", "save_snapshot"]
