"""Parse and format 3x3 move notation.

The accepted notation is specified for users in ``docs/NOTATION.md``. In short:

- WCA moves plus the common extensions: slices, lowercase wide moves (``r`` = ``Rw``) and
  uppercase rotations (``X`` = ``x``);
- an optional count (1, 2 or 3) then an optional prime (an apostrophe, a curly right quote or
  the prime symbol), so ``R2'`` is ``R2`` and ``R3`` is ``R'``;
- spaces between moves are optional, parentheses are checked for balance and dropped, and
  ``//`` comments are kept with the number of moves before them.

:func:`to_text` prints the canonical form, and ``parse(to_text(seq)) == seq`` always holds.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Final, overload

from subeventually_core.cube import Amount, Layer, Move, invert

_FACES: Final = frozenset("UDLRFB")
_LOWER_WIDES: Final = frozenset("udlrfb")
_DIGITS: Final = frozenset("0123456789")
_PRIMES: Final = frozenset("'\N{RIGHT SINGLE QUOTATION MARK}\N{PRIME}")
_COMMUTATOR_CHARS: Final = frozenset("[],:")

# The letter that starts a move, before any "w" turns a face into a wide move.
_LETTERS: Final[dict[str, Layer]] = {
    **{face: Layer[face] for face in _FACES},
    **{wide: Layer[wide.upper() + "W"] for wide in _LOWER_WIDES},
    **{slice_: Layer[slice_] for slice_ in "MES"},
    **{rotation: Layer[rotation.upper()] for rotation in "xyzXYZ"},
}

_AMOUNTS: Final[dict[tuple[int, bool], Amount]] = {
    (1, False): 1,
    (2, False): 2,
    (3, False): 3,
    (1, True): 3,
    (2, True): 2,
    (3, True): 1,
}

_W_MESSAGE: Final = "'w' must come right after U, D, L, R, F or B, as in Rw"


class NotationError(ValueError):
    """Text that is not valid notation. ``str()`` gives ``"line L, column C: message"``.

    ``line`` and ``column`` are 1-based and count characters; ``message`` is the reason alone.
    """

    def __init__(self, line: int, column: int, message: str) -> None:
        super().__init__(f"line {line}, column {column}: {message}")
        self.line = line
        self.column = column
        self.message = message


@dataclass(frozen=True, slots=True)
class Comment:
    """A ``//`` comment, written after the first ``position`` moves of its sequence."""

    position: int
    text: str

    def __post_init__(self) -> None:
        if self.position < 0:
            raise ValueError(f"comment position must not be negative, got {self.position}")
        if "\n" in self.text or self.text != self.text.strip():
            raise ValueError(f"comment text must be one stripped line, got {self.text!r}")


@dataclass(frozen=True, slots=True)
class MoveSequence(Sequence[Move]):
    """Moves together with the comments written between them.

    Behaves as a read-only sequence of its moves, so it can be passed wherever moves are
    expected (``CubeState.apply_all``, ``invert``). Equality includes the comments; compare
    :attr:`moves` to ignore them. ``str()`` gives the canonical form (see :func:`to_text`).
    """

    moves: tuple[Move, ...] = ()
    comments: tuple[Comment, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.moves, tuple) or not isinstance(self.comments, tuple):
            raise TypeError("moves and comments must be tuples")
        previous = 0
        for comment in self.comments:
            if not previous <= comment.position <= len(self.moves):
                raise ValueError(
                    f"comment positions must be non-decreasing and at most {len(self.moves)}, "
                    f"got {comment.position} after {previous}"
                )
            previous = comment.position

    def __len__(self) -> int:
        return len(self.moves)

    def __iter__(self) -> Iterator[Move]:
        return iter(self.moves)

    @overload
    def __getitem__(self, index: int) -> Move: ...
    @overload
    def __getitem__(self, index: slice) -> tuple[Move, ...]: ...
    def __getitem__(self, index: int | slice) -> Move | tuple[Move, ...]:
        return self.moves[index]

    def inverse(self) -> MoveSequence:
        """Return the sequence that undoes this one. Comments are dropped."""
        return MoveSequence(invert(self.moves))

    def __str__(self) -> str:
        return to_text(self)


