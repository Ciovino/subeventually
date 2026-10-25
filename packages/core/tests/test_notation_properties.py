from hypothesis import given
from hypothesis import strategies as st

from subeventually_core import notation
from subeventually_core.cube import ALL_MOVES, Move
from subeventually_core.notation import Comment, MoveSequence, NotationError

comment_texts = st.text(max_size=20).map(str.strip).filter(lambda text: "\n" not in text)


@st.composite
def sequences(draw: st.DrawFn) -> MoveSequence:
    moves = tuple(draw(st.lists(st.sampled_from(ALL_MOVES), max_size=30)))
    positions = sorted(draw(st.lists(st.integers(0, len(moves)), max_size=3)))
    return MoveSequence(moves, tuple(Comment(p, draw(comment_texts)) for p in positions))


# Random text rarely gets past the first character, so also build it from notation pieces.
NOTATION_ALPHABET = (
    "UDLRFBMESudlrfbmesxyzXYZwW0123456789'\N{RIGHT SINGLE QUOTATION MARK}\N{PRIME}"
    "\N{SUPERSCRIPT TWO} \t\r\n()[],:/.#"
)
texts = st.text() | st.text(alphabet=NOTATION_ALPHABET)


@given(st.lists(st.sampled_from(ALL_MOVES), max_size=50))
def test_format_then_parse_gives_the_moves_back(moves: list[Move]) -> None:
    sequence = MoveSequence(tuple(moves))
    assert notation.parse(notation.format(sequence)) == sequence


@given(sequences())
def test_format_then_parse_keeps_comments(sequence: MoveSequence) -> None:
    assert notation.parse(notation.format(sequence)) == sequence


@given(texts)
def test_parse_succeeds_or_raises_notation_error(text: str) -> None:
    error: NotationError | None = None
    try:
        sequence = notation.parse(text)
    except NotationError as raised:
        error = raised
    if error is not None:
        assert 1 <= error.line <= text.count("\n") + 1
        assert error.column >= 1
    else:
        # Whatever was accepted is printed in a form that reads back the same.
        assert notation.parse(notation.format(sequence)) == sequence
