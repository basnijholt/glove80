"""Primary editor screen used throughout the milestones."""

from __future__ import annotations

from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen

from ..state import LayoutStore
from ..widgets.footer import FooterBar
from ..widgets.inspector import InspectorPanel
from ..widgets.key_canvas import KeyCanvas
from ..widgets.layer_sidebar import LayerSidebar
from ..widgets.ribbon import ProjectRibbon
from ..messages import InspectorFocusRequested


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
        self._initial_variant = initial_variant or "base"
        self._sidebar: LayerSidebar | None = None
        self._canvas: KeyCanvas | None = None
        self._inspector: InspectorPanel | None = None

    def compose(self) -> ComposeResult:
        self._sidebar = LayerSidebar(store=self.store)
        self._canvas = KeyCanvas(store=self.store)
        self._inspector = InspectorPanel(store=self.store)

        yield ProjectRibbon(current_layout=self._initial_layout, current_variant=self._initial_variant)
        yield Horizontal(self._sidebar, self._canvas, self._inspector, id="editor-workspace")
        yield FooterBar()

    @on(InspectorFocusRequested)
    def _handle_focus_request(self, _: InspectorFocusRequested) -> None:
        if self._inspector is not None:
            self._inspector.key_inspector.focus_value_field()
