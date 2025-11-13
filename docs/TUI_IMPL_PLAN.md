# Glove80 TUI Implementation Plan

This plan operationalizes `TUI_DESIGN.md` and `docs/TUI_CHECKLIST.md` into a concrete Textual architecture, phased delivery milestones, and a scoped testing strategy. It synthesizes the agent surveys (repository map, validation loop, CLI hook guidance, testing strategy) to keep implementation aligned with the existing Glove80 toolchain.

_Progress snapshot (2025-11-12): Milestones 1–3 complete (foundation, editing core, Key Inspector). Macro Studio (Milestone 4) is delivered with full CRUD + pilot coverage, and Workstream 1 of Milestone 5 (BuilderBridge + HRM preview/apply) is also shipped. Remaining milestones—HoldTap/Combo/Listener studios, cursor/mouse bundles, validation/regen/save flow, command palette/search, accessibility polish—are pending._

## 1. Module Architecture (src/glove80/tui)

| Module / Path | Responsibilities | Checklist & Design Alignment |
| --- | --- | --- |
| `app.py` | Defines `Glove80TuiApp` (`textual.app.App`), registers global key bindings (`Ctrl/Cmd+K/S`, `F5/F6`, undo/redo), initializes the central store, mounts main/regen screens, handles theme persistence and telemetry logging. | Keyboard-native UX, theming, observable state (`TUI_DESIGN.md §2, §3.1, §9`; `TUI_CHECKLIST.md lines 45-72`). |
| `screens/editor.py` | Implements the three-pane workspace (Project Ribbon, Layer Sidebar, Key Canvas, Inspector tabs) plus Footer/Status bar. Coordinates selection context and passes actions to the store. | IA & widget tree requirements (`TUI_DESIGN.md §3, §4`; `TUI_CHECKLIST.md lines 24-44`). |
| `screens/regen_preview.py` | Runs CLI dry-run via worker, renders section-by-section diffs (layers, macros, hold taps, combos, listeners, metadata), supports accept/skip per section, writes reconciled payload. | Deterministic regen preview (`TUI_DESIGN.md §5-8`; `TUI_CHECKLIST.md lines 117-130`). |
| `widgets/ribbon.py` | Project ribbon with family/variant picker (using `glove80.layouts.family.REGISTRY`), file loader, Validate/Regen/Save/Undo/Redo/Theme/Palette buttons. | Header obligations (`TUI_DESIGN.md §3.1.1`; `TUI_CHECKLIST.md lines 26-29`). |
| `widgets/layer_sidebar.py` | Lists `layer_names`, handles drag/drop reorder, rename, duplicate, pick-up/drop, provenance badges, and keeps `LayerRef` references updated. | Layer operations & provenance (`TUI_DESIGN.md §3.1.2, §7.7`; `TUI_CHECKLIST.md lines 30-37, 104-115`). |
| `widgets/key_canvas.py` | 80-key geometry with keyboard/pointer navigation, multi-layer split view, copy/drop interactions, visual focus outlines, ASCII fallback. | Key canvas UX & accessibility (`TUI_DESIGN.md §3.1.2, §7.1`; `TUI_CHECKLIST.md lines 45-72`). |
| `widgets/inspector/*` | Tab modules (Key, Macro, Hold Tap, Combo, Listener, Features, Advanced, Metadata) with schema-driven forms, autocomplete, raw JSON fallbacks, cross-links to selection. | Schema parity + workflow studios (`TUI_DESIGN.md §5-7`; `TUI_CHECKLIST.md lines 86-115`). |
| `widgets/footer.py` | Status/log bar showing dirty flag, active layer, validation counts, background worker progress, undo history glimpses. | Footer obligations (`TUI_DESIGN.md §3.1.3, §8`; `TUI_CHECKLIST.md lines 37-40, 73-85`). |
| `screens/palette.py`, `screens/search.py` | Command palette (Ctrl/Cmd+K) and Search/Jump panel for keys/layers/macros/combos/listeners. | Secondary surfaces (`TUI_DESIGN.md §3.2`; `TUI_CHECKLIST.md lines 40-44`). |
| `state/store.py` | Normalized `LayoutPayload` store, action dispatch, undo/redo log, dirty tracking, selectors, semantic validation hooks. | Observable state + validators (`TUI_DESIGN.md §5, §7, §9`; `TUI_CHECKLIST.md lines 73-85, 117-123`). |
| `state/actions.py`, `state/selectors.py`, `state/history.py` | Action definitions (`AddCombo`, `ApplyFeatureBundle`, etc.), query helpers, undo batching. | Command log + undo/redo requirements (`TUI_CHECKLIST.md lines 55-57, 75-78`). |
| `services/builder_bridge.py` | Wraps `LayoutBuilder`, `LayoutFeatureComponents`, `merge_components` to preview/apply HRM/Cursor/Mouse bundles and reconcile diffs back into the store. | Spec/build parity + feature bundles (`TUI_DESIGN.md §6`; `TUI_CHECKLIST.md lines 11-15`). |
| `services/schema_loader.py` | Loads `docs/layout_payload.schema.json`, exposes form metadata, refresh command triggers `scripts/export_layout_schema.py`. | Schema refresh flow (`TUI_DESIGN.md §5`; `TUI_CHECKLIST.md lines 7-15, 159-165`). |
| `services/validator.py` | Debounced JSON Schema + Pydantic validation plus semantic checks (layer counts, unique names, ranges), surfaces inline + footer errors. | Validation obligations (`TUI_DESIGN.md §5.3, §8`; `TUI_CHECKLIST.md lines 117-123`). |
| `services/cli_runner.py` | Runs `uv run glove80 validate` / `generate --dry-run`, streams Rich-formatted logs, returns structured diff payloads while keeping UI responsive via Textual workers. | Regen/validate background flow (`TUI_DESIGN.md §8-9`; `TUI_CHECKLIST.md lines 117-130`). |
| `services/task_runner.py` | Thin wrapper over Textual workers with task registry/cancellation hooks feeding Footer progress indicators. | Background task UX (`TUI_DESIGN.md §8, §9`; `TUI_CHECKLIST.md lines 37-40`). |
| `services/persistence.py` | Load/save JSON, metadata injection, prompts for Save-As, optional auto-validate after save. | Release artifact guarantees (`TUI_DESIGN.md §8`; `TUI_CHECKLIST.md lines 15-23, 128-130`). |
| `utils/keyboard.py`, `utils/theme.py`, `utils/geometry.py` | Centralize key binding definitions, theme palettes (light/dark/high-contrast/ASCII), and key-layout math for canvas + listeners. | Accessibility & keyboard patterns (`TUI_CHECKLIST.md lines 45-72`). |
| `tui/__main__.py` (optional) | Allows `python -m glove80.tui` / `textual run glove80.tui.app:Glove80TuiApp` for development. | Supports validation loop step 3 (`TUI_CHECKLIST.md lines 145-153`). |

