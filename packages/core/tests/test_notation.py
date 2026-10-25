import pytest

from subeventually_core import notation
from subeventually_core.cube import (
    ALL_MOVES,
    M2,
    M_PRIME,
    R2,
    R_PRIME,
    SOLVED,
    U2,
    U_PRIME,
    M,
    Move,
    R,
    U,
    invert,
)
from subeventually_core.notation import Comment, MoveSequence, NotationError

CURLY = "\N{RIGHT SINGLE QUOTATION MARK}"
PRIME = "\N{PRIME}"


@pytest.mark.parametrize("move", ALL_MOVES, ids=str)
def test_every_move_name_parses_to_that_move(move: Move) -> None:
    assert notation.parse(str(move)).moves == (move,)


@pytest.mark.parametrize(
    ("text", "canonical"),
    [
        # aliases
        ("r U r'", "Rw U Rw'"),
        ("u d l r f b", "Uw Dw Lw Rw Fw Bw"),
        ("Lw2 l2", "Lw2 Lw2"),
        ("X Y Z X' Y2", "x y z x' y2"),
        (f"R{CURLY} U{PRIME}", "R' U'"),
        # counts
        ("R2'", "R2"),
        ("R3", "R'"),
        ("R3'", "R"),
        ("R1 R1'", "R R'"),
        ("M2' r3 y2' Lw2", "M2 Rw' y2 Lw2"),
        (f"U2{CURLY} x3{PRIME}", "U2 x"),
        # spacing
        ("RUR'U'", "R U R' U'"),
        ("R2U", "R2 U"),
        ("RwU", "Rw U"),
        ("R  U\t\nR'", "R U R'"),
        ("  R U  ", "R U"),
        # parentheses
        ("(R U R' U') (R' F R F')", "R U R' U' R' F R F'"),
        ("((R) U)", "R U"),
        ("()", ""),
        # empty
        ("", ""),
        (" \n\t", ""),
        # examples from docs/NOTATION.md
        ("y (r U r') U2' (R U R3)", "y Rw U Rw' U2 R U R'"),
        (f"Y RUR{CURLY}U{CURLY}", "y R U R' U'"),
        ("x2'  M2 U M2", "x2 M2 U M2"),
        ("(R U R' U') (R' F) (R2 U' R') U' (R U R' F')", "R U R' U' R' F R2 U' R' U' R U R' F'"),
        ("y2 (R U R' U) R U2' R3", "y2 R U R' U R U2 R'"),
        (f"Y rUR{CURLY}U{CURLY}r{CURLY}FRF{CURLY}", "y Rw U R' U' Rw' F R F'"),
    ],
)
def test_accepted_input_is_printed_canonically(text: str, canonical: str) -> None:
    sequence = notation.parse(text)
    assert notation.to_text(sequence) == canonical
    assert notation.parse(canonical) == sequence


RECONSTRUCTION = """x2 y      // inspection
R' F R2 D' // cross
U R U' R'
U2 (R U R') // first pair
"""


def test_comments_are_kept_at_their_position_and_end_their_line() -> None:
    sequence = notation.parse(RECONSTRUCTION)
    assert sequence.comments == (
        Comment(2, "inspection"),
        Comment(6, "cross"),
        Comment(14, "first pair"),
    )
    assert notation.to_text(sequence) == (
        "x2 y // inspection\nR' F R2 D' // cross\nU R U' R' U2 R U R' // first pair"
    )


@pytest.mark.parametrize(
    ("text", "canonical"),
    [
        ("// Solve 3\nR U R'", "// Solve 3\nR U R'"),
        ("// a\n// b\nR", "// a\n// b\nR"),
        ("R //   ", "R //"),
        ("R // cross\r\nU", "R // cross\nU"),
        ("R // (U) [x] // y", "R // (U) [x] // y"),
        ("(R // inside\nU)", "R // inside\nU"),
        ("// only a comment", "// only a comment"),
    ],
)
def test_comment_layout(text: str, canonical: str) -> None:
    assert notation.to_text(notation.parse(text)) == canonical


