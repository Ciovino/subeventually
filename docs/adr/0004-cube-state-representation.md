# 0004. Cube state representation

- Status: proposed
- Date: 2026-10-21

## Context

Every later part of the project (notation, algorithm validation and recognition, stage goals, solvers, analysis) operates on a 3x3 cube state, so its representation is hard to change later. It has to:

- be compact, immutable and hashable (states are dictionary keys in lookup and search);
- make the 18 face turns cheap, and admit precomputed move tables and pruning tables for the solvers;
- port directly to Rust if the hot paths move there (see ARCHITECTURE.md, Performance);
- support slice moves (M, E, S), wide moves and rotations (x, y, z) in M1b without a redesign, because solve reconstructions use them and the cost model penalizes rotations;
- be able to represent impossible cubes, so user input can be checked and rejected with a reason.

The cube-solving literature (Kociemba's two-phase algorithm and the solvers derived from it) uses a cubie model with well-known numbering and orientation conventions. Following it lets us compare against published coordinates and test vectors.

## Decision

### Cubie model

A state stores the 8 corners and 12 edges as permutation and orientation arrays, **relative to the centers**, plus a `frame`: which of the 24 whole-cube orientations the cube is held in. Centers are never stored as pieces. A facelet (sticker) view exists only for display and input validation.

### Numbering

Positions (slots) and pieces share the same indices, following Kociemba. The piece with index `i` belongs in slot `i`.

| Index | Corner | Index | Edge | Index | Edge |
|---|---|---|---|---|---|
| 0 | URF | 0 | UR | 8 | FR |
| 1 | UFL | 1 | UF | 9 | FL |
| 2 | ULB | 2 | UL | 10 | BL |
| 3 | UBR | 3 | UB | 11 | BR |
| 4 | DFR | 4 | DR | | |
| 5 | DLF | 5 | DF | | |
| 6 | DBL | 6 | DL | | |
| 7 | DRB | 7 | DB | | |

The E-slice edges have the contiguous indices 8-11. They are exposed as `Corner` and `Edge` `IntEnum`s.

### Permutation meaning

The canonical arrays are **slot-indexed**: `cp[slot]` is the corner piece currently in `slot`, and `co[slot]` is its orientation there (likewise `ep`, `eo`). This is the "is replaced by" form used in the literature, and it makes composition a single indexing pass.

Piece-indexed views are not stored. `corner_slot(piece)` and `edge_slot(piece)` compute on demand the slot a piece is in, by scanning `cp` or `ep` (at most 8 or 12 entries). The state therefore has a single source of truth and nothing to keep consistent. Orientation is slot-indexed only; a piece's orientation is `co[corner_slot(piece)]`.

### Orientation conventions

Corners. Each corner slot lists its facelets clockwise (seen from outside the cube), starting from its U/D facelet: URF = (U, R, F), UFL = (U, F, L), ULB = (U, L, B), UBR = (U, B, R), DFR = (D, F, R), DLF = (D, L, F), DBL = (D, B, L), DRB = (D, R, B). `co[slot]` is the index (0, 1, 2) of the facelet showing the piece's U/D sticker: 0 = oriented, 1 = twisted clockwise, 2 = twisted counter-clockwise.

Edges. Each edge slot and each edge piece has a reference sticker: the U/D one for U- and D-layer edges, the F/B one for E-slice edges. `eo[slot]` is 0 if the piece's reference sticker is on the slot's reference facelet, else 1. With this definition only F and B quarter turns change edge orientation, the familiar ZZ "good/bad edge" rule. `<R, L, U, D>` and all half turns preserve it.

Invariants of every reachable state:

- sum of `co` ≡ 0 (mod 3);
- sum of `eo` ≡ 0 (mod 2);
- parity of `cp` equals parity of `ep`.

### Move storage and application

Each move is a precomputed cubie transformation with the same shape as a state (`cp`, `co`, `ep`, `eo`). Applying a move `m` to a state `s` is the product `s · m`:

```
cp[i] = s.cp[m.cp[i]]
co[i] = (s.co[m.cp[i]] + m.co[i]) % 3
ep[i] = s.ep[m.ep[i]]
eo[i] = (s.eo[m.ep[i]] + m.eo[i]) % 2
```

Only the six clockwise quarter turns are written by hand. `X2` and `X'` are built at import time by composing them (`X·X`, `X·X·X`), so the 18 tables cannot disagree with each other. Applying a move to the solved state yields its own transformation, for example:

```
U:  cp = (UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB)   co = (0, 0, 0, 0, 0, 0, 0, 0)
    ep = (UB, UR, UF, UL, DR, DF, DL, DB, FR, FL, BL, BR)   eo = all 0
R:  cp = (DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR)   co = (2, 0, 0, 1, 1, 0, 0, 2)
    ep = (FR, UF, UL, UB, BR, DF, DL, DB, DR, FL, BL, UR)   eo = all 0
F:  cp = (UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB)   co = (1, 2, 0, 0, 2, 1, 0, 0)
    ep = (UR, FL, UL, UB, DR, FR, DL, DB, UF, DF, BL, BR)
    eo = (0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0)
```

The tables are private module data. Integer coordinate move tables and pruning tables (twist, flip, slice, ...) are built later by the solvers on top of these transformations. They are not part of the state. The product formula and tables translate 1:1 into Rust (`[u8; 8]`, `[u8; 12]`).

### Centers, slices, wide moves and rotations

Implemented in M1b. They fit the model as follows:

- `frame` identifies which fixed-center face is currently on top and which is in front. Frame 0 is the WCA scrambling orientation (white on U, green on F).
- A face move written in notation turns the fixed face that the current frame puts in that position. Under frame 0 this is the identity mapping.
- A rotation changes only `frame`; the cubies, being relative to the centers, are unchanged.
- Slice and wide moves are face turns followed by a rotation:

  | Move | Equivalent | Move | Equivalent |
  |---|---|---|---|
  | M | R L' x' | Rw | L x |
  | E | U D' y' | Uw | D y |
  | S | F' B z | Fw | B z |

  Lw, Dw and Bw follow by symmetry (R x', U y', F z').

The face turns of M1a never change the frame, so it is always 0 there.

### Public API

All in the module `subeventually_core.cube`:

```python
class Layer(Enum): U, D, L, R, F, B         # M1b extends it

@dataclass(frozen=True, slots=True)
class Move:
    layer: Layer
    amount: Literal[1, 2, 3]                 # 3 = prime
    def inverse(self) -> Move: ...           # amount -> 4 - amount
    def __str__(self) -> str: ...            # "R", "R2", "R'"

U, U2, U_PRIME, D, ..., B_PRIME: Move       # the 18 face turns

@dataclass(frozen=True, slots=True)
class CubeState:
    cp: tuple[int, ...]                      # 8, slot -> piece
    co: tuple[int, ...]                      # 8, values 0..2
    ep: tuple[int, ...]                      # 12, slot -> piece
    eo: tuple[int, ...]                      # 12, values 0..1
    frame: int = 0                           # 0..23

    @property
    def cubies(self) -> tuple[...]: ...      # (cp, co, ep, eo), frame-free key
    def corner_slot(self, piece: Corner) -> Corner: ...  # piece -> slot
    def edge_slot(self, piece: Edge) -> Edge: ...        # piece -> slot
    def apply(self, move: Move) -> CubeState: ...
    def apply_all(self, moves: Iterable[Move]) -> CubeState: ...
    def is_solved(self) -> bool: ...
    def is_valid(self) -> bool: ...
    def validate(self) -> None: ...          # raises, naming the broken invariant

SOLVED: CubeState

def invert(moves: Sequence[Move]) -> tuple[Move, ...]: ...
```

- `Layer` names what a move turns. In M1a its members are the six faces. M1b adds slices, wide layers and rotations as new members, so the type is not renamed later.
- Public construction checks **shape only**: array lengths, value ranges, `cp` and `ep` are permutations, `frame` in range. It does not check solvability. `is_valid()` and `validate()` check the three invariants, so an impossible cube (a twisted corner, a single flipped edge, two swapped pieces) can still be represented and reported.
- `apply()` and `apply_all()` build their results through a private unchecked constructor that skips the shape checks. This is safe because every `CubeState` is shape-valid by construction, every move table is shape-valid, and the product of two shape-valid transformations is shape-valid (permutations compose to permutations, orientations stay in range modulo 3 and 2). It relies only on shape, not on solvability, so it also holds for impossible states.
- A move sequence is a plain `tuple[Move, ...]`. A richer algorithm type (parsing, comments, stage markers) is left to M1b and will wrap a tuple.

### Equality and solvedness

- `==` and `hash` compare `cp`, `co`, `ep`, `eo` and `frame`. A state records the cube exactly as held.
- `is_solved()` ignores `frame`: a solved cube held after `y2` is solved.
- Code that must not distinguish orientations (solvers, case lookup tables, stage goals) keys on `cubies`.

## Consequences

- The solvers get a fixed-center model on which standard coordinates and pruning tables can be defined directly, and results can be checked against reference implementations.
- Slice moves, wide moves and rotations need no change to the state in M1b: they are face turns plus a frame change. Reconstructions and display keep track of how the cube is held.
- Impossible user input can be represented and rejected with a specific reason.
- A state stores only `cp`, `co`, `ep`, `eo` and `frame`. Finding a piece's slot is a linear scan (at most 12 entries) rather than O(1). That is negligible next to the cost of building states, and searches that track pieces heavily are expected to use coordinates anyway.
- Moves skip the shape checks, so applying them costs only the product itself. The skip relies on an invariant (every move table is shape-valid) that the tests must cover, since a broken table would no longer be caught at construction.
- Pure-Python search over `CubeState` objects will still be slow. The solvers are expected to search over integer coordinates instead, and that is where any Rust port belongs.
- `==` being frame-sensitive is a trap: callers comparing cubes "as positions" must compare `cubies`, not states.
- Naming the type `Layer` from the start means M1b only adds members, with no rename. Code that matches exhaustively on `Layer` will still need updating then.
- Once this ADR is accepted, the "Cube model" section of ARCHITECTURE.md should point to it.
