# Architecture

This project keeps every part of the Glove80 layout toolchain in version control so the published JSON artifacts can be recreated exactly from code.

## Source of Truth
- **Specs (`src/glove80/families/*/specs/`)** define macros, hold-taps, combos, input listeners, and per-layer overrides using typed dataclasses from `glove80.specs.primitives`.
- **Layer factories (`src/glove80/families/*/layers/`)** build sparse `LayerSpec` objects into the 80-key arrays expected by the Glove80 firmware.
- TailorKey factories mix and match reusable helpers (mouse, cursor, HRM, etc.), while QuantumTouch layers reuse the same primitives to build finger-training variants.
- Glorious Engrammer stores Sunaku's 32 layers as explicit row tuples that feed the same `rows_to_layer_spec` helper as the other families.
- **Metadata (`src/glove80/families/<family>/metadata.json`)** stores the immutable release information checked in by the original layout authors (UUIDs, parent UUIDs, titles, tags, notes, and the relative output path). Packaging the metadata keeps CLI invocations and library imports perfectly aligned.

## Generation Flow
1. `glove80 generate` loads the metadata for each registered layout family via `glove80.metadata`.
2. `glove80.layouts.family` registers every family at import time; `glove80.layouts.generator` iterates that registry, builds the layouts, augments them with metadata, and writes the JSON into `layouts/<family>/releases`.
3. Re-running the command is idempotent: if the serialized JSON already matches the generated payload, the file is left untouched.

## Shared Helpers
`glove80/layouts/common.py` and the higher-level `glove80.layouts.LayoutBuilder` codify the shared logic between layout families: resolving `LayerRef` placeholders, assembling the ordered layer list, and injecting metadata fields. Layout authors can now compose whole layouts by instantiating the builder, feeding it layer providers, and calling `.build()`—the same workflow used inside the built-in families. The builder exposes ergonomics-focused helpers such as `add_mouse_layers()`, `add_cursor_layer()`, and `add_home_row_mods()`; you wire in the concrete providers (e.g., `build_mouse_layers`) once and then script against those high-level methods for both library and CLI workflows.

```python
from glove80.layouts import LayoutBuilder
from glove80.layouts.components import LayoutFeatureComponents
from glove80.families.tailorkey.layers import build_mouse_layers, build_cursor_layer, build_hrm_layers

def _hrm_layers_for(variant: str):
    layers = build_hrm_layers(variant)
    return LayoutFeatureComponents(layers=layers)

generated_layers = build_all_layers(variant)
builder = LayoutBuilder(
    metadata_key="tailorkey",
    variant=variant,
    common_fields=COMMON_FIELDS,
    layer_names=_layer_names(variant),
    mouse_layers_provider=build_mouse_layers,
    cursor_layers_provider=lambda v: {"Cursor": build_cursor_layer(v)},
    home_row_provider=_hrm_layers_for,
)
builder.add_layers(generated_layers)
builder.add_home_row_mods(target_layer="Typing", position="before")
builder.add_cursor_layer(insert_after="Autoshift")
builder.add_mouse_layers(insert_after="Lower")
payload = builder.build()
```

The helper methods guarantee that the required macros, combos, input listeners, and layer indices stay in sync each time the feature is applied, so TailorKey, Default, QuantumTouch, Glorious Engrammer, and any user scripts all share one consistent pipeline.

## Tests & CI
- Layer-focused tests under `tests/tailorkey/` lock down every specialized factory (HRM, cursor, mouse, etc.).
- Parity tests under `tests/glorious_engrammer/` ensure the Sunaku release stays identical to the generated payload.
- Layout parity tests compare the composed dictionary against the checked-in JSON for every variant in `layouts/<layout>/releases`.
- The GitHub Actions `ci.yml` workflow runs `just regen` and `just ci`, so a pull request cannot be merged unless the generated JSON matches the code and all tests pass.
