# Footer & Notifications UX Spec

## Overview
Minimal, Textual-friendly feedback for two high-frequency actions: **layer switching** and **key copying**.

_Status (2025-11-12): Implemented – FooterBar + KeyCanvas copy notifications behave as specified; severity levels + catalog below define how new workflows (Macro/HoldTap/Combo/Listener, palette actions) surface status._

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

### Severity & Styling

| Severity | Color/Style | Duration | Usage |
| --- | --- | --- | --- |
| `info` | Neutral (slate) text on default background | ≤ 2 s | Layer switches, palette hints, no-op copy |
| `success` | Green accent background/text | 2–3 s | Successful copy, save/apply, CLI validation success |
| `error` | Red accent background/text | 3–4 s | Validation failures, delete blocked, CLI errors |

Toast helpers (`app.notify(...)`) must pass the severity so Textual themes can render consistent colors, and the FooterBar mirrors the last severity badge when showing messages inline.

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

### Message Catalog (Layer & Key Ops)

| Event ID | Severity | Text Template | Trigger |
| --- | --- | --- | --- |
| `layer.selected` | info | `Layer: {layer} · Key: #{key:02d} · dirty={yes|no}` | Sidebar selection, palette jump |
| `layer.wrap_next` | info | `Wrapped to {layer}` | `]` on last layer or palette wrap command |
| `layer.wrap_prev` | info | `Wrapped to {layer}` | `[` on first layer |
| `key.copy.success` | success | `Copied key #{key:02d} → {layer}` | `copy_key_to_layer` returned True |
| `key.copy.noop` | info | `Key #{key:02d} already matches {layer}` | `copy_key_to_layer` returned False |
| `key.copy.error` | error | `Cannot copy: {reason}` | Exception raised from `copy_key_to_layer` |
| `macro.save` | success | `Saved macro {name}` | MacroTab Apply/Add |
| `macro.rename` | success | `Renamed macro {old} → {new}` | MacroTab rename action |
| `macro.delete_blocked` | error | `Cannot delete {name}: referenced {count}×` | MacroTab delete attempt with references |
| `palette.command.error` | error | `Command failed: {message}` | Command palette action raised |
| `palette.command.success` | success | `Ran {command_label}` | Command palette action completed |

Widgets should standardize on these IDs so logs/telemetry can aggregate usage; text templates may add detail but must include the key/layer names for debugging.
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
