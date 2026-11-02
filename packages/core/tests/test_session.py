import subprocess
import sys

import pytest

from subeventually_core.cube import SOLVED, Face, R, X
from subeventually_core.facelets import FaceletError
from subeventually_core.notation import MoveSequence, NotationError, parse
from subeventually_core.session import Session, SessionError

SEXY = "R U R' U'"


def test_new_session_is_solved_and_empty() -> None:
    session = Session()
    assert session.state == SOLVED
    assert session.history == ()
    assert session.undone == ()
    assert session.move_count == 0


def test_apply_text_adds_one_entry() -> None:
    session = Session().apply_text(SEXY)
    assert session.history == (parse(SEXY),)
    assert session.state == SOLVED.apply_all(parse(SEXY))


def test_entries_are_applied_in_order() -> None:
    session = Session().apply_text("R").apply_text("U")
    assert session.state == SOLVED.apply_all(parse("R U"))
    assert session.state != SOLVED.apply_all(parse("U R"))


def test_invalid_text_raises_and_keeps_the_session() -> None:
    session = Session().apply_text("R")
    before = session
    with pytest.raises(NotationError) as exc_info:
        session.apply_text("R U2 3Rw")
    assert exc_info.value.column == 6
    assert session == before


@pytest.mark.parametrize("text", ["", "   ", "// only a comment"])
def test_empty_text_changes_nothing(text: str) -> None:
    session = Session().apply_text("R").apply_text("U").undo()
    assert session.apply_text(text) == session


def test_undo_with_empty_history_raises() -> None:
    with pytest.raises(SessionError, match="nothing to undo"):
        Session().undo()


def test_redo_with_nothing_undone_raises() -> None:
    with pytest.raises(SessionError, match="nothing to redo"):
        Session().apply_text("R").redo()


def test_undo_removes_the_whole_last_line() -> None:
    session = Session().apply_text("U").apply_text(SEXY).undo()
    assert session.history == (parse("U"),)
    assert session.state == SOLVED.apply_all(parse("U"))
    assert session.undone == (parse(SEXY),)


def test_undo_then_redo_round_trips() -> None:
    session = Session().apply_text("U").apply_text(SEXY)
    assert session.undo().redo() == session
    assert session.undo().undo().redo().redo() == session


def test_new_sequence_after_undo_clears_redo() -> None:
    session = Session().apply_text("R").undo().apply_text("U")
    assert session.undone == ()
    with pytest.raises(SessionError):
        session.redo()


def test_invert_returns_to_the_start_in_one_entry() -> None:
    session = Session().apply_text("y R").apply_text("U x").invert()
    assert session.state == SOLVED
    assert session.state.frame == 0
    assert len(session.history) == 3
    assert session.history[-1] == parse("x' U' R' y'")


def test_undo_after_invert_restores_the_state() -> None:
    session = Session().apply_text(SEXY)
    assert session.invert().undo().state == session.state


def test_invert_with_empty_history_raises() -> None:
    with pytest.raises(SessionError, match="nothing to invert"):
        Session().invert()


def test_invert_starts_from_a_loaded_state() -> None:
    session = Session.from_moves("F").apply_text("R").invert()
    assert session.state == SOLVED.apply_all(parse("F"))


def test_reset_gives_a_new_session() -> None:
    assert Session().apply_text(SEXY).apply_text("U").undo().reset() == Session()


def test_from_facelets() -> None:
    session = Session.from_facelets("UUFUUFUUFRRRRRRRRRFFDFFDFFDDDBDDBDDBLLLLLLLLLUBBUBBUBB")
    assert session.state == SOLVED.apply(R)
    assert session.history == ()


def test_from_facelets_reads_the_frame_from_the_centers() -> None:
    session = Session.from_facelets("FFFFFFFFFRRRRRRRRRDDDDDDDDDBBBBBBBBBLLLLLLLLLUUUUUUUUU")
    assert session.state == SOLVED.apply(X)
    assert session.state.held == (Face.F, Face.D)


def test_from_facelets_rejects_an_impossible_cube() -> None:
    with pytest.raises(FaceletError, match="must have 54 characters"):
        Session.from_facelets("UUU")


def test_from_moves_starts_with_an_empty_history() -> None:
    session = Session.from_moves(SEXY)
    assert session.start == SOLVED.apply_all(parse(SEXY))
    assert session.state == session.start
    assert session.history == ()
    assert session.move_count == 0


def test_from_moves_rejects_invalid_notation() -> None:
    with pytest.raises(NotationError):
        Session.from_moves("R'2")


@pytest.mark.parametrize(
    ("lines", "expected"),
    [(["y R U R'"], 3), (["M2 Rw x"], 2), (["x y z"], 0), ([SEXY, "y U2", "M'"], 6)],
)
def test_move_count_excludes_rotations(lines: list[str], expected: int) -> None:
    session = Session()
    for line in lines:
        session = session.apply_text(line)
    assert session.move_count == expected


def test_history_keeps_comments() -> None:
    session = Session().apply_text("(R U R') // pair")
    assert str(session.history[0]) == "R U R' // pair"


def test_apply_takes_a_parsed_sequence() -> None:
    sequence = MoveSequence((R,))
    assert Session().apply(sequence).history == (sequence,)


def test_session_does_not_load_a_ui_library() -> None:
    code = (
        "import sys, subeventually_core.session; "
        "print(sorted({'rich', 'textual'} & set(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
