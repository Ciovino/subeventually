from hypothesis import given
from hypothesis import strategies as st

from subeventually_core.cube import ALL_MOVES, SOLVED, CubeState, Move, invert

sequences = st.lists(st.sampled_from(ALL_MOVES), max_size=50)


@given(sequences)
def test_sequence_then_inverse_is_solved_in_frame_0(seq: list[Move]) -> None:
    assert SOLVED.apply_all([*seq, *invert(seq)]) == SOLVED


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
