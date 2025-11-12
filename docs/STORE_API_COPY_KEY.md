# `LayoutStore.copy_key_to_layer` Contract (2025-11-12)

This document codifies the behavior of `LayoutStore.copy_key_to_layer` (see `src/glove80/tui/state/store.py`) so future UI surfaces, command palette entries, and tests can rely on an identical contract.

## Signature

```python
def copy_key_to_layer(
    *,
    source_layer_index: int,
    target_layer_index: int,
    key_index: int,
) -> bool:
    """Copy the slot at (source_layer_index, key_index) into the same key on target layer."""
```

## Inputs & Validation

1. **Layer indices wrap, not clamp**: callers may pass values outside `[0, len(layers))`. The store first validates range; UI helpers wrap before invoking the API so pressing `]` on the last layer selects the first layer, keeping keyboard navigation seamless.
2. **Key index wrapping**: keyboard navigation wraps (KeyCanvas handles this), but the store treats `key_index` strictly. It validates against `len(layer.slots)` (always 80) and raises `IndexError` if the caller forgot to wrap.
3. **Source equals target**: if both layers resolve to the same index, the method returns `False` (no mutation) without touching undo/redo stacks.

## Mutation Semantics

1. **Snapshot/undo**: when a copy actually changes the destination slot, `_record_snapshot()` is invoked before mutation. Undo restores the previous payload, ensuring multi-layer copy operations can be backed out in a single step.
2. **No-op detection**: if the source slot is identical to the target slot (`value` + `params` deep compare), the method returns `False`, skips snapshotting, and leaves redo stack untouched. Callers can use the boolean return to decide whether to emit a `FooterMessage`.
3. **Dirty flag**: because the store only mutates on real changes, downstream listeners (`FooterBar`, command log) can infer dirty state from `StoreUpdated` broadcasts.

## Event Flow (UI expectation)

```
Canvas shortcut (e.g., `.`) → copy_key_to_layer(...)
    ↳ returns False → emit FooterMessage("Key already matches") at info level
    ↳ returns True  → dispatch StoreUpdated(), FooterMessage("Copied key from {src_layer} to {dst_layer}") at success level
```

- **Success path**: after `True` is returned, the caller must broadcast `StoreUpdated()` so LayerSidebar/KeyCanvas refresh and undo/redo enable. Footer should use success styling (`info` vs `success` vs `error`, see updated footer spec) to surface the completed copy.
- **Failure/exception**: invalid indices bubble up as `IndexError`; UI surfaces catch and display an error footer entry (`error` severity) while leaving store state untouched.

## Testing Notes

- Unit coverage lives in `tests/tui/unit/test_store.py::test_copy_key_to_layer_*`, asserting range checks, no-op behavior, and undo integration.
- When adding new surfaces (palette command, multi-copy tool), re-use these semantics rather than duplicating logic. Prefer checking the boolean return to avoid duplicate dirty events.
