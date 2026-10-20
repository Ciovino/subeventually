import pytest

from subeventually_core.cube import SOLVED, Corner, CubeState, Edge, R, U

SOLVED_CP = tuple(range(8))
SOLVED_CO = (0,) * 8
SOLVED_EP = tuple(range(12))
SOLVED_EO = (0,) * 12


def test_solved_state_is_solved_and_valid() -> None:
    assert SOLVED.is_solved()
    assert SOLVED.is_valid()
    assert SOLVED.frame == 0


def test_solved_state_equals_a_freshly_built_one() -> None:
    fresh = CubeState(SOLVED_CP, SOLVED_CO, SOLVED_EP, SOLVED_EO)
    assert fresh == SOLVED
    assert hash(fresh) == hash(SOLVED)


@pytest.mark.parametrize(
    ("cp", "co", "ep", "eo", "frame", "message"),
    [
        (SOLVED_CP[:7], SOLVED_CO, SOLVED_EP, SOLVED_EO, 0, "cp must have 8 entries"),
        ((0, 0, 2, 3, 4, 5, 6, 7), SOLVED_CO, SOLVED_EP, SOLVED_EO, 0, "cp must be a permutation"),
        (SOLVED_CP, (3, 0, 0, 0, 0, 0, 0, 0), SOLVED_EP, SOLVED_EO, 0, "co values must be in"),
        (SOLVED_CP, SOLVED_CO[:7], SOLVED_EP, SOLVED_EO, 0, "co must have 8 entries"),
        (SOLVED_CP, SOLVED_CO, tuple(range(1, 13)), SOLVED_EO, 0, "ep must be a permutation"),
        (SOLVED_CP, SOLVED_CO, SOLVED_EP, (2,) + (0,) * 11, 0, "eo values must be in"),
        (SOLVED_CP, SOLVED_CO, SOLVED_EP, SOLVED_EO, 24, "frame must be in"),
        (SOLVED_CP, SOLVED_CO, SOLVED_EP, SOLVED_EO, -1, "frame must be in"),
    ],
)
def test_construction_rejects_malformed_shapes(
    cp: tuple[int, ...],
    co: tuple[int, ...],
    ep: tuple[int, ...],
    eo: tuple[int, ...],
    frame: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        CubeState(cp, co, ep, eo, frame)


def test_construction_rejects_lists() -> None:
    with pytest.raises(TypeError, match="cp must be a tuple"):
        CubeState(list(SOLVED_CP), SOLVED_CO, SOLVED_EP, SOLVED_EO)  # type: ignore[arg-type]


def test_frame_is_part_of_equality_but_not_of_solvedness() -> None:
    held_differently = CubeState(SOLVED_CP, SOLVED_CO, SOLVED_EP, SOLVED_EO, frame=3)
    assert held_differently != SOLVED
    assert hash(held_differently) != hash(SOLVED)
    assert held_differently.is_solved()
    assert held_differently.cubies == SOLVED.cubies


def test_moves_with_a_non_zero_frame_are_not_implemented_yet() -> None:
    held_differently = CubeState(SOLVED_CP, SOLVED_CO, SOLVED_EP, SOLVED_EO, frame=3)
    with pytest.raises(NotImplementedError):
        held_differently.apply(U)
    with pytest.raises(NotImplementedError):
        held_differently.apply_all([U])


def test_cubies_is_the_four_arrays() -> None:
    state = SOLVED.apply(R)
    assert state.cubies == (state.cp, state.co, state.ep, state.eo)


def test_piece_slots_on_solved_are_the_identity() -> None:
    assert all(SOLVED.corner_slot(c) == c for c in Corner)
    assert all(SOLVED.edge_slot(e) == e for e in Edge)


def test_piece_slots_after_u() -> None:
    state = SOLVED.apply(U)
    # U moves the URF corner to UFL and the UF edge to UL.
    assert state.corner_slot(Corner.URF) is Corner.UFL
    assert state.edge_slot(Edge.UF) is Edge.UL


def test_twisted_corner_is_representable_but_invalid() -> None:
    state = CubeState(SOLVED_CP, (1,) + (0,) * 7, SOLVED_EP, SOLVED_EO)
    assert not state.is_valid()
    with pytest.raises(ValueError, match="corner twist"):
        state.validate()


def test_flipped_edge_is_representable_but_invalid() -> None:
    state = CubeState(SOLVED_CP, SOLVED_CO, SOLVED_EP, (1,) + (0,) * 11)
    assert not state.is_valid()
    with pytest.raises(ValueError, match="edge flip"):
        state.validate()


def test_two_swapped_edges_are_representable_but_invalid() -> None:
    state = CubeState(SOLVED_CP, SOLVED_CO, (1, 0, *range(2, 12)), SOLVED_EO)
    assert not state.is_valid()
    with pytest.raises(ValueError, match="parity"):
        state.validate()
