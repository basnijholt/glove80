# Glove80 Textual TUI Layout Editor Design (Canonical Plan)

This document is the single source of truth for the upcoming Textual (Python) TUI that edits Glove80 layouts. Every requirement below is derived from the checked-in Python toolchain (`src/glove80`), the exported JSON schema at `docs/layout_payload.schema.json`, and the existing CLI workflows (`uv run glove80 …`, `just regen`, `just ci`).

> **Instructions for agents**: Before making changes, read this file end-to-end, follow its requirements, and record any new decisions, deviations, or discoveries back into this document (append brief dated notes in the relevant section). Treat it as a living blueprint.

> **Progress note (2025-11-12)**: Milestones 1–3 are live in `tui/` (LayerSidebar, KeyCanvas navigation/copy, validated Key Inspector). Macro Studio shipped with full CRUD, undo/redo, and Textual pilot coverage, and the Features tab previews/applies HRM bundles via the BuilderBridge service. HoldTap/Combo/Listener studios plus Command Palette/Search are next. Keep `docs/TUI_CHECKLIST.md` and `docs/TUI_IMPL_PLAN.md` in sync with any changes captured here.

IMPORTANT: Also make sure to commit often and run the tests with `uv run pytest`!

## 1. Source-of-Truth Context & Guarantees

| Concern | Canonical Location | TUI Obligation |
| --- | --- | --- |
| Specs, macros, combos, hold taps | `src/glove80/families/<family>/specs/` | Never invent behavior shapes—read/write through the dataclasses already used to generate releases. |
| Feature bundles (HRM, cursor, mouse, thumb layers) | `src/glove80/features/` + `glove80.layouts.components` | Invoke the same helpers (via `LayoutBuilder` or `merge_components`) so macros/combos/listeners stay in sync. |
| Layout assembly + registry | `src/glove80/layouts/builder.py`, `.../generator.py`, `.../family.py` | Mirror the builder’s ordering rules, metadata injection, and dry-run comparison before writing JSON. |
| Release artifacts | `layouts/<family>/releases/*.json` | Treat them as outputs only—never hand-edit; regenerate via the CLI after TUI changes. |
| Schema | `docs/layout_payload.schema.json` exported by `scripts/export_layout_schema.py` | Validate and drive forms from this schema; refresh whenever models change. |
| Tests | `tests/<family>/…`, `tests/test_builder.py`, etc. | Assume `just ci` enforces parity; TUI workflows must not introduce nondeterminism. |

## 2. Design Principles (Repo-Aligned)
1. **Schema parity first** – All edits flow through `LayoutPayload` (Pydantic) and the exported JSON schema; saves fail fast if validation fails.
2. **Spec/build parity** – Any “smart” operation (mouse stack, HRM, cursor, thumb behavior, feature bundle) delegates to `LayoutBuilder` helpers or `LayoutFeatureComponents` so the TUI can never diverge from `glove80 generate`.
3. **Deterministic round-trip** – “Regen Preview” shells out to `uv run glove80 generate --layout <family> --variant <variant> --dry-run` and shows per-section diffs before writing.
4. **Keyboard-native UX** – Inspired by Textual’s strengths: command palette, shortcuts, focus outlines, and optional pointing device support.
5. **Observable state** – Central store with undo/redo, action log, and debug inspectors so layout authors can audit every mutation.
6. **Single doc, family-agnostic** – TailorKey, Default, QuantumTouch, Glorious Engrammer, and future families all use the same `LayoutPayload`; examples reference real data but the UI must remain generic.

## 3. Information Architecture & Layout

