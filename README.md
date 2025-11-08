# Glove80 Layout Toolkit

This repository is the canonical, code-first source of the TailorKey and QuantumTouch Glove80 layouts.  Every
release JSON under `layouts/*/releases` can be regenerated deterministically from the declarative specs and metadata
checked into `src/glove80`.

## Highlights
- TailorKey and QuantumTouch live in Python packages with typed specs, factories, and regression tests (see `docs/`).
- Metadata travels with the package (`src/glove80/layouts/*/metadata.json`), so the CLI and library always agree on
  UUIDs, release notes, and output paths.
- A Typer-powered CLI (`python -m glove80 generate …`) replaces ad-hoc scripts and keeps the regeneration workflow
  uniform across layouts.
- Release artifacts are grouped under `layouts/<layout>/releases`, keeping the repo root clean while preserving the
  published JSON verbatim.

## Quick Start
1. Install dependencies (the repo uses [uv](https://github.com/astral-sh/uv)):
   ```bash
   uv sync
   ```
2. Regenerate every release JSON:
   ```bash
   just regen
   ```
3. Run the full regression suite (per-layer tests + layout parity checks):
   ```bash
   just ci
   ```
4. Need a single variant? Use the CLI directly:
   ```bash
   python -m glove80 generate --layout tailorkey --variant mac
   ```

`just --list` shows the available helper tasks.

## Repository Layout
```
.
├─ layouts/                     # checked-in release JSON
│  ├─ tailorkey/releases/
│  └─ quantum_touch/releases/
├─ docs/                        # architecture + per-layout guides
├─ src/glove80/
│  ├─ cli/                      # Typer CLI
│  ├─ layouts/                  # packaged metadata + generator helpers
│  ├─ tailorkey/                # TailorKey specs, layers, layout builder
│  └─ quantum_touch/            # QuantumTouch specs, layers, layout builder
└─ tests/                       # split by layout family
```

- Read `docs/architecture.md` for a walkthrough of the data flow and regeneration pipeline.
- `docs/tailorkey.md` and `docs/quantum_touch.md` explain how each layout family is structured, the available layers,
  and the steps for adding new variants.

## CI Contract
`.github/workflows/ci.yml` runs the same steps you do locally:
- `just regen` must leave `layouts/*/releases` unchanged or the build fails, proving the checked-in JSON matches the
  current code.
- `just ci` (`uv run pytest`) covers every layer factory plus whole-layout comparisons.
- Pull requests are required to keep both commands clean, so regeneration + tests are the only gatekeepers.

## Contributing
1. Edit specs or metadata, re-run `just regen`, and inspect the resulting diffs under `layouts/`.
2. Extend/adjust the targeted per-layer tests under `tests/<layout>/` when you change behavior.
3. Document intentional changes in the relevant guide under `docs/` so future contributors understand the rationale.
