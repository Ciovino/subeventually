"""A playground session: a cube state with a history of applied sequences, undo and redo.

A :class:`Session` is immutable, like :class:`CubeState`: every operation returns a new
session. An operation that fails raises and leaves the caller with the session it had, so a
failed operation never changes the state.

The state is always the start state with every sequence of the history applied in order.
Resetting or loading a state starts a new session, with an empty history.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import chain
from typing import Final

from subeventually_core.cube import SOLVED, CubeState, Layer
from subeventually_core.facelets import from_facelet_string
from subeventually_core.notation import MoveSequence, parse

_ROTATIONS: Final = frozenset({Layer.X, Layer.Y, Layer.Z})


class SessionError(ValueError):
    """An operation that can't be done now, such as undo with no history.

    ``message`` is the reason.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True, slots=True)
class Session:
    """A start state, the sequences applied to it (oldest first) and the undone ones.

    ``undone`` is the redo stack: the most recently undone sequence is last. Applying a new
    sequence clears it.
    """

    start: CubeState = SOLVED
    history: tuple[MoveSequence, ...] = ()
    undone: tuple[MoveSequence, ...] = ()

    @property
    def state(self) -> CubeState:
        """The current state: ``start`` after every sequence of the history."""
        return self.start.apply_all(chain.from_iterable(self.history))

    @property
    def move_count(self) -> int:
        """The moves in the history, rotations excluded; any face, slice or wide move is 1."""
        return sum(move.layer not in _ROTATIONS for move in chain.from_iterable(self.history))

    def apply(self, sequence: MoveSequence) -> Session:
        """Return the session with ``sequence`` added to the history; redo is no longer possible.

        An empty sequence (for example only a comment) changes nothing.
        """
        if not sequence:
            return self
        return replace(self, history=(*self.history, sequence), undone=())

    def apply_text(self, text: str) -> Session:
        """Parse ``text`` as notation and apply it as one sequence.

        Raises:
            NotationError: if ``text`` is not valid notation.
        """
        return self.apply(parse(text))

    def undo(self) -> Session:
        """Return the session without its last sequence, which can be redone.

        Raises:
            SessionError: if the history is empty.
        """
        if not self.history:
            raise SessionError("nothing to undo")
        return replace(self, history=self.history[:-1], undone=(*self.undone, self.history[-1]))

    def redo(self) -> Session:
        """Return the session with the last undone sequence applied again.

        Raises:
            SessionError: if nothing was undone since the last new sequence.
        """
        if not self.undone:
            raise SessionError("nothing to redo")
        return replace(self, history=(*self.history, self.undone[-1]), undone=self.undone[:-1])

    def invert(self) -> Session:
        """Apply the inverse of the whole history as one sequence, back to the start state.

        Raises:
            SessionError: if the history is empty.
        """
        if not self.history:
            raise SessionError("nothing to invert")
        whole = MoveSequence(tuple(chain.from_iterable(self.history)))
        return self.apply(whole.inverse())

    def reset(self) -> Session:
        """Return a new session on a solved cube."""
        return Session()

    @classmethod
    def from_facelets(cls, text: str) -> Session:
        """Return a new session starting from the state of a facelet string.

        Raises:
            FaceletError: if ``text`` is not the facelet string of a real cube.
        """
        return cls(start=from_facelet_string(text))

    @classmethod
    def from_moves(cls, text: str) -> Session:
        """Return a new session starting from a solved cube after the moves of ``text``.

        Raises:
            NotationError: if ``text`` is not valid notation.
        """
        return cls(start=SOLVED.apply_all(parse(text)))
