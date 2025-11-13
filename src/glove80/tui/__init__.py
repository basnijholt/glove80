"""Textual TUI scaffolding for Glove80 (Milestone 1)."""

from __future__ import annotations

from typing import Optional

from .app import Glove80TuiApp

__all__ = ["Glove80TuiApp", "run_tui"]


def run_tui(*, layout: Optional[str] = None, variant: Optional[str] = None, devtools: bool = False) -> None:
    """Launch the minimal Textual application.

    Parameters mirror the CLI options even though the Milestone 1 shell does not yet
    load specific layouts. This keeps the interface stable for future milestones.
    """

    app = Glove80TuiApp(initial_layout=layout, initial_variant=variant, enable_devtools=devtools)
    app.run()
