import subprocess
import sys
from collections import Counter

import pytest
from hypothesis import given
from hypothesis import strategies as st

from subeventually_core.cube import ALL_MOVES, SOLVED, CubeState, F, Face, Layer, M, Move, R, U, X
from subeventually_core.facelets import WCA_COLORS, facelets, net, to_facelet_string, to_net

sequences = st.lists(st.sampled_from(ALL_MOVES), max_size=30)


def test_solved_exports_to_the_standard_string() -> None:
    assert to_facelet_string(SOLVED) == ("UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB")


# Standard Kociemba facelet strings of single turns.
@pytest.mark.parametrize(
    ("move", "expected"),
    [
        (R, "UUFUUFUUFRRRRRRRRRFFDFFDFFDDDBDDBDDBLLLLLLLLLUBBUBBUBB"),
        (U, "UUUUUUUUUBBBRRRRRRRRRFFFFFFDDDDDDDDDFFFLLLLLLLLLBBBBBB"),
        (F, "UUUUUULLLURRURRURRFFFFFFFFFRRRDDDDDDLLDLLDLLDBBBBBBBBB"),
    ],
)
def test_single_turns_export_to_the_standard_strings(move: Move, expected: str) -> None:
    assert to_facelet_string(SOLVED.apply(move)) == expected


def test_x_puts_the_green_face_on_top() -> None:
    assert to_facelet_string(SOLVED.apply(X)) == (
        "FFFFFFFFFRRRRRRRRRDDDDDDDDDBBBBBBBBBLLLLLLLLLUUUUUUUUU"
    )


@pytest.mark.parametrize("frame", range(24))
def test_solved_cube_shows_its_frame_in_the_centers(frame: int) -> None:
    state = CubeState(*SOLVED.cubies, frame=frame)
    text = to_facelet_string(state)
    blocks = [text[i : i + 9] for i in range(0, 54, 9)]
    assert all(len(set(block)) == 1 for block in blocks)
    up, front = state.held
    assert (text[4], text[22]) == (up.name, front.name)


@given(sequences)
def test_every_color_appears_nine_times(seq: list[Move]) -> None:
    counts = Counter(facelets(SOLVED.apply_all(seq)))
    assert counts == dict.fromkeys(Face, 9)


# An independent model of the stickers: each facelet as (cubie position, face normal), and
# each move as quarter turns of the stickers in some layers about a coordinate axis.

type Vector = tuple[int, int, int]

NORMALS: dict[Face, Vector] = {
    Face.U: (0, 1, 0),
    Face.R: (1, 0, 0),
    Face.F: (0, 0, 1),
    Face.D: (0, -1, 0),
    Face.L: (-1, 0, 0),
    Face.B: (0, 0, -1),
}
# For each face as drawn in the net: the directions of "right" and "down" on the drawing.
DRAWING_AXES: dict[Face, tuple[Vector, Vector]] = {
    Face.U: ((1, 0, 0), (0, 0, 1)),
    Face.R: ((0, 0, -1), (0, -1, 0)),
    Face.F: ((1, 0, 0), (0, -1, 0)),
    Face.D: ((1, 0, 0), (0, 0, -1)),
    Face.L: ((0, 0, 1), (0, -1, 0)),
    Face.B: ((-1, 0, 0), (0, -1, 0)),
}


