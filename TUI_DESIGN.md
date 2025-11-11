# Keymap Studio – Textual TUI Layout Editor Design Plan

## 1. Context & Intent
- The current repo hosts a React/Vite prototype (`apps/keymap-studio`) plus reusable TypeScript packages (`packages/schema`, `packages/data`, `packages/core`) and a production bundle of the legacy web app in the repo root. These assets encode the full UX surface: multi-source import (demo/GitHub/local/clipboard), rich layer and behavior editing, combos/macros/sensors, validation, theming, and persistence flows.
- Goal: deliver a Python **Textual** (https://textual.textualize.io) TUI that preserves the feature set, data semantics, and user expectations of the browser-based Keymap Studio while optimizing for keyboard-centric workflows.
- Deliverable: a first-class architectural plan enumerating every feature, how it maps onto Textual primitives, and how the Python stack mirrors the TypeScript data models so parity work stays deterministic.

## 2. Grounding in the Existing Codebase
| Area | Source Artifacts | Key Takeaways for the TUI |
| --- | --- | --- |
| Data & schema | `packages/schema/src/index.ts` | Behaviors, bindings, layers, combos, macros, sensors, warnings, keymaps defined via Zod. TUI must mirror these structures (e.g., Python `pydantic` models) to keep serialization/validation lossless. |
| Demo content | `packages/data/src/index.ts` | `DemoKeyboard` shape (keys array + `KeyGeometry`) and `Keymap` composition supply default canvases. TUI needs identical demo bootstrapping for offline-first experience. |
| Core helpers | `packages/core/src` | `summarizeLayers` + theming utilities show how UI derives summaries from keymap data. TUI will port the layer summarization logic and add terminal-friendly theme persistence. |
| App shell | `apps/keymap-studio/src` | Sidebar of layers, top bar with source picker/theme toggle, canvas showing key grid, binding inspector, React Query powered source API mock. These interactions define the minimum parity surface for the TUI interface architecture. |
| Legacy bundle | `main.*.js`, chunked feature files, `REVERSE_ENGINEERING.md` | Confirms advanced features (conditional layers, combos, macros, sensors, warnings tab, multiple source adapters). All of these must have corresponding TUI affordances even if implemented iteratively. |

## 3. Design Pillars
1. **Parity-first** – Every feature from the legacy/web versions must map to a TUI affordance, even if staged. No feature is “web-only”.
2. **Observable state** – Reflect web Redux/query stores via explicit, inspectable Python state containers so power users can debug their layout changes.
3. **Asynchronous friendliness** – GitHub/file-system/clipboard adapters run in background workers with progress streaming into the TUI status bar.
4. **Keyboard-native UX** – All commands exposed via shortcuts, command palette, contextual quick actions; pointing device optional.
5. **Extensibility** – New tabs or editors should drop in as Textual `Screen`/`Dock` components without reshaping the whole app.

## 4. Target Stack & High-Level Architecture
- **Runtime:** Python 3.12+, Textual ≥0.59 for CSS-like layout, data tables, and background tasks.
- **Data models:** Pydantic v2 models mirroring the Zod schemas (Behavior, Binding, Layer, Combo, Macro, Sensor, Warning, Keymap). Provide JSON serialization adapters to stay compatible with the data already stored under `keyboard-data` and `locales`.
- **Persistence/adapters:**
  - Demo data sourced from the existing TypeScript `packages/data` JSON (convert via script or expose through generated JSON artifacts).
  - GitHub adapter built with `httpx` + GitHub REST API v3 (token optional); supports repo browse, branch pick, file fetch.
  - Local FS adapter reads `.keymap/.dtsi` files via `pathlib`; File System Access parity delivered via Textual file picker widget.
  - Clipboard adapter uses `pyperclip` (macOS/Linux/Windows) with fallback instructions.
- **Core services:**
  - `KeymapStore` (observable state tree) handling undo/redo, selection, dirty flags, validation snapshots.
  - `SourceService`, `ParserService`, `SerializerService`, `ValidationService` mirroring responsibilities from the web version.
- **UI composition:**
  - Root `KeymapStudioApp` extends `textual.app.App` with CSS layout: left dock (sources/layers), center stage (canvas/inspectors), right dock (detail panes), bottom status/log bar, modal stack.
  - Each web “tab” (Layers, Conditional Layers, Combos, Macros, Behaviors, Warnings) becomes either a dedicated `Screen` or a `TabbedContent` widget inside the main stage.
- **Task orchestration:** use `textual.worker` for background operations (GitHub fetches, parsing, serialization). Results dispatched as messages to the UI components.

### Component/Module Map
| Module | Responsibility |
| --- | --- |
| `models/` | Pydantic models + dataclasses representing behaviors, bindings, etc. |
| `services/source_adapters/` | Demo, GitHub, Local, Clipboard adapters producing `KeymapDocument` objects (same shape as `src/api/types.ts`). |
| `services/parser.py` | Wraps existing ZMK parser (initially stubbed like `parseKeymap` in schema package) with pluggable implementations. |
| `services/serializer.py` | Outputs `.keymap` text; parity with `serializeKeymap`. |
| `services/validator.py` | Applies schema validation + domain checks (duplicate combos, conflicting layers). |
| `state/store.py` | Central event bus, undo stack, derived selectors (port of `summarizeLayers`). |
| `ui/screens/` | Textual screens: `DashboardScreen`, `LayerEditorScreen`, `ComboScreen`, `MacroScreen`, `BehaviorsScreen`, `WarningsScreen`, `SourceWizardScreen`. |
| `ui/widgets/` | Reusable widgets: Layer list, key grid, inspector sheet, sensor dial, status/log, notification toaster. |
| `commands/` | Command palette definitions, key bindings, macros for automation. |

### Data & Message Flow (ASCII)
```
[User Action]→[UI Widget]→(Message)→[KeymapStore]→(event)
     ↓                                          ↑
 [Background Worker]←(Task request)—[Service]←--+
     ↓
 [Result]→[UI Notification/Store update]→[Render]
```

## 5. Layout & Navigation Concept
```
┌───────────────────────────────────────────────────────────────┐
│ Source Bar │ Layer Stack │             Stage Tabs            │
│            │             │  [Layers] [Combos] [Macros] ...   │
├────────────┼─────────────┼───────────────────────────────────┤
│ Picker     │ Active list │  Canvas / Grid / Table            │
│ history    │ Layer meta  │                                   │
│ + filters  │ + commands  │                                   │
├────────────┴─────────────┼───────────────┬───────────────────┤
│ Inspector / Behavior form│ Sensor pane   │ Validation feed   │
├──────────────────────────┴───────────────┴───────────────────┤
│ Status line (mode, GitHub, dirty flag, background jobs)      │
└───────────────────────────────────────────────────────────────┘
```
- Dock arrangement adjustable via shortcut (switch to focus-only canvas, show/hide inspector, etc.).
- Command palette (`Ctrl+P`) lists all actions (import, navigate to screen, run validation, export, etc.).
- Breadcrumbs show `Source ▶ Keyboard ▶ Layer` to mirror the Topbar context in the React app.

## 6. Core Workflow Specifications

### 6.1 Source Onboarding (parity with `SourcePickerDialog` + legacy pickers)
1. **Step 1 – Select source kind** via carousel/list (Demo, GitHub, Local, Clipboard). Mirrors the two-step dialog in the web app.
2. **Step 2 – Configure** using contextual forms:
   - Demo: pick from `listKeyboards()` (converted to JSON). Show preview metadata.
   - GitHub: repo (`owner/name`), branch/tag, path to `keymap.dtsi`. Supports PAT input + caching.
   - Local: file picker (Textual `FileTree`) + MRU list.
   - Clipboard: paste area with syntax-highlight preview.
3. **Step 3 – Import** triggers background fetch + parse pipeline, streaming progress to status bar. Result populates `KeymapStore`, updates `layers` view via `summarizeLayers` equivalent.
4. **Document management** – track `KeymapDocument` metadata (id, sourceId, updatedAt) for display + persistence, matching `/src/api/types.ts` semantics.

### 6.2 Layer Editing & Canvas (parity with `Canvas.tsx` + LayerEditor chunks)
- Render keyboard geometry using Textual `Canvas` widget or custom grid. Align `KeyGeometry` using `row`, `col`, `width`, `rotation`. Provide optional ASCII fallback for simple terminals.
- Selection model: arrow keys cycle keys; `Enter` opens inspector, `Space` toggles multi-select, `Shift+{Arrow}` extends selection.
- Visual states mimic web colors (base, layer toggle, holds). Provide legend widget just like the React card footnote.
- Tab list replicates `Tabs/TabsTrigger` behavior: `Layers`, `Conditional`, `Combos`, `Macros`, `Behaviors`, `Warnings`. Focus switching uses `Ctrl+Tab`.
- Quick actions: `a` adds layer, `d` duplicates, `r` renames, `g` go-to layer by index.

### 6.3 Binding Inspector (parity with `BindingInspector.tsx`)
- Appears as right-docked sheet. Shows key legend, behavior code, parameters table.
- Editing flows: inline editing of override display, selecting behavior templates (via list filtered by locale), editing params with validation.
- Actions: apply to selection, apply to entire row/column, revert to keyboard default, mark as macro trigger.

### 6.4 Behavior/Macro/Combo/Conditional Editors
- **Behaviors Tab**: tabular view derived from `BehaviorEditorTab.*` chunk. Supports filtering by kind, editing parameters, duplication detection.
- **Combos Tab**: multi-row table showing source keys, output behavior, notes. Provide combination builder widget (select keys from grid, confirm). Validations highlight overlaps.
- **Conditional Layers Tab**: manager for activation rules (e.g., sensors, positional combos). Provide detail form for condition type (hold tap, sensor threshold, custom behaviors) to match original feature chunk.
- **Macros Tab**: step editor (tap/text/delay), preview, and playback simulation.
- Each editor integrates with `Warnings Tab` aggregator which surfaces issues (missing definitions, duplicates) just like the React warnings dashboard.

### 6.5 Sensors & Encoders
- Dedicated pane showing left/right encoder bindings, tilt sensors, RGB controls. Use dial widgets to convey rotation degrees. Behavior selection shares the binding inspector foundation.
- Support per-sensor overrides plus global defaults.

### 6.6 Validation & Warnings
- Background validation runs on significant mutations (debounced). Collect warnings (info/warn/error) with location references (layer/key/macro). Display summary count in status line and detail view replicating `WarningsTab.*` chunk.
- Provide quick-fix shortcuts (jump to offending binding, auto-deduplicate combos, etc.).

### 6.7 Persistence & Export
- Support saving back to original source via adapter contract:
  - Demo: read-only (warn user).
  - GitHub: create commit via REST (optionally open PR) – stage as future enhancement but plan API contract now.
  - Local: write file or export to target path.
  - Clipboard: copy serialized `.keymap` text.
- Always show dirty indicator and prompt before exit.

### 6.8 Localization & Keycode Catalog
- Mirror `locales/*.js` by bundling JSON; allow user to switch locale, altering available keycodes in behavior picker. Provide preview popover inside inspector.

## 7. State Management & Data Integrity
- `KeymapStore` uses an event-sourced pattern: actions (e.g., `SelectLayer`, `UpdateBinding`, `AddCombo`) logged with timestamps and undo metadata.
- Derived selectors: `get_active_layer()`, `get_binding(key_id)`, `list_layers()` (port of `summarizeLayers`), `list_warnings()`, etc.
- Snapshot persistence for autosave (YAML/JSON) stored in `~/.keymap-studio-tui/projects/{sourceId}.json`.
- Validation pipeline: structural validation (Pydantic) → semantic validation (duplicate detection) → adapter warnings (e.g., GitHub auth failure). All results normalized into `Warning` objects identical to schema package.

## 8. Interaction & Commands
- Global keymap:
  - `Ctrl+P` open command palette; `:` toggles quick command mode (like Vim) for actions `:export`, `:reload`, `:goto layer base`.
  - `F1` toggles help overlay summarizing shortcuts (replaces Topbar tagline from React app).
  - `Ctrl+S` save via active source adapter; `Ctrl+Shift+S` “Save As” (local export or new branch).
  - `Alt+[` / `Alt+]` cycle tabs; `Ctrl+/` toggles log pane.
- Notifications appear as toasts near bottom-right (mirrors web modals) with actions (undo, open log).
- Mouse support optional (Textual supports), but all operations reachable via keyboard sequences.

## 9. Background Tasks & Networking
- Wrap long-running adapters in `textual.worker` to avoid blocking UI. Provide cancellable progress modals with logs.
- Use `asyncio` + `httpx.AsyncClient` for GitHub operations; implement rate-limit handling and offline fallback (cached responses).
- File watcher: when editing local source, optional `watchdog` monitors file for external changes and prompts reload (parity with browser auto-refresh expectation).

## 10. Theming & Accessibility
- Terminal color themes: `light`, `dark`, `high-contrast`. Persist preference in `~/.config/keymap-studio-tui/settings.json`, analogous to `saveTheme` logic in `packages/core/src/theme.ts`.
- Respect system theme via `darkdetect` on macOS/Linux or Windows registry query.
- Provide monospace font fallback detection; degrade gracefully on limited color terminals (using ASCII-style keycaps if necessary).
- Ensure screen-reader compatibility by exposing textual descriptions (Textual’s accessibility APIs) for selected key, layer, warning.

## 11. Testing & Tooling
- **Unit tests:** Pydantic models, selector logic, adapters with mocked IO.
- **Golden tests:** serialization/deserialization parity vs. existing TypeScript schemas using shared fixture JSON.
- **TUI integration tests:** use `textual-dev`’s pilot to simulate keypresses (load demo, edit binding, export) for regression coverage.
- **Adapter contract tests:** record/replay HTTP interactions for GitHub operations via `pytest-httpx` to ensure deterministic runs.
- **Performance budgets:** ensure rendering 70+ keys + combos stays under 50ms per frame; measure with Textual instrumentation.

## 12. Implementation Roadmap
1. **Foundation (Parity scaffolding)**
   - Port schemas to Pydantic, implement storage, load demo keyboard.
   - Build `KeymapStore` + selectors, autosave scaffolding.
   - Render base layout (source bar, layer list, canvas with key selection) using demo data.
2. **Source integrations**
   - Implement Source Wizard with demo + clipboard first, then local FS, finally GitHub (read-only, later write-back).
3. **Editors & inspectors**
   - Binding inspector + key legend editing.
   - Combos/macros/sensor screens and associated state reducers.
4. **Validation & warnings**
   - Semantic validators, warnings tab, inline badges, quick fixes.
5. **Persistence & export**
   - Serialize to `.keymap`, clipboard export, file save, GitHub save (branch or PR creation as stretch).
6. **Polish**
   - Command palette, theming, help overlay, logging panel, plugin hooks.

Each phase should end with recorded demo GIFs (Textual capture) and docs updates referencing parity checkpoints.

## 13. Documentation & Handoff
- Maintain this plan plus incremental notes (`docs/tui/decisions/*.md`).
- Update `PLAN.md` milestones to reflect TUI direction once implementation starts.
- Provide onboarding runbook covering environment setup (`uv`/`poetry`), dev commands (`textual run keymap_studio/app.py`), and troubleshooting (terminal config, GitHub tokens).

This design keeps the spirit and power features of Keymap Studio while embracing a Textual-first experience, ensuring that every capability present in the existing React/web artifacts has a clearly defined home in the terminal UI.
