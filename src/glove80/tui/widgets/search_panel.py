"""Lightweight search/jump panel used by the TUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, Sequence

from textual import on
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Input, Static

from ..messages import JumpRequested, SearchHighlights, SearchPanelClosed
from ..state import LayoutStore


MatchKind = Literal["key", "macro", "listener"]


@dataclass
class SearchResult:
    kind: MatchKind
    label: str
    layer_index: int
    key_index: int
    metadata: dict[str, str]


class SearchPanel(Horizontal):
    """Slash-invoked search bar with F3 navigation."""

    BINDINGS = [
        Binding("enter", "jump", "Jump", show=False),
        Binding("escape", "close", "Close Search", show=False),
    ]

    def __init__(self, *, store: LayoutStore) -> None:
        super().__init__(id="search-panel", classes="search-panel hidden")
        self.store = store
        self._input = Input(placeholder="Search keys, macros, listeners…", id="search-input")
        self._status = Static("", id="search-status")
        self._results: list[SearchResult] = []
        self._cursor = -1
        self._visible = False
        self._previous_focus: Widget | None = None

    def compose(self):  # type: ignore[override]
        yield self._input
        yield self._status

    # ------------------------------------------------------------------
    def open(self) -> None:
        if self._visible:
            self._input.value = ""
        self._visible = True
        self.remove_class("hidden")
        self._previous_focus = self.screen.focused if self.screen else None
        self._input.value = ""
        self._status.update("Type to search…")
        self._results.clear()
        self._cursor = -1
        self.call_after_refresh(lambda: self._input.focus())
        self._broadcast_highlights([])

    def close(self) -> None:
        if not self._visible:
            return
        self._visible = False
        self.add_class("hidden")
        self._results.clear()
        self._cursor = -1
        self._restore_previous_focus()
        self._broadcast_highlights([])
        self.post_message(SearchPanelClosed())

    def action_close(self) -> None:  # noqa: D401
        self.close()

    def action_jump(self) -> None:  # noqa: D401
        self._jump(self._cursor if self._cursor >= 0 else 0)

    # ------------------------------------------------------------------
    def next_result(self, delta: int) -> None:
        if not self._results:
            return
        self._cursor = (self._cursor + delta) % len(self._results)
        self._jump(self._cursor)

    @property
    def is_open(self) -> bool:
        return self._visible

    # ------------------------------------------------------------------
    @on(Input.Changed)
    def _handle_input_changed(self, event: Input.Changed) -> None:
        if event.input is not self._input:
            return
        self._results = self._build_results(event.value)
        self._cursor = -1
        self._status.update(f"{len(self._results)} match(es)")
        self._broadcast_highlights(self._results)

    @on(Input.Submitted)
    def _handle_input_submitted(self, event: Input.Submitted) -> None:
        if event.input is not self._input:
            return
        self.action_jump()

    # ------------------------------------------------------------------
    def _build_results(self, query: str) -> list[SearchResult]:
        normalized = query.strip().lower()
        if not normalized:
            return []
        results: list[SearchResult] = []
        results.extend(self._find_keys(normalized))
        results.extend(self._find_macros(normalized))
        results.extend(self._find_listeners(normalized))
        return results

    def _find_keys(self, needle: str) -> list[SearchResult]:
        matches: list[SearchResult] = []
        for layer_index, record in enumerate(self.store.state.layers):
            for key_index, slot in enumerate(record.slots):
                value = str(slot.get("value", ""))
                params = str(slot.get("params", ""))
                if needle in value.lower() or needle in params.lower():
                    label = f"Key #{key_index:02d} · {record.name} · {value or '—'}"
                    matches.append(
                        SearchResult(
                            kind="key",
                            label=label,
                            layer_index=layer_index,
                            key_index=key_index,
                            metadata={},
                        )
                    )
        return matches

    def _find_macros(self, needle: str) -> list[SearchResult]:
        matches: list[SearchResult] = []
        for macro in self.store.list_macros():
            name = str(macro.get("name", ""))
            if not name:
                continue
            description = str(macro.get("description", ""))
            haystack = f"{name} {description}".lower()
            if needle not in haystack:
                continue
            target_layer, target_key = self._reference_location(self.store.find_macro_references(name))
            label = f"Macro · {name}"
            matches.append(
                SearchResult(
                    kind="macro",
                    label=label,
                    layer_index=target_layer,
                    key_index=target_key,
                    metadata={"macro": name},
                )
            )
        return matches

    def _find_listeners(self, needle: str) -> list[SearchResult]:
        matches: list[SearchResult] = []
        for listener in self.store.list_listeners():
            code = str(listener.get("code", ""))
            if not code:
                continue
            description = str(listener.get("description", ""))
            haystack = f"{code} {description}".lower()
            if needle not in haystack:
                continue
            target_layer, target_key = self._reference_location(self.store.find_listener_references(code))
            label = f"Listener · {code}"
            matches.append(
                SearchResult(
                    kind="listener",
                    label=label,
                    layer_index=target_layer,
                    key_index=target_key,
                    metadata={"listener": code},
                )
            )
        return matches

    def _reference_location(
        self,
        references: Mapping[str, Sequence[Mapping[str, int | str]]],
    ) -> tuple[int, int]:
        keys = references.get("keys", ())
        if keys:
            entry = keys[0]
            return int(entry.get("layer_index", 0)), int(entry.get("key_index", 0))
        selection = self.store.selection
        return max(selection.layer_index, 0), max(selection.key_index, 0)

    def _jump(self, index: int) -> None:
        if not self._results:
            return
        index = max(0, min(index, len(self._results) - 1))
        self._cursor = index
        result = self._results[index]
        metadata = dict(result.metadata)
        if result.kind == "macro":
            metadata.setdefault("macro", "")
        if result.kind == "listener":
            metadata.setdefault("listener", "")
        self.post_message(
            JumpRequested(
                layer_index=result.layer_index,
                key_index=result.key_index,
                jump_type=result.kind,
                metadata=metadata,
            )
        )
        self._status.update(f"Jumped to {result.label}")

    def _broadcast_highlights(self, results: Iterable[SearchResult]) -> None:
        active_layer = max(self.store.selection.layer_index, 0)
        indices = tuple(res.key_index for res in results if res.kind == "key" and res.layer_index == active_layer)
        self.post_message(SearchHighlights(layer_index=active_layer, indices=indices))

    def _restore_previous_focus(self) -> None:
        target = self._previous_focus
        self._previous_focus = None
        if target is None:
            return
        try:
            target.focus()
        except Exception:  # pragma: no cover - defensive
            pass


__all__ = ["SearchPanel", "SearchResult"]