### Event & State Flow Summary

```
Widget Input (keyboard/mouse/palette)
   → Textual Message (e.g., UpdateKeyBehavior)
      → state.actions.dispatch()
         → store.reduce() + history.push()
            → selectors notify subscribers (widgets, footer)
               → validators enqueue schema/semantic jobs (task_runner)
                  → CLI/services emit events/logs back into store/UI
```

This single-store approach guarantees deterministic undo/redo, consistent provenance tagging, and central logging for the command palette while keeping UI components dumb rendering surfaces.

### CLI Integration Hook

- `src/glove80/cli/__init__.py` gains `@app.command("tui")` that lazy-imports `glove80.tui.app.Glove80TuiApp`, performs basic terminal checks (`isatty`, `$TERM`), and runs the Textual app. Missing dependencies or unsupported terminals print Rich error output and exit non-zero, per agent recommendations.
- Optional `glove80/tui/__main__.py` enables `python -m glove80.tui` and mirrors the same checks.
- Documentation (`README.md`, `docs/TUI_CHECKLIST.md`) should mention installation/run commands (`glove80 tui`, `uv run textual run src/glove80/tui/app.py --dev`).

## 2. Phased Milestones (Frequent Commits)

Each milestone is intentionally narrow to support the “commit/push whenever tests are green” cadence. Acceptance criteria map directly back to checklist items.

