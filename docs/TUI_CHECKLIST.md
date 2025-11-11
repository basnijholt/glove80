# Glove80 Textual TUI Checklist

Single source of truth for implementing `TUI_DESIGN.md`. Each section groups explicit and implicit requirements plus measurable acceptance criteria. Revisit this checklist before coding and update it whenever the design doc evolves.

_Progress snapshot (2025-11-11): Milestones 1–3 are live (Layer Sidebar, KeyCanvas navigation/copy, validated Key Inspector). BuilderBridge + Features tab currently ship the HRM preview/apply path; the remaining checklist items (cursor/mouse bundles, macro/hold-tap/combo studios, regen/saving flows, palette/search, accessibility polish) are still outstanding._

## Source-of-Truth Guarantees

- **Schema parity first** — Every edit flows through `LayoutPayload` (Pydantic) + `docs/layout_payload.schema.json`.
  - Acceptance criteria:
    - On save, the TUI validates via JSON Schema *and* Pydantic before touching disk.
    - Forms auto-generate field constraints (enums, min/max, required flags) from the exported schema.
- **Spec/build parity** — Feature bundles and smart mutations delegate to existing helpers.
  - Acceptance criteria:
    - `tui/services/builder_bridge.py` only uses `LayoutBuilder`, `LayoutFeatureComponents`, or `merge_components`.
    - Toggling HRM/Cursor/Mouse stacks yields byte-for-byte identical sections as `glove80 generate`.
- **Release artifacts remain write-only**.
  - Acceptance criteria:
    - All writes go through the regen flow; the TUI never edits `layouts/<family>/releases/*.json` directly.
    - Save/export uses the same metadata injection logic as `generator.py` to prevent drift.
- **Deterministic round-trip** — Regen Preview mirrors CLI dry-run output.
  - Acceptance criteria:
    - “Regen Preview” shells out to `uv run glove80 generate --layout <family> --variant <variant> --dry-run` and shows per-section diffs.
    - Users can accept/reject diffs per section before JSON is emitted.

## Layout & Information Architecture

- **Project Ribbon (Header)** — Family/variant picker, file I/O, primary actions.
  - Acceptance criteria:
    - Picker sources variants from `glove80.layouts.family.REGISTRY` via `build_layout`.
    - Buttons: Validate, Regen Preview, Save, Undo, Redo, Theme, Command Palette, Path selector.
- **Editor Workspace (Three panes)**.
  - Layer Sidebar: drag/drop reorder, duplicate, rename, hide/show, “pick up & drop”, provenance badges (HRM/mouse/cursor/custom).
  - Key Canvas: 80-key geometry per layer, keyboard + pointer selection, multi-layer split view for copy/drop.
  - Inspector Tabs: Key, Macro, Hold Tap, Combo, Listener, Features, Advanced, Metadata.
  - Acceptance criteria:
    - Sidebar mutations rewrite `layer_names`, `layers`, and any `LayerRef` usage deterministically.
    - Canvas enforces layer length == 80 and highlights active selection across split view.
  - _Status 2025-11-11: Sidebar + Key Canvas + Key tab are implemented (incl. selection + HRM copy gestures). Macro/HoldTap/Combo/Listener/Advanced/Metadata tabs remain TODO; Features tab currently exposes only HRM preview/apply._
- **Status & Logs Footer** — Dirty flag, active layer, validation counts, async task progress/log stream.
  - Acceptance criteria:
    - Background workers report progress + cancellation states without freezing the UI.
- **Secondary surfaces** — Regen Preview, Command Palette (Ctrl/Cmd+K), Search/Jump panel.
  - Acceptance criteria:
    - Command palette exposes at least: add layer, go to macro, toggle HRM, validate now.
    - Search jumps by key index, layer name, macro/hold tap/combo/listener identifiers.

## Navigation & Input Patterns

- **Keyboard-native UX** per Textual norms.
  - Acceptance criteria:
    - Global shortcuts: `Ctrl/Cmd+K`, `Ctrl/Cmd+S`, `Ctrl/Cmd+Shift+S`, `Ctrl/Cmd+Z`, `Ctrl/Cmd+Shift+Z`, `F5`, `F6`.
    - Canvas shortcuts: arrows/hjkl, `Enter`, `.`, `[`, `]`, `P`, `D`.
- **Pointer support** — optional but polished.
  - Acceptance criteria:
    - Mouse interactions (click, drag/drop) match keyboard operations and emit identical actions in the store log.
- **Command log & undo/redo**.
  - Acceptance criteria:
    - Store tracks named actions (`AddCombo`, `ApplyFeatureBundle`, etc.) and exposes undo/redo stacks with titles for palette usage.

## Theming & Accessibility

- **Theme modes** — Light, Dark, High-contrast, ASCII fallback.
  - Acceptance criteria:
    - Theme switcher updates Textual app theme dynamically and persists user choice per project.
- **Font size & focus outlines**.
  - Acceptance criteria:
    - Users can adjust font scale without reloading; focus is always visible for keyboard navigation.
- **Descriptive labels & ARIA-friendly metadata**.
  - Acceptance criteria:
    - Every key/layer/lister component exposes textual labels for screen readers/log dumps.
- **Terminal capability fallback**.
  - Acceptance criteria:
    - Provide ASCII canvas mode when color depth or braille support is missing; surfaces degrade gracefully (no rendering crashes).

## Data Flow, State & Undo Infrastructure

- **Central store (`tui/state/store.py`)** — action log, selectors, undo/redo, dirty tracking.
  - Acceptance criteria:
    - Undo/redo works across composite actions (e.g., layer rename rewrites refs + names as one transaction).
    - Store exposes query APIs (active layer, key spec, macro list) for widgets + command palette.
