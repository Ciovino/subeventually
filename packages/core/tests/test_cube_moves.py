from typing import Literal

import pytest

from subeventually_core.cube import (
    R_PRIME,
    SOLVED,
    U_PRIME,
    Corner,
    CubeState,
    Edge,
    Layer,
    Move,
    R,
    U,
)

AMOUNTS: tuple[Literal[1, 2, 3], ...] = (1, 2, 3)
FACE_TURNS = tuple(Move(layer, amount) for layer in Layer for amount in AMOUNTS)


def test_there_are_18_distinct_face_turns() -> None:
    assert len(set(FACE_TURNS)) == 18


def test_move_names() -> None:
    assert [str(m) for m in FACE_TURNS] == [
        f"{face}{suffix}" for face in "UDLRFB" for suffix in ("", "2", "'")
    ]


def test_move_constants_match_their_names() -> None:
    assert (str(U), str(U_PRIME), str(R), str(R_PRIME)) == ("U", "U'", "R", "R'")


@pytest.mark.parametrize("move", FACE_TURNS, ids=str)
def test_inverse_of_inverse_is_the_move(move: Move) -> None:
    assert move.inverse().inverse() == move
    assert move.inverse().layer is move.layer


def test_inverse_amounts() -> None:
    assert R.inverse() == R_PRIME
    assert Move(Layer.R, 2).inverse() == Move(Layer.R, 2)


@pytest.mark.parametrize("amount", [0, 4, -1])
def test_move_rejects_bad_amounts(amount: int) -> None:
    with pytest.raises(ValueError, match="amount"):
        Move(Layer.U, amount)  # type: ignore[arg-type]


# Hand-checked against a physical cube: hold white on U, green on F, do one turn,
# and read off which piece sits in each slot and how it is twisted or flipped.


def test_u_by_hand() -> None:
    state = SOLVED.apply(U)
    # U layer cycles clockwise seen from above: UBR -> URF -> UFL -> ULB -> UBR.
    assert state.cp[Corner.URF] == Corner.UBR
    assert state.cp[Corner.UFL] == Corner.URF
    assert state.cp[Corner.ULB] == Corner.UFL
    assert state.cp[Corner.UBR] == Corner.ULB
    assert state.ep[Edge.UR] == Edge.UB
    assert state.ep[Edge.UF] == Edge.UR
    assert state.ep[Edge.UL] == Edge.UF
    assert state.ep[Edge.UB] == Edge.UL
    # The U/D stickers stay on U: nothing twists or flips.
    assert state.co == (0,) * 8
    assert state.eo == (0,) * 12
    # D layer and E slice are untouched.
    for c in (Corner.DFR, Corner.DLF, Corner.DBL, Corner.DRB):
        assert state.cp[c] == c
    for e in (Edge.DR, Edge.DF, Edge.DL, Edge.DB, Edge.FR, Edge.FL, Edge.BL, Edge.BR):
        assert state.ep[e] == e


def test_r_by_hand() -> None:
    state = SOLVED.apply(R)
    # R corners: DFR -> URF -> UBR -> DRB -> DFR (front goes up).
    assert state.cp[Corner.URF] == Corner.DFR
    assert state.cp[Corner.UBR] == Corner.URF
    assert state.cp[Corner.DRB] == Corner.UBR
    assert state.cp[Corner.DFR] == Corner.DRB
    # Twists: the white/yellow sticker ends up on F at URF (2), on B at UBR (1), ...
    assert state.co[Corner.URF] == 2
    assert state.co[Corner.UBR] == 1
    assert state.co[Corner.DRB] == 2
    assert state.co[Corner.DFR] == 1
    # R edges: FR -> UR -> BR -> DR -> FR.
    assert state.ep[Edge.UR] == Edge.FR
    assert state.ep[Edge.BR] == Edge.UR
    assert state.ep[Edge.DR] == Edge.BR
    assert state.ep[Edge.FR] == Edge.DR
    # R never flips edges (F/B rule).
    assert state.eo == (0,) * 12
    # L-side pieces are untouched.
    for c in (Corner.UFL, Corner.ULB, Corner.DLF, Corner.DBL):
        assert state.cp[c] == c
        assert state.co[c] == 0


# For F, D, L and B the docstrings say what to look for on a real cube (white U, green F,
# red R; so orange L, blue B, yellow D).
# Corner twist: each slot lists its faces clockwise starting from U/D (URF = U, R, F);
# the twist is the position (0, 1, 2) of the face showing the white/yellow sticker.
# Edge flip: an edge is flipped (1) when its white/yellow sticker, or green/blue for the
# four E-slice edges, is not on the slot's U/D face (or F/B face for an E-slice slot).


def _assert_untouched(state: CubeState, corners: list[Corner], edges: list[Edge]) -> None:
    for c in corners:
        assert (state.cp[c], state.co[c]) == (c, 0)
    for e in edges:
        assert (state.ep[e], state.eo[e]) == (e, 0)