1. **Foundation & Ribbon (Milestone 1)**
   - Deliverables: project scaffolding, `Glove80TuiApp`, `state/store` hydration, Project Ribbon with picker + stubbed actions, footer shell.
   - Acceptance: `glove80 tui` launches read-only view of default layout; ribbon buttons render; `uv run pytest tests/tui/test_foundation.py` passes.
   - _Status 2025-11-11: ✅ Complete (landed with initial Textual scaffold)._

2. **Layer Sidebar & Undo Core (Milestone 2)**
   - Deliverables: `LayerSidebar` with rename/reorder/duplicate/pick-up/drop, undo/redo stack, provenance badges.
   - Acceptance: Layer rename updates all `LayerRef` references; undo/redo collapses composite actions; tests `tests/tui/test_sidebar.py` cover ref rewrites + history.
   - _Status 2025-11-11: ✅ Complete (sidebar + undo live)._

3. **Key Canvas & Inspector Key Tab (Milestone 3)**
   - Deliverables: 80-key canvas with keyboard/pointer navigation, Key inspector tab with presets + raw JSON editor, focus outlines, footer selection info.
   - Acceptance: Shortcuts (`arrow/hjkl`, `Enter`, `.`, `[`, `]`, `P/D`) work; schema-driven editor enforces constraints; unit + pilot tests (`test_canvas.py`, `test_key_tab.py`) pass.
   - _Status 2025-11-11: ✅ Complete (current build satisfies these acceptance tests)._

4. **Studios & Command Surfaces (Milestone 4)**
   - Deliverables: Macro/Hold Tap/Combo/Listener tabs, command palette, Search/Jump panel, cross-linking (jump from key to macro, etc.).
   - Acceptance (ordered, each must land with unit + pilot coverage):
     1. **Macro Studio – ✅ 2025‑11‑12**: `LayoutStore.list/add/update/rename/delete/find_macro_references` snapshot every mutation, rename rewrites all references, delete blocked unless forced cleanup. Inspector MacroTab (list + detail) emits `StoreUpdated`/`FooterMessage`, and `tests/tui/integration/test_macro_tab.py` exercises create → bind → rename → undo.
     2. **HoldTap Studio – ✅ 2025‑11‑12**: CRUD parity with macros (timings ≥ 0, `holdTriggerKeyPositions` 0–79 deduped). Inspector tab mirrors MacroTab UX, includes key picker, and pilot `tests/tui/integration/test_hold_tap_tab.py` covers create → bind → rename → delete/undo. Store API exposes references and blocks delete while in use.
     3. **Combo Studio – ✅ 2025‑11‑12**: CRUD enforces unique names + trigger chords, ensures `keyPositions` and `LayerRef` targets valid, and rename rewrites references. UI provides chord picker + layer scope chips. Tests `tests/tui/unit/test_combos.py` + `tests/tui/integration/test_combo_tab.py` cover conflicts, rename propagation, and undo/redo.
     4. **Listener Studio – ✅ 2025‑11‑12**: Store exposes listener CRUD/reference APIs with unique `code` validation and delete guard. Inspector ListenerTab lists listeners with ref counts, detail pane edits processors/nodes/layers, and pilot `tests/tui/integration/test_listener_tab.py` verifies create/edit/delete plus reference blocking.
     5. **Command Palette & Search/Jump – 🚧**: Global registry powers Ctrl/Cmd+K palette with commands for layer ops, studio focus, bundle toggles, validation/regen/save, undo/redo, and search launches Jump panel for keys/layers/macros/hold taps/combos/listeners. Palette/Jump actions must dispatch store mutations (or selection events), emit footer messages, and ship with integration tests (`test_command_palette.py`, `test_search_panel.py`).
   - _Status 2025-11-12: 🚧 Command Palette & Search/Jump pending; studios ✅._

5. **Feature Bundles & Builder Bridge (Milestone 5)**
   - Deliverables: `services/builder_bridge`, Features tab diff preview, Layer provenance badges autopopulated, action log inspector.
   - Acceptance: Toggling HRM/mouse/cursor layers produces diffs identical to `LayoutBuilder`; diff preview must be accepted before commit; builder bridge tests compare outputs to known fixtures.
   - _Status 2025-11-11: ✅ HRM preview/apply shipped (BuilderBridge + Features tab); cursor/mouse bundles + provenance + action log inspector still pending._