- **Observable state inspectors** — debug panels for developers.
  - Acceptance criteria:
    - Action log view shows timestamped actions and payload diffs.
- **Background workers** — CLI commands, validators, schema refresh.
  - Acceptance criteria:
    - Workers never block the main loop; results stream into footer logs and notifications.

## Data Entry, Features & Workflow Support

- **Key behavior editor** — presets + raw JSON fallback.
  - Acceptance criteria:
    - Autocomplete sources layer names, macros, hold taps, combos, keycodes, HRM bindings.
    - Raw JSON editor validates incremental changes and can be diffed per key.
- **Macro studio** (`macros[]`).
  - Acceptance criteria:
    - Enforces `name` uniqueness, `&` prefix, editing of `bindings[]`, `params[]`, `waitMs`, `tapMs`.
- **Hold Tap studio** (`holdTaps[]`).
  - Acceptance criteria:
    - Provides key pickers for `holdTriggerKeyPositions[]` and ensures timing fields ≥ 0.
- **Combo builder** (`combos[]`).
  - Acceptance criteria:
    - Key picker enforces unique positions 0–79; `layers[]` encourages `LayerRef` usage with rename-safe updates.
- **Listener graph editor** (`inputListeners[]`).
  - Acceptance criteria:
    - Visualizes nodes/processors; ensures layer refs resolve and warns on empty `layers[]`.
- **Feature bundles tab**.
  - Acceptance criteria:
    - Toggling HRM/cursor/mouse layers shows diff preview before commit and uses builder bridge to reconcile macros/combos/listeners.
- **Advanced tab** — custom behaviors, devicetree, config/layout parameters, metadata.
  - Acceptance criteria:
    - Editors provide syntax highlighting + optional lint (e.g., `dtc`), enforce JSON types, and surface metadata fields (UUID/parent/title/notes/tags) with read-only guards where immutable.
- **Layer operations**.
  - Acceptance criteria:
    - Rename warns on duplicates and rewrites every reference.
    - Reorder uses drag/drop + shortcuts and keeps `layer_names`/`layers` arrays aligned.
    - Duplicate optionally clones dependent macros.
    - Pick-up/drop operations are undoable single actions.

## Validation, CLI Integration & Regen Flow

- **Schema + semantic validation**.
  - Acceptance criteria:
    - Real-time (debounced) validation runs after edits; blocking errors surface inline and in footer counts.
    - Semantic rules enforced: len(layer_names) == len(layers), layers length 80, unique macro/hold tap names, valid combos/listeners.
- **CLI parity hooks**.
  - Acceptance criteria:
    - Validate button runs `glove80 validate` on exported JSON and streams Rich output into footer log.
    - Regen Preview uses CLI dry-run as described above and offers per-section accept/skip toggles.
- **Save/export**.
  - Acceptance criteria:
    - Save-as allows choosing output path and optionally invoking `glove80 validate path` automatically.
    - Dirty flag resets only after validation + optional regen succeed.

## Integration Points (Existing Code)

- `src/glove80/layouts/builder.py` — authoritative ordering + helper APIs; all feature insertions must flow through here.
- `src/glove80/features/*` + `glove80.layouts.components` — provide bundle components reused by builder bridge.
- `src/glove80/layouts/schema.py` & `docs/layout_payload.schema.json` — feed the form generator + validators.
- `src/glove80/layouts/generator.py` & `glove80.layouts.family.REGISTRY` — drive family/variant picker and regen flows.
- `src/glove80/cli/__init__.py` — Typer commands to invoke for validation/regeneration parity.
- `scripts/export_layout_schema.py` — refresh schema (`just schema`).

## Validation Loop (Fast Inner Dev Cycle)

Leverage the shared Python toolchain to validate relentlessly and commit/push whenever tests are green.

| Step | Command | Purpose |
| --- | --- | --- |
| 1 | `uv sync --dev` | Ensure runtime + dev deps (Textual, Typer, pytest, mypy, ruff) match `pyproject.toml`. |
| 2 | `just schema` | Regenerate `docs/layout_payload.schema.json` whenever dataclasses/specs change. |
| 3 | `uv run textual run src/glove80/tui/app.py --dev` | Launch TUI with hot reload for rapid iteration. |
| 4 | `uv run pytest tests/test_builder.py tests/test_features.py tests/test_cli.py -k tui` | Fast guardrail for builder/state regressions during development. |
| 5 | `just ci` | Full pytest suite with coverage (CI parity). Run before every push. |
| 6 | `uv run glove80 generate --layout <family> --variant <variant> --dry-run` | Compare TUI state against canonical generator output (same command used inside Regen Preview). |
| 7 | `just regen-one <family> <variant>` / `just regen` | Update release artifacts touched by the session; inspect diffs immediately. |

Inner-loop checklist after *every* meaningful change:
1. Run the scoped pytest command (Step 4). If green, stage and consider a commit.
2. When ready for integration or before sharing, run Steps 5–7 sequentially; only push after `just ci` is green.

## Ambiguities & Blockers

- **Textual entry point path** — `TUI_DESIGN.md` references modules like `tui/services/builder_bridge.py`, but no package exists yet. Decision needed on final module layout before coding.
- **Listener graph UX depth** — Design calls for “graph view + processor forms” but does not define the exact Textual widgets (tree vs. canvas). Requires prototyping.
- **Diff granularity in Regen Preview** — Section-by-section diff is required, but tooling (e.g., textual diff viewer) is unspecified. Need to evaluate existing diff widgets vs. custom implementation.
- **Devicetree lint integration** — `dtc` hook is optional; confirm whether to bundle `dtc`, shell out, or offer best-effort lint with graceful failure.
- **Schema refresh cadence** — Document instructs refreshing schema when models change; decide whether TUI triggers this automatically or prompts the user.
