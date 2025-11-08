# TailorKey Layout Sources

TailorKey is a zero-code Glove80 layout created by [@moosy](https://sites.google.com/view/keyboards/glove80_tailorkey) and inspired by Sunaku’s Glorious Engrammer. This repository captures the published TailorKey variants and provides tooling to regenerate the release JSON files deterministically from a single source of truth.

## Goals

- Preserve each TailorKey variant exactly as it was shared upstream.
- Regenerate the release JSON files from canonical sources deterministically.
- Enable CI workflows that publish the generated layout files as artifacts.
- Provide a clean place to continue evolving TailorKey while maintaining a
auditable history of every change.

## Repository Layout

```
.
├─ original/                   # canonical TailorKey variants (JSON)
├─ sources/
│  └─ variant_metadata.json    # release filenames + UUIDs + notes
├─ src/
│  ├─ glove80/base.py        # shared KeySpec/layer helpers
│  ├─ glove80/metadata.py    # typed metadata loader
│  └─ glove80/tailorkey/     # TailorKey-specific code
├─ scripts/
│  └─ generate_layouts.py
├─ tests/                      # pytest suites (layers + full layouts)
└─ README.md
```

- **original/** contains the exact artifacts Moosy published. We treat them as
  the source of truth; regeneration must leave them unchanged.
- **sources/variant_metadata.json** stores the metadata we need to keep intact
  (titles, UUIDs, notes, tags, release filenames).
- **src/glove80/base.py** defines the shared `LayerSpec`/`KeySpec`
  helpers used by all layouts, regardless of brand.
- **src/glove80/tailorkey/** contains the TailorKey implementation:
  declarative layer modules under `layers/`, the `layouts.py` composer, and the
  layer registry used by tests/CI.
- **src/glove80/quantum_touch/** currently replays the canonical QuantumTouch
  layout; its layers can be codified the same way as TailorKey over time.
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

1. Modify the generator code under `src/glove80/` (or adjust metadata
   in `sources/variant_metadata.json` if the release notes/UUIDs change).
2. Run the generator:

   ```bash
   python3 scripts/generate_layouts.py
   ```

   The script rebuilds each JSON under `original/`. A clean `git diff` confirms
   the new code still matches Moosy’s published layouts.

3. Run the tests:

   ```bash
   uv run pytest
   ```

   The suite re-checks every layer module plus the full-layout comparison to
   ensure nothing regressed.

## Extending the Layout

- When adding a new TailorKey layer, implement it in
  `src/glove80/tailorkey/layers/…` using `LayerSpec`/`KeySpec`, then
  register its builder in `glove80.tailorkey.layers.LAYER_PROVIDERS`.
- To introduce a new release variant, add its entry to
  `sources/variant_metadata.json`; the typed loader (`metadata.py`) keeps the
  rest of the tooling in sync automatically.

## Continuous Integration

A future CI workflow can simply execute the two commands above. The generated
release JSON files can then be uploaded as build artifacts or attached to a
GitHub release, ensuring the hosted layouts always correspond to the committed
source files.
