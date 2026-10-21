import pytest

from subeventually_core.cube import (
    ALL_MOVES,
    FACE_TURNS,
    M2,
    RW,
    SOLVED,
    U2,
    Corner,
    CubeState,
    E,
    Edge,
    Face,
    Layer,
    M,
    Move,
    S,
    U,
)

NEW_LAYERS = tuple(dict.fromkeys(m.layer for m in ALL_MOVES if m not in FACE_TURNS))
FLIPPING_LAYERS = {Layer.F, Layer.B, Layer.S, Layer.FW, Layer.BW}


def test_there_are_54_distinct_moves_starting_with_the_face_turns() -> None:
    assert len(set(ALL_MOVES)) == 54
    assert ALL_MOVES[:18] == FACE_TURNS


def test_new_move_names() -> None:
    names = [str(m) for m in ALL_MOVES[18:]]
    tokens = ["M", "E", "S", "Uw", "Dw", "Lw", "Rw", "Fw", "Bw", "x", "y", "z"]
    assert names == [f"{token}{suffix}" for token in tokens for suffix in ("", "2", "'")]


@pytest.mark.parametrize("layer", NEW_LAYERS, ids=lambda layer: layer.value)
def test_new_quarter_turn_has_order_exactly_4(layer: Layer) -> None:
    quarter = Move(layer, 1)
    states = [SOLVED.apply_all([quarter] * k) for k in range(1, 5)]
    assert [s == SOLVED for s in states] == [False, False, False, True]


@pytest.mark.parametrize("move", ALL_MOVES, ids=str)
def test_move_then_inverse_is_identity(move: Move) -> None:
    start = SOLVED.apply_all([U, M, RW])  # unsolved and held differently
    assert start.apply(move).apply(move.inverse()) == start


@pytest.mark.parametrize("layer", NEW_LAYERS, ids=lambda layer: layer.value)
def test_half_turn_is_two_quarter_turns(layer: Layer) -> None:
    quarter = Move(layer, 1)
    assert SOLVED.apply(Move(layer, 2)) == SOLVED.apply_all([quarter, quarter])


@pytest.mark.parametrize("move", ALL_MOVES, ids=str)
def test_only_moves_with_f_or_b_quarter_turns_flip_edges(move: Move) -> None:
    flips = any(SOLVED.apply(move).eo)
    assert flips == (move.layer in FLIPPING_LAYERS and move.amount != 2)


@pytest.mark.parametrize("move", ALL_MOVES, ids=str)
def test_every_move_keeps_shape_and_validity(move: Move) -> None:
    state = SOLVED.apply(move)
    # Re-run the public shape checks that the unchecked apply() path skips.
    assert CubeState(*state.cubies, frame=state.frame) == state
    assert state.is_valid()


def test_h_perm() -> None:
    state = SOLVED.apply_all([M2, U, M2, U2, M2, U, M2])
    assert state.frame == 0
    assert state.cp == SOLVED.cp
    assert state.co == SOLVED.co
    assert state.eo == SOLVED.eo
    assert (state.edge_slot(Edge.UF), state.edge_slot(Edge.UB)) == (Edge.UB, Edge.UF)
    assert (state.edge_slot(Edge.UL), state.edge_slot(Edge.UR)) == (Edge.UR, Edge.UL)
    assert state.ep[4:] == SOLVED.ep[4:]


# Hand-checked against a physical cube: start solved, white on top, green in front.
# Pieces are stored relative to the centers, so each check says which centers a piece
# now sits between; on a real cube, look at the centers around the piece.


def test_m_by_hand() -> None:
    state = SOLVED.apply(M)
    # White center moves to the front, green down, yellow to the back, blue up.
    assert state.held == (Face.B, Face.U)
    # The white-green-red corner did not move; it now sits between blue, white and red.
    assert state.corner_slot(Corner.URF) is Corner.UBR
    # The white-green-orange corner now sits between blue, white and orange.
    assert state.corner_slot(Corner.UFL) is Corner.ULB
    # The white-red edge did not move; it sits between blue and red, white next to blue.
    assert state.edge_slot(Edge.UR) is Edge.BR
    assert state.eo[Edge.BR] == 0
    # The white-green edge travelled with its centers: still between white and green.
    assert state.edge_slot(Edge.UF) is Edge.UF
    assert state.eo[Edge.UF] == 0


def test_e_by_hand() -> None:
    state = SOLVED.apply(E)
    # Green center moves to the right, red to the back, blue to the left, orange to the front.
    assert state.held == (Face.U, Face.L)
    # The white-green-red corner (still top-front-right) sits between white, orange, green.
    assert state.corner_slot(Corner.URF) is Corner.UFL
    # The white-green edge (still top-front) sits between white and orange, not flipped.
    assert state.edge_slot(Edge.UF) is Edge.UL
    assert state.eo[Edge.UL] == 0
    # The green-red edge travelled with its centers: still between green and red.
    assert state.edge_slot(Edge.FR) is Edge.FR


def test_s_by_hand() -> None:
    state = SOLVED.apply(S)
    # White center moves to the right, red down, yellow to the left, orange up.
    assert state.held == (Face.L, Face.F)
    # The white-green-red corner (still top-front-right) sits between orange, green, white.
    assert state.corner_slot(Corner.URF) is Corner.UFL
    # The white-green edge (still top-front) sits between orange and green, white sticker
    # facing up, away from green: a bad edge in ZZ terms.
    assert state.edge_slot(Edge.UF) is Edge.FL
    assert state.eo[Edge.FL] == 1
    # The white-red edge travelled with its centers: still between white and red.
    assert state.edge_slot(Edge.UR) is Edge.UR
    assert state.eo[Edge.UR] == 0


def test_rw_by_hand() -> None:
    state = SOLVED.apply(RW)
    # Green center moves up, white to the back, blue down, yellow to the front.
    assert state.held == (Face.F, Face.D)
    # The white-green-red corner turned with its centers: still between white, green, red.
    assert state.corner_slot(Corner.URF) is Corner.URF
    # Only the L layer seems turned: the white-green-orange corner did not move and now
    # sits between green, yellow and orange.
    assert state.corner_slot(Corner.UFL) is Corner.DLF
    # The white-orange edge (still top-left) sits between green and orange, not flipped.
    assert state.edge_slot(Edge.UL) is Edge.FL
    assert state.eo[Edge.FL] == 0
