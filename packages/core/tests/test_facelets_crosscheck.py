"""Facelet strings checked against external references.

Each expected string was compared sticker by sticker with alg.cubing.net, a physical cube held
in WCA orientation, and Kociemba's solver (the relabeled string solves back to our state).
"""

import pytest

from subeventually_core.cube import SOLVED
from subeventually_core.facelets import from_facelet_string, to_facelet_string
from subeventually_core.notation import parse

CROSS_CHECKED = [
    pytest.param(
        "R U R' U'",
        "UULUUFUUFRRUBRRURRFFDFFUFFFDDRDDDDDDBLLLLLLLLBRRBBBBBB",
        id="sexy-move",
    ),
    pytest.param(
        "R U R' U' R' F R2 U' R' U' R U R' F'",
        "UUUUUUUUUBLFRRRRRRFFRFFFFFFDDDDDDDDDLRLLLLLLLRBBBBBBBB",
        id="t-perm",
    ),
    pytest.param(
        "D2 F2 U' B2 R2 U2 R2 F2 D' L2 U' R' D B' L' U' R F' L' U2 B",
        "FFUUURLBUBBFDRRBDDBLRRFLFDDDRLUDBDFRLFUBLFBLLRDUUBUFLR",
        id="wca-scramble",
    ),
    pytest.param(
        "y M' U2 Rw E S' x Fw2 D' Lw z' B Uw2 M2 Dw' Bw",
        "LRRFFFFRRULDLDRDUBRFBLLDRFLFDBRBBULLFUDDUBLUUBDDBRBUUF",
        id="slices-wides-rotations",
    ),
]


@pytest.mark.parametrize(("alg", "expected"), CROSS_CHECKED)
def test_export_matches_the_cross_checked_string(alg: str, expected: str) -> None:
    assert to_facelet_string(SOLVED.apply_all(parse(alg))) == expected


@pytest.mark.parametrize(("alg", "expected"), CROSS_CHECKED)
def test_import_of_the_cross_checked_string(alg: str, expected: str) -> None:
    assert from_facelet_string(expected) == SOLVED.apply_all(parse(alg))
