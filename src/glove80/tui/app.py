"""Minimal Textual application shell for the Glove80 TUI (Milestone 1)."""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Mapping, Optional

from textual import on
from textual.app import App
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget

from .messages import SaveStateChanged, StoreUpdated, ValidationCompleted
from .screens.editor import EditorScreen
from .services import CommandRegistry, SaveCoordinator, ValidationCoordinator
from .state import DEFAULT_SAMPLE_LAYOUT, LayoutStore
from .widgets import CommandPaletteModal, FooterBar, RegenPreviewModal


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

    #search-panel {
        dock: top;
        padding: 0 2;
        height: 3;
        background: $surface 20%;
        color: $text 90%;
        border-bottom: heavy $surface 40%;
    }

    #search-panel.hidden {
        display: none;
    }

    .key-cap.highlighted {
        border: dashed $warning;
        color: $warning;
    }

    .command-palette-modal {
        layer: overlay;
        align: center middle;
    }

    #command-palette-container {
        background: $surface 50%;
        border: round $accent;
        min-width: 60;
        max-width: 80;
        padding: 1 2;
        height: auto;
    }

    .regen-modal-screen {
        layer: overlay;
        align: center middle;
    }

    #regen-modal-container {
        background: $surface 40%;
        border: round $accent;
        min-width: 70;
        max-width: 100;
        min-height: 30;
        max-height: 45;
        padding: 1 2;
    }

    #regen-diff-view {
        height: 1fr;
        border: solid $surface 20%;
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
        Binding("/", "search", "Search"),
        Binding("f3", "search_next", "Next Match", show=False),
        Binding("shift+f3", "search_prev", "Prev Match", show=False),
        Binding("escape", "search_close", "Close Search", show=False),
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
        save_path: str | Path | None = None,
    ) -> None:
        super().__init__(css_path=None)
        self._initial_layout = initial_layout or _DEFAULT_FAMILY
        self._initial_variant = initial_variant or _DEFAULT_VARIANT
        base_payload = copy.deepcopy(_resolve_initial_payload(payload))
        self.store = LayoutStore.from_payload(base_payload)
        self._command_registry: CommandRegistry | None = None
        self._editor_screen: EditorScreen | None = None
        self._save_path = Path(save_path or "glove80-layout.json")
        self._validation_coordinator = ValidationCoordinator(
            store=self.store,
            post_message=self.post_message,
        )
        self._save_coordinator = SaveCoordinator(
            store=self.store,
            post_message=self.post_message,
        )
        self._background_tasks: set[asyncio.Task[None]] = set()

    def on_mount(self) -> None:
        """Push the editor screen on startup."""
        editor_screen = EditorScreen(
            store=self.store,
            initial_layout=self._initial_layout,
            initial_variant=self._initial_variant,
        )
        self._editor_screen = editor_screen
        self.push_screen(editor_screen)
        self.call_later(self._populate_command_registry)
        self.call_later(self._validation_coordinator.begin_debounced_validation)
        self.call_later(self._emit_initial_status)

    def action_palette(self) -> None:
        registry = self._command_registry
        if registry is None or not registry.commands:
            self.notify("Commands are still indexing — try again in a moment.")
            return

        previous_focus = self.focused

        def _on_close(command_id: str | None) -> None:
            self._restore_focus(previous_focus)
            if not command_id:
                return
            self._execute_palette_command(command_id)

        self.push_screen(CommandPaletteModal(registry), _on_close)

    def action_search(self) -> None:
        editor = self._active_editor()
        if editor is None:
            return
        editor.open_search_panel()

    def action_search_next(self) -> None:
        editor = self._active_editor()
        if editor is None:
            return
        editor.cycle_search_results(1)

    def action_search_prev(self) -> None:
        editor = self._active_editor()
        if editor is None:
            return
        editor.cycle_search_results(-1)

    def action_search_close(self) -> None:
        editor = self._active_editor()
        if editor is None:
            return
        editor.close_search_panel()

    def action_validate(self) -> None:
        self._schedule_async_action("validate", self._async_validate)

    def action_save(self) -> None:
        self._schedule_async_action("save", self._async_save)

    def action_save_as(self) -> None:
        self.action_save()

    def action_regen(self) -> None:
        self._schedule_async_action("regen", self._async_regen)

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

    # ------------------------------------------------------------------
    def _active_editor(self) -> EditorScreen | None:
        return self._editor_screen

    def _restore_focus(self, target: Widget | None) -> None:
        if target is None:
            return
        try:
            target.focus()
        except Exception:  # pragma: no cover - defensive
            pass

    def _footer_bar(self) -> FooterBar | None:
        screen = self._editor_screen
        if screen is None:
            return None
        try:
            return screen.query_one(FooterBar)
        except Exception:  # pragma: no cover - defensive
            return None

    def _emit_initial_status(self) -> None:
        self._validation_coordinator.publish_last_summary()
        self._save_coordinator.publish_state(path=self._save_path)

    def flag_manual_validation_errors(self, issue_count: int) -> None:
        self._validation_coordinator.record_manual_issues(issue_count)

    def clear_manual_validation_errors(self) -> None:
        self._validation_coordinator.clear_manual_issues()

    def _populate_command_registry(self) -> None:
        registry = CommandRegistry()
        registry.register_bindings(source=self, bindings=self.BINDINGS, category="Application")
        editor = self._active_editor()
        if editor is not None:
            editor.register_commands(registry)
        self._command_registry = registry

    def _execute_palette_command(self, command_id: str) -> None:
        registry = self._command_registry
        if registry is None:
            return
        command = registry.get(command_id)
        if command is None:
            self.notify("Command is no longer available.")
            return
        action_name = f"action_{command.action}"
        target = command.source
        handler = getattr(target, action_name, None)
        if handler is None:
            self.notify(f"{command.label} cannot be executed right now.")
            return
        try:
            handler()
        except Exception as exc:  # pragma: no cover - surfaced to devtools
            self.notify(f"Failed to run {command.label}: {exc}")
            raise

    def _schedule_async_action(
        self,
        label: str,
        task_factory: Callable[[], Awaitable[None]],
    ) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # pragma: no cover - Textual guarantees loop during runtime
            self.log.warning("Cannot schedule %s action; no running loop", label)
            return
        task = loop.create_task(self._guard_async_action(label, task_factory))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _guard_async_action(
        self,
        label: str,
        task_factory: Callable[[], Awaitable[None]],
    ) -> None:
        try:
            await task_factory()
        except asyncio.CancelledError:  # pragma: no cover - propagate cancellation
            raise
        except Exception as exc:  # pragma: no cover - surfaced to UI
            self.log.exception("%s action failed", label)
            self.notify(f"{label.capitalize()} failed: {exc}")

    async def _async_validate(self) -> None:
        await self._validation_coordinator.validate_now()

    async def _async_save(self) -> None:
        summary = self._validation_coordinator.last_summary
        if not summary.is_valid:
            summary = await self._validation_coordinator.validate_now()
        if not summary.is_valid:
            self.notify("Fix validation issues before saving.")
            return
        try:
            path = await self._save_coordinator.save_atomic(self._save_path)
        except Exception as exc:  # pragma: no cover - surfaced to UI
            self.notify(f"Save failed: {exc}")
            return
        self.notify(f"Layout saved → {path}")

    async def _async_regen(self) -> None:
        current = self.store.export_payload()
        try:
            loop = asyncio.get_running_loop()
            regenerated = await loop.run_in_executor(None, self._regenerate_payload)
        except Exception as exc:  # pragma: no cover - surfaced to UI
            self.notify(f"Regen failed: {exc}")
            return
        if regenerated == current:
            self.notify("Regen produced no changes.")
            return

        def _on_close(accepted: bool | None) -> None:
            if not accepted:
                return
            self.store.replace_payload(regenerated)
            self.post_message(StoreUpdated())

        self.push_screen(
            RegenPreviewModal(before=current, after=regenerated),
            _on_close,
        )

    def _regenerate_payload(self) -> Mapping[str, Any]:
        from glove80.layouts.family import build_layout

        return build_layout(self._initial_layout, self._initial_variant)

    @on(StoreUpdated)
    def _handle_store_updated(self, _: StoreUpdated) -> None:
        self._save_coordinator.mark_dirty()
        self._validation_coordinator.begin_debounced_validation()

    @on(SaveStateChanged)
    def _handle_save_state_changed(self, event: SaveStateChanged) -> None:
        if event.error:
            self.notify(f"Save error: {event.error}")

    @on(ValidationCompleted)
    def _handle_validation_completed(self, event: ValidationCompleted) -> None:
        footer = self._footer_bar()
        if footer is not None:
            footer.set_validation_issue_count(event.issue_count)
