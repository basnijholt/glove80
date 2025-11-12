# Keyboard-First TUI Sketch

ASCII mockup highlighting the keys as the primary element:

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ Glove80 ▾   Layout: Default ▾   Variant: Windows ▾                 Layer: Base ▾                 Save  Undo  Redo ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐           ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
│Esc  │  │ 1   │  │ 2   │  │ 3   │  │ 4   │  │ 5   │           │ 6   │  │ 7   │  │ 8   │  │ 9   │  │ 0   │  │ -   │
│&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │           │&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │
│param│  │freq ▌│  │freq ▌│  │freq ▌│  │freq ▌│  │freq ▌│       │freq ▌│  │freq ▌│  │freq ▌│  │freq ▌│  │freq ▌│  │freq ▌│
└─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘           └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘

┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐           ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
│Tab  │  │ Q   │  │ W   │  │ E   │  │ R   │  │ T   │           │ Y   │  │ U   │  │ I   │  │ O   │  │ P   │  │ Bsp │
│&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │    gap    │&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │  │&kp  │
│     │  │hold:│  │hold:│  │hold:│  │hold:│  │hold:│           │hold:│  │hold:│  │hold:│  │hold:│  │hold:│  │hold:│
└─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘           └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘

┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐           ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
│Ctrl │  │ A   │  │ S   │  │ D   │  │ F   │  │ G   │           │ H   │  │ J   │  │ K   │  │ L   │  │ ;   │  │ '   │
│held │  │tap  │  │tap  │  │tap  │  │tap  │  │tap  │           │tap  │  │tap  │  │tap  │  │tap  │  │tap  │  │tap  │
│none │  │hold │  │hold │  │hold │  │hold │  │hold │           │hold │  │hold │  │hold │  │hold │  │hold │  │hold │
└─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘           └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘

Thumb fans continue with the same square caps, offset lower and angled inward:

   ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                    ┌─────┐  ┌─────┐  ┌─────┐
   │Cmd  │  │Space│  │Lower│  │Raise│                    │Mouse│  │Enter│  │Adjust│
   │mt   │  │tap  │  │hold │  │hold │                    │tap  │  │tap  │  │hold │
   │none │  │none │  │layer│  │layer│                    │mode │  │macro│  │layer│
   └─────┘  └─────┘  └─────┘  └─────┘                    └─────┘  └─────┘  └─────┘

Bottom strip stays minimal:

`[ Base* ] [ Lower ] [ Raise ] [ Mouse ] [ Adjust ]    + Layer ▾    Inspector ▸`

Each keycap carries its tap behavior, hold behavior, and parameter text in three short lines, letting the physical layout remain the star of the interface.
