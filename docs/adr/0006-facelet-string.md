# 0006. Facelet string

- Status: accepted
- Date: 2026-10-27

## Context

[ADR 0004](0004-cube-state-representation.md) keeps a facelet (sticker) view for display and input validation only. M1d adds that view, and with it a text form of a whole cube state: a string of 54 stickers. This string will be used in ways that make it hard to change later:

- it is how we compare our cube model with external tools (solvers, alg viewers), so it should match what they use;
- users will type or paste it to enter a physical cube state, and it will be stored alongside solves;
- it has to represent how the cube is held. States carry a `frame` ([ADR 0005](0005-frame-encoding.md)), while most tools assume the centers never move.

The widely used format is the 54-character string in URFDLB order from Kociemba's two-phase solver. It has no notion of a held orientation.

## Decision

The exact format is defined in [NOTATION.md, section "Facelets"](../NOTATION.md#facelets), the single source of truth. This ADR records the choices behind it:

- **Standard order and layout.** Faces in the order U, R, F, D, L, B, nine stickers each, laid out as in Kociemba's solver. A cube held in WCA orientation (frame 0) has exactly the string other tools use.
- **Letters are colors.** Each letter is a sticker's color, named by the `Face` whose center has that color in frame 0 (`U` = white, …, `B` = blue). Face letters are used rather than color letters (W, Y, G, …) because they are what the standard format uses and they don't depend on a color scheme.
- **Positions are as held.** The string shows the cube as the user sees it, so after a rotation the centers move. The six centers encode the frame, and import reads the frame back from them. No extra field is needed, and frame-0 strings stay compatible with external tools.
- **Strict input.** Import accepts exactly 54 face letters, after stripping leading and trailing whitespace. Anything else is rejected with a reason. A string that uses color letters gets a hint to use face letters. A more forgiving input layer (color letters, other schemes, separators) may come later, and it will translate to this format, not change it.
- **Impossible states are rejected.** Import reports the first problem found, from wrong length up to the invariants of ADR 0004. The categories are listed in NOTATION.md. The wording of messages is not part of the format.

## Consequences

- The format is a compatibility contract. Changing the order, the layout, the letters or the rule about centers requires a new ADR and a migration of stored strings.
- Frame-0 strings can be passed to and from external tools unchanged. A string for any other frame must have its letters relabeled by the centers before a center-fixed tool can read it.
- A state and its string correspond one to one, including the frame: import(export(s)) == s.
- Because the format is defined only in NOTATION.md, the docs and the ADR cannot disagree on details. This ADR changes only if the decision itself changes.
