"""Project ribbon with primary controls."""

from __future__ import annotations

from textual import on
from textual.containers import Horizontal
from textual.widgets import Button, Static

from ..messages import InspectorToggleRequested, SelectionChanged
from ..state import LayoutStore


class ProjectRibbon(Horizontal):
    """Header showing layout/variant plus quick actions."""

    def __init__(
        self,
        *,
        store: LayoutStore,
        current_layout: str,
        current_variant: str,
    ) -> None:
        super().__init__(classes="project-ribbon")
        self.store = store
        self._current_layout = current_layout
        self._current_variant = current_variant
        self._layer_label = Static(self._layer_text(), classes="ribbon-pill layer-pill")
        self._inspector_button = Button("Inspector ▸", id="toggle-inspector")

    def _layer_text(self) -> str:
        name = self.store.selected_layer_name or "—"
        return f"Layer: {name}"

    def compose(self):  # type: ignore[override]
        yield Static("Glove80", classes="ribbon-title")
        yield Static(f"Layout: {self._current_layout}", classes="ribbon-pill")
        yield Static(f"Variant: {self._current_variant}", classes="ribbon-pill")
        yield self._layer_label
        yield Static("", classes="ribbon-spacer")
        yield Button("Save", id="save-action", classes="ribbon-action")
        yield Button("Undo", id="undo-action", classes="ribbon-action")
        yield Button("Redo", id="redo-action", classes="ribbon-action")
        yield self._inspector_button

    def update_layer_text(self) -> None:
        self._layer_label.update(self._layer_text())

    def set_inspector_expanded(self, expanded: bool) -> None:
        label = "Inspector ▾" if expanded else "Inspector ▸"
        self._inspector_button.label = label

    @on(Button.Pressed)
    def _handle_button(self, event: Button.Pressed) -> None:
        if event.button.id == "toggle-inspector":
            self.post_message(InspectorToggleRequested())
        elif event.button.id == "save-action":
            self.app.action_save()
        elif event.button.id == "undo-action":
            self.app.action_undo()
        elif event.button.id == "redo-action":
            self.app.action_redo()

    @on(SelectionChanged)
    def _handle_selection_changed(self, _: SelectionChanged) -> None:
        self.update_layer_text()