@pytest.mark.parametrize(
    ("text", "line", "column", "message"),
    [
        ("3Rw", 1, 1, "big-cube notation is not supported (3x3 only)"),
        ("2R", 1, 1, "big-cube notation is not supported (3x3 only)"),
        ("2-4r", 1, 1, "big-cube notation is not supported (3x3 only)"),
        ("3r", 1, 1, "big-cube notation is not supported (3x3 only)"),
        ("R U2 3Rw", 1, 6, "big-cube notation is not supported (3x3 only)"),
        (
            "[R, U]",
            1,
            1,
            "commutator and conjugate notation are not supported; write the moves out",
        ),
        (
            "R [R: U]",
            1,
            3,
            "commutator and conjugate notation are not supported; write the moves out",
        ),
        ("(R U)3", 1, 6, "repeating a group is not supported; write the moves out"),
        ("(R U)'", 1, 6, "inverting a group is not supported; write the moves out"),
        (f"(R U){CURLY}", 1, 6, "inverting a group is not supported; write the moves out"),
        ("R'2", 1, 3, "the count goes before the prime: write R2'"),
        ("r'3", 1, 3, "the count goes before the prime: write r3'"),
        ("Rw'2", 1, 4, "the count goes before the prime: write Rw2'"),
        ("R'4", 1, 3, "turn count must be 1, 2 or 3"),
        ("R4", 1, 2, "turn count must be 1, 2 or 3"),
        ("R0", 1, 2, "turn count must be 1, 2 or 3"),
        ("R22", 1, 2, "turn count must be 1, 2 or 3"),
        ("Rw02", 1, 3, "turn count must be 1, 2 or 3"),
        ("R''", 1, 3, "a move can have only one prime mark"),
        (f"R2'{CURLY}", 1, 4, "a move can have only one prime mark"),
        ("' R", 1, 1, "prime mark without a move"),
        ("rw", 1, 1, "unknown move 'rw': write Rw or r"),
        ("rW", 1, 1, "unknown move 'rW': write Rw or r"),
        ("RW", 1, 1, "unknown move 'RW': write Rw or r"),
        ("m", 1, 1, "unknown move 'm': slices are uppercase, as in M"),
        ("e", 1, 1, "unknown move 'e': slices are uppercase, as in E"),
        ("s", 1, 1, "unknown move 's': slices are uppercase, as in S"),
        ("R w", 1, 3, "'w' must come right after U, D, L, R, F or B, as in Rw"),
        ("Mw", 1, 2, "'w' must come right after U, D, L, R, F or B, as in Rw"),
        ("xw", 1, 2, "'w' must come right after U, D, L, R, F or B, as in Rw"),
        ("R2w", 1, 3, "'w' must come right after U, D, L, R, F or B, as in Rw"),
        ("(R U", 1, 1, "'(' is never closed"),
        ("(R (U)", 1, 1, "'(' is never closed"),
        ("R U)", 1, 4, "')' has no matching '('"),
        ("R . U", 1, 3, "unexpected character '.'"),
        ("R # U", 1, 3, "unexpected character '#'"),
        ("R / U", 1, 3, "unexpected character '/'"),
        ("R /* x */", 1, 3, "unexpected character '/'"),
        ("Q", 1, 1, "unexpected character 'Q'"),
        ("R\N{SUPERSCRIPT TWO}", 1, 2, "unexpected character '\N{SUPERSCRIPT TWO}'"),
        # line and column on later lines; only the first problem is reported
        ("R U\n  R' 3Rw", 2, 6, "big-cube notation is not supported (3x3 only)"),
        ("R // 3Rw ]\n\nQ", 3, 1, "unexpected character 'Q'"),
        ("(R U) 3Rw (", 1, 7, "big-cube notation is not supported (3x3 only)"),
    ],
)
def test_rejected_input(text: str, line: int, column: int, message: str) -> None:
    with pytest.raises(NotationError) as info:
        notation.parse(text)
    assert (info.value.line, info.value.column, info.value.message) == (line, column, message)


