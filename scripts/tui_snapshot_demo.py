#!/usr/bin/env python3
"""Minimal CLI to capture before/after TUI snapshots with a simulated click."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from glove80.tui.app import Glove80TuiApp
from glove80.tui.testing import capture_snapshot, save_snapshot


async def _demo(output_dir: Path, width: int, height: int) -> None:
    app = Glove80TuiApp()

    async with app.run_test() as pilot:
        await pilot.resize_terminal(width=width, height=height)
        await pilot.pause()

        before = capture_snapshot(app)
        save_snapshot(app, output_dir / "before.txt")

        # Try an obvious action: click the Key Inspector "Apply" button
        try:
            await pilot.click("#apply-form")
        except Exception:
            # If the selector fails (e.g., layout changed), fall back to a harmless key press
            await pilot.press("tab")
        await pilot.pause()

        after = capture_snapshot(app)
        save_snapshot(app, output_dir / "after.txt")

        print("\n=== BEFORE SNAPSHOT ===\n")
        print(before)
        print("\n=== AFTER SNAPSHOT ===\n")
        print(after)


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