def sticker(index: int) -> tuple[Vector, Vector]:
    face, row, col = Face(index // 9), index % 9 // 3, index % 3
    normal, (right, down) = NORMALS[face], DRAWING_AXES[face]
    x, y, z = (
        n + (col - 1) * r + (row - 1) * d for n, r, d in zip(normal, right, down, strict=True)
    )
    return (x, y, z), normal


STICKERS = [sticker(i) for i in range(54)]
INDEX = {s: i for i, s in enumerate(STICKERS)}


def clockwise(v: Vector, axis: Vector) -> Vector:
    # A quarter turn clockwise looking at the face on the +axis side: -90 degrees about axis,
    # which is v -> a(a.v) - a x v for a unit axis a.
    a = axis
    dot = sum(p * q for p, q in zip(a, v, strict=True))
    cross = (a[1] * v[2] - a[2] * v[1], a[2] * v[0] - a[0] * v[2], a[0] * v[1] - a[1] * v[0])
    return (a[0] * dot - cross[0], a[1] * dot - cross[1], a[2] * dot - cross[2])


# Layer -> (axis it turns clockwise around, layers turned as coordinates along that axis).
X_AXIS, Y_AXIS, Z_AXIS = (1, 0, 0), (0, 1, 0), (0, 0, 1)
MINUS = {X_AXIS: (-1, 0, 0), Y_AXIS: (0, -1, 0), Z_AXIS: (0, 0, -1)}
LAYERS: dict[Layer, tuple[Vector, set[int]]] = {
    Layer.R: (X_AXIS, {1}),
    Layer.L: (MINUS[X_AXIS], {-1}),
    Layer.M: (MINUS[X_AXIS], {0}),
    Layer.RW: (X_AXIS, {0, 1}),
    Layer.LW: (MINUS[X_AXIS], {-1, 0}),
    Layer.X: (X_AXIS, {-1, 0, 1}),
    Layer.U: (Y_AXIS, {1}),
    Layer.D: (MINUS[Y_AXIS], {-1}),
    Layer.E: (MINUS[Y_AXIS], {0}),
    Layer.UW: (Y_AXIS, {0, 1}),
    Layer.DW: (MINUS[Y_AXIS], {-1, 0}),
    Layer.Y: (Y_AXIS, {-1, 0, 1}),
    Layer.F: (Z_AXIS, {1}),
    Layer.B: (MINUS[Z_AXIS], {-1}),
    Layer.S: (Z_AXIS, {0}),
    Layer.FW: (Z_AXIS, {0, 1}),
    Layer.BW: (MINUS[Z_AXIS], {-1, 0}),
    Layer.Z: (Z_AXIS, {-1, 0, 1}),
}


def turn_stickers(stickers: tuple[Face, ...], move: Move) -> list[Face]:
    axis, layers = LAYERS[move.layer]
    coordinate = next(i for i, a in enumerate(axis) if a)
    result = list(stickers)
    for i, (position, normal) in enumerate(STICKERS):
        if position[coordinate] not in layers:
            continue
        for _ in range(move.amount):
            position, normal = clockwise(position, axis), clockwise(normal, axis)
        result[INDEX[position, normal]] = stickers[i]
    return result


def test_independent_model_covers_every_layer() -> None:
    assert set(LAYERS) == set(Layer)


@given(sequences, st.sampled_from(ALL_MOVES))
def test_facelets_follow_the_moves_as_held(seq: list[Move], move: Move) -> None:
    state = SOLVED.apply_all(seq)
    assert list(facelets(state.apply(move))) == turn_stickers(facelets(state), move)


def test_net_is_nine_rows_of_twelve_cells() -> None:
    grid = net(SOLVED)
    assert len(grid) == 9
    assert all(len(row) == 12 for row in grid)
    assert sum(cell is not None for row in grid for cell in row) == 54


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (
            SOLVED,
            [
                "       U U U",
                "       U U U",
                "       U U U",
                "L L L  F F F  R R R  B B B",
                "L L L  F F F  R R R  B B B",
                "L L L  F F F  R R R  B B B",
                "       D D D",
                "       D D D",
                "       D D D",
            ],
        ),
        (
            SOLVED.apply(R),
            [
                "       U U F",
                "       U U F",
                "       U U F",
                "L L L  F F D  R R R  U B B",
                "L L L  F F D  R R R  U B B",
                "L L L  F F D  R R R  U B B",
                "       D D B",
                "       D D B",
                "       D D B",
            ],
        ),
        (
            SOLVED.apply(U),
            [
                "       U U U",
                "       U U U",
                "       U U U",
                "F F F  R R R  B B B  L L L",
                "L L L  F F F  R R R  B B B",
                "L L L  F F F  R R R  B B B",
                "       D D D",
                "       D D D",
                "       D D D",
            ],
        ),
        (
            SOLVED.apply(F),
            [
                "       U U U",
                "       U U U",
                "       L L L",
                "L L D  F F F  U R R  B B B",
                "L L D  F F F  U R R  B B B",
                "L L D  F F F  U R R  B B B",
                "       R R R",
                "       D D D",
                "       D D D",
            ],
        ),
        (
            SOLVED.apply(X),
            [
                "       F F F",
                "       F F F",
                "       F F F",
                "L L L  D D D  R R R  U U U",
                "L L L  D D D  R R R  U U U",
                "L L L  D D D  R R R  U U U",
                "       B B B",
                "       B B B",
                "       B B B",
            ],
        ),
        (
            SOLVED.apply(M),
            [
                "       U B U",
                "       U B U",
                "       U B U",
                "L L L  F U F  R R R  B D B",
                "L L L  F U F  R R R  B D B",
                "L L L  F U F  R R R  B D B",
                "       D F D",
                "       D F D",
                "       D F D",
            ],
        ),
    ],
    ids=["solved", "R", "U", "F", "x", "M"],
)
def test_plain_net(state: CubeState, expected: list[str]) -> None:
    assert to_net(state) == "\n".join(expected)


def test_wca_colors_name_every_face() -> None:
    assert dict(WCA_COLORS) == {
        Face.U: "white",
        Face.R: "red",
        Face.F: "green",
        Face.D: "yellow",
        Face.L: "orange",
        Face.B: "blue",
    }


def test_core_does_not_load_a_ui_library() -> None:
    code = (
        "import sys, subeventually_core.facelets; "
        "print(sorted({'rich', 'textual'} & set(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
