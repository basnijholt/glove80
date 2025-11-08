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
├─ original/                   # published layouts (generated artifacts)
├─ sources/
│  └─ variant_metadata.json    # mapping of variants → release metadata
├─ src/
│  └─ tailorkey_builder/       # Python package for layered generation
├─ scripts/
│  └─ generate_tailorkey_layouts.py
├─ tests/                      # pytest suites (release + layer builders)
└─ README.md
```

- **sources/variant_metadata.json** lists each variant, the release filename,
  and the metadata (uuid, parent_uuid, tags, notes, etc.) that should be
  applied when regenerating the published JSON.
- **scripts/generate_tailorkey_layouts.py** builds every layer from code and
  rewrites the release file so it matches the committed canonical layout.
- **original/** is where the generator writes the published JSON files that ship
  with releases or get uploaded as CI artifacts.
- **src/tailorkey_builder** is the growing Python package that will eventually
  synthesize every layer from shared building blocks (starting with mouse
  layers).
- **tests/** contains pytest suites that validate both the published layouts and
  individual generator modules.

## Regeneration Workflow

1. Modify the generator code under `src/tailorkey_builder/` (or adjust the
   metadata in `sources/variant_metadata.json`).
2. Run the generator:

   ```bash
   python3 scripts/generate_tailorkey_layouts.py
   ```

   The script rewrites every release JSON under `original/`. Because the layout
   is generated from code, the working tree will only show diffs for files you
   intentionally changed.

3. Run the tests:

   ```bash
   pytest
   ```

   The test suite compares the generated layouts with the committed files under
   `original/`. This guards against accidental changes to the published
   layouts.

## Continuous Integration

A future CI workflow can simply execute the two commands above. The generated
release JSON files can then be uploaded as build artifacts or attached to a
GitHub release, ensuring the hosted layouts always correspond to the committed
source files.