### 3.1 Primary Surfaces
1. **Project Ribbon (Header)** – Family/variant picker (`glove80.build_layout`), file loader, output path selector, primary actions (Validate, Regen Preview, Save, Undo/Redo, Theme, Command Palette). Mirrors CLI workflows from `README.md`.
2. **Editor Workspace** – Three-pane layout:
   - **Layer Sidebar** (left) – Renders `layer_names[]`, supports drag/drop reorder, duplicate, rename, hide/show, “pick up & drop” interactions, and badges showing feature provenance (HRM/mouse/cursor/custom). Layer actions update references (`LayerRef`) everywhere.
   - **Key Canvas** (center) – 80-key grid per layer (tailored to Glove80 geometry). Click or navigate via keyboard to inspect/modify key behaviors; multi-layer split view available for copy/drop operations.
   - **Inspector Tabs** (right) – Context-aware forms: Key, Macro, Hold Tap, Combo, Listener, Features (builder toggles), Advanced (custom behaviors/device tree/config/layout parameters), Metadata.
     - _Note (2025-11-12): Key tab + validation/autocomplete are implemented, MacroTab is feature-complete (list/detail editor + pilot tests), and a minimal Features tab previews/applies HRM bundles via BuilderBridge; HoldTap/Combo/Listener/Advanced/Metadata tabs remain TODO._
3. **Status & Logs (Footer)** – Shows dirty flag, active layer, validation counts, background task progress (e.g., regen, CLI validation), and streaming logs.

### 3.2 Secondary Surfaces
- **Regen Preview Screen** – Section-by-section diff between current TUI state and CLI dry-run output; user decides whether to accept generator results or keep edits per section.
- **Command Palette (Ctrl/Cmd+K)** – Fuzzy action runner (add layer, go to macro, toggle HRM bundle, validate now, etc.).
- **Search/Jump Panel** – Jump to key index (0–79), layer by name, macro/hold tap/combo by name, or listener node by code.

### 3.3 ASCII Layout Sketch
```
┌──────────────────────────── Project Ribbon ─────────────────────────────┐
│ Family/Variant ▾ | Path ▾ | Validate | Regen | Save | Undo/Redo | …     │
├─────────────┬───────────────────────────┬───────────────────────────────┤
│ Layer List  │        Key Canvas         │        Inspector Tabs        │
│ (reorder,   │  (active layer grid with  │  [Key][Macro][HoldTap][…]    │
│ rename,     │  key legends + selection) │  forms fed by JSON schema    │
│ pick up)    │                           │                               │
├─────────────┴───────────────────────────┴───────────────────────────────┤
│ Status / Validation / Background Tasks / Log Stream                      │
└──────────────────────────────────────────────────────────────────────────┘
```

## 4. Widget Tree
```
App
└─ MainScreen
   ├─ HeaderBar
   │  ├─ FamilyVariantPicker
   │  ├─ PathSelector
   │  └─ ActionButtons (Validate | Regen | Save | Undo/Redo | Theme | Palette)
   ├─ Body (Horizontal)
   │  ├─ LayerSidebar (ListView + Toolbar)
   │  ├─ KeyCanvas (custom widget, selection model)
   │  └─ Inspector (TabbedContent)
   │     ├─ KeyTab (Behavior editor + references)
   │     ├─ MacroTab (Table + detail pane)
   │     ├─ HoldTapTab (Table + timing editor)
   │     ├─ ComboTab (Builder + key picker)
   │     ├─ ListenerTab (Graph view + processor forms)
   │     ├─ FeaturesTab (HRM/Cursor/Mouse toggles)
   │     ├─ AdvancedTab (custom behaviors/devicetree/config/layout params)
   │     └─ MetadataTab (UUID/title/notes/tags)
   └─ FooterBar (StatusLine + TaskProgress + ValidationBadge)
```

## 5. Data Model & Schema Bridge

The TUI operates on `LayoutPayload` (see `glove80.layouts.schema`). The JSON Schema exported to `docs/layout_payload.schema.json` is loaded at runtime to drive form generation, validation, and auto-complete.

### 5.1 Section Responsibilities

