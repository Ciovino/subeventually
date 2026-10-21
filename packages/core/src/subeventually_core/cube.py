"""Cubie-based 3x3 cube state, moves and inverses.

The representation is decided in ``docs/adr/0004-cube-state-representation.md``:

- corners and edges are numbered in Kociemba order (see :class:`Corner` and :class:`Edge`);
- permutation arrays are slot-indexed: ``cp[slot]`` is the piece in that slot;
- corner twist is the index of the facelet showing the piece's U/D sticker, with the
  slot's facelets listed clockwise from its U/D facelet;
- edge flip uses the F/B rule: only F and B quarter turns change it;
- the cubies are stored relative to the centers, plus a ``frame`` (one of the 24 whole-cube
  orientations). Rotations change only the frame; a face move turns the fixed face that the
  frame puts in that position.

The frame numbering is decided in ``docs/adr/0005-frame-encoding.md``:
``frame = 4 * up + n``, where ``up`` is the :class:`Face` on top and ``n`` counts ``y``
rotations from a base orientation for that top face.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Final, Literal

type Amount = Literal[1, 2, 3]
type Cubies = tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, ...]]

_N_CORNERS: Final = 8
_N_EDGES: Final = 12
_N_FRAMES: Final = 24


class Corner(IntEnum):
    """Corner slots and pieces, in Kociemba order."""

    URF = 0
    UFL = 1
    ULB = 2
    UBR = 3
    DFR = 4
    DLF = 5
    DBL = 6
    DRB = 7


class Edge(IntEnum):
    """Edge slots and pieces, in Kociemba order. The E-slice edges are 8-11."""

    UR = 0
    UF = 1
    UL = 2
    UB = 3
    DR = 4
    DF = 5
    DL = 6
    DB = 7
    FR = 8
    FL = 9
    BL = 10
    BR = 11


class Face(IntEnum):
    """A fixed face, named by where its center is in frame 0 (white on U, green on F).

    Ordered like the standard facelet string (U, R, F, D, L, B). A :class:`Layer` is a
    position in notation; a ``Face`` is a center, wherever the cube is held.
    """

    U = 0  # white
    R = 1  # red
    F = 2  # green
    D = 3  # yellow
    L = 4  # orange
    B = 5  # blue


class Layer(Enum):
    """What a move turns: a face, a middle slice, a wide layer or the whole cube (x, y, z).

    Each value is the WCA notation token.
    """

    U = "U"
    D = "D"
    L = "L"
    R = "R"
    F = "F"
    B = "B"
    M = "M"
    E = "E"
    S = "S"
    UW = "Uw"
    DW = "Dw"
    LW = "Lw"
    RW = "Rw"
    FW = "Fw"
    BW = "Bw"
    X = "x"
    Y = "y"
    Z = "z"


_INVERSE_AMOUNT: Final[dict[Amount, Amount]] = {1: 3, 2: 2, 3: 1}
_SUFFIX: Final[dict[Amount, str]] = {1: "", 2: "2", 3: "'"}


@dataclass(frozen=True, slots=True)
class Move:
    """A turn of ``layer`` by ``amount`` clockwise quarter turns (3 means prime)."""

    layer: Layer
    amount: Amount

    def __post_init__(self) -> None:
        if self.amount not in _SUFFIX:
            raise ValueError(f"move amount must be 1, 2 or 3, got {self.amount!r}")

    def inverse(self) -> Move:
        """Return the move that undoes this one (``R`` -> ``R'``, ``R2`` -> ``R2``)."""
        return Move(self.layer, _INVERSE_AMOUNT[self.amount])

    def __str__(self) -> str:
        return self.layer.value + _SUFFIX[self.amount]


U: Final = Move(Layer.U, 1)
U2: Final = Move(Layer.U, 2)
U_PRIME: Final = Move(Layer.U, 3)
D: Final = Move(Layer.D, 1)
D2: Final = Move(Layer.D, 2)
D_PRIME: Final = Move(Layer.D, 3)
L: Final = Move(Layer.L, 1)
L2: Final = Move(Layer.L, 2)
L_PRIME: Final = Move(Layer.L, 3)
R: Final = Move(Layer.R, 1)
R2: Final = Move(Layer.R, 2)
R_PRIME: Final = Move(Layer.R, 3)
F: Final = Move(Layer.F, 1)
F2: Final = Move(Layer.F, 2)
F_PRIME: Final = Move(Layer.F, 3)
B: Final = Move(Layer.B, 1)
B2: Final = Move(Layer.B, 2)
B_PRIME: Final = Move(Layer.B, 3)
M: Final = Move(Layer.M, 1)
M2: Final = Move(Layer.M, 2)
M_PRIME: Final = Move(Layer.M, 3)
E: Final = Move(Layer.E, 1)
E2: Final = Move(Layer.E, 2)
E_PRIME: Final = Move(Layer.E, 3)
S: Final = Move(Layer.S, 1)
S2: Final = Move(Layer.S, 2)
S_PRIME: Final = Move(Layer.S, 3)
UW: Final = Move(Layer.UW, 1)
UW2: Final = Move(Layer.UW, 2)
UW_PRIME: Final = Move(Layer.UW, 3)
DW: Final = Move(Layer.DW, 1)
DW2: Final = Move(Layer.DW, 2)
DW_PRIME: Final = Move(Layer.DW, 3)
LW: Final = Move(Layer.LW, 1)
LW2: Final = Move(Layer.LW, 2)
LW_PRIME: Final = Move(Layer.LW, 3)
RW: Final = Move(Layer.RW, 1)
RW2: Final = Move(Layer.RW, 2)
RW_PRIME: Final = Move(Layer.RW, 3)
FW: Final = Move(Layer.FW, 1)
FW2: Final = Move(Layer.FW, 2)
FW_PRIME: Final = Move(Layer.FW, 3)
BW: Final = Move(Layer.BW, 1)
BW2: Final = Move(Layer.BW, 2)
BW_PRIME: Final = Move(Layer.BW, 3)
X: Final = Move(Layer.X, 1)
X2: Final = Move(Layer.X, 2)
X_PRIME: Final = Move(Layer.X, 3)
Y: Final = Move(Layer.Y, 1)
Y2: Final = Move(Layer.Y, 2)
Y_PRIME: Final = Move(Layer.Y, 3)
Z: Final = Move(Layer.Z, 1)
Z2: Final = Move(Layer.Z, 2)
Z_PRIME: Final = Move(Layer.Z, 3)

_AMOUNTS: Final[tuple[Amount, ...]] = (1, 2, 3)
_FACE_LAYERS: Final = (Layer.U, Layer.D, Layer.L, Layer.R, Layer.F, Layer.B)

FACE_TURNS: Final = tuple(Move(layer, amount) for layer in _FACE_LAYERS for amount in _AMOUNTS)
"""The 18 face turns: U, U2, U', D, ..., B'."""

ALL_MOVES: Final = tuple(Move(layer, amount) for layer in Layer for amount in _AMOUNTS)
"""Every 3x3 move (54): the face turns, then slices, wide moves and rotations."""


def _parity(perm: tuple[int, ...]) -> int:
    """Return 0 for an even permutation, 1 for an odd one (inversion count, n <= 12)."""
    n = len(perm)
    return sum(perm[i] > perm[j] for i in range(n) for j in range(i + 1, n)) % 2


def _check_permutation(name: str, perm: tuple[int, ...], n: int) -> None:
    if len(perm) != n:
        raise ValueError(f"{name} must have {n} entries, got {len(perm)}")
    if sorted(perm) != list(range(n)):
        raise ValueError(f"{name} must be a permutation of 0..{n - 1}, got {perm}")


def _check_orientation(name: str, orient: tuple[int, ...], n: int, modulus: int) -> None:
    if len(orient) != n:
        raise ValueError(f"{name} must have {n} entries, got {len(orient)}")
    if not all(0 <= value < modulus for value in orient):
        raise ValueError(f"{name} values must be in 0..{modulus - 1}, got {orient}")


@dataclass(frozen=True, slots=True)
class CubeState:
    """An immutable cube state: cubies relative to the centers, plus the held orientation.

    ``cp``/``ep`` are slot-indexed permutations (``cp[slot]`` is the piece in ``slot``) and
    ``co``/``eo`` the orientation of the piece in each slot. Construction checks shape only;
    use :meth:`is_valid` or :meth:`validate` to check that the state is solvable.
    Equality and hashing include ``frame``; compare :attr:`cubies` to ignore it.
    """

    cp: tuple[int, ...]
    co: tuple[int, ...]
    ep: tuple[int, ...]
    eo: tuple[int, ...]
    frame: int = 0

    def __post_init__(self) -> None:
        for name in ("cp", "co", "ep", "eo"):
            if not isinstance(getattr(self, name), tuple):
                raise TypeError(f"{name} must be a tuple, got {type(getattr(self, name))}")
        _check_permutation("cp", self.cp, _N_CORNERS)
        _check_orientation("co", self.co, _N_CORNERS, 3)
        _check_permutation("ep", self.ep, _N_EDGES)
        _check_orientation("eo", self.eo, _N_EDGES, 2)
        if not 0 <= self.frame < _N_FRAMES:
            raise ValueError(f"frame must be in 0..{_N_FRAMES - 1}, got {self.frame}")

    @classmethod
    def _unchecked(
        cls,
        cp: tuple[int, ...],
        co: tuple[int, ...],
        ep: tuple[int, ...],
        eo: tuple[int, ...],
        frame: int,
    ) -> CubeState:
        # Skips __post_init__: only for results of products of shape-valid states (ADR 0004).
        state = object.__new__(cls)
        object.__setattr__(state, "cp", cp)
        object.__setattr__(state, "co", co)
        object.__setattr__(state, "ep", ep)
        object.__setattr__(state, "eo", eo)
        object.__setattr__(state, "frame", frame)
        return state

    def _multiply(self, m: CubeState, frame: int) -> CubeState:
        # The cubies of self · m, held in ``frame`` (m.frame is ignored).
        cp, co, ep, eo = self.cp, self.co, self.ep, self.eo
        return CubeState._unchecked(
            tuple(cp[i] for i in m.cp),
            tuple((co[i] + t) % 3 for i, t in zip(m.cp, m.co, strict=True)),
            tuple(ep[i] for i in m.ep),
            tuple((eo[i] + f) % 2 for i, f in zip(m.ep, m.eo, strict=True)),
            frame,
        )

    @property
    def cubies(self) -> Cubies:
        """The frame-free part of the state, ``(cp, co, ep, eo)``, for orientation-blind keys."""
        return (self.cp, self.co, self.ep, self.eo)

    def corner_slot(self, piece: Corner) -> Corner:
        """Return the slot that corner ``piece`` is currently in."""
        return Corner(self.cp.index(piece))

    def edge_slot(self, piece: Edge) -> Edge:
        """Return the slot that edge ``piece`` is currently in."""
        return Edge(self.ep.index(piece))

    @property
    def held(self) -> tuple[Face, Face]:
        """How the cube is held: the ``(up, front)`` faces, e.g. ``(Face.U, Face.F)`` in frame 0."""
        faces = _FRAME_FACES[self.frame]
        return (faces[Layer.U], faces[Layer.F])

    def apply(self, move: Move) -> CubeState:
        """Return the state after ``move``, read relative to how the cube is held."""
        transformation, frame = _MOVE_TABLE[self.frame, move]
        return self._multiply(transformation, frame)

    def apply_all(self, moves: Iterable[Move]) -> CubeState:
        """Return the state after applying ``moves`` in order."""
        state = self
        for move in moves:
            transformation, frame = _MOVE_TABLE[state.frame, move]
            state = state._multiply(transformation, frame)
        return state

    def is_solved(self) -> bool:
        """Return whether every cubie is solved, whatever orientation the cube is held in."""
        return self.cubies == SOLVED.cubies

    def validate(self) -> None:
        """Check that the state is reachable by turning a solved cube.

        Raises:
            ValueError: naming the first broken invariant (corner twist, edge flip, parity).
        """
        if sum(self.co) % 3 != 0:
            raise ValueError(f"corner twist sum is {sum(self.co)}, must be a multiple of 3")
        if sum(self.eo) % 2 != 0:
            raise ValueError(f"edge flip sum is {sum(self.eo)}, must be even")
        if _parity(self.cp) != _parity(self.ep):
            raise ValueError("corner and edge permutations have different parity")

    def is_valid(self) -> bool:
        """Return whether the state is reachable by turning a solved cube."""
        try:
            self.validate()
        except ValueError:
            return False
        return True


SOLVED: Final = CubeState(
    tuple(range(_N_CORNERS)), (0,) * _N_CORNERS, tuple(range(_N_EDGES)), (0,) * _N_EDGES
)


def _quarter_turn(
    cp: tuple[Corner, ...], co: tuple[int, ...], ep: tuple[Edge, ...], eo: tuple[int, ...]
) -> CubeState:
    # Through the public constructor, so a typo in a hand-written table fails at import.
    return CubeState(tuple(int(c) for c in cp), co, tuple(int(e) for e in ep), eo)


_C, _E = Corner, Edge
_QUARTER_TURNS: Final[dict[Layer, CubeState]] = {
    Layer.U: _quarter_turn(
        (_C.UBR, _C.URF, _C.UFL, _C.ULB, _C.DFR, _C.DLF, _C.DBL, _C.DRB),
        (0, 0, 0, 0, 0, 0, 0, 0),
        (_E.UB, _E.UR, _E.UF, _E.UL, _E.DR, _E.DF, _E.DL, _E.DB, _E.FR, _E.FL, _E.BL, _E.BR),
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ),
    Layer.D: _quarter_turn(
        (_C.URF, _C.UFL, _C.ULB, _C.UBR, _C.DLF, _C.DBL, _C.DRB, _C.DFR),
        (0, 0, 0, 0, 0, 0, 0, 0),
        (_E.UR, _E.UF, _E.UL, _E.UB, _E.DF, _E.DL, _E.DB, _E.DR, _E.FR, _E.FL, _E.BL, _E.BR),
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ),
    Layer.L: _quarter_turn(
        (_C.URF, _C.ULB, _C.DBL, _C.UBR, _C.DFR, _C.UFL, _C.DLF, _C.DRB),
        (0, 1, 2, 0, 0, 2, 1, 0),
        (_E.UR, _E.UF, _E.BL, _E.UB, _E.DR, _E.DF, _E.FL, _E.DB, _E.FR, _E.UL, _E.DL, _E.BR),
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ),
    Layer.R: _quarter_turn(
        (_C.DFR, _C.UFL, _C.ULB, _C.URF, _C.DRB, _C.DLF, _C.DBL, _C.UBR),
        (2, 0, 0, 1, 1, 0, 0, 2),
        (_E.FR, _E.UF, _E.UL, _E.UB, _E.BR, _E.DF, _E.DL, _E.DB, _E.DR, _E.FL, _E.BL, _E.UR),
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ),
    Layer.F: _quarter_turn(
        (_C.UFL, _C.DLF, _C.ULB, _C.UBR, _C.URF, _C.DFR, _C.DBL, _C.DRB),
        (1, 2, 0, 0, 2, 1, 0, 0),
        (_E.UR, _E.FL, _E.UL, _E.UB, _E.DR, _E.FR, _E.DL, _E.DB, _E.UF, _E.DF, _E.BL, _E.BR),
        (0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0),
    ),
    Layer.B: _quarter_turn(
        (_C.URF, _C.UFL, _C.UBR, _C.DRB, _C.DFR, _C.DLF, _C.ULB, _C.DBL),
        (0, 0, 1, 2, 0, 0, 2, 1),
        (_E.UR, _E.UF, _E.UL, _E.BR, _E.DR, _E.DF, _E.DL, _E.BL, _E.FR, _E.FL, _E.UB, _E.DB),
        (0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1),
    ),
}


# Frames (ADR 0005). A frame is stored as a map from notation position to the fixed face
# currently there. All 24 are derived from three rotation permutations, never written out.

type _FaceMap = dict[Layer, Face]

# For each rotation, position <- the position whose face moves there (others stay).
_ROTATION_SOURCES: Final[dict[Layer, dict[Layer, Layer]]] = {
    Layer.X: {Layer.U: Layer.F, Layer.F: Layer.D, Layer.D: Layer.B, Layer.B: Layer.U},
    Layer.Y: {Layer.F: Layer.R, Layer.R: Layer.B, Layer.B: Layer.L, Layer.L: Layer.F},
    Layer.Z: {Layer.U: Layer.L, Layer.R: Layer.U, Layer.D: Layer.R, Layer.L: Layer.D},
}

# The single rotation that brings each face up, with its quarter-turn count.
_BASE_ROTATIONS: Final[dict[Face, tuple[Layer, int] | None]] = {
    Face.U: None,
    Face.R: (Layer.Z, 3),
    Face.F: (Layer.X, 1),
    Face.D: (Layer.Z, 2),
    Face.L: (Layer.Z, 1),
    Face.B: (Layer.X, 3),
}


def _rotate(faces: _FaceMap, rotation: Layer, quarters: int) -> _FaceMap:
    sources = _ROTATION_SOURCES[rotation]
    for _ in range(quarters % 4):
        faces = {pos: faces[sources.get(pos, pos)] for pos in _FACE_LAYERS}
    return faces


def _held(faces: _FaceMap) -> tuple[Face, Face]:
    return (faces[Layer.U], faces[Layer.F])


def _build_frames() -> tuple[_FaceMap, ...]:
    identity = {layer: Face[layer.name] for layer in _FACE_LAYERS}
    frames: list[_FaceMap] = []
    for up in Face:
        base = identity
        if (setup := _BASE_ROTATIONS[up]) is not None:
            base = _rotate(base, *setup)
        frames.extend(_rotate(base, Layer.Y, n) for n in range(4))
    # Guards the derivation: 24 distinct orientations, numbered 4 * up + n.
    if len({_held(f) for f in frames}) != _N_FRAMES:
        raise RuntimeError("frame table does not list 24 distinct orientations")
    if any(_held(f)[0] != i // 4 for i, f in enumerate(frames)):
        raise RuntimeError("frame table does not satisfy frame // 4 == up")
    return tuple(frames)


_FRAME_FACES: Final = _build_frames()
_FRAME_INDEX: Final = {_held(faces): frame for frame, faces in enumerate(_FRAME_FACES)}
_ROTATED_FRAME: Final = {
    rotation: tuple(_FRAME_INDEX[_held(_rotate(faces, rotation, 1))] for faces in _FRAME_FACES)
    for rotation in _ROTATION_SOURCES
}


def frame_of(up: Face, front: Face) -> int:
    """Return the frame in which ``up`` is on top and ``front`` is in front (ADR 0005).

    Raises:
        ValueError: if the two faces are equal or opposite.
    """
    try:
        return _FRAME_INDEX[up, front]
    except KeyError:
        raise ValueError(
            f"front must be adjacent to up, got up={up.name}, front={front.name}"
        ) from None


# Each layer as face turns (notation position, quarter turns) followed by an optional
# rotation (axis, quarter turns), as in ADR 0004. A move by ``amount`` repeats every part
# ``amount`` times; this is valid because a rotation never moves the faces turned with it.
type _Recipe = tuple[tuple[tuple[Layer, int], ...], tuple[Layer, int] | None]

_RECIPES: Final[dict[Layer, _Recipe]] = {
    **{face: (((face, 1),), None) for face in _FACE_LAYERS},
    Layer.M: (((Layer.R, 1), (Layer.L, 3)), (Layer.X, 3)),
    Layer.E: (((Layer.U, 1), (Layer.D, 3)), (Layer.Y, 3)),
    Layer.S: (((Layer.F, 3), (Layer.B, 1)), (Layer.Z, 1)),
    Layer.UW: (((Layer.D, 1),), (Layer.Y, 1)),
    Layer.DW: (((Layer.U, 1),), (Layer.Y, 3)),
    Layer.LW: (((Layer.R, 1),), (Layer.X, 3)),
    Layer.RW: (((Layer.L, 1),), (Layer.X, 1)),
    Layer.FW: (((Layer.B, 1),), (Layer.Z, 1)),
    Layer.BW: (((Layer.F, 1),), (Layer.Z, 3)),
    **{rotation: ((), (rotation, 1)) for rotation in _ROTATION_SOURCES},
}


def _build_move_table() -> dict[tuple[int, Move], tuple[CubeState, int]]:
    # (frame, move) -> (cubie transformation, frame afterwards). Face turns are mapped
    # to the fixed face in that position before the rotation changes the frame.
    table: dict[tuple[int, Move], tuple[CubeState, int]] = {}
    for frame, faces in enumerate(_FRAME_FACES):
        for layer, (turns, rotation) in _RECIPES.items():
            for amount in _AMOUNTS:
                transformation = SOLVED
                for position, quarters in turns:
                    quarter = _QUARTER_TURNS[Layer[faces[position].name]]
                    for _ in range(quarters * amount % 4):
                        transformation = transformation._multiply(quarter, 0)
                new_frame = frame
                if rotation is not None:
                    axis, quarters = rotation
                    for _ in range(quarters * amount % 4):
                        new_frame = _ROTATED_FRAME[axis][new_frame]
                table[frame, Move(layer, amount)] = (transformation, new_frame)
    return table


_MOVE_TABLE: Final = _build_move_table()


def invert(moves: Sequence[Move]) -> tuple[Move, ...]:
    """Return the sequence that undoes ``moves``: reversed, each move inverted."""
    return tuple(move.inverse() for move in reversed(moves))
