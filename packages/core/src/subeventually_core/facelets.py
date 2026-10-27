"""The 54-sticker view of a cube, the facelet string and a plain-text net.

The layout is specified for users in ``docs/NOTATION.md`` (section "Facelets"). In short:

- facelets are in the standard URFDLB order, 9 per face, row by row, so index
  ``9 * face + 3 * row + col``; the corner and edge facelets are Kociemba's;
- the view is the cube as held: index ``i`` is a position in notation (the face currently
  on top is the U block), and each sticker is the :class:`Face` whose color it has;
- so in frame 0 the string is the usual one, and the six centers always show the frame.

This module only describes stickers. Turning colors into terminal output is the UI's job.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from enum import IntEnum
from types import MappingProxyType
from typing import Final

from subeventually_core.cube import Corner, CubeState, Edge, Face, frame_of

_N_FACELETS: Final = 54
_N_FRAMES: Final = 24

WCA_COLORS: Final[Mapping[Face, str]] = MappingProxyType(
    {
        Face.U: "white",
        Face.R: "red",
        Face.F: "green",
        Face.D: "yellow",
        Face.L: "orange",
        Face.B: "blue",
    }
)
"""The WCA color scheme: the color of each face's center."""

# Facelets of each slot in the order of ADR 0004 (corners clockwise from the U/D facelet,
# edges reference facelet first), so co and eo index them directly. Same as Kociemba's.
_CORNER_FACELETS: Final = (
    (8, 9, 20),  # URF
    (6, 18, 38),  # UFL
    (0, 36, 47),  # ULB
    (2, 45, 11),  # UBR
    (29, 26, 15),  # DFR
    (27, 44, 24),  # DLF
    (33, 53, 42),  # DBL
    (35, 17, 51),  # DRB
)
_EDGE_FACELETS: Final = (
    (5, 10),  # UR
    (7, 19),  # UF
    (3, 37),  # UL
    (1, 46),  # UB
    (32, 16),  # DR
    (28, 25),  # DF
    (30, 43),  # DL
    (34, 52),  # DB
    (23, 12),  # FR
    (21, 41),  # FL
    (50, 39),  # BL
    (48, 14),  # BR
)
_CENTER_FACELETS: Final = tuple(9 * face + 4 for face in Face)

