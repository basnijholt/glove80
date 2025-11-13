"""Interactive layer sidebar for Milestone 2."""

from __future__ import annotations

from typing import Optional

from textual import on
from textual.binding import Binding
from textual.widgets import Label, ListItem, ListView

from ..state import LayoutStore
from ..messages import SelectionChanged, StoreUpdated
from .rename_modal import RenameLayerModal


class LayerSidebar(ListView):
    BINDINGS = [
        Binding("r", "rename_layer", "Rename"),
        Binding("ctrl+d", "duplicate_layer", "Duplicate"),
        Binding("ctrl+up", "move_up", "Move Up", show=False),
        Binding("ctrl+down", "move_down", "Move Down", show=False),
        Binding("p", "pick_up", "Pick Up"),
        Binding("o", "drop", "Drop"),
    ]

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(classes="layer-sidebar")
        self.store = store

    def on_mount(self) -> None:
        self._refresh()
        if self.children:
            self.index = 0
            self.focus()
            self.store.set_active_layer(0)
            self._emit_selection()

    # ------------------------------------------------------------------
    def _refresh(self, *, preferred: Optional[str] = None) -> None:
        if preferred is None:
            preferred = self._selected_name()
        self.call_after_refresh(self._rebuild, preferred)

    async def _rebuild(self, preferred: Optional[str]) -> None:
        await self.clear()
        items = []
        for idx, name in enumerate(self.store.layer_names):
            items.append(ListItem(Label(name), id=f"layer-item-{idx}-{name}"))
        if items:
            await self.mount(*items)
        if preferred and preferred in self.store.layer_names:
            self.index = self.store.layer_names.index(preferred)

    def _selected_name(self) -> Optional[str]:
        if self.index is None:
            return None
        if self.index >= len(self.store.layer_names):
            return None
        return self.store.layer_names[self.index]

    def _emit_selection(self) -> None:
        selection = self.store.selection
        self.post_message(
            SelectionChanged(
                layer_index=selection.layer_index,
                layer_name=self.store.selected_layer_name,
                key_index=selection.key_index,
            )
        )

    # Actions -----------------------------------------------------------
    def action_rename_layer(self) -> None:
        current = self._selected_name()
        if not current:
            return

        def _callback(result: Optional[str]) -> None:
            if result and result != current:
                self._apply_rename(current=current, new_name=result)

        self.app.push_screen(RenameLayerModal(current_name=current), callback=_callback)

    def rename_selected_for_test(self, new_name: str) -> None:
        current = self._selected_name()
        if not current or new_name == current:
            return
        self._apply_rename(current=current, new_name=new_name)

    def action_duplicate_layer(self) -> None:
        current = self._selected_name()
        if not current:
            return
        self.store.duplicate_layer(source_name=current)
        self._refresh(preferred=current)
        self.post_message(StoreUpdated())
        self._emit_selection()

    def action_move_up(self) -> None:
        if self.index is None or self.index == 0:
            return
        self.store.reorder_layer(source_index=self.index, dest_index=self.index - 1)
        self.index -= 1
        self._refresh()
        self.post_message(StoreUpdated())
        self.store.set_active_layer(self.index)
        self._emit_selection()

    def action_move_down(self) -> None:
        if self.index is None or self.index >= len(self.store.layer_names) - 1:
            return
        self.store.reorder_layer(source_index=self.index, dest_index=self.index + 1)
        self.index += 1
        self._refresh()
        self.post_message(StoreUpdated())
        self.store.set_active_layer(self.index)
        self._emit_selection()

    def action_pick_up(self) -> None:
        current = self._selected_name()
        if not current:
            return
        self.store.pick_up_layer(name=current)

    def action_drop(self) -> None:
        if self.index is None:
            return
        self.store.drop_layer(target_index=self.index)
        self._refresh()
        self.post_message(StoreUpdated())
        self.store.set_active_layer(min(self.index, len(self.store.layer_names) - 1))
        self._emit_selection()

    @on(ListView.Highlighted)
    def _handle_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view is not self:
            return
        if self.index is None:
            return
        self.store.set_active_layer(self.index)
        self._emit_selection()

    # ------------------------------------------------------------------
    @on(StoreUpdated)
    def _handle_store_update(self, _: StoreUpdated) -> None:
        self._refresh()

    def _apply_rename(self, *, current: str, new_name: str) -> None:
        self.store.rename_layer(old_name=current, new_name=new_name)
        self._refresh(preferred=new_name)
        self.post_message(StoreUpdated())
        if self.index is not None:
            self.store.set_active_layer(self.index)
        self._emit_selection()
