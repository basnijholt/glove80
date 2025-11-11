"""Minimal Textual application shell for the Glove80 TUI (Milestone 1)."""

from __future__ import annotations

import copy
from typing import Any, Mapping, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message

from .messages import StoreUpdated
from .screens.editor import EditorScreen
from .state import DEFAULT_SAMPLE_LAYOUT, LayoutStore


class Glove80TuiApp(App[None]):
    """Entry point for the forthcoming Glove80 Textual editor."""

    TITLE = "Glove80 Layout Editor"
    CSS = """
    Screen {
        layout: vertical;
        background: $background;
        color: $text;
    }

    #editor-workspace {
        layout: horizontal;
        height: 1fr;
    }

    .project-ribbon {
        padding: 1 2;
        background: $boost;
        color: $text;
    }

    .layer-sidebar {
        width: 28;
        border: heavy $surface 10%;
        padding: 0 1;
    }

    .key-canvas {
        width: 1fr;
        border: solid $surface 10%;
        padding: 1;
        min-height: 20;
    }

    .inspector-panel {
        width: 34;
        border: solid $surface 10%;
        padding: 1;
    }

    .features-tab {
        border-top: solid $surface 20%;
        margin-top: 1;
        padding-top: 1;
    }

    .footer-bar {
        padding: 0 2;
        background: $surface 10%;
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
        self._initial_layout = initial_layout
        self._initial_variant = initial_variant
        base_payload = copy.deepcopy(payload) if payload is not None else copy.deepcopy(DEFAULT_SAMPLE_LAYOUT)
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