# The colors of each piece, in the same order as its home slot's facelets.
_CORNER_FACES: Final = tuple(tuple(Face(i // 9) for i in slot) for slot in _CORNER_FACELETS)
_EDGE_FACES: Final = tuple(tuple(Face(i // 9) for i in slot) for slot in _EDGE_FACELETS)

# Guards the hand-written tables: with the centers they name every facelet once.
if sorted(
    [*_CENTER_FACELETS, *(i for slot in (*_CORNER_FACELETS, *_EDGE_FACELETS) for i in slot)]
) != list(range(_N_FACELETS)):
    raise RuntimeError("facelet tables do not cover 0..53 exactly once")


# Frames as facelet permutations. Each facelet gets integer coordinates (x right, y up,
# z towards the viewer): the position of its cubie and the normal of its face. Whole-cube
# rotations are then rotation matrices, so no sticker permutation is written by hand.

type _Vector = tuple[int, int, int]
type _Sticker = tuple[_Vector, _Vector]


def _sticker(index: int) -> _Sticker:
    face, row, col = Face(index // 9), index % 9 // 3, index % 3
    # Each face as drawn in the net: U from above with B at the top, D from below with F at
    # the top, the others from their own front with U at the top.
    match face:
        case Face.U:
            return (col - 1, 1, row - 1), (0, 1, 0)
        case Face.R:
            return (1, 1 - row, 1 - col), (1, 0, 0)
        case Face.F:
            return (col - 1, 1 - row, 1), (0, 0, 1)
        case Face.D:
            return (col - 1, -1, 1 - row), (0, -1, 0)
        case Face.L:
            return (-1, 1 - row, col - 1), (-1, 0, 0)
        case Face.B:
            return (1 - col, 1 - row, -1), (0, 0, -1)


_STICKERS: Final = tuple(_sticker(i) for i in range(_N_FACELETS))
_INDEX: Final = {sticker: i for i, sticker in enumerate(_STICKERS)}

# x turns like R (front goes up), y like U (right goes to the front), z like F (up goes right).
_ROTATIONS: Final[tuple[Callable[[_Vector], _Vector], ...]] = (
    lambda v: (v[0], v[2], -v[1]),
    lambda v: (-v[2], v[1], v[0]),
    lambda v: (v[1], -v[0], v[2]),
)


def _sources(rotate: Callable[[_Vector], _Vector]) -> tuple[int, ...]:
    # sources[i] is the facelet whose sticker the rotation brings to facelet i.
    sources = [0] * _N_FACELETS
    for i, (position, normal) in enumerate(_STICKERS):
        sources[_INDEX[rotate(position), rotate(normal)]] = i
    return tuple(sources)


def _build_frame_facelets() -> tuple[tuple[int, ...], ...]:
    # For each frame, held[i] = fixed[perm[i]], where fixed is the frame-0 layout. Every
    # orientation is reached by composing x, y and z, and numbered with frame_of (ADR 0005)
    # from the centers it puts on top and in front.
    rotations = tuple(_sources(rotate) for rotate in _ROTATIONS)
    found: dict[int, tuple[int, ...]] = {}
    pending = [tuple(range(_N_FACELETS))]
    while pending:
        perm = pending.pop()
        up = Face(perm[_CENTER_FACELETS[Face.U]] // 9)
        front = Face(perm[_CENTER_FACELETS[Face.F]] // 9)
        frame = frame_of(up, front)
        if frame in found:
            # Two centers fix a rotation, so the same frame must give the same stickers.
            if found[frame] != perm:
                raise RuntimeError(f"frame {frame} is reached with two sticker layouts")
            continue
        found[frame] = perm
        pending.extend(tuple(perm[s] for s in sources) for sources in rotations)
    if len(found) != _N_FRAMES:
        raise RuntimeError(f"found {len(found)} orientations instead of {_N_FRAMES}")
    return tuple(found[frame] for frame in range(_N_FRAMES))


_FRAME_FACELETS: Final = _build_frame_facelets()


def facelets(state: CubeState) -> tuple[Face, ...]:
    """Return the 54 stickers of ``state`` as the cube is held, in URFDLB order.

    Index ``i`` is a position (``0..8`` is the face currently on top), and each value is the
    :class:`Face` whose color the sticker has. See ``docs/NOTATION.md`` for the layout.
    """
    fixed: list[Face] = [Face.U] * _N_FACELETS
    for face, index in zip(Face, _CENTER_FACELETS, strict=True):
        fixed[index] = face
    for slot, (piece, twist) in enumerate(zip(state.cp, state.co, strict=True)):
        for n, face in enumerate(_CORNER_FACES[piece]):
            fixed[_CORNER_FACELETS[slot][(n + twist) % 3]] = face
    for slot, (piece, flip) in enumerate(zip(state.ep, state.eo, strict=True)):
        for n, face in enumerate(_EDGE_FACES[piece]):
            fixed[_EDGE_FACELETS[slot][(n + flip) % 2]] = face
    return tuple(fixed[source] for source in _FRAME_FACELETS[state.frame])


def to_facelet_string(state: CubeState) -> str:
    """Return the 54-character facelet string of ``state`` as held, e.g. ``"UUUUUUUUUR..."``."""
    return "".join(face.name for face in facelets(state))


class FaceletError(ValueError):
    """A facelet string that does not describe a real cube. ``message`` is the reason."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


_LETTERS: Final = frozenset(face.name for face in Face)
_COLOR_LETTERS: Final = frozenset("WYGO")  # white, yellow, green, orange; R and B are faces
_CORNER_PIECES: Final = {faces: piece for piece, faces in enumerate(_CORNER_FACES)}
_EDGE_PIECES: Final = {faces: piece for piece, faces in enumerate(_EDGE_FACES)}
_CENTER_PLACES: Final = {
    Face.R: "on the right",
    Face.D: "at the bottom",
    Face.L: "on the left",
    Face.B: "at the back",
}


def _facelet_name(index: int) -> str:
    return f"{Face(index // 9).name}{index % 9 + 1}"


def _times(count: int) -> str:
    return "1 time" if count == 1 else f"{count} times"


def _read_stickers(text: str) -> tuple[Face, ...]:
    if len(text) != _N_FACELETS:
        raise FaceletError(f"facelet string must have {_N_FACELETS} characters, got {len(text)}")
    for i, char in enumerate(text):
        if char not in _LETTERS:
            if char.upper() in _COLOR_LETTERS:
                advice = "use face letters (U, R, F, D, L, B), not color letters"
            else:
                advice = "only U, R, F, D, L and B are allowed"
            raise FaceletError(f"character {i + 1} ({_facelet_name(i)}) is {char!r}: {advice}")
    stickers = tuple(Face[char] for char in text)
    counts = Counter(stickers)
    wrong = [f"{face.name} appears {_times(counts[face])}" for face in Face if counts[face] != 9]
    if wrong:
        raise FaceletError("each color must appear 9 times: " + ", ".join(wrong))
    return stickers


def _read_frame(held: tuple[Face, ...]) -> int:
    up, front = held[_CENTER_FACELETS[Face.U]], held[_CENTER_FACELETS[Face.F]]
    try:
        frame = frame_of(up, front)
    except ValueError:
        relation = "are the same" if up == front else "are opposite"
        raise FaceletError(
            f"centers {up.name} on top and {front.name} in front {relation}: "
            "no cube can be held like that"
        ) from None
    expected = [Face(_FRAME_FACELETS[frame][center] // 9) for center in _CENTER_FACELETS]
    actual = [held[center] for center in _CENTER_FACELETS]
    if actual != expected:
        mirrored = list(expected)
        mirrored[Face.R], mirrored[Face.L] = expected[Face.L], expected[Face.R]
        problem = "centers are a mirror image" if actual == mirrored else "impossible centers"
        position = next(p for p in Face if actual[p] != expected[p])
        raise FaceletError(
            f"{problem}: with {up.name} on top and {front.name} in front, "
            f"{expected[position].name} must be {_CENTER_PLACES[position]}, "
            f"got {actual[position].name}"
        )
    return frame


def _read_pieces(
    kind: str,
    names: type[IntEnum],
    places: Sequence[tuple[int, ...]],
    pieces: Mapping[tuple[Face, ...], int],
    fixed: Sequence[Face],
    held: Sequence[Face],
    held_index: Sequence[int],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    # Reads one orbit from the frame-0 layout. Errors name slots and stickers as held:
    # held_index[i] is where fixed facelet i is shown.
    held_slots = {frozenset(slot): i for i, slot in enumerate(places)}
    perm: list[int] = []
    orient: list[int] = []
    seen: dict[int, int] = {}
    for slot in places:
        colors = tuple(fixed[i] for i in slot)
        held_slot = held_slots[frozenset(held_index[i] for i in slot)]
        # The orientation is the rotation that lists the colors as the piece lists them.
        found = [
            (pieces[turned], k)
            for k in range(len(colors))
            if (turned := colors[k:] + colors[:k]) in pieces
        ]
        if not found:
            stickers = ", ".join(held[i].name for i in places[held_slot])
            reason = (
                " (clockwise): no corner has these colors in this order"
                if kind == "corner"
                else ": no edge has these colors"
            )
            raise FaceletError(
                f"the {kind} at {names(held_slot).name} has stickers {stickers}{reason}"
            )
        piece, orientation = found[0]
        if piece in seen:
            raise FaceletError(
                f"{kind} {names(piece).name} appears twice, at {names(seen[piece]).name} "
                f"and {names(held_slot).name}"
            )
        seen[piece] = held_slot
        perm.append(piece)
        orient.append(orientation)
    return tuple(perm), tuple(orient)


def from_facelet_string(text: str) -> CubeState:
    """Return the state described by a 54-character facelet string, as held.

    The inverse of :func:`to_facelet_string`: the centers give the frame. Leading and
    trailing whitespace is ignored; otherwise only the letters U, R, F, D, L, B are allowed.

    Raises:
        FaceletError: naming the first problem found (length, characters, sticker counts,
            centers, pieces, then the invariants checked by :meth:`CubeState.validate`).
    """
    held = _read_stickers(text.strip())
    frame = _read_frame(held)
    fixed = [Face.U] * _N_FACELETS
    held_index = [0] * _N_FACELETS
    for i, source in enumerate(_FRAME_FACELETS[frame]):
        fixed[source] = held[i]
        held_index[source] = i
    cp, co = _read_pieces(
        "corner", Corner, _CORNER_FACELETS, _CORNER_PIECES, fixed, held, held_index
    )
    ep, eo = _read_pieces("edge", Edge, _EDGE_FACELETS, _EDGE_PIECES, fixed, held, held_index)
    state = CubeState(cp, co, ep, eo, frame)
    try:
        state.validate()
    except ValueError as error:
        if sum(co) % 3:
            hint = "a twisted corner"
        elif sum(eo) % 2:
            hint = "a flipped edge"
        else:
            hint = "two swapped pieces"
        raise FaceletError(f"impossible cube: {error} ({hint})") from None
    return state


# Where each face's block goes in the net, in face units (row, column): U above F,
# then L F R B in a row, then D below F.
_NET_BLOCKS: Final = {
    Face.U: (0, 1),
    Face.L: (1, 0),
    Face.F: (1, 1),
    Face.R: (1, 2),
    Face.B: (1, 3),
    Face.D: (2, 1),
}


def net(state: CubeState) -> tuple[tuple[Face | None, ...], ...]:
    """Return the unfolded net of ``state`` as held: 9 rows of 12 cells, ``None`` for gaps.

    U is at the top, then L, F, R and B in a row, then D, each face drawn as in the facelet
    string. Renderers (plain text here, colors in the UI) should draw from this grid.
    """
    stickers = facelets(state)
    grid: list[list[Face | None]] = [[None] * 12 for _ in range(9)]
    for face, (block_row, block_col) in _NET_BLOCKS.items():
        for i in range(9):
            grid[3 * block_row + i // 3][3 * block_col + i % 3] = stickers[9 * face + i]
    return tuple(tuple(row) for row in grid)


def to_net(state: CubeState) -> str:
    """Return the net of ``state`` as plain text: one letter per sticker, no colors.

    Stickers are separated by a space and faces by two, with no trailing spaces::

               U U U
               ...
        L L L  F F F  R R R  B B B
               ...
               D D D
    """
    lines = []
    for row in net(state):
        # Not "if cell": Face.U is 0, so it is falsy.
        letters = [" " if cell is None else cell.name for cell in row]
        blocks = (" ".join(letters[col : col + 3]) for col in range(0, 12, 3))
        lines.append("  ".join(blocks).rstrip())
    return "\n".join(lines)
