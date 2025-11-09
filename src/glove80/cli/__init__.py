from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..layouts.generator import GenerationResult, available_layouts, generate_layouts
from ..layouts.family import REGISTRY

app = typer.Typer(help="Utilities for working with Glove80 layouts.")
console = Console()


def _print_results(results: list[GenerationResult]) -> None:
    table = Table(title="✨ Layout Generation Results", show_header=True, header_style="bold magenta")
    table.add_column("Layout", style="cyan", no_wrap=True)
    table.add_column("Variant", style="blue")
    table.add_column("Destination", style="white")
    table.add_column("Status", justify="center")

    for result in results:
        status_icon = "✅ updated" if result.changed else "⚪ unchanged"
        status_style = "[green]" if result.changed else "[dim white]"
        table.add_row(
            result.layout,
            result.variant,
            str(result.destination),
            f"{status_style}{status_icon}[/]"
        )

    console.print(table)


@app.command("families")
def families() -> None:
    """List registered layout families and their variants."""

    table = Table(title="🎹 Available Layout Families", show_header=True, header_style="bold cyan")
    table.add_column("Family", style="yellow", no_wrap=True)
    table.add_column("Variants", style="green")

    for registered in REGISTRY.families():
        variants = ", ".join(sorted(registered.family.variants()))
        table.add_row(registered.name, variants)

    console.print(table)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Show the top-level help when no sub-command is provided."""

    if ctx.invoked_subcommand is None:
        help_text = ctx.get_help()
        panel = Panel(help_text, title="[bold cyan]Glove80 Utilities[/]", border_style="cyan")
        console.print(panel)
        raise typer.Exit()


@app.command("generate")
def generate(
    layout: Optional[str] = typer.Option(None, help="Limit regeneration to a single layout family."),
    variant: Optional[str] = typer.Option(None, help="Limit regeneration to a single variant."),
    metadata: Optional[Path] = typer.Option(
        None,
        help="Optional path to a metadata JSON file (useful for layout experiments).",
    ),
    dry_run: bool = typer.Option(False, help="Only compare outputs; do not rewrite files."),
) -> None:
    """Regenerate release JSON artifacts from the canonical sources."""

    if metadata is not None and layout is None:
        raise typer.BadParameter("--metadata requires --layout to be specified")

    results = generate_layouts(layout=layout, variant=variant, metadata_path=metadata, dry_run=dry_run)
    if not results:
        available = ", ".join(available_layouts())
        console.print(f"[bold yellow]⚠️  No results generated.[/] Known layouts: [cyan]{available}[/]")
        raise typer.Exit(code=1)

    _print_results(results)


__all__ = ["app"]
