# Glove80 Layout Sources

This repository captures canonical Glove80 layouts (TailorKey, QuantumTouch, …) and provides tooling to regenerate their release JSON files deterministically from a single source of truth. TailorKey is the zero-code layout created by [@moosy](https://sites.google.com/view/keyboards/glove80_tailorkey) and inspired by Sunaku’s Glorious Engrammer; QuantumTouch builds on similar ideas with Bilateral HRM training layers.

## Goals

- Preserve every supported Glove80 layout exactly as it was shared upstream.
- Regenerate the release JSON files from canonical sources deterministically.
- Run CI that guarantees the generated artifacts stay in lockstep with the
  checked-in JSON.
- Provide a clean place to continue evolving these layouts while maintaining an
  auditable history of every change.

## Repository Layout

```
.
├─ original/                   # canonical Glove80 layouts (JSON)
├─ sources/
│  ├─ variant_metadata.json    # TailorKey release metadata
│  └─ quantum_touch_metadata.json
├─ src/
│  ├─ glove80/base.py           # shared KeySpec/layer helpers
│  ├─ glove80/metadata.py       # typed metadata loader
│  ├─ glove80/tailorkey/        # TailorKey implementation
│  └─ glove80/quantum_touch/    # QuantumTouch implementation
├─ scripts/
│  └─ generate_layouts.py
├─ tests/                      # pytest suites (layers + full layouts)
└─ README.md
```

- **original/** contains the exact artifacts Moosy published. We treat them as
  the source of truth; regeneration must leave them unchanged.
- **sources/…_metadata.json** store the metadata we need to keep intact
  (titles, UUIDs, notes, tags, release filenames) per layout family.
- **src/glove80/base.py** defines the shared `LayerSpec`/`KeySpec`
  helpers used by all layouts, regardless of brand.
- **src/glove80/tailorkey/** contains the TailorKey implementation:
  declarative layer modules under `layers/`, the `layouts.py` composer, and the
  layer registry used by tests/CI.
- **src/glove80/quantum_touch/** mirrors the same structure for the
  QuantumTouch layout—all layers are generated via `LayerSpec`/`KeySpec`.
- **src/glove80/metadata.py** loads the release metadata (UUIDs,
  titles, etc.) once with type checking so scripts and tests share it safely.
- **scripts/generate_layouts.py** regenerates every supported layout (TailorKey,
  QuantumTouch, …) from their source code/metadata and overwrites the files in
  `original/`.
- **tests/** contains per-layer tests (ensuring every module reproduces its
  canonical layer) plus a top-level test that compares `build_layout()` against
  the checked-in `original/*.json`. This guarantees we never drift from the
  historical layouts.

## Workflow

1. Modify the generator code under `src/glove80/` (or adjust the appropriate
   metadata file in `sources/` if the release notes/UUIDs change).
2. Run the generator:

   ```bash
   python3 scripts/generate_layouts.py
   ```

   The script rebuilds each JSON under `original/`. A clean `git diff` confirms
   the new code still matches the published layouts.

3. Run the tests:

   ```bash
   uv run pytest
   ```

   The suite re-checks every layer module plus the full-layout comparison to
   ensure nothing regressed.

## Extending the Layout

- When adding a new TailorKey layer, implement it in
  `src/glove80/tailorkey/layers/…` using `LayerSpec`/`KeySpec`, then
  register its builder in `glove80.tailorkey.layers.LAYER_PROVIDERS`. Follow
  the same pattern under `glove80/quantum_touch/…` (or a new layout folder) for
  other families.
- To introduce a new release variant, add its entry to the appropriate metadata
  file under `sources/`; the typed loader (`metadata.py`) keeps the rest of the
  tooling in sync automatically.

## Continuous Integration

GitHub Actions already runs `uv run pytest` plus `python3 scripts/generate_layouts.py` on every push/PR and fails the build if `original/` changes. This ensures the checked-in JSON artifacts always match the code-generated layouts.