| LayoutPayload Fields | Notes from Schema | UI Responsibilities |
| --- | --- | --- |
| `keyboard`, `firmware_api_version`, `locale`, `unlisted` | Scalars | Exposed in Metadata tab (read-only defaults unless author overrides). |
| `custom_defined_behaviors` | String blob | Syntax-highlight editor, snippet palette. |
| `custom_devicetree` | String blob | DT-aware editor with optional `dtc` lint integration. |
| `config_parameters[]` | Array of objects (`additionalProperties: true`) | Table editor with key/value typing. |
| `layout_parameters{}` | Object map | JSON editor with inline validation. |
| `layer_names[]` + `layers[][80]` | Each layer = 80 dict entries (`value`, `params[]`) | Layer sidebar + key canvas; ensure `len(layer_names) == len(layers)` and each layer length stays 80. |
| `macros[]` (`$defs.Macro`) | `name`, optional `description`, `bindings[]`, `params[]`, `waitMs`, `tapMs` | Macro studio with sequence editor and reference checks. |
| `holdTaps[]` (`$defs.HoldTap`) | `name`, `bindings[]`, timing fields, `flavor` enum, `holdTriggerKeyPositions[]` (0–79) | Hold-tap studio with validation and key linkage. |
| `combos[]` (`$defs.Combo`) | `binding` object, `keyPositions[]`, `layers[]` (int or `LayerRef`), `timeoutMs?` | Combo builder with key picker and layer scope selection. |
| `inputListeners[]` | `code`, `nodes[]`, `inputProcessors[]` | Listener graph showing sensors/encoders (e.g., mouse move/scroll scalers). |
| Metadata (`uuid`, `parent_uuid`, `date`, `title`, `notes`, `tags`, `creator`) | Optional fields | Displayed for context; allow editing where appropriate (except immutable IDs unless CLI author decides otherwise). |

### 5.2 Behavior Editor
- Each key entry is `{ "value": <behavior code>, "params": [ ... ] }`.
- Provide common presets (`&kp(KEY)`, `&mo(LAYER)`, `&tog`, `&sk`, macros like `&AS_Shifted_v1_TKZ`, HRM bindings like `&HRM_left_index_v1_TKZ`).
- Maintain a raw JSON editor fallback with schema-aware linting for arbitrary nesting.
- Auto-complete sources: known behavior codes in current layout, known keycodes (via `glove80.keycodes`), layer names (offers writing `LayerRef` objects), macro/hold-tap names.

### 5.3 Validators
1. Schema validation (JSON Schema) on every save and major edit.
2. Pydantic validation (LayoutPayload) before calling builder/generator helpers.
3. Semantic checks:
   - `len(layer_names) == len(layers)`; each layer has exactly 80 entries.
   - Macro/HoldTap names unique and referenced keys resolve.
   - Combo `keyPositions[]` unique per combo and stay in `[0,79]`; `layers[]` use `LayerRef` when possible and resolve to valid names.
   - Listener nodes have non-empty `layers[]` and valid refs.
   - Layer rename/reorder updates every `LayerRef` in combos/listeners/macros.
   - Hold-tap timing fields non-negative; `holdTriggerKeyPositions` in range (matches schema guard).

## 6. Feature Bundles & Builder Integration

- **Builder bridge (`tui/services/builder_bridge.py`)** wraps `LayoutBuilder` + `LayoutFeatureComponents` to apply or remove bundled features:
  - `add_home_row_mods(target_layer=…, position=…)`
  - `add_cursor_layer(insert_after=…)`
  - `add_mouse_layers(insert_after=…)`
  - _Note (2025-11-11): HRM preview/apply is implemented (w/ CLI parity tests); cursor + mouse bundles still outstanding._
- The Features tab shows a diff preview (layers/macros/hold taps/combos/input listeners) before applying a bundle.
- Internally, builder bridge produces a shadow layout, calls `merge_components`, and then reconciles changes back into the TUI store—mirroring the runtime feature application path documented in `docs/architecture.md`.

## 7. Key Workflows

### 7.1 Edit a Key
1. Select a key on the canvas (keyboard arrows or mouse click).
2. Key tab displays current `value` and `params[]` with context (macro, hold tap, HRM, etc.).
3. Choose a new behavior via presets or raw JSON.
4. Apply → Store logs `SetLayerKeyBehavior`; validators run; status bar reflects dirty flag.
5. Quick links (“Jump to macro”, “Jump to hold tap”, “Highlight combos using this key”) help trace dependencies.

