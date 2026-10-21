import pytest
from hypothesis import given
from hypothesis import strategies as st

from subeventually_core.cube import (
    FACE_TURNS,
    SOLVED,
    X2,
    X_PRIME,
    Y2,
    Y_PRIME,
    Z2,
    Z_PRIME,
    B,
    CubeState,
    F,
    Face,
    L,
    Layer,
    Move,
    R,
    U,
    X,
    Y,
    Z,
    frame_of,
)

ROTATIONS = (X, X2, X_PRIME, Y, Y2, Y_PRIME, Z, Z2, Z_PRIME)
OPPOSITE = {Face.U: Face.D, Face.R: Face.L, Face.F: Face.B}
OPPOSITE |= {b: a for a, b in OPPOSITE.items()}

# Independent oracle for the face on the right: each corner's facelets listed clockwise
# seen from outside (ADR 0004). Up, right, front appear in that clockwise order.
CLOCKWISE_CORNERS = ("URF", "UFL", "ULB", "UBR", "DFR", "DLF", "DBL", "DRB")


def right_of(up: Face, front: Face) -> Face:
    for corner in CLOCKWISE_CORNERS:
        for k in range(3):
            turned = corner[k:] + corner[:k]
            if (Face[turned[0]], Face[turned[2]]) == (up, front):
                return Face[turned[1]]
    raise AssertionError(f"no corner has {up.name} and {front.name} adjacent")


def faces_held(up: Face, front: Face) -> dict[Layer, Face]:
    right = right_of(up, front)
    return {
        Layer.U: up,
        Layer.D: OPPOSITE[up],
        Layer.F: front,
        Layer.B: OPPOSITE[front],
        Layer.R: right,
        Layer.L: OPPOSITE[right],
    }


def held_in(frame: int) -> CubeState:
    return CubeState(*SOLVED.cubies, frame=frame)


# Encoding (ADR 0005)


def test_frame_0_is_white_up_green_front() -> None:
    assert frame_of(Face.U, Face.F) == 0
    assert SOLVED.held == (Face.U, Face.F)


@pytest.mark.parametrize("frame", range(24))
def test_frame_of_and_held_round_trip(frame: int) -> None:
    up, front = held_in(frame).held
    assert frame_of(up, front) == frame
    assert frame // 4 == up


def test_a_few_frames_from_the_adr_table() -> None:
    assert held_in(1).held == (Face.U, Face.R)
    assert held_in(8).held == (Face.F, Face.D)
    assert held_in(12).held == (Face.D, Face.F)
    assert held_in(23).held == (Face.B, Face.L)


@pytest.mark.parametrize(("up", "front"), [(Face.U, Face.U), (Face.U, Face.D), (Face.R, Face.L)])
def test_frame_of_rejects_faces_that_are_not_adjacent(up: Face, front: Face) -> None:
    with pytest.raises(ValueError, match="adjacent"):
        frame_of(up, front)


# Rotations


@pytest.mark.parametrize("frame", range(24))
def test_rotations_move_the_centers_as_on_a_real_cube(frame: int) -> None:
    up, front = held_in(frame).held
    right = right_of(up, front)
    # x brings the front up, y brings the right face to the front, z brings the left face up.
    assert held_in(frame).apply(X).held == (front, OPPOSITE[up])
    assert held_in(frame).apply(Y).held == (up, right)
    assert held_in(frame).apply(Z).held == (OPPOSITE[right], front)


@pytest.mark.parametrize("frame", range(24))
def test_y_only_changes_the_last_two_bits(frame: int) -> None:
    after = held_in(frame).apply(Y).frame
    assert after // 4 == frame // 4
    assert after % 4 == (frame + 1) % 4


@pytest.mark.parametrize("rotation", ROTATIONS, ids=str)
def test_rotations_change_only_the_frame(rotation: Move) -> None:
    state = SOLVED.apply_all([R, U, F])
    assert state.apply(rotation).cubies == state.cubies


@pytest.mark.parametrize("rotation", [X, Y, Z], ids=str)
def test_rotation_has_order_exactly_4(rotation: Move) -> None:
    frames = [SOLVED.apply_all([rotation] * k).frame for k in range(1, 5)]
    assert frames[3] == 0
    assert 0 not in frames[:3]


@given(st.lists(st.sampled_from(ROTATIONS), max_size=30))
def test_solved_cube_stays_solved_under_any_rotations(seq: list[Move]) -> None:
    assert SOLVED.apply_all(seq).is_solved()


# Face turns under a frame


@pytest.mark.parametrize("frame", range(24))
def test_face_turn_turns_the_face_in_that_position(frame: int) -> None:
    state = held_in(frame).apply_all([R, U])  # not solved, so the turn has something to act on
    faces = faces_held(*state.held)
    for move in FACE_TURNS:
        fixed = Move(Layer[faces[move.layer].name], move.amount)
        expected = CubeState(*state.cubies).apply(fixed)
        assert state.apply(move) == CubeState(*expected.cubies, frame=state.frame), move


def test_y_r_y_prime_is_b() -> None:
    assert SOLVED.apply_all([Y, R, Y_PRIME]) == SOLVED.apply(B)


def test_x_u_x_prime_is_f() -> None:
    assert SOLVED.apply_all([X, U, X_PRIME]) == SOLVED.apply(F)


# Hand-checked against a physical cube: start solved, white on top, green in front.


def test_x_by_hand() -> None:
    # Green comes to the top, yellow to the front.
    assert SOLVED.apply(X).held == (Face.F, Face.D)


def test_y_by_hand() -> None:
    # Red comes to the front, white stays on top; no piece moves relative to the centers.
    state = SOLVED.apply(Y)
    assert state.held == (Face.U, Face.R)
    assert state.cubies == SOLVED.cubies


def test_z2_then_r_turns_the_orange_face() -> None:
    # Yellow on top, green in front: the face on the right is orange, the frame-0 L.
    state = SOLVED.apply_all([Z2, R])
    assert state.held == (Face.D, Face.F)
    assert state.cubies == SOLVED.apply(L).cubies
