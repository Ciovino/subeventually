from itertools import chain

import pytest
from hypothesis import given
from hypothesis import strategies as st

from subeventually_core.cube import ALL_MOVES
from subeventually_core.notation import MoveSequence
from subeventually_core.session import Session, SessionError

sequences = st.lists(st.sampled_from(ALL_MOVES), min_size=1, max_size=10).map(
    lambda moves: MoveSequence(tuple(moves))
)
histories = st.lists(sequences, max_size=8)
starts = st.lists(st.sampled_from(ALL_MOVES), max_size=20).map(
    lambda moves: Session.from_moves(" ".join(str(move) for move in moves))
)


@given(starts, histories)
def test_undo_step_by_step_goes_back_through_every_state(
    session: Session, history: list[MoveSequence]
) -> None:
    states = [session.state]
    for sequence in history:
        session = session.apply(sequence)
        states.append(session.state)
    for expected in reversed(states[:-1]):
        session = session.undo()
        assert session.state == expected
    assert session.history == ()


@given(starts, histories)
def test_undo_all_then_redo_all_gives_the_final_state(
    session: Session, history: list[MoveSequence]
) -> None:
    for sequence in history:
        session = session.apply(sequence)
    final = session
    for _ in history:
        session = session.undo()
    for _ in history:
        session = session.redo()
    assert session == final


@given(starts, histories.filter(bool))
def test_invert_returns_to_the_start(session: Session, history: list[MoveSequence]) -> None:
    for sequence in history:
        session = session.apply(sequence)
    assert session.invert().state == session.start


# Each operation is a sequence to apply, "undo" or "redo", checked against two plain lists.
operations = st.lists(st.sampled_from(["undo", "redo"]) | sequences, max_size=20)


@given(starts, operations)
def test_session_matches_a_list_model(session: Session, ops: list[MoveSequence | str]) -> None:
    applied: list[MoveSequence] = []
    undone: list[MoveSequence] = []
    for op in ops:
        if isinstance(op, MoveSequence):
            applied.append(op)
            undone.clear()
            session = session.apply(op)
        elif op == "undo" and applied:
            undone.append(applied.pop())
            session = session.undo()
        elif op == "redo" and undone:
            applied.append(undone.pop())
            session = session.redo()
        else:
            with pytest.raises(SessionError):
                session.undo() if op == "undo" else session.redo()
        assert session.history == tuple(applied)
        assert session.undone == tuple(undone)
        assert session.state == session.start.apply_all(chain.from_iterable(applied))