### 7.2 Create & Bind a Macro _(delivered 2025-11-12)_
1. Macro tab → “New” → provide `name` (must start with `&`), optional `description`, add `bindings[]`, `params[]`, `waitMs`, `tapMs`.
2. Save macro → store enforces uniqueness, snapshots for undo, and records the action for the command log.
3. Return to Key tab → set behavior `value` to macro name (auto-complete ensures it exists).
4. **CRUD guarantees**: `LayoutStore.add_macro/update_macro/delete_macro/list_macros/find_macro_references` (see `src/glove80/tui/state/store.py`) always snapshot before mutation, rename rewrites every reference (`layers`, `macros`, `holdTaps`, `combos`, `inputListeners`), delete is blocked while references exist (unless forced cleanup), and undo/redo restores the previous payload byte-for-byte.
5. Integration pilot (`tests/tui/integration/test_macro_tab.py`) covers create → bind → rename → undo; use it as reference for future studios.

### 7.3 Compose a Hold Tap
1. Hold Tap tab → “New” → enter `name`, `bindings[]`, pick `flavor` (enum), fill timing fields, optionally choose `holdTriggerKeyPositions[]` via key picker.
2. Bind to keys exactly like macros (behavior value = hold tap name).

### 7.4 Build a Combo
1. Combo tab → “New” → click “Pick Keys” to select positions 0–79 on the canvas.
2. Define `binding` via behavior editor, choose `layers[]` (prefer `LayerRef` names), optional `timeoutMs`.
3. Save; table shows combos; selecting a combo highlights its keys/layers.

### 7.5 Toggle Mouse/Cursor/HRM Features
1. Features tab lists available bundles (based on variant metadata) with toggles.
2. Toggling “Mouse stack” calls builder bridge to insert `Mouse`, `MouseSlow`, `MouseFast`, `MouseWarp` layers plus associated listeners (e.g., `&mmv_input_listener` nodes referencing `zip_xy_scaler`).
3. Confirmation dialog shows diff (layers/macros/hold taps/combos/input listeners) before applying.

### 7.6 Custom Behaviors & Device Tree
1. Advanced tab provides two editors: Custom Behaviors (string) and Custom Devicetree (string) with syntax highlighting and lint buttons (calls optional `dtc`).
2. Config/Layout parameters appear as editable tables with type auto-detection.

### 7.7 Layer Operations
- Rename: inline edit of sidebar entry; updates `layer_names` + all `LayerRef` references; warns if duplicates.
- Reorder: drag/drop or shortcuts (`Alt+↑/↓`), rewriting both arrays; diff preview optional.
- Duplicate: clones layer content and optional dependent macros; prompts for new name.
- Pick up / Drop: `P` picks up current layer contents, `D` drops onto target layer; undoable transaction.
- Navigation wrap-around: canvas layer navigation (`[`/`]`) and sidebar arrow keys wrap at boundaries (Raise → Base and vice versa) so keyboard-only users can keep moving without reversing direction. The copy contract (`copy_key_to_layer`) that powers these shortcuts is spelled out in `docs/STORE_API_COPY_KEY.md`.

### 7.8 Studio & Command Surfaces Roadmap _(updated 2025-11-12)_
- **HoldTap Studio**
  - Store API mirrors macro CRUD (`list_hold_taps`, `add_hold_tap`, `update_hold_tap`, `rename_hold_tap`, `delete_hold_tap`, `find_hold_tap_references`), enforces `&`-prefixed unique names, rewrites references on rename, and blocks delete while referenced unless forced cleanup. Timing fields (`tappingTermMs`, `quickTapMs`, `requirePriorIdleMs`) must be ≥ 0; `holdTriggerKeyPositions[]` validated to 0–79 and de-duped. Undo/redo wraps every mutation.
  - UI = MacroTab parity: list with reference counts + detail editor (name/description/bindings/timings/flavor/key picker). Inline validation and footer messaging before commits. Pilot test must create → bind → rename → delete/undo.
- **Combo Studio**
  - CRUD ensures combo names unique, trigger key positions unique per layout, `layers[]` resolve via `LayerRef`, and rename propagates to all dependent sections. Delete blocked when combos referenced by macros/other systems unless forced. Reference finder exposes key/layer contexts for warnings.
  - UI includes chord picker (multi-key capture on KeyCanvas), layer scope selector, binding editor, timeout entry, and conflict badges when triggers overlap with hold taps or combos. Unit + pilot coverage required.
