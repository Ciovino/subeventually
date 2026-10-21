# 0005. Frame encoding

- Status: accepted
- Date: 2026-10-21

## Context

[ADR 0004](0004-cube-state-representation.md) stores a cube as cubies relative to the centers plus a `frame`: which of the 24 whole-cube orientations the cube is held in. Its section "Centers, slices, wide moves and rotations" fixes the semantics:

- frame 0 is the WCA orientation, white on U and green on F;
- a face move turns the fixed face that the frame puts in that position;
- rotations change only the frame;
- slices and wide moves are face turns followed by a rotation.

It does not say how the other 23 frames are numbered. That number is public: it is an argument of the `CubeState` constructor and part of `==` and `hash`, and it will be persisted later. Once chosen, it cannot change without migrating stored data. Issue #6 also asks for a readable way to tell how a state is held.

This ADR extends ADR 0004. It does not supersede it.

## Decision

### Fixed faces

A new public `IntEnum`, `Face`, names the six fixed faces by the position of their center in frame 0:

| Face | Value | Center |
|---|---|---|
| U | 0 | white |
| R | 1 | red |
| F | 2 | green |
| D | 3 | yellow |
| L | 4 | orange |
| B | 5 | blue |

The order is the facelet order U, R, F, D, L, B used by the standard 54-character facelet string, so the facelet view can reuse it.

`Face` and `Layer` are different types on purpose. A `Layer` is a position in notation ("the face that is on the right now"). A `Face` is a center ("the red center"). Under frame 0 they coincide, and under any other frame they do not.

### Numbering

```
frame = 4 * up + n
```

- `up` is the `Face` currently on top, so `frame // 4` reads it directly.
- `n` (0..3) is the number of `y` rotations made after a base orientation for that top face. The base orientation is the one reached by the single rotation that brings that face up:

  | Up | Base rotation | Front in the base orientation |
  |---|---|---|
  | U (white) | none | F (green) |
  | R (red) | `z'` | F (green) |
  | F (green) | `x` | D (yellow) |
  | D (yellow) | `z2` | F (green) |
  | L (orange) | `z` | F (green) |
  | B (blue) | `x'` | U (white) |

The full table (up / front):

| frame | up / front | frame | up / front | frame | up / front |
|---|---|---|---|---|---|
| 0 | white / green | 8 | green / yellow | 16 | orange / green |
| 1 | white / red | 9 | green / red | 17 | orange / white |
| 2 | white / blue | 10 | green / white | 18 | orange / blue |
| 3 | white / orange | 11 | green / orange | 19 | orange / yellow |
| 4 | red / green | 12 | yellow / green | 20 | blue / white |
| 5 | red / yellow | 13 | yellow / orange | 21 | blue / red |
| 6 | red / blue | 14 | yellow / blue | 22 | blue / yellow |
| 7 | red / white | 15 | yellow / red | 23 | blue / orange |

A `y` rotation moves a frame to the next one in its block of four (3 wraps to 0). `x` and `z` move between blocks.

### Derived tables

Nothing in this section is written by hand. At import time, each frame is built from the identity by applying its base rotation and then `n` times `y`. The rotations are permutations of positions (`new[position] = old[source]`):

| Rotation | Permutation |
|---|---|
| `x` | U <- F, F <- D, D <- B, B <- U |
| `y` | F <- R, R <- B, B <- L, L <- F |
| `z` | U <- L, R <- U, D <- R, L <- D |

From this, two private tables are derived:

- a face map per frame, from notation face (U, D, L, R, F, B) to the `Face` currently in that position;
- for each of `x`, `y` and `z`, a map from frame to the frame after the rotation. Rotations are relative to how the cube is currently held, as in WCA notation.

An import-time check asserts that the 24 (up, front) pairs are distinct and that `frame // 4` is the top face.

A notation face move under a frame turns the mapped `Face` in the same direction. Whole-cube rotations preserve handedness, so "clockwise seen from outside the face" carries over.

### Move application

Slices and wide moves expand to face turns and a rotation as listed in ADR 0004. Each rotation is about the same axis as the face turns it follows, so it never changes where those faces map. A move with amount `k` is the same expansion with every part repeated `k` times: `M2 = R2 L2 x2`.

For every pair (frame, move), a private table holds the cubie transformation and the resulting frame. There are 24 frames × 54 moves, built at import from the 18 face-turn transformations. `apply` therefore stays one product and one lookup, as in ADR 0004, and the table ports to Rust as a fixed-size array indexed by `[frame][move]`.

### Public API

In addition to the API in ADR 0004, all in `subeventually_core.cube`:

```python
class Face(IntEnum): U, R, F, D, L, B        # values 0..5

class Layer(Enum):                           # ADR 0004 members, plus:
    M, E, S                                  # values "M", "E", "S"
    UW, DW, LW, RW, FW, BW                   # values "Uw", "Dw", "Lw", "Rw", "Fw", "Bw"
    X, Y, Z                                  # values "x", "y", "z"

class CubeState:
    @property
    def held(self) -> tuple[Face, Face]: ... # (up, front)

def frame_of(up: Face, front: Face) -> int: ...  # ValueError if equal or opposite

FACE_TURNS: tuple[Move, ...]                 # the 18 face turns
ALL_MOVES: tuple[Move, ...]                  # all 54 moves: face turns, slices, wide moves, rotations
M, M2, M_PRIME, ..., Z, Z2, Z_PRIME: Move    # one constant per new move
```

`str(Move)` is unchanged: the layer's value plus `""`, `"2"` or `"'"`, giving `M'`, `Rw2` and `x'`.

`apply()` and `apply_all()` accept any frame. The M1a restriction to frame 0 is removed.

## Consequences

- Reading a frame number needs no table: `frame // 4` is the center on top, and `frame % 4` counts `y` turns from a fixed base.
- The numbering is now a compatibility contract. Changing it later requires a new ADR and a migration of stored states.
- Frames and rotation results are derived from three small permutations, so they cannot disagree with each other. The import-time check guards the derivation.
- Adding rotations and slices to `Layer` breaks code that iterates `Layer` expecting the six faces. Such code should use `FACE_TURNS`.
- `Face` and `Layer` overlap in their first six names, which can be confused. The type checker catches passing one where the other is expected.
