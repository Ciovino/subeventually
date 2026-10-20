from typing import Literal

from hypothesis import given
from hypothesis import strategies as st

from subeventually_core.cube import SOLVED, CubeState, Layer, Move, invert

AMOUNTS: tuple[Literal[1, 2, 3], ...] = (1, 2, 3)
FACE_TURNS = tuple(Move(layer, amount) for layer in Layer for amount in AMOUNTS)

sequences = st.lists(st.sampled_from(FACE_TURNS), max_size=50)


@given(sequences)
def test_sequence_then_inverse_is_solved(seq: list[Move]) -> None:
    assert SOLVED.apply_all([*seq, *invert(seq)]).is_solved()


@given(sequences)
def test_reachable_states_are_valid_and_well_formed(seq: list[Move]) -> None:
    state = SOLVED.apply_all(seq)
    assert state.is_valid()
    assert CubeState(*state.cubies, frame=state.frame) == state


@given(sequences)
def test_apply_all_equals_applying_one_by_one(seq: list[Move]) -> None:
    state = SOLVED
    for move in seq:
        state = state.apply(move)
    assert SOLVED.apply_all(seq) == state


@given(sequences)
def test_invert_is_an_involution(seq: list[Move]) -> None:
    assert invert(invert(seq)) == tuple(seq)
