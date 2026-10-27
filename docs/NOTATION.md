# Notation

This page describes how to write scrambles, algorithms and reconstructions in subeventually: which moves you can type, which common variants are understood, how text is printed back, and what is rejected and why.

Everything here is for the **3x3** cube. The notation is [WCA notation](https://www.worldcubeassociation.org/regulations/#article-12-notation), plus the extensions every cuber uses (slice moves, lowercase wide moves). The rule of thumb:

- **When you type**, the common ways of writing an alg are accepted, so you can paste it from an alg sheet, a phone note or a video description.
- **When we print**, there is a single canonical form: WCA style, single spaces.

## Quick reference

### Face turns

| Move | Turns | Direction |
|---|---|---|
| `U` | top layer | clockwise, looking at the U face |
| `D` | bottom layer | clockwise, looking at the D face |
| `R` | right layer | clockwise, looking at the R face |
| `L` | left layer | clockwise, looking at the L face |
| `F` | front layer | clockwise, looking at the F face |
| `B` | back layer | clockwise, looking at the B face |

### Slice moves

| Move | Turns | Direction |
|---|---|---|
| `M` | middle layer between L and R | same as `L` |
| `E` | middle layer between U and D | same as `D` |
| `S` | middle layer between F and B | same as `F` |

`M`, `E` and `S` are not in the WCA regulations, but they are standard in algorithms.

### Wide moves

A wide move turns a face together with the middle layer next to it.

| Move | Also written | Turns |
|---|---|---|
| `Rw` | `r` | R and M, in the direction of `R` |
| `Lw` | `l` | L and M, in the direction of `L` |
| `Uw` | `u` | U and E, in the direction of `U` |
| `Dw` | `d` | D and E, in the direction of `D` |
| `Fw` | `f` | F and S, in the direction of `F` |
| `Bw` | `b` | B and S, in the direction of `B` |

`Rw` is the WCA spelling. `r` is the same move and is just as welcome: `r U r'` and `Rw U Rw'` mean the same thing.

### Rotations

| Move | Also written | Rotates the whole cube |
|---|---|---|
| `x` | `X` | in the direction of `R` |
| `y` | `Y` | in the direction of `U` |
| `z` | `Z` | in the direction of `F` |

After a rotation, every following move is read from how the cube is now held. In `y R U R'`, the `R` turns whatever face is on the right after the `y`.

## Turn amounts

Every move takes an optional count and an optional prime mark, in that order.

| You type | Read as | Meaning |
|---|---|---|
| `R` | `R` | quarter turn clockwise |
| `R'` | `R'` | quarter turn counter-clockwise |
| `R2` | `R2` | half turn |
| `R2'` | `R2` | half turn (see below) |
| `R3` | `R'` | three quarter turns clockwise = one counter-clockwise |
| `R3'` | `R` | three quarter turns counter-clockwise = one clockwise |
| `R1` | `R` | |

The same applies to every move: `M2'`, `r3`, `y2'`, `Lw2` and so on.

> **About `R2'`.** Many alg sheets write `R2'` or `U2'` to say which way to do the double turn, as a fingertrick hint. The cube ends up the same either way, so subeventually reads `R2'` as `R2` and prints it as `R2`. The hint is not kept.

## Accepted variants

### Prime marks

Any of these work as the prime mark:

| Character | Where it comes from |
|---|---|
| `'` | the normal apostrophe on a keyboard |
| `’` | "smart quotes" on phones, macOS, word processors and many web pages |
| `′` | the typographic prime symbol |

`R’` and `R′` are both read as `R'`.

### Spaces

Spaces between moves are optional, and any amount of spaces, tabs and line breaks counts as a single separator. All of these are the same:

```
R U R' U'
R  U   R'  U'
RUR'U'
R U
R' U'
```

A digit right after a move is always that move's count, so `R2U` is `R2 U`.

### Parentheses

Parentheses group moves for readability, usually to show fingertricks:

```
(R U R' U') (R' F R F')
```

They are accepted and then ignored. They must be balanced, and they may be nested. They are not printed back: the line above is printed as `R U R' U' R' F R F'`.

## Comments

`//` starts a comment that runs to the end of the line. This is mostly useful for reconstructions:

```
x2 y      // inspection
R' F R2 D' // cross
U R U' R'
U2 (R U R') // first pair
```

Comments are kept together with the place where they appear in the move sequence. When printed back, each comment ends its line. Line breaks without a comment are not kept, so the example above is printed as:

```
x2 y // inspection
R' F R2 D' // cross
U R U' R' U2 R U R' // first pair
```

A comment with no moves before it gets a line of its own:

```
// Solve 3
R U R'
```

Only `//` starts a comment. `#` and `/* ... */` are not comments.

## Canonical output

When subeventually prints a move sequence, it always uses this form:

- WCA spelling: `Rw`, never `r`; rotations in lowercase (`x`, `y`, `z`).
- The ASCII apostrophe `'` for primes.
- Half turns as `R2`, never `R2'`. `R3` becomes `R'`, `R3'` becomes `R`, `R1` becomes `R`.
- No parentheses.
- One space between moves, nothing at the start or end.
- Each comment as `// text` at the end of its line, followed by a line break (except after the last line).

For example:

| You type | Printed as |
|---|---|
| `y (r U r') U2' (R U R3)` | `y Rw U Rw' U2 R U R'` |
| `Y RUR’U’` | `y R U R' U'` |
| `x2'  M2 U M2` | `x2 M2 U M2` |

Printing is stable: if you type the printed form back in, you get exactly the same sequence and the same text.

## What is not accepted

When something can't be read, you get the **first** problem found, with its line and column (both counted from 1) and a message, for example:

```
line 1, column 6: big-cube notation is not supported (3x3 only)
```

| You type | Problem | Message |
|---|---|---|
| `3Rw`, `2R`, `2-4r`, `3r` | big-cube notation | big-cube notation is not supported (3x3 only) |
| `[R, U]`, `[R: U]` | commutator or conjugate | commutator and conjugate notation are not supported; write the moves out |
| `(R U)3` | repeated group | repeating a group is not supported; write the moves out |
| `(R U)'` | inverted group | inverting a group is not supported; write the moves out |
| `R'2` | prime before the count | the count goes before the prime: write R2' |
| `R4`, `R0`, `R22` | turn count out of range | turn count must be 1, 2 or 3 |
| `R''` | two prime marks | a move can have only one prime mark |
| `' R` | prime with no move | prime mark without a move |
| `rw`, `rW`, `RW` | wrong case for a wide move | unknown move 'rw': write Rw or r |
| `m`, `e`, `s` | lowercase slice | unknown move 'm': slices are uppercase, as in M |
| `R w`, `Mw`, `xw` | `w` not right after a face letter | 'w' must come right after U, D, L, R, F or B, as in Rw |
| `(R U` | unclosed parenthesis | '(' is never closed |
| `R U)` | extra closing parenthesis | ')' has no matching '(' |
| `R . U`, `R # U`, `R / U`, `Q` | anything else | unexpected character '.' |

The position points at the character where the problem starts. For example, in `R U2 3Rw` the error is at column 6, the `3`.

Commutators, conjugates and repetition are useful shorthand, but they are out of scope for now. Write the moves out in full instead.

An empty input, or one with only comments, is not an error: it is an empty sequence.

## Examples

| What | You type | Printed as |
|---|---|---|
| WCA scramble | `D2 F2 U' B2 R2 U2 R2 F2 D' L2 U' R' D B' L' U' R F' L' U2 B` | same |
| Sexy move | `(R U R' U')` | `R U R' U'` |
| T perm | `(R U R' U') (R' F) (R2 U' R') U' (R U R' F')` | `R U R' U' R' F R2 U' R' U' R U R' F'` |
| U perm (Ua) | `R U' R U R U R U' R' U' R2` | same |
| H perm | `M2 U M2 U2 M2 U M2` | same |
| Sune from the back, with an extra-turn `R3` | `y2 (R U R' U) R U2' R3` | `y2 R U R' U R U2 R'` |
| An OLL typed on a phone | `Y rUR’U’r’FRF’` | `y Rw U R' U' Rw' F R F'` |

## Facelets

A cube state can also be written sticker by sticker, as a **facelet string**: 54 letters, one per sticker. This is the format used by most cube solvers and tools, so states can be compared with them. Each letter is the color of a sticker, named by the face whose center has that color in WCA orientation:

| Letter | Color |
|---|---|
| `U` | white |
| `R` | red |
| `F` | green |
| `D` | yellow |
| `L` | orange |
| `B` | blue |

### Order

The stickers come face by face in the order U, R, F, D, L, B, nine per face, row by row. The numbers below are the positions in the string, counted from 0, on the unfolded cube:

```
           0  1  2
           3  4  5
           6  7  8
36 37 38  18 19 20   9 10 11  45 46 47
39 40 41  21 22 23  12 13 14  48 49 50
42 43 44  24 25 26  15 16 17  51 52 53
          27 28 29
          30 31 32
          33 34 35
```

The top block is U, the middle row is L, F, R, B, and the bottom block is D. Each face is drawn as you see it when you look straight at it:

| Face | Looked at from | The top row of the drawing is next to |
|---|---|---|
| U | above | B (so 6 7 8 are next to F) |
| L, F, R, B | its own side, U on top | U |
| D | below | F (so 27 28 29 are next to F) |

In particular, B is seen from behind: its left column (45 48 51) is next to R.

A solved cube is:

```
UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
```

and after `R`:

```
UUFUUFUUFRRRRRRRRRFFDFFDFFDDDBDDBDDBLLLLLLLLLUBBUBBUBB
```

### Rotations and the centers

The string shows the cube **as you hold it**: positions 0 to 8 are whatever face is on top now. The letters are still colors, so after a rotation the centers (positions 4, 13, 22, 31, 40, 49) move. After `x`, green is on top:

```
FFFFFFFFFRRRRRRRRRDDDDDDDDDBBBBBBBBBLLLLLLLLLUUUUUUUUU
```

So the centers tell how the cube is held. Most other tools assume the centers never move. They read and write the same strings as subeventually for a cube held in WCA orientation (`U` center on top, `F` center in front).

### Reading a facelet string

A facelet string must be exactly 54 of the letters `U`, `R`, `F`, `D`, `L`, `B`. Spaces and line breaks at the start or end are ignored; nothing else is. How the cube is held is read from the centers, so reading a string back gives exactly the state it was printed from.

When the string is not a real cube, you get the **first** problem found, checked in the order below. Characters are counted from 1, after the surrounding spaces are removed, and also named by face and sticker (`R4` is the fourth sticker of the R block). Pieces are named by where they are as the cube is held.

| Problem | Example message |
|---|---|
| wrong length | facelet string must have 54 characters, got 53 |
| color letters instead of face letters | character 1 (U1) is 'W': use face letters (U, R, F, D, L, B), not color letters |
| any other character | character 13 (R4) is 'x': only U, R, F, D, L and B are allowed |
| a color not on exactly 9 stickers | each color must appear 9 times: U appears 10 times, R appears 8 times |
| top and front centers equal or opposite | centers U on top and D in front are opposite: no cube can be held like that |
| centers of a mirrored cube | centers are a mirror image: with U on top and F in front, R must be on the right, got L |
| other impossible centers | impossible centers: with U on top and F in front, R must be on the right, got B |
| a corner that does not exist | the corner at URF has stickers U, F, R (clockwise): no corner has these colors in this order |
| an edge that does not exist | the edge at UF has stickers F, F: no edge has these colors |
| the same piece twice | corner UFL appears twice, at UFL and DFR |
| a twisted corner | impossible cube: corner twist sum is 1, must be a multiple of 3 (a twisted corner) |
| a flipped edge | impossible cube: edge flip sum is 1, must be even (a flipped edge) |
| two swapped pieces | impossible cube: corner and edge permutations have different parity (two swapped pieces) |

A corner's stickers are listed clockwise, starting from the one on the top or bottom face.

### Text net

The same layout, printed as text with a letter per sticker:

```
       U U U
       U U U
       U U U
L L L  F F F  R R R  B B B
L L L  F F F  R R R  B B B
L L L  F F F  R R R  B B B
       D D D
       D D D
       D D D
```
