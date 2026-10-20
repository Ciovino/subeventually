"""Cubie-based 3x3 cube state, face turns and inverses.

The representation is decided in ``docs/adr/0004-cube-state-representation.md``:

- corners and edges are numbered in Kociemba order (see :class:`Corner` and :class:`Edge`);
- permutation arrays are slot-indexed: ``cp[slot]`` is the piece in that slot;
- corner twist is the index of the facelet showing the piece's U/D sticker, with the
  slot's facelets listed clockwise from its U/D facelet;
- edge flip uses the F/B rule: only F and B quarter turns change it;
- the cubies are stored relative to the centers, plus a ``frame`` (one of the 24 whole-cube
  orientations). In this milestone face turns never change the frame.
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


class Layer(Enum):
    """What a move turns. In this milestone only the six faces."""

    U = "U"
    D = "D"
    L = "L"
    R = "R"
    F = "F"
    B = "B"


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

    def _multiply(self, m: CubeState) -> CubeState:
        cp, co, ep, eo = self.cp, self.co, self.ep, self.eo
        return CubeState._unchecked(
            tuple(cp[i] for i in m.cp),
            tuple((co[i] + t) % 3 for i, t in zip(m.cp, m.co, strict=True)),
            tuple(ep[i] for i in m.ep),
            tuple((eo[i] + f) % 2 for i, f in zip(m.ep, m.eo, strict=True)),
            self.frame,
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

    def _check_frame_supported(self) -> None:
        if self.frame != 0:
            raise NotImplementedError("applying moves with a frame other than 0 comes in M1b")

    def apply(self, move: Move) -> CubeState:
        """Return the state after ``move``.

        Raises:
            NotImplementedError: if ``frame`` is not 0 (frames are implemented in M1b).
        """
        self._check_frame_supported()
        return self._multiply(_MOVE_TABLE[move])

    def apply_all(self, moves: Iterable[Move]) -> CubeState:
        """Return the state after applying ``moves`` in order.

        Raises:
            NotImplementedError: if ``frame`` is not 0 (frames are implemented in M1b).
        """
        self._check_frame_supported()
        state = self
        for move in moves:
            state = state._multiply(_MOVE_TABLE[move])
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


def _build_move_table() -> dict[Move, CubeState]:
    table: dict[Move, CubeState] = {}
    for layer, quarter in _QUARTER_TURNS.items():
        half = quarter._multiply(quarter)
        table[Move(layer, 1)] = quarter
        table[Move(layer, 2)] = half
        table[Move(layer, 3)] = half._multiply(quarter)
    return table


_MOVE_TABLE: Final = _build_move_table()


def invert(moves: Sequence[Move]) -> tuple[Move, ...]:
    """Return the sequence that undoes ``moves``: reversed, each move inverted."""
    return tuple(move.inverse() for move in reversed(moves))