- **Listener Studio**
  - Store adds `add_listener/update_listener/delete_listener/list_listeners/find_listener_references`, validating unique `code`, required processors/nodes, and resolving all layer names. Delete is prohibited while bindings reference the listener; rename updates bindings and listener graphs.
  - UI tab: left list of listeners with type badges (mouse/cursor/custom), right pane showing processors + per-layer nodes, plus modal editor for CRUD. Reference summary links back to offending layers. Events emit `StoreUpdated` and `FooterMessage` for every mutation.
- **Command Palette & Search Panel**
  - Command registry (Ctrl/Cmd+K) exposes at least: layer add/rename/delete, jump to Macro/HoldTap/Combo/Listener, toggle bundles, run validation, open Search/Jump, undo/redo. Commands respect `enabled()` predicates (e.g., delete disabled when only one layer remains) and integrate with StoreUpdated/Footer logs when actions succeed/fail.
  - Search/Jump panel lets users type `k 42`, `layer typing`, `macro &HRM_left_index`, etc., and moves focus accordingly. Palette/search interactions must be testable via Textual pilot: open palette, run `Add Layer`, verify store mutation/log entries.

## 8. Validation & Regeneration Flow

```
[Open Layout (family/variant or file)]
        │
        ▼
LayoutPayload load + schema validation
        │
        ▼
Store state  ←── Undo/Redo log
        │
        ▼
User edits ──► Semantic validators (debounced)
        │
        ▼
Schema + Pydantic validation on save
        │
        └── Regen Preview (optional)
                │
                ▼
   `uv run glove80 generate --layout … --variant … --dry-run`
                │
                ▼
      Diff viewer per section → Apply/Skip per section
                │
                ▼
   Write JSON + (optional) `glove80 validate path/to.json`
```

All regen/validate subprocesses run via Textual workers so the UI remains responsive; logs stream to the footer panel.

> **Footer messaging & severity**: use the catalog in `docs/UX_SPEC_FOOTER_NOTIFICATIONS.md` for all success/info/error notifications so Command Palette, studios, and CLI hooks emit consistent toast/footer output.

## 9. State Management, Commands & Accessibility

- **Store** (`tui/state/store.py`): action log (`AddCombo`, `ApplyFeatureBundle`, `RenameLayer`, etc.), selectors (`active_layer()`, `get_key(layer, index)`, `list_macros()`), undo/redo stack.
- **Background workers**: schema validation, CLI commands (`glove80 validate`, `glove80 generate --dry-run`), optional schema refresh via `scripts/export_layout_schema.py`.
- **Commands / Key Bindings**:
  - Global: `Ctrl/Cmd+K` (palette), `Ctrl/Cmd+S` (Save), `Ctrl/Cmd+Shift+S` (Save As), `F5` (Validate), `F6` (Regen Preview), `Ctrl/Cmd+Z` / `Shift+Ctrl/Cmd+Z` (Undo/Redo).
  - Canvas: arrow keys/hjkl (navigation), `Enter` (open inspector), `.` (copy key to other layer), `[` / `]` (prev/next layer), `P` / `D` (pick up/drop layer).
- **Accessibility & Theming**: Light/Dark/High-contrast themes, configurable font size, focus outlines, descriptive labels for keys/layers, optional ASCII fallback when colors limited.

## 10. Sample Payload Snapshot (TailorKey v4.2h – macOS)

Using `layouts/tailorkey/releases/eee91968-ac8e-4d6f-95a3-4a5e2f3b4b44_TailorKey v4.2h - macOS.json`:
- `layer_names`: `["HRM_macOS", "Typing", "Autoshift", "Cursor", "Symbol", "Gaming", "Lower", "Mouse", "MouseSlow", "MouseFast", "MouseWarp", "Magic"]`.
- Sample macro: `&AS_Shifted_v1_TKZ` (uses `waitMs`, `tapMs`, bindings stack) — Macro tab must render/allow editing of these fields.
- Sample hold tap: `&AS_HT_v2_TKZ` — Hold-tap editor exposes tapping/quick tap/idle timings and `holdTriggerKeyPositions` (where provided).
- Sample combo: `F11_v1_TKZ` — Shows `keyPositions`, `layers` referencing layer indices; UI should encourage storing as `LayerRef {"name": "Typing"}` for resilience.
- Sample listener: `&mmv_input_listener` with nodes referencing `Mouse`, `MouseSlow`, `MouseFast`, `MouseWarp` layers; Listener tab visualizes nodes + processors (`zip_xy_scaler`, `zip_scroll_scaler`).

