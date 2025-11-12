"""Primary editor screen used throughout the milestones."""

from __future__ import annotations

from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen

from ..state import LayoutStore
from ..widgets.footer import FooterBar
from ..widgets.inspector import InspectorDrawer
from ..widgets.key_canvas import KeyCanvas
from ..widgets.layer_strip import LayerStrip
from ..widgets.ribbon import ProjectRibbon
from ..messages import InspectorFocusRequested, InspectorToggleRequested, SelectionChanged


class EditorScreen(Screen[None]):
    """Static editor layout scaffolding."""

    def __init__(
        self,
        *,
        store: LayoutStore,
        initial_layout: Optional[str],
        initial_variant: Optional[str],
    ) -> None:
        super().__init__()
        self.store = store
        self._initial_layout = initial_layout or "default"
        self._initial_variant = initial_variant or "factory_default"
        self._canvas: KeyCanvas | None = None
        self._inspector: InspectorDrawer | None = None
        self._layers: LayerStrip | None = None
        self._ribbon: ProjectRibbon | None = None

    def compose(self) -> ComposeResult:
        self._canvas = KeyCanvas(store=self.store)
        self._inspector = InspectorDrawer(store=self.store, variant=self._initial_variant)
        self._layers = LayerStrip(store=self.store)
        self._ribbon = ProjectRibbon(
            store=self.store,
            current_layout=self._initial_layout,
            current_variant=self._initial_variant,
        )

        yield self._ribbon
        yield self._inspector
        yield self._canvas
        yield self._layers
        yield FooterBar()

    @on(InspectorFocusRequested)
    def _handle_focus_request(self, _: InspectorFocusRequested) -> None:
        if self._inspector is not None:
            self._inspector.expand()
            self._inspector.panel.key_inspector.focus_value_field()
        if self._ribbon is not None:
            self._ribbon.set_inspector_expanded(True)

    @on(InspectorToggleRequested)
    def _handle_inspector_toggle(self, _: InspectorToggleRequested) -> None:
        if self._inspector is None:
            return
        self._inspector.toggle()
        if self._ribbon is not None:
            self._ribbon.set_inspector_expanded(self._inspector.expanded)

    @on(SelectionChanged)
    def _handle_selection_changed(self, event: SelectionChanged) -> None:
        if event.layer_index < 0 or event.key_index < 0:
            return
        if self._canvas is None:
            return
        self._canvas.apply_selection(layer_index=event.layer_index, key_index=event.key_index)