6. **Validation, Regen Preview & Save Flow (Milestone 6)**
   - Deliverables: Debounced schema + semantic validators, CLI Validate/Regen buttons, Regen Preview screen with accept/skip, Save/Save-As plus optional auto-validate, CLI command wiring.
   - Acceptance: `uv run glove80 generate --layout … --variant … --dry-run` is invoked via CLI runner; regen diffs show per section; acceptance updates store; integration tests `test_regen_preview.py`, `test_validation_messaging.py` pass; README updated.
   - _Status 2025-11-11: 🚧 Not started._

7. **Polish & Accessibility (Milestone 7)**
   - Deliverables: Theme switcher (light/dark/high-contrast/ASCII), font scaling, focus outlines, advanced tab (custom behaviors, devicetree, config/layout parameters, metadata), final documentation updates.
   - Acceptance: Accessibility checklist satisfied; final `just ci` + `just regen` green; `docs/TUI_CHECKLIST.md` cross-checked with implementation.
   - _Status 2025-11-11: 🚧 Not started._

## 3. Focused Testing Strategy

The agent-derived test strategy is adopted verbatim, emphasizing fast unit tests and Textual Pilot integration tests:

### Directory Layout

```
tests/tui/
├── conftest.py          # Pilot harness, sample payload fixtures, CLI mocks
├── unit/
│   ├── test_store.py
│   ├── test_builder_bridge.py
│   └── test_validator.py
├── integration/
│   ├── test_app_boot.py
│   ├── test_keyboard_navigation.py
│   ├── test_layer_operations.py
│   ├── test_regen_preview.py
│   └── test_validation_messaging.py
└── snapshots/          # Optional snapshot outputs (pilot render dumps)
```

### Key Coverage Areas

- **Store / Actions**: Ensure rename/reorder/pick-up/drop update `LayerRef`s and act as single undoable transactions; confirm dirty flag + selectors.
- **Builder Bridge**: Unit tests compare feature bundle diffs to `LayoutBuilder` results; integration tests verify diff previews before acceptance.
- **Validators**: Schema + semantic errors surfaced inline and in footer; debounced worker scheduling respects idle windows.
- **Pilot Suites**: Cover app boot, keyboard shortcuts, layer sidebar operations, regen preview CLI delegation/mocking, validation messaging, command palette.
- **Snapshots**: Capture stable surfaces (header layout, diff dialog) with sanitized timestamps to detect accidental UI regressions.

### Fixtures & Mocking

- `sample_payload` fixture loads TailorKey v4.2h release for parity tests.
- `minimal_payload` fixture provides a single-layer layout for unit speed.
- `pilot_app` fixture wraps Textual `AppTest`/`Pilot` to drive UI interactions deterministically.
- `fake_cli_runner` fixture monkeypatches `services/cli_runner` to assert `uv run glove80 …` arguments and feed deterministic dry-run output, keeping CI hermetic.

### CI Hooks

- Add `just test-tui` target (`uv run pytest tests/tui --cov=src/glove80/tui --cov-fail-under=85`).
- Ensure standard `just ci` invokes `just test-tui` or expands its glob to include new tests.
- Document `uv run pytest tests/tui -k regen` as the quick guardrail for regen flows.

## 4. Integration Dependencies & Open Questions

- **Schema refresh automation**: Decide whether to ship a “Refresh Schema” command that runs `just schema` or prompt the user to do so manually; current plan assumes manual invocation (`TUI_CHECKLIST.md lines 145-149`).
- **Listener graph UX**: Need to choose between adjacency-table vs. mini-graph widget for `ListenerTab` (design doc leaves this open).
- **Diff viewer implementation**: Evaluate Textual’s built-in diff widgets vs. a custom delta renderer for Regen Preview (risk noted in checklist).
- **Devicetree linting**: Determine whether to bundle `dtc` or provide best-effort linting with graceful failure when the binary is missing.

Tracking these questions early ensures we extend the plan without violating deterministic guarantees or the frequent-commit workflow.

---

With this architecture, milestone map, and testing strategy in place, we can proceed into Milestone 1 immediately: scaffold the `tui` package, integrate the `glove80 tui` command, and land the foundation tests in rapid, test-backed commits.
