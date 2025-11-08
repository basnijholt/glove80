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
│  ├─ tailorkey_builder/layers # per-layer generators + shared helpers
│  └─ tailorkey_builder/layouts.py
├─ scripts/
│  └─ generate_tailorkey_layouts.py
├─ tests/                      # pytest suites (layers + full layouts)
└─ README.md
```

- **original/** contains the exact artifacts Moosy published. We treat them as
  the source of truth; regeneration must leave them unchanged.
- **sources/variant_metadata.json** stores the metadata we need to keep intact
  (titles, UUIDs, notes, tags, release filenames).
- **src/tailorkey_builder/layers/** defines every layer declaratively using
  `LayerSpec`/`KeySpec`. Each module encodes the canonical bindings, applies
  any OS- or feature-specific tweaks in code, and returns the finished layer.
  `layers/base.py` houses the shared helpers for building, cloning, and
  patching layers.
- **src/tailorkey_builder/layouts.py** composes all layers for a variant and
  merges them with the preserved metadata. This is the single entry point the
  generator and tests call.
- **scripts/generate_tailorkey_layouts.py** simply runs `build_layout()` for
  each variant listed in `variant_metadata.json` and overwrites the file in
  `original/`.
- **tests/** contains per-layer tests (ensuring every module reproduces its
  canonical layer) plus a top-level test that compares `build_layout()` against
  the checked-in `original/*.json`. This guarantees we never drift from the
  historical layouts.

## Workflow

1. Modify the generator code under `src/tailorkey_builder/` (or adjust metadata
   in `sources/variant_metadata.json` if the release notes/UUIDs change).
2. Run the generator:

   ```bash
   python3 scripts/generate_tailorkey_layouts.py
   ```

   The script rebuilds each JSON under `original/`. A clean `git diff` confirms
   the new code still matches Moosy’s published layouts.

3. Run the tests:

   ```bash
   uv run pytest
   ```

   The suite re-checks every layer module plus the full-layout comparison to
   ensure nothing regressed.

## Continuous Integration

A future CI workflow can simply execute the two commands above. The generated
release JSON files can then be uploaded as build artifacts or attached to a
GitHub release, ensuring the hosted layouts always correspond to the committed
source files.
