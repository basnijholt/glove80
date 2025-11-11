# Footer & Notifications UX Spec

## Overview
Minimal, Textual-friendly feedback for two high-frequency actions: **layer switching** and **key copying**.

_Status (2025-11-11): Implemented – FooterBar + KeyCanvas copy notifications behave as specified; doc retained for future UX tweaks._

---

## Footer Display

### Baseline (No Action)
```
Layer: Base · Key: #00 · dirty=no
```

### Layer Switch
**Timing:** Instant on layer selection in sidebar
**Pattern:** `Layer: {layer_name} · Key: #{key_index:02d} · dirty={yes|no}`

**Examples:**
- `Layer: Lower · Key: #15 · dirty=no`
- `Layer: Upper · Key: -- · dirty=yes` _(when no key selected in new layer)_

**Behavior:**
- Updates immediately when sidebar item is clicked
- Preserves key_index from previous layer, or shows `--` if unavailable
- Dirty flag reflects current store state

---

## Notifications (Toast/Brief)

### Copy Success (Status Bar Pop-up)
**Trigger:** User presses copy button or shortcut in Inspector
**Duration:** 2–3 seconds
**Message Pattern:** `Copied key #{key_index:02d}: {behavior} → {layer_name}`

**Examples:**
- `Copied key #00: &kp TAB → Lower`
- `Copied key #25: &lt KC_A KC_B &gt → Base`
- `Copied key #40: &tog_layer Upper → Upper`

**Style:** Success/info level (neutral or green tint if color available)

### Error: No Selection
**Trigger:** Copy pressed with no key selected (layer_index < 0 or key_index unset)
**Duration:** 1–2 seconds
**Message:** `Cannot copy: no key selected`

**Style:** Warning/error level (red tint if color available)

### Error: Out of Range
**Trigger:** Destination key position invalid or layer not found
**Duration:** 1–2 seconds
**Message:** `Cannot copy: invalid position or layer`

**Style:** Warning/error level (red tint if color available)

---

## Implementation Notes

1. **Footer:** Rendered by `FooterBar` widget; updates via `SelectionChanged` message

2. **Notifications:** Use `app.notify(message, severity="info"|"warning")` from Textual

3. **Consistency:** Keep messages simple, lowercase, plain English (avoid jargon)

4. **No Modals:** All feedback is non-blocking; modals reserved for name input or critical confirmations

5. **Dirty State:** Footer reflects store mutations; copy action should trigger `StoreUpdated()` message for consistency

---

## Message Hierarchy

| Action | Feedback | Channel | Block |
|--------|----------|---------|-------|
| Switch layer | Instant footer update | Footer bar | No |
| Copy key (success) | Toast notification | Toast/notify | No |
| Copy key (no selection) | Error toast | Toast/notify | No |
| Copy key (invalid dest.) | Error toast | Toast/notify | No |

---

## Future Extensions

- **Multi-select feedback:** "Copied N keys to layer X"
- **Undo notification:** "Undo: reverted key #00 in Base"
- **Validation:** Live hint in footer if current key has warnings (e.g., undefined param)
