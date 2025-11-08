# TailorKey Layout Sources

This repository captures the released TailorKey ZMK layouts for the Glove80
keyboard and provides tooling to regenerate the published JSON files from a
single source of truth.

## Goals

- Preserve each TailorKey variant exactly as it was shared upstream.
- Regenerate the release JSON files from canonical sources deterministically.
- Enable CI workflows that publish the generated layout files as artifacts.
- Provide a clean place to continue evolving TailorKey while maintaining a
auditable history of every change.

## Repository Layout

```
.
├─ sources/
│  ├─ variant_metadata.json    # mapping of variants → release metadata
│  └─ variants/                # canonical source JSON per layout variant
├─ scripts/
│  └─ generate_tailorkey_layouts.py
├─ tests/
│  └─ test_generate_layouts.py
├─ *.json                      # release files produced by the generator
└─ README.md
```

- **sources/variants** contains the original layouts, one file per variant.
  These are treated as the authoritative copies that should be edited when
  making changes.
- **sources/variant_metadata.json** lists each variant, the path to its
  canonical source, the release filename, and the metadata (uuid, parent_uuid,
  tags, notes, etc.) that should be applied when regenerating the published
  JSON.
- **scripts/generate_tailorkey_layouts.py** copies the canonical source JSON to
  the release file path and overwrites its headline metadata so it matches the
  upstream release exactly.
- **tests/** contains a pytest suite that asserts every release file matches the
  canonical source after the generator runs.

## Regeneration Workflow

1. Modify the canonical source in `sources/variants/*.json` or adjust the
   metadata in `sources/variant_metadata.json`.
2. Run the generator:

   ```bash
   python3 scripts/generate_tailorkey_layouts.py
   ```

   The script rewrites every release JSON in the repository. Because it pulls
   from the canonical source, the working tree will only show diffs for files
   you intentionally edited.

3. Run the tests:

   ```bash
   pytest
   ```

   The test suite reruns the generator for each variant and asserts that the
   release file exactly matches the canonical source. This guards against
   accidental edits to the public layouts.

## Continuous Integration

A future CI workflow can simply execute the two commands above. The generated
release JSON files can then be uploaded as build artifacts or attached to a
GitHub release, ensuring the hosted layouts always correspond to the committed
source files.
