from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from glove80.layouts.family import REGISTRY
from glove80.layouts.generator import GenerationResult, available_layouts, generate_layouts
from glove80.layouts.parse import parse_typed_sections

from pathlib import Path

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
        table.add_row(result.layout, result.variant, str(result.destination), f"{status_style}{status_icon}[/]")

    console.print(table)
    summary = ", ".join(f"{r.layout}:{r.variant}" for r in results)
    if summary:
        console.print(summary)


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
        raise typer.Exit


@app.command("generate")
def generate(
    layout: str | None = typer.Option(None, help="Limit regeneration to a single layout family."),
    variant: str | None = typer.Option(None, help="Limit regeneration to a single variant."),
    metadata: Path | None = typer.Option(
        None,
        help="Optional path to a metadata JSON file (useful for layout experiments).",
    ),
    dry_run: bool = typer.Option(False, help="Only compare outputs; do not rewrite files."),
    out: Path | None = typer.Option(
        None,
        help="Override destination path (requires --layout and --variant). If provided with --metadata, only the destination is overridden.",
    ),
) -> None:
    """Regenerate release JSON artifacts from the canonical sources."""
    if metadata is not None and layout is None:
        msg = "--metadata requires --layout to be specified"
        raise typer.BadParameter(msg)

    if out is not None and (layout is None or variant is None):
        raise typer.BadParameter("--out requires both --layout and --variant")

    results = generate_layouts(
        layout=layout,
        variant=variant,
        metadata_path=metadata,
        dry_run=dry_run,
        out=out,
    )
    if not results:
        available = ", ".join(available_layouts())
        console.print(f"[bold yellow]⚠️  No results generated.[/] Known layouts: [cyan]{available}[/]")
        raise typer.Exit(code=1)

    _print_results(results)


__all__ = ["app"]


@app.command("typed-parse")
def typed_parse(
    path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help="Path to a layout JSON file."),
) -> None:
    """Parse a layout JSON into typed Pydantic models and report a summary."""
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    payload, macros, hold_taps, combos, listeners = parse_typed_sections(data)

    table = Table(title=f"Typed Parse: {path.name}", show_header=True, header_style="bold green")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right")
    table.add_row("layer_names", str(len(payload.layer_names)))
    table.add_row("macros", str(len(macros)))
    table.add_row("holdTaps", str(len(hold_taps)))
    table.add_row("combos", str(len(combos)))
    table.add_row("inputListeners", str(len(listeners)))
    console.print(table)

    console.print("[green]Validation OK[/] — sections parsed into typed models.")


# Friendly alias for typed-parse
@app.command("validate")
def validate(
    path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help="Path to a layout JSON file."),
) -> None:
    """Alias for ``typed-parse`` with a more descriptive name."""
    typed_parse(path)