def test_error_text_includes_the_position() -> None:
    with pytest.raises(ValueError, match=r"^line 1, column 6: big-cube notation"):
        notation.parse("R U2 3Rw")


# Real-world inputs


def test_wca_scramble_is_unchanged() -> None:
    scramble = "D2 F2 U' B2 R2 U2 R2 F2 D' L2 U' R' D B' L' U' R F' L' U2 B"
    assert notation.to_text(notation.parse(scramble)) == scramble


@pytest.mark.parametrize(
    ("text", "moves"),
    [
        ("(R U R' U')", (R, U, R_PRIME, U_PRIME)),
        ("M2 U M2 U2 M2 U M2", (M2, U, M2, U2, M2, U, M2)),
        ("M2 U M U2 M' U M2", (M2, U, M, U2, M_PRIME, U, M2)),
        ("R2' U R", (R2, U, R)),
    ],
)
def test_known_algorithms(text: str, moves: tuple[Move, ...]) -> None:
    assert notation.parse(text).moves == moves


def test_sexy_move_six_times_solves_the_cube() -> None:
    assert SOLVED.apply_all(notation.parse("(R U R' U') " * 6)).is_solved()


def test_applying_a_sequence_is_applying_its_moves() -> None:
    sequence = notation.parse(RECONSTRUCTION)
    assert SOLVED.apply_all(sequence) == SOLVED.apply_all(sequence.moves)


# MoveSequence


def test_move_sequence_is_a_sequence_of_its_moves() -> None:
    sequence = notation.parse("R U // pair\nR'")
    assert len(sequence) == 3
    assert list(sequence) == [R, U, R_PRIME]
    assert sequence[0] == R
    assert sequence[-1] == R_PRIME
    assert sequence[1:] == (U, R_PRIME)
    assert U in sequence


def test_inverse_reverses_inverts_and_drops_comments() -> None:
    sequence = notation.parse("R U2 // pair\nM'")
    assert sequence.inverse() == MoveSequence((M, U2, R_PRIME))
    assert invert(sequence) == sequence.inverse().moves
    assert SOLVED.apply_all([*sequence, *sequence.inverse()]) == SOLVED


def test_str_is_the_canonical_form() -> None:
    sequence = notation.parse("r U' // set up\n R")
    assert str(sequence) == notation.to_text(sequence) == "Rw U' // set up\nR"


def test_equality_includes_comments() -> None:
    assert notation.parse("R // a") != notation.parse("R // b")
    assert notation.parse("R // a").moves == notation.parse("R // b").moves
    assert notation.parse("(R U)") == notation.parse("R U")
    assert hash(notation.parse("R // a")) == hash(MoveSequence((R,), (Comment(1, "a"),)))


@pytest.mark.parametrize(
    ("moves", "comments", "error"),
    [
        ((R,), (Comment(2, "a"),), "comment positions"),
        ((R, U), (Comment(2, "a"), Comment(1, "b")), "comment positions"),
        ([R], (), "must be tuples"),
    ],
)
def test_move_sequence_rejects_bad_comments(
    moves: tuple[Move, ...], comments: tuple[Comment, ...], error: str
) -> None:
    with pytest.raises((ValueError, TypeError), match=error):
        MoveSequence(moves, comments)


@pytest.mark.parametrize(
    ("position", "text"),
    [(-1, "a"), (0, "a\nb"), (0, " a"), (0, "a ")],
)
def test_comment_rejects_bad_values(position: int, text: str) -> None:
    with pytest.raises(ValueError, match="comment"):
        Comment(position, text)
