# Glove80 Simplification Plan — Status: COMPLETE (2025-11-09)

This plan has been executed. Summary of outcomes:
- Phase 1 (1–3): DONE
- Phase 2 (5–6): DONE (scaffold command deferred)
- Phase 3 (7–8): DONE
- Phase 4 (9): DONE
- Phase 5 (10–11): 10 DONE; 11 DEFERRED
- Step 4 (Prefer direct compose for simple families): CANCELLED by request — builder retained for all families.

This plan streamlines the codebase with a user‑first bias, fewer concepts, and a single source of truth. Changes are organized into phases that can land as small, independently reviewable PRs without breaking existing users or release JSON.

## Principles
- User first: the easy path should be obvious and short.
- One concept per capability (avoid parallel abstractions).
- Single source of truth for discovery/metadata.
- Progressive complexity: simple families don’t need advanced builders.
- Deterministic outputs and green tests at every step.

---

## Phase 1 — Low‑risk consolidation (highest ROI)

### 1) Unify family discovery (remove triple wiring) — DONE
- Problem: Families are declared in three places (generator import list, metadata package map, import‑time registry). Easy to desync.
- Change:
  - Derive import targets from `LAYOUT_METADATA_PACKAGES` (src/glove80/metadata.py:18). For each value `pkg`, import `f"{pkg}.layouts"`.
  - Remove hardcoded `_FAMILY_LAYOUT_MODULES` in `src/glove80/layouts/generator.py` and replace with a loop over `LAYOUT_METADATA_PACKAGES.values()`.
- Files to change:
  - `src/glove80/layouts/generator.py` (replace ` _FAMILY_LAYOUT_MODULES` and `_register_families()` logic).
  - (No change to `src/glove80/metadata.py` structure.)
- Tests:
  - `tests/test_cli.py::test_cli_families_lists_registered` should still pass without edits.
  - Add a small unit test asserting that generator imports all packages named in `LAYOUT_METADATA_PACKAGES`.
- Risk/mitigation: Low; if a family lacks `*.layouts` module, fail with a clear error listing the package name.

### 2) Consolidate feature merge logic into one helper — DONE
- Problem: Duplicate logic in `LayoutBuilder._merge_feature_components` and `features.apply_feature()` increases drift risk.
- Change:
  - Add `src/glove80/layouts/merge.py` with a single function `merge_components(layout: dict, components: LayoutFeatureComponents) -> None`.
  - Refactor both `LayoutBuilder._merge_feature_components` and `glove80.features.base.apply_feature` to call this.
- Files to change:
  - `src/glove80/layouts/merge.py` (new file).
  - `src/glove80/layouts/builder.py` (replace body of `_merge_feature_components` with a one‑liner call).
  - `src/glove80/features/base.py` (delegate to shared helper).
- Tests:
  - Keep `tests/test_features.py` and `tests/test_builder.py` but assert one canonical behavior (no change to expectations).
- Risk/mitigation: Very low; behavior stays identical. Add unit test for the helper if helpful.

### 3) Always resolve layer references (remove the toggle) — DONE
- Problem: `resolve_refs` is a branchy option with little upside; always resolving is simpler and a no‑op when not used.
- Change:
  - Remove the `resolve_refs` parameter from `compose_layout()` and `LayoutBuilder` ctor. Always resolve.
- Files to change:
  - `src/glove80/layouts/common.py` (drop parameter and the conditional; keep resolution call).
  - `src/glove80/layouts/builder.py` (remove `_resolve_refs` state and arg pass‑through).
  - Families that pass `resolve_refs=False` (default, glorious_engrammer) should stop passing it.
- Tests:
  - Update any imports or ctor calls in tests that referenced the flag.
- Risk/mitigation: Low; families that didn’t use refs are unaffected.

### 4) Prefer direct compose for simple families — CANCELLED
- Problem: Builder adds a concept where families just pour sections into `compose_layout`.
- Change:
  - In `default`, `quantum_touch`, and `glorious_engrammer` families, replace the `LayoutBuilder` usage with a direct call to `compose_layout()`.
  - Keep `LayoutBuilder` only for TailorKey, where ordering and feature insertion matter.
- Files to change:
  - `src/glove80/families/default/layouts.py`
  - `src/glove80/families/quantum_touch/layouts.py`
  - `src/glove80/families/glorious_engrammer/layouts.py`
- Tests:
  - Existing tests should remain valid. Update any that assert on builder internals.
- Risk/mitigation: Low; functional equivalence. Fewer moving parts for readers.

---

## Phase 2 — API and CLI ergonomics

### 5) Flatten and document the public API — DONE
- Goal: New users need a minimal, obvious surface.
- Change:
  - Export `list_families()` and `features.apply_feature` from the top‑level package.
  - Optional: also export `features.bilateral_home_row_components` for a batteries‑included example.
