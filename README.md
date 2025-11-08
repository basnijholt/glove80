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
│  ├─ glove80/base.py           # shared LayerSpec/KeySpec primitives
│  ├─ glove80/specs/            # reusable spec dataclasses & helpers
│  ├─ glove80/metadata.py       # typed metadata loader
│  ├─ glove80/tailorkey/        # TailorKey implementation (layers + specs)
│  └─ glove80/quantum_touch/    # QuantumTouch implementation (layers + specs)
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
  helpers used by every layout. `src/glove80/specs/` builds on top of that with
  declarative macro/hold-tap/combo/input-listener data classes.
- **src/glove80/tailorkey/** contains TailorKey’s generated layers (styled with
  helpers such as `layers/mouse.py` and `layers/hrm.py`), the `specs/`
  describing macros/combos/etc., and the `layouts.py` composer that stitches
  everything together.
- **src/glove80/quantum_touch/** mirrors the same structure for QuantumTouch;
  mouse layers and finger-training layers are driven by shared factories so new
  variants only require spec changes.
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

1. Modify the declarative specs under `src/glove80/<layout>/specs/` or the
   supporting layer helpers in `src/glove80/<layout>/layers/`. If the release
   metadata (UUID, title, notes, output path) changes, edit the JSON file under
   `sources/`.
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

- When adding a new TailorKey layer, extend the appropriate factory (for
  example `tailorkey/layers/mouse.py` or `tailorkey/layers/hrm.py`) or create a
  new `LayerSpec`-driven module and register it in
  `glove80.tailorkey.layers.LAYER_PROVIDERS`. QuantumTouch already generates
  mouse/finger-training layers from shared helpers
  (`quantum_touch/layers/mouse_layers.py` and `finger_layers.py`); update those
  factories instead of copying JSON.
- To introduce a new release variant, add its entry to the appropriate metadata
  file under `sources/`; the typed loader (`metadata.py`) keeps the rest of the
  tooling in sync automatically.

## Continuous Integration

GitHub Actions already runs `uv run pytest` plus `python3 scripts/generate_layouts.py` on every push/PR and fails the build if `original/` changes. This ensures the checked-in JSON artifacts always match the code-generated layouts.