def _error(text: str, index: int, message: str) -> NotationError:
    line = text.count("\n", 0, index) + 1
    column = index - text.rfind("\n", 0, index)
    return NotationError(line, column, message)


def _read_count(text: str, start: int) -> tuple[str, int]:
    end = start
    while text[end : end + 1] in _DIGITS:
        end += 1
    return text[start:end], end


def _read_move(text: str, start: int) -> tuple[Move, int]:
    # Reads one move starting at text[start], which is not whitespace, "(", ")" or "//".
    char = text[start]
    if char in _DIGITS:
        raise _error(text, start, "big-cube notation is not supported (3x3 only)")
    if char in _COMMUTATOR_CHARS:
        raise _error(
            text,
            start,
            "commutator and conjugate notation are not supported; write the moves out",
        )
    if char in _PRIMES:
        raise _error(text, start, "prime mark without a move")
    if char in "mes":
        raise _error(
            text, start, f"unknown move '{char}': slices are uppercase, as in {char.upper()}"
        )
    if char == "w":
        raise _error(text, start, _W_MESSAGE)
    if char not in _LETTERS:
        raise _error(text, start, f"unexpected character {char!r}")

    layer = _LETTERS[char]
    i = start + 1
    after = text[i : i + 1]
    if char in _FACES and after == "w":
        layer = Layer[char + "W"]
        i += 1
    elif (char in _FACES and after == "W") or (char in _LOWER_WIDES and after in ("w", "W")):
        raise _error(
            text, start, f"unknown move '{char}{after}': write {char.upper()}w or {char.lower()}"
        )

    token_end = i
    digits, i = _read_count(text, i)
    if digits and digits not in ("1", "2", "3"):
        raise _error(text, token_end, "turn count must be 1, 2 or 3")
    prime = text[i : i + 1] in _PRIMES
    if prime:
        i += 1
    after = text[i : i + 1]
    if after in _PRIMES:
        raise _error(text, i, "a move can have only one prime mark")
    if prime and not digits and after in _DIGITS:
        late_digits, _ = _read_count(text, i)
        if late_digits not in ("1", "2", "3"):
            raise _error(text, i, "turn count must be 1, 2 or 3")
        token = text[start:token_end]
        raise _error(text, i, f"the count goes before the prime: write {token}{late_digits}'")
    if after == "w":
        raise _error(text, i, _W_MESSAGE)
    return Move(layer, _AMOUNTS[int(digits or 1), prime]), i


def parse(text: str) -> MoveSequence:
    """Read notation as specified in ``docs/NOTATION.md``.

    Raises:
        NotationError: for the first problem found, with its line and column.
    """
    moves: list[Move] = []
    comments: list[Comment] = []
    open_parens: list[int] = []
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            end = len(text) if end == -1 else end
            comments.append(Comment(len(moves), text[i + 2 : end].strip()))
            i = end
        elif char == "(":
            open_parens.append(i)
            i += 1
        elif char == ")":
            if not open_parens:
                raise _error(text, i, "')' has no matching '('")
            open_parens.pop()
            i += 1
            after = text[i : i + 1]
            if after in _DIGITS:
                raise _error(text, i, "repeating a group is not supported; write the moves out")
            if after in _PRIMES:
                raise _error(text, i, "inverting a group is not supported; write the moves out")
        else:
            move, i = _read_move(text, i)
            moves.append(move)
    if open_parens:
        raise _error(text, open_parens[0], "'(' is never closed")
    return MoveSequence(tuple(moves), tuple(comments))


def to_text(sequence: MoveSequence) -> str:
    """Return the canonical text of ``sequence``.

    WCA spelling with single spaces (``Rw``, ``x``, ``R'``, ``R2``), no parentheses, and each
    comment as ``// text`` ending its line. No leading or trailing whitespace.
    """
    lines: list[str] = []
    words: list[str] = []
    comments = iter(sequence.comments)
    comment = next(comments, None)
    for position in range(len(sequence.moves) + 1):
        while comment is not None and comment.position == position:
            words.append(f"// {comment.text}" if comment.text else "//")
            lines.append(" ".join(words))
            words = []
            comment = next(comments, None)
        if position < len(sequence.moves):
            words.append(str(sequence.moves[position]))
    if words:
        lines.append(" ".join(words))
    return "\n".join(lines)
