"""Command discovery and fuzzy search utilities for the palette."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from textual.binding import Binding


@dataclass(frozen=True)
class Command:
    """A palette-executable command."""

    command_id: str
    action: str
    label: str
    description: str
    category: str
    shortcut: str | None
    source: object


class CommandRegistry:
    """Collects commands from Textual bindings and exposes fuzzy search."""

    def __init__(self) -> None:
        self._commands: list[Command] = []
        self._seen_ids: set[str] = set()

    # ------------------------------------------------------------------
    def register_bindings(
        self,
        *,
        source: object,
        bindings: Sequence[Binding],
        category: str,
    ) -> None:
        for binding in bindings:
            action = binding.action
            if not action:
                continue
            namespace = getattr(source, "palette_namespace", source.__class__.__name__).lower()
            raw_identifier = f"{namespace}-{action}"
            safe_identifier = "".join(
                char if char.isalnum() or char in {"-", "_"} else "-" for char in raw_identifier
            ).strip("-")
            command_id = safe_identifier or f"{namespace}-command"
            if command_id in self._seen_ids:
                continue
            label = binding.description or action.replace("_", " ").title()
            shortcut = binding.key
            self._commands.append(
                Command(
                    command_id=command_id,
                    action=action,
                    label=label,
                    description=binding.description or label,
                    category=category,
                    shortcut=shortcut,
                    source=source,
                )
            )
            self._seen_ids.add(command_id)

    # ------------------------------------------------------------------
    @property
    def commands(self) -> tuple[Command, ...]:
        return tuple(self._commands)

    def search(self, query: str) -> list[Command]:
        normalized = query.strip().lower()
        if not normalized:
            return list(self._commands)
        matches: list[Command] = []
        for command in self._commands:
            haystack = " ".join(
                filter(
                    None,
                    [
                        command.label.lower(),
                        command.action.lower(),
                        command.description.lower(),
                        command.command_id.lower(),
                        command.category.lower(),
                    ],
                )
            )
            if normalized in haystack:
                matches.append(command)
        return matches

    def get(self, command_id: str) -> Command | None:
        for command in self._commands:
            if command.command_id == command_id:
                return command
        return None


__all__ = ["Command", "CommandRegistry"]