def test_f_by_hand() -> None:
    """F (front face clockwise): U stickers go to R, R to D, D to L, L to U.

    Corners:
    - white-green-orange (UFL) goes to URF, white on R: URF is (U, R, F), twist 1;
    - white-red-green (URF) goes to DFR, white on R: DFR is (D, F, R), twist 2;
    - yellow-green-red (DFR) goes to DLF, yellow on L: DLF is (D, L, F), twist 1;
    - yellow-orange-green (DLF) goes to UFL, yellow on L: UFL is (U, F, L), twist 2.

    Edges, all four flipped:
    - white-green (UF) goes to FR, white on R instead of F;
    - green-red (FR) goes to DF, green on F instead of D;
    - yellow-green (DF) goes to FL, yellow on L instead of F;
    - green-orange (FL) goes to UF, green on F instead of U.

    The B layer and the U/D edges at the sides and back do not move.
    """
    state = SOLVED.apply(Move(Layer.F, 1))
    assert (state.cp[Corner.URF], state.co[Corner.URF]) == (Corner.UFL, 1)
    assert (state.cp[Corner.DFR], state.co[Corner.DFR]) == (Corner.URF, 2)
    assert (state.cp[Corner.DLF], state.co[Corner.DLF]) == (Corner.DFR, 1)
    assert (state.cp[Corner.UFL], state.co[Corner.UFL]) == (Corner.DLF, 2)
    assert (state.ep[Edge.FR], state.eo[Edge.FR]) == (Edge.UF, 1)
    assert (state.ep[Edge.DF], state.eo[Edge.DF]) == (Edge.FR, 1)
    assert (state.ep[Edge.FL], state.eo[Edge.FL]) == (Edge.DF, 1)
    assert (state.ep[Edge.UF], state.eo[Edge.UF]) == (Edge.FL, 1)
    _assert_untouched(
        state,
        [Corner.ULB, Corner.UBR, Corner.DBL, Corner.DRB],
        [Edge.UR, Edge.UL, Edge.UB, Edge.DR, Edge.DL, Edge.DB, Edge.BL, Edge.BR],
    )


def test_d_by_hand() -> None:
    """D (bottom face clockwise, seen from below): F stickers go to R, R to B, B to L, L to F.

    Corners, no twists (yellow stays on D):
    - yellow-green-red (DFR) goes to DRB;
    - yellow-red-blue (DRB) goes to DBL;
    - yellow-blue-orange (DBL) goes to DLF;
    - yellow-orange-green (DLF) goes to DFR.

    Edges, no flips (yellow stays on D):
    - yellow-green (DF) goes to DR;
    - yellow-red (DR) goes to DB;
    - yellow-blue (DB) goes to DL;
    - yellow-orange (DL) goes to DF.

    The U layer and the E slice do not move.
    """
    state = SOLVED.apply(Move(Layer.D, 1))
    assert (state.cp[Corner.DRB], state.co[Corner.DRB]) == (Corner.DFR, 0)
    assert (state.cp[Corner.DBL], state.co[Corner.DBL]) == (Corner.DRB, 0)
    assert (state.cp[Corner.DLF], state.co[Corner.DLF]) == (Corner.DBL, 0)
    assert (state.cp[Corner.DFR], state.co[Corner.DFR]) == (Corner.DLF, 0)
    assert (state.ep[Edge.DR], state.eo[Edge.DR]) == (Edge.DF, 0)
    assert (state.ep[Edge.DB], state.eo[Edge.DB]) == (Edge.DR, 0)
    assert (state.ep[Edge.DL], state.eo[Edge.DL]) == (Edge.DB, 0)
    assert (state.ep[Edge.DF], state.eo[Edge.DF]) == (Edge.DL, 0)
    _assert_untouched(
        state,
        [Corner.URF, Corner.UFL, Corner.ULB, Corner.UBR],
        [Edge.UR, Edge.UF, Edge.UL, Edge.UB, Edge.FR, Edge.FL, Edge.BL, Edge.BR],
    )


def test_l_by_hand() -> None:
    """L (left face clockwise): U stickers go to F, F to D, D to B, B to U.

    Corners:
    - white-green-orange (UFL) goes to DLF, white on F: DLF is (D, L, F), twist 2;
    - yellow-orange-green (DLF) goes to DBL, yellow on B: DBL is (D, B, L), twist 1;
    - yellow-blue-orange (DBL) goes to ULB, yellow on B: ULB is (U, L, B), twist 2;
    - white-orange-blue (ULB) goes to UFL, white on F: UFL is (U, F, L), twist 1.

    Edges, none flipped (each reference sticker lands on the new slot's reference face):
    - white-orange (UL) goes to FL, white on F;
    - green-orange (FL) goes to DL, green on D;
    - yellow-orange (DL) goes to BL, yellow on B;
    - blue-orange (BL) goes to UL, blue on U.

    The R layer and the U/D edges at the front and back do not move.
    """
    state = SOLVED.apply(Move(Layer.L, 1))
    assert (state.cp[Corner.DLF], state.co[Corner.DLF]) == (Corner.UFL, 2)
    assert (state.cp[Corner.DBL], state.co[Corner.DBL]) == (Corner.DLF, 1)
    assert (state.cp[Corner.ULB], state.co[Corner.ULB]) == (Corner.DBL, 2)
    assert (state.cp[Corner.UFL], state.co[Corner.UFL]) == (Corner.ULB, 1)
    assert (state.ep[Edge.FL], state.eo[Edge.FL]) == (Edge.UL, 0)
    assert (state.ep[Edge.DL], state.eo[Edge.DL]) == (Edge.FL, 0)
    assert (state.ep[Edge.BL], state.eo[Edge.BL]) == (Edge.DL, 0)
    assert (state.ep[Edge.UL], state.eo[Edge.UL]) == (Edge.BL, 0)
    _assert_untouched(
        state,
        [Corner.URF, Corner.UBR, Corner.DFR, Corner.DRB],
        [Edge.UR, Edge.UF, Edge.UB, Edge.DR, Edge.DF, Edge.DB, Edge.FR, Edge.BR],
    )