- Files to change:
  - `src/glove80/__init__.py` (export `list_families`, `apply_feature`, and optionally the bilateral helper).
  - README: add a “minimal API” snippet that builds + applies a feature in <10 lines.
- Tests: Add a smoke test importing these names from `glove80`.

### 6) CLI affordances — DONE (scaffold command DEFERRED)
- Add `validate` command as a friendlier alias for `typed-parse`.
- Add `--out` to `generate` to override the destination path without crafting a metadata file (applies when `--layout` and `--variant` are specified). If both `--out` and `--metadata` are given, `--out` wins for destination only.
- Optional (later): `scaffold` command to generate a minimal Python spec file for a custom family/layout. Start with a minimal template; YAML can come later if desired.
- Files to change:
  - `src/glove80/cli/__init__.py`
  - Update README examples.
- Tests:
  - Extend `tests/test_cli.py` for new commands/options.
- Risk/mitigation: Low; defaults unchanged.

---

## Phase 3 — Data/naming simplifications

### 7) Normalize family naming / aliasing — DONE
- Problem: `glorious_engrammer` (code) vs `glorious-engrammer` (folder). Mild friction.
- Change:
  - Introduce a simple alias map used by CLI display and `available_layouts()`, keeping canonical keys unchanged.
- Files to change:
  - `src/glove80/layouts/generator.py` (formatting/display only) or `src/glove80/layouts/family.py` (helper for names/aliases).
  - README note.
- Risk: Very low; it’s cosmetic.

### 8) Simplify `LayoutFeatureComponents` — DONE (added `macros_by_name` non-breaking)
- Problem: `macros` + `macro_overrides` is two ways to express the same thing.
- Change (non‑breaking, staged):
  - Add a new optional field `macros_by_name: Mapping[str, Macro]`.
  - Merge logic prefers `macros_by_name` when present; otherwise falls back to current fields. Deprecate `macro_overrides` in docs.
- Files to change:
  - `src/glove80/layouts/components.py`
  - `src/glove80/layouts/merge.py` (new helper) to implement precedence.
  - Docs.
- Tests: Add coverage for both forms.
- Risk: Low; keep backward compatibility until a later cleanup.

---

## Phase 4 — Documentation & examples

### 9) Short-path docs and examples — DONE
- Add “Quick Start: Custom layout in 5 minutes” showing:
  - `build_layout('tailorkey', 'windows')`
  - `bilateral_home_row_components()` + `apply_feature()`
  - `glove80 generate --layout tailorkey --variant windows --dry-run`
- Add a “How to add a new family” doc: minimal compose only; introduce the builder as an optional advanced tool for ordered insertions.
- Files to change:
  - `README.md`, `docs/architecture.md` (trim builder emphasis; highlight `compose_layout`).

---

## Phase 5 — Deprecations & cleanup (optional follow‑ups)

### 10) Remove `resolve_refs` traces entirely — DONE

### 11) Consider a plugin/entry‑points discovery (later) — DEFERRED

---

## Milestones & sequencing

- M1: Family discovery unification (1 PR)
- M2: Shared merge helper + refactor builder/features (1 PR)
- M3: Always resolve refs + remove flag usage (1 PR)
- M4: Compose in simple families (1 PR)
- M5: API/CLI ergonomics (1–2 PRs)
- M6: Naming alias + docs refresh (1 PR)
- M7: Optional component API simplification (1 PR)

Each milestone should keep `just regen` and `just ci` green.

---

## Acceptance criteria
- One source of truth for family discovery; no hardcoded module list remains.
- One implementation of feature merging used by both Builder and runtime feature application.
- No `resolve_refs` option; references are always resolved.
- Simple families read like data assembly (compose) rather than builder choreography.
- Top‑level API lets a new user build and tweak a layout in <10 lines.
- CLI supports validating an arbitrary JSON and overriding the output path.
- Documentation shows a 5‑minute quick start and a minimal family recipe.

---

## Validation checklist
- `just ci` passes.
- `just regen` produces no diffs on a clean main.
- CLI: `families`, `generate --dry-run`, `validate`, `generate --out` all work.
- Manual smoke: build TailorKey (windows, mac, dual), Default (factory_*), QuantumTouch (default), Glorious Engrammer (variants) and load JSON in the editor.

---

## Rollback plan
- Each PR is mechanically reversible; keep changes scoped.
- Preserve current behavior in tests; where behavior changes, add explicit migration notes in commit messages and docs.

---

## Out of scope (for now)
- YAML DSL for authoring specs.
- Third‑party plugin system.
- Large redesign of layer factories.
