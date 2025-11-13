#!/usr/bin/env python3
"""Minimal CLI to capture before/after TUI snapshots with a simulated click."""

from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path
from typing import Any

from textual.widgets import Button

from glove80.tui.app import Glove80TuiApp
from glove80.tui.screens.editor import EditorScreen
from glove80.tui.testing import capture_snapshot
from glove80.tui.widgets.layer_strip import LayerStrip
from glove80.tui.widgets.ribbon import ProjectRibbon


async def _demo(output_dir: Path, width: int, height: int) -> None:
    app = Glove80TuiApp()

    async with app.run_test() as pilot:
        await pilot.resize_terminal(width=width, height=height)
        await _wait_for_editor_ready(app, pilot, width, height)

        before = await _capture_snapshot_with_chrome(app, pilot, output_dir / "before.txt")

        # Open the inspector overlay so the "after" snapshot demonstrates the slide-over
        try:
            ribbon = pilot.app.screen.query_one(ProjectRibbon)
            toggle_button = ribbon.query_one("#toggle-inspector", Button)
            toggle_button.press()
        except Exception:
            await pilot.press("tab")
        await _wait_for_editor_ready(app, pilot, width, height)

        after = await _capture_snapshot_with_chrome(app, pilot, output_dir / "after.txt")

        print("\n=== BEFORE SNAPSHOT ===\n")
        print(before)
        print("\n=== AFTER SNAPSHOT ===\n")
        print(after)


async def _wait_for_editor_ready(
    app: Glove80TuiApp,
    pilot: Any,
    width: int,
    height: int,
    timeout: float = 1.5,
) -> None:
    """Pause until the EditorScreen, ribbon, and layer strip are mounted."""

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        screen = getattr(app, "screen", None)
        size = getattr(app, "size", None)

        screen_ready = isinstance(screen, EditorScreen)
        size_ready = bool(size) and size.width == width and size.height == height

        ribbon_ready = layer_ready = False
        if screen_ready:
            try:
                screen.query_one(ProjectRibbon)
                ribbon_ready = True
            except Exception:
                ribbon_ready = False
            try:
                screen.query_one(LayerStrip)
                layer_ready = True
            except Exception:
                layer_ready = False

        if screen_ready and size_ready and ribbon_ready and layer_ready:
            # Give Textual one more frame to settle layout.
            await pilot.pause()
            return

        await pilot.pause()

    raise RuntimeError("Timed out waiting for Editor UI to settle")


async def _capture_snapshot_with_chrome(
    app: Glove80TuiApp,
    pilot: Any,
    output_path: Path,
    attempts: int = 3,
) -> str:
    """Capture a snapshot, retrying until the ribbon/layer strip appear."""

    for remaining in range(attempts, 0, -1):
        snapshot = capture_snapshot(app)
        if _snapshot_has_chrome(snapshot) or remaining == 1:
            output_path.write_text(snapshot)
            return snapshot
        await pilot.pause()

    return snapshot  # pragma: no cover - defensive


def _snapshot_has_chrome(snapshot: str) -> bool:
    return "Glove80" in snapshot and "+ Layer" in snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("snapshots"),
        help="Directory where before/after snapshot.txt files are written",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=140,
        help="Snapshot terminal width (columns)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=40,
        help="Snapshot terminal height (rows)",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    asyncio.run(_demo(args.output_dir, width=args.width, height=args.height))


if __name__ == "__main__":
    main()