def test_b_by_hand() -> None:
    """B (back face clockwise, seen from behind): U stickers go to L, L to D, D to R, R to U.

    Corners:
    - white-blue-red (UBR) goes to ULB, white on L: ULB is (U, L, B), twist 1;
    - white-orange-blue (ULB) goes to DBL, white on L: DBL is (D, B, L), twist 2;
    - yellow-blue-orange (DBL) goes to DRB, yellow on R: DRB is (D, R, B), twist 1;
    - yellow-red-blue (DRB) goes to UBR, yellow on R: UBR is (U, B, R), twist 2.

    Edges, all four flipped:
    - white-blue (UB) goes to BL, white on L instead of B;
    - blue-orange (BL) goes to DB, blue on B instead of D;
    - yellow-blue (DB) goes to BR, yellow on R instead of B;
    - blue-red (BR) goes to UB, blue on B instead of U.

    The F layer and the U/D edges at the sides do not move.
    """
    state = SOLVED.apply(Move(Layer.B, 1))
    assert (state.cp[Corner.ULB], state.co[Corner.ULB]) == (Corner.UBR, 1)
    assert (state.cp[Corner.DBL], state.co[Corner.DBL]) == (Corner.ULB, 2)
    assert (state.cp[Corner.DRB], state.co[Corner.DRB]) == (Corner.DBL, 1)
    assert (state.cp[Corner.UBR], state.co[Corner.UBR]) == (Corner.DRB, 2)
    assert (state.ep[Edge.BL], state.eo[Edge.BL]) == (Edge.UB, 1)
    assert (state.ep[Edge.DB], state.eo[Edge.DB]) == (Edge.BL, 1)
    assert (state.ep[Edge.BR], state.eo[Edge.BR]) == (Edge.DB, 1)
    assert (state.ep[Edge.UB], state.eo[Edge.UB]) == (Edge.BR, 1)
    _assert_untouched(
        state,
        [Corner.URF, Corner.UFL, Corner.DFR, Corner.DLF],
        [Edge.UR, Edge.UF, Edge.UL, Edge.DR, Edge.DF, Edge.DL, Edge.FR, Edge.FL],
    )


@pytest.mark.parametrize("layer", Layer, ids=lambda layer: layer.value)
def test_quarter_turn_has_order_exactly_4(layer: Layer) -> None:
    quarter = Move(layer, 1)
    states = [SOLVED.apply_all([quarter] * k) for k in range(1, 5)]
    assert [s.is_solved() for s in states] == [False, False, False, True]


@pytest.mark.parametrize("layer", Layer, ids=lambda layer: layer.value)
def test_move_then_inverse_is_identity(layer: Layer) -> None:
    for amount in AMOUNTS:
        move = Move(layer, amount)
        assert SOLVED.apply(move).apply(move.inverse()) == SOLVED


@pytest.mark.parametrize("layer", Layer, ids=lambda layer: layer.value)
def test_half_turn_is_two_quarter_turns(layer: Layer) -> None:
    quarter = Move(layer, 1)
    assert SOLVED.apply(Move(layer, 2)) == SOLVED.apply(quarter).apply(quarter)


@pytest.mark.parametrize("move", FACE_TURNS, ids=str)
def test_only_f_and_b_quarter_turns_flip_edges(move: Move) -> None:
    flips = any(SOLVED.apply(move).eo)
    assert flips == (move.layer in (Layer.F, Layer.B) and move.amount != 2)


def test_f_flips_the_four_f_edges() -> None:
    eo = SOLVED.apply(Move(Layer.F, 1)).eo
    assert {Edge(i) for i, flip in enumerate(eo) if flip} == {Edge.UF, Edge.DF, Edge.FR, Edge.FL}


def test_sexy_move_has_order_6() -> None:
    sexy = [R, U, R_PRIME, U_PRIME]
    solved_after = [SOLVED.apply_all(sexy * k).is_solved() for k in range(1, 7)]
    assert solved_after == [False] * 5 + [True]


@pytest.mark.parametrize("move", FACE_TURNS, ids=str)
def test_every_move_keeps_shape_and_validity(move: Move) -> None:
    state = SOLVED.apply(move)
    # Re-run the public shape checks that the unchecked apply() path skips.
    assert CubeState(*state.cubies, frame=state.frame) == state
    assert state.is_valid()