This concrete payload should remain part of automated regression tests (load → mutate one key → save → reload → expect deterministic diff).

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Drift from builder helpers when toggling features | Non-deterministic JSON vs. CLI | Route all feature toggles through builder bridge + `LayoutBuilder` so we reuse shared merge logic. |
| Layer renames break `LayerRef` references | Combos/listeners fail | Prefer `LayerRef` writes; on rename, rewrite all references; warn if raw indices remain. |
| Arbitrary behavior params confuse users | Bad bindings | Provide guided presets plus raw JSON; include lint + previews. |
| Regen/validate blocking UI | Poor UX | Use Textual workers with streaming logs and cancel buttons. |
| Schema changes break forms | Editor errors | Ship “Refresh schema” command that re-runs `scripts/export_layout_schema.py`; forms read schema dynamically. |
| Terminal capability variance | Visual bugs | Provide compatibility theme + ASCII canvas fallback; test across major terminals. |
| Macro/HoldTap name collisions | Runtime failures | Enforce uniqueness client-side, surface references, provide rename tools that update bindings. |

## 12. Implementation Roadmap
1. **Foundation** – Load any `LayoutPayload`, stand up store, render layer sidebar + read-only canvas.
2. **Editing Core** – Key behavior editor, layer rename/reorder/duplicate/pickup, undo/redo wiring.
3. **Studios** – Macro (✅ 2025‑11‑12), Hold Tap, Combo, Listener screens with cross-linking from keys.
4. **Feature Bundles** – Implement builder bridge and diff preview for HRM/cursor/mouse layers, provenance badges, action log inspector.
5. **Advanced Editors** – Custom behaviors, device tree, config/layout parameter tables, metadata panel.
6. **Validation & Regen** – Schema/Pydantic validators, background CLI calls, Regen Preview diff UI, Save/Export flows.
7. **Polish & QA** – Command palette, Search/Jump, theming, accessibility passes, regression tests (Textual pilot scripts), docs updates, screen recordings.

_Milestone gates: see `docs/TUI_IMPL_PLAN.md` for per-feature test requirements and `docs/TUI_CHECKLIST.md` for acceptance criteria. Highlights below summarize the blocking items:_

- **HoldTap Studio**: Same CRUD guarantees as macros (rename rewrites references, delete blocked while referenced, timings ≥ 0, key positions 0–79). Inspector tab must reuse MacroTab ergonomics and ship unit + pilot tests.
- **Combo Studio**: Enforce unique name + trigger chords, validate `LayerRef` targets, surface conflicts, snapshot mutations for undo/redo, and cover flows via store + pilot tests.
- **Listener Studio**: Provide listener CRUD with unique `code`, node/processor validation, delete guard, reference summaries, and pilot tests for create/edit/delete.
- **Command Palette/Search**: Registry-driven palette (Ctrl/Cmd+K) and Search/Jump panel must execute common commands, respect `enabled()` predicates, emit severity-coded footer/toast messages, and include integration coverage.
- **Feature Bundles & Provenance**: Cursor/mouse bundles flow through BuilderBridge with diff preview parity; provenance badges/action log inspector surface origins for every layer/action.
- **Validation/Regen/Save**: Debounced validators, Regen Preview CLI runner, Save/Save-As with optional auto-validate; all flows tested via unit + pilot suites.
- **Polish & Accessibility**: Theme switcher (light/dark/high-contrast/ASCII), font scaling, Advanced tab, accessibility audit items, final documentation sign-off.

## 13. Deliverables & Handoff
- `docs/layout_payload.schema.json` kept fresh via `scripts/export_layout_schema.py` (already added).
- This `TUI_DESIGN.md` is the authoritative design brief.
- `docs/tui_ai_prompt.txt` referencing this doc + schema for future AI collaborations.
- `just schema` helper (see `justfile`) runs `uv run python scripts/export_layout_schema.py` so agents can refresh the schema on demand.

With these details in place, every contributor (human or AI) can follow a single, accurate plan that honors the existing Glove80 codebase while delivering a feature-complete Textual TUI.
