"""Protocol and registry for layout families."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Protocol


class LayoutFamily(Protocol):
    """Common interface every layout family must implement."""

    name: str

    def variants(self) -> Iterable[str]:
        """Return the iterable of supported variant identifiers."""

    def build(self, variant: str) -> dict:
        """Build the layout payload for the requested variant."""

    def metadata_key(self) -> str:
        """Return the metadata namespace used in sources/layouts.<family>."""


@dataclass(frozen=True)
class RegisteredFamily:
    name: str
    family: LayoutFamily


class LayoutRegistry:
    """Simple registry for layout families."""

    def __init__(self) -> None:
        self._families: Dict[str, LayoutFamily] = {}

    def register(self, family: LayoutFamily) -> None:
        if family.name in self._families:
            raise ValueError(f"Duplicate layout family '{family.name}'")
        self._families[family.name] = family

    def get(self, name: str) -> LayoutFamily:
        return self._families[name]

    def families(self) -> Iterable[RegisteredFamily]:
        return (RegisteredFamily(name, family) for name, family in sorted(self._families.items()))


REGISTRY = LayoutRegistry()

__all__ = ["LayoutFamily", "LayoutRegistry", "REGISTRY", "RegisteredFamily"]
