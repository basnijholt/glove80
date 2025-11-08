# Architecture

This project keeps every part of the Glove80 layout toolchain in version control so the published JSON artifacts can be recreated exactly from code.

## Source of Truth
- **Specs (`src/glove80/*/specs/`)** define macros, hold-taps, combos, input listeners, and per-layer overrides using typed dataclasses from `glove80.specs.primitives`.
- **Layer factories (`src/glove80/*/layers/`)** build sparse `LayerSpec` objects into the 80-key arrays expected by the Glove80 firmware.
- TailorKey factories mix and match reusable helpers (mouse, cursor, HRM, etc.), while QuantumTouch layers reuse the same primitives to build finger-training variants.
- **Metadata (`src/glove80/layouts/<layout>/metadata.json`)** stores the immutable release information checked in by the original layout authors (UUIDs, parent UUIDs, titles, tags, notes, and the relative output path).
- Packaging the metadata keeps CLI invocations and library imports perfectly aligned.

## Generation Flow
1. `python -m glove80 generate` loads the metadata for each registered layout family via `glove80.metadata`.
2. `glove80.layouts.generator` dispatches to the appropriate `build_layout` implementation (TailorKey or QuantumTouch), augments the generated payload with metadata fields, and writes the JSON into `layouts/<layout>/releases`.
3. Re-running the command is idempotent: if the serialized JSON already matches the generated payload, the file is left untouched.

## Shared Helpers
`glove80/layouts/common.py` codifies the shared logic between layout families: resolving `LayerRef` placeholders, assembling the ordered layer list, and injecting metadata fields.
That keeps TailorKey and QuantumTouch layout builders focused on their declarative input rather than boilerplate.

## Tests & CI
- Layer-focused tests under `tests/tailorkey/` lock down every specialized factory (HRM, cursor, mouse, etc.).
- Layout parity tests compare the composed dictionary against the checked-in JSON for every variant in `layouts/<layout>/releases`.
- The GitHub Actions `ci.yml` workflow runs `just regen` and `just ci`, so a pull request cannot be merged unless the generated JSON matches the code and all tests pass.
