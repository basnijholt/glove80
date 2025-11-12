"""Project ribbon placeholder."""

from __future__ import annotations

from textual.widgets import Static


class ProjectRibbon(Static):
    """Minimal header showing selected family/variant."""

    def __init__(self, *, current_layout: str, current_variant: str) -> None:
        super().__init__(
            f"Glove80 · layout={current_layout} · variant={current_variant} · Milestone 1 scaffold",
            classes="project-ribbon",
        )
