"""Minimal Textual application shell for the Glove80 TUI (Milestone 1)."""

from __future__ import annotations

import copy
import logging
from typing import Any, Mapping, Optional

from textual import on
from textual.app import App
from textual.binding import Binding
from textual.message import Message

from .messages import StoreUpdated
from .screens.editor import EditorScreen
from .state import DEFAULT_SAMPLE_LAYOUT, LayoutStore


_LOGGER = logging.getLogger(__name__)
_DEFAULT_FAMILY = "default"
_DEFAULT_VARIANT = "factory_default"


def _load_default_family_payload() -> Mapping[str, Any]:
    from glove80.layouts.family import build_layout

    return build_layout(_DEFAULT_FAMILY, _DEFAULT_VARIANT)


def _resolve_initial_payload(payload: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    if payload is not None:
        return payload
    try:
        return _load_default_family_payload()
    except Exception as exc:  # pragma: no cover - defensive fallback path
        _LOGGER.warning(
            "Falling back to sample layout after failing to load %s/%s: %s",
            _DEFAULT_FAMILY,
            _DEFAULT_VARIANT,
            exc,
        )
        return DEFAULT_SAMPLE_LAYOUT


class Glove80TuiApp(App[None]):
    """Entry point for the forthcoming Glove80 Textual editor."""

    TITLE = "Glove80 Layout Editor"
    CSS = """
    Screen {
        layout: vertical;
        background: $background;
        color: $text;
        layers: base overlay;
    }

    .project-ribbon {
        layout: horizontal;
        padding: 1 2;
        background: $boost;
        color: $text;
        height: 3;
        border-bottom: heavy $surface 30%;
    }

    .project-ribbon .ribbon-pill {
        padding: 0 1;
        border: solid $surface 20%;
        margin-right: 1;
        background: $surface 15%;
        color: $text 80%;
    }

    .project-ribbon .ribbon-title {
        text-style: bold;
        color: $accent;
    }

    .project-ribbon .ribbon-spacer {
        width: 1fr;
    }

    .project-ribbon Button {
        height: 1;
    }

    .inspector-drawer {
        border-bottom: solid $surface 15%;
        padding: 1 2;
        overflow: hidden;
    }

    .inspector-panel {
        border: solid $surface 10%;
        padding: 1;
        background: $surface 5%;
    }

    .inspector-panel Input {
        width: 1fr;
    }

    .inspector-drawer.collapsed {
        height: 0;
        min-height: 0;
        padding: 0 2;
        border: none;
    }

    .inspector-drawer.collapsed .inspector-panel {
        display: none;
    }

    .key-canvas {
        width: 1fr;
        height: 1fr;
        border: solid $surface 10%;
        padding: 2;
        min-height: 24;
        margin: 1 2;
    }

    #key-grid {
        padding: 1 0;
    }

    .key-row {
        padding: 0 1;
    }

    .key-hand-gap {
        width: 3;
    }

    .key-cap {
        min-width: 7;
        width: 7;
        height: 4;
        border: solid $surface 25%;
        padding: 0;
        text-align: center;
        margin: 0;
    }

    .key-cap.selected {
        border: heavy $accent;
        background: $accent 20%;
        color: $text;
    }

    .layer-strip {
        padding: 0 2;
        border-top: heavy $surface 30%;
        color: $text 80%;
        height: 3;
        background: $surface 5%;
    }

    .footer-bar {
        padding: 0 2;
        background: $surface 10%;
    }

    #inspector-overlay {
        layer: overlay;
        dock: right;
        min-width: 38;
        width: 48;
        max-width: 80;
        height: 100%;
        padding: 1 2;
        background: $surface 8%;
        border-left: heavy $surface 30%;
        offset-x: 100%;
        opacity: 0;
        transition: offset 200ms in_out_cubic, opacity 150ms in_out_cubic;
    }

    #inspector-overlay.visible {
        offset-x: 0;
        opacity: 100%;
    }
    """
    BINDINGS = [
        Binding("ctrl+s", "save", "Save", show=False),
        Binding("ctrl+shift+s", "save_as", "Save As", show=False),
        Binding("ctrl+k", "palette", "Command Palette"),
        Binding("f5", "validate", "Validate"),
        Binding("f6", "regen", "Regen Preview"),
        Binding("ctrl+z", "undo", "Undo", show=False),
        Binding("ctrl+shift+z", "redo", "Redo", show=False),
    ]

    def __init__(
        self,
        *,
        initial_layout: Optional[str] = None,
        initial_variant: Optional[str] = None,
        enable_devtools: bool = False,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(css_path=None)
        self._initial_layout = initial_layout or _DEFAULT_FAMILY
        self._initial_variant = initial_variant or _DEFAULT_VARIANT
        base_payload = copy.deepcopy(_resolve_initial_payload(payload))
        self.store = LayoutStore.from_payload(base_payload)

    def on_mount(self) -> None:
        """Push the editor screen on startup."""
        editor_screen = EditorScreen(
            store=self.store,
            initial_layout=self._initial_layout,
            initial_variant=self._initial_variant,
        )
        self.push_screen(editor_screen)

    def action_palette(self) -> None:  # pragma: no cover - placeholder binding
        self.notify("Command palette will arrive in a later milestone.")

    def action_save(self) -> None:  # pragma: no cover
        self.notify("Saving is disabled in this milestone.")

    action_save_as = action_save

    def action_validate(self) -> None:  # pragma: no cover - placeholder binding
        self.notify("Validation hooks land in Milestone 6.")

    def action_regen(self) -> None:  # pragma: no cover - placeholder binding
        self.notify("Regen preview is not available yet.")

    def action_undo(self) -> None:
        self.store.undo()
        self.post_message(StoreUpdated())

    def action_redo(self) -> None:
        self.store.redo()
        self.post_message(StoreUpdated())

    @on(Message)
    def log_message(self, event: Message) -> None:  # pragma: no cover - dev aid
        """Catch-all debug hook while the UI is mostly static."""

        self.log.debug("event=%s", event)
