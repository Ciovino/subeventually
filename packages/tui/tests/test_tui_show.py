import shutil
import subprocess
from io import StringIO

import pytest
from rich.console import Console

from subeventually_core.cube import SOLVED, CubeState, R
from subeventually_core.facelets import WCA_COLORS, to_net
from subeventually_core.notation import parse
from subeventually_tui import cli
from subeventually_tui.cli import main
from subeventually_tui.display import (
    BACKDROP,
    BACKGROUNDS,
    FOREGROUNDS,
    LETTERS,
    NET_STYLES,
    NetStyle,
    colored_net,
    print_net,
)


def color_console(*, no_color: bool = False) -> tuple[Console, StringIO]:
    file = StringIO()
    console = Console(
        file=file, force_terminal=True, color_system="truecolor", width=80, no_color=no_color
    )
    return console, file


# The command.


def test_show_prints_the_plain_net_when_not_a_terminal(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["show", "R U R' U'"]) == 0
    assert capsys.readouterr().out == to_net(SOLVED.apply_all(parse("R U R' U'"))) + "\n"


def test_show_without_moves_prints_the_solved_cube(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["show", ""]) == 0
    assert capsys.readouterr().out == to_net(SOLVED) + "\n"


def test_show_rejects_invalid_moves(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["show", "R U2 3Rw"])
    assert exc_info.value.code == 2
    error = capsys.readouterr().err
    assert "line 1, column 6: big-cube notation is not supported (3x3 only)" in error


@pytest.mark.parametrize(
    ("argv", "style"),
    [(["show", "R"], "letters"), (["show", "--style", "blocks", "R"], "blocks")],
    ids=["default", "blocks"],
)
def test_show_passes_the_style(
    monkeypatch: pytest.MonkeyPatch, argv: list[str], style: NetStyle
) -> None:
    calls: list[tuple[CubeState, NetStyle]] = []
    monkeypatch.setattr(cli, "print_net", lambda state, _, s: calls.append((state, s)))
    assert main(argv) == 0
    assert calls == [(SOLVED.apply(R), style)]


def test_show_rejects_an_unknown_style(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["show", "--style", "nope", "R"])
    assert exc_info.value.code == 2
    assert "invalid choice: 'nope'" in capsys.readouterr().err


def test_console_script_shows_a_cube() -> None:
    executable = shutil.which("subeventually")
    assert executable is not None, "the subeventually console script is not on PATH"
    result = subprocess.run([executable, "show", "R"], capture_output=True, text=True, check=True)
    assert result.stdout == to_net(SOLVED.apply_all(parse("R"))) + "\n"


# Colors and letters.


def test_every_core_color_has_a_letter_and_two_colors() -> None:
    colors = set(WCA_COLORS.values())
    assert set(LETTERS) == set(FOREGROUNDS) == set(BACKGROUNDS) == colors
    assert sorted(LETTERS.values()) == ["B", "G", "O", "R", "W", "Y"]


def luminance(color: str) -> float:
    # WCAG 2 relative luminance of "#rrggbb".
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


@pytest.mark.parametrize("color", sorted(FOREGROUNDS))
def test_letters_are_readable_on_the_backdrop(color: str) -> None:
    lighter, darker = sorted((luminance(FOREGROUNDS[color]), luminance(BACKDROP)), reverse=True)
    assert (lighter + 0.05) / (darker + 0.05) >= 4.5


# Rendering.


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (
            SOLVED,
            [
                "",
                "         W W W",
                "         W W W",
                "         W W W",
                "  O O O  G G G  R R R  B B B",
                "  O O O  G G G  R R R  B B B",
                "  O O O  G G G  R R R  B B B",
                "         Y Y Y",
                "         Y Y Y",
                "         Y Y Y",
                "",
            ],
        ),
        (
            SOLVED.apply(R),
            [
                "",
                "         W W G",
                "         W W G",
                "         W W G",
                "  O O O  G G Y  R R R  W B B",
                "  O O O  G G Y  R R R  W B B",
                "  O O O  G G Y  R R R  W B B",
                "         Y Y B",
                "         Y Y B",
                "         Y Y B",
                "",
            ],
        ),
    ],
    ids=["solved", "R"],
)
def test_letters_snapshot(state: CubeState, expected: list[str]) -> None:
    lines = colored_net(state, "letters").plain.split("\n")
    assert [line.rstrip() for line in lines] == expected


@pytest.mark.parametrize("style", NET_STYLES)
def test_net_is_a_rectangle_on_the_backdrop(style: NetStyle) -> None:
    text = colored_net(SOLVED, style)
    lines = text.plain.split("\n")
    assert len(lines) == 11
    assert len({len(line) for line in lines}) == 1
    assert text.style == f"on {BACKDROP}"


def test_letters_style_has_one_bold_colored_letter_per_sticker() -> None:
    text = colored_net(SOLVED, "letters")
    assert len(text.spans) == 54
    for span in text.spans:
        letter = text.plain[span.start : span.end]
        color = next(c for c, ch in LETTERS.items() if ch == letter)
        assert span.style == f"bold {FOREGROUNDS[color]}"


def test_blocks_style_has_one_colored_cell_per_sticker() -> None:
    text = colored_net(SOLVED, "blocks")
    assert len(text.spans) == 54
    assert all(span.end - span.start == 2 for span in text.spans)
    assert {span.style for span in text.spans} == {f"on {c}" for c in BACKGROUNDS.values()}


def test_letters_on_a_color_terminal() -> None:
    console, file = color_console()
    print_net(SOLVED, console)
    output = file.getvalue()
    assert "\x1b[1;38;2;31;214;95;48;2;28;28;28mG" in output  # bold green G on the backdrop
    assert output.count("\n") == 11


def test_blocks_on_a_color_terminal() -> None:
    console, file = color_console()
    print_net(SOLVED, console, "blocks")
    output = file.getvalue()
    assert "48;2;0;155;72m  " in output  # a green cell, #009b48
    assert output.count("\n") == 11


@pytest.mark.parametrize("style", NET_STYLES)
def test_no_color_terminal_gets_the_plain_net(style: NetStyle) -> None:
    console, file = color_console(no_color=True)
    print_net(SOLVED, console, style)
    assert file.getvalue() == to_net(SOLVED) + "\n"
