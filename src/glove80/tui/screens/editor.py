"""Primary editor screen used throughout the milestones."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen

from ..messages import (
    InspectorFocusRequested,
    InspectorToggleRequested,
    JumpRequested,
    SearchHighlights,
    SearchPanelClosed,
    SelectionChanged,
)
from ..state import LayoutStore
from ..widgets import SearchPanel
from ..widgets.footer import FooterBar
from ..widgets.inspector import InspectorDrawer, InspectorOverlay
from ..widgets.key_canvas import KeyCanvas
from ..widgets.layer_strip import LayerStrip
from ..widgets.ribbon import ProjectRibbon

if TYPE_CHECKING:  # pragma: no cover - type assistance only
    from ..services import CommandRegistry


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
        self._overlay: InspectorOverlay | None = None
        self._layers: LayerStrip | None = None
        self._ribbon: ProjectRibbon | None = None
        self._search_panel: SearchPanel | None = None

    def compose(self) -> ComposeResult:
        self._search_panel = SearchPanel(store=self.store)
        self._canvas = KeyCanvas(store=self.store)
        self._inspector = InspectorDrawer(store=self.store, variant=self._initial_variant, expanded=False)
        self._layers = LayerStrip(store=self.store)
        self._ribbon = ProjectRibbon(
            store=self.store,
            current_layout=self._initial_layout,
            current_variant=self._initial_variant,
        )
        self._overlay = InspectorOverlay(
            store=self.store,
            variant=self._initial_variant,
            focus_fallback=lambda: self._canvas,
            on_visibility_change=self._handle_overlay_visibility,
        )

        yield self._ribbon
        if self._search_panel is not None:
            yield self._search_panel
        yield self._inspector
        yield self._canvas
        yield self._layers
        yield FooterBar()
        if self._overlay is not None:
            yield self._overlay

    # ------------------------------------------------------------------
    def register_commands(self, registry: "CommandRegistry") -> None:
        self._register_object_bindings(registry, self, "Editor Screen")
        if self._canvas is not None:
            self._register_object_bindings(registry, self._canvas, "Key Canvas")
        if self._layers is not None:
            self._register_object_bindings(registry, self._layers, "Layer Strip")
        if self._overlay is not None:
            self._register_object_bindings(registry, self._overlay, "Inspector Overlay")

    def open_search_panel(self) -> None:
        if self._search_panel is None:
            return
        self._search_panel.open()

    def cycle_search_results(self, delta: int) -> None:
        if self._search_panel is None or not self._search_panel.is_open:
            return
        self._search_panel.next_result(delta)

    def close_search_panel(self) -> None:
        if self._search_panel is None or not self._search_panel.is_open:
            return
        self._search_panel.close()

    @on(InspectorFocusRequested)
    def _handle_focus_request(self, _: InspectorFocusRequested) -> None:
        if self._overlay is not None:
            self._overlay.focus_panel()
        elif self._inspector is not None:
            self._inspector.expand()
            self._inspector.panel.key_inspector.focus_value_field()

    @on(InspectorToggleRequested)
    def _handle_inspector_toggle(self, _: InspectorToggleRequested) -> None:
        if self._overlay is not None:
            self._overlay.toggle()
        elif self._inspector is not None:
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

    @on(JumpRequested)
    def _handle_jump_requested(self, event: JumpRequested) -> None:
        selection = self.store.set_selection(layer_index=event.layer_index, key_index=event.key_index)
        self.post_message(
            SelectionChanged(
                layer_index=selection.layer_index,
                layer_name=self.store.selected_layer_name,
                key_index=selection.key_index,
            )
        )
        self._focus_canvas()
        self._focus_inspector_for_jump(event)

    @on(SearchPanelClosed)
    def _handle_search_closed(self, _: SearchPanelClosed) -> None:
        self._focus_canvas()

    @on(SearchHighlights)
    def _handle_search_highlights(self, event: SearchHighlights) -> None:
        if self._canvas is None:
            return
        self._canvas.update_search_highlights(layer_index=event.layer_index, indices=event.indices)

    # ------------------------------------------------------------------
    def _handle_overlay_visibility(self, visible: bool) -> None:
        if self._ribbon is not None:
            self._ribbon.set_inspector_expanded(visible)

    # ------------------------------------------------------------------
    def _register_object_bindings(
        self,
        registry: "CommandRegistry",
        obj: object,
        category: str,
    ) -> None:
        bindings = getattr(obj, "BINDINGS", None)
        if not bindings:
            return
        registry.register_bindings(source=obj, bindings=bindings, category=category)

    def _focus_canvas(self) -> None:
        if self._canvas is None:
            return
        try:
            self._canvas.focus()
        except Exception:  # pragma: no cover - defensive
            pass

    def _focus_inspector_for_jump(self, event: JumpRequested) -> None:
        panel = self._resolve_inspector_panel()
        if panel is None:
            return
        if event.jump_type == "macro":
            panel.focus_tab("tab-macros")
            macro_name = event.metadata.get("macro", "") if isinstance(event.metadata, dict) else ""
            if macro_name:
                panel.focus_macro(macro_name)
        elif event.jump_type == "listener":
            panel.focus_tab("tab-listeners")
            code = event.metadata.get("listener", "") if isinstance(event.metadata, dict) else ""
            if code:
                panel.focus_listener(code)
        else:
            panel.focus_tab("tab-key")

    def _resolve_inspector_panel(self):
        if self._overlay is not None and self._overlay.visible:
            return self._overlay.panel
        if self._inspector is not None and self._inspector.expanded:
            return self._inspector.panel
        if self._overlay is not None:
            self._overlay.show(focus=False)
            return self._overlay.panel
        if self._inspector is not None:
            self._inspector.expand()
            return self._inspector.panel
        return None
