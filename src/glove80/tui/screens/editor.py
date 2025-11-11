"""Read-only editor screen placeholder for Milestone 1."""

from __future__ import annotations

from typing import Optional

from textual.containers import Horizontal
from textual.screen import Screen

from ..widgets.footer import FooterBar
from ..widgets.key_canvas import KeyCanvas
from ..widgets.layer_sidebar import LayerSidebar
from ..widgets.ribbon import ProjectRibbon
from ..widgets.stub import InspectorPanel
from ..state import LayoutStore


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

    def compose(self):
        yield ProjectRibbon(current_layout=self._initial_layout, current_variant=self._initial_variant)
        yield Horizontal(
            LayerSidebar(store=self.store),
            KeyCanvas(),
            InspectorPanel(),
            id="editor-workspace",
        )
        yield FooterBar()
