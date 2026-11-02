import asyncio
import subprocess
import sys
from collections.abc import Awaitable, Callable

import pytest
from textual.content import Content
from textual.pilot import Pilot
from textual.widgets import Input, Static

from subeventually_core.cube import SOLVED, X
from subeventually_core.facelets import to_facelet_string
from subeventually_core.notation import NotationError, parse
from subeventually_core.session import Session
from subeventually_tui.cli import main
from subeventually_tui.display import colored_net
from subeventually_tui.playground import (
    COMMAND_NAMES,
    Command,
    CommandError,
    PlaygroundApp,
    error_caret,
    history_text,
    parse_command,
    status_line,
)

SEXY = "R U R' U'"
# The cube held after x, from docs/NOTATION.md.
AFTER_X = "FFFFFFFFFRRRRRRRRRDDDDDDDDDBBBBBBBBBLLLLLLLLLUUUUUUUUU"


# Pure helpers.


@pytest.mark.parametrize("text", [SEXY, "", "  R", "// :undo is only a comment"])
def test_moves_are_not_commands(text: str) -> None:
    assert parse_command(text) is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (":undo", Command("undo")),
        ("  :reset  ", Command("reset")),
        (":setup R U  R'", Command("setup", "R U  R'")),
        (":state", Command("state")),
        (f":state   {AFTER_X} ", Command("state", AFTER_X)),
    ],
)
def test_parse_command(text: str, expected: Command) -> None:
    assert parse_command(text) == expected


def test_every_command_is_known() -> None:
    for name in COMMAND_NAMES:
        argument = " R" if name == "setup" else ""
        assert parse_command(f":{name}{argument}") == Command(name, argument.strip())


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (":foo", "unknown command ':foo', type :help for the list"),
        (":", "unknown command ':', type :help for the list"),
        (":Undo", "unknown command ':Undo', type :help for the list"),
        (":undo now", ":undo takes no argument"),
        (":setup", ":setup needs moves, for example :setup R U R' U'"),
    ],
)
def test_parse_command_rejects(text: str, message: str) -> None:
    with pytest.raises(CommandError) as exc_info:
        parse_command(text)
    assert exc_info.value.message == message


@pytest.mark.parametrize(
    ("session", "expected"),
    [
        (Session(), "white on top, green in front · solved · 0 moves"),
        (Session().apply_text("R"), "white on top, green in front · not solved · 1 move"),
        (Session().apply_text("x"), "green on top, yellow in front · solved · 0 moves"),
        (Session().apply_text("y M2 U M2"), "white on top, red in front · not solved · 3 moves"),
    ],
)
def test_status_line(session: Session, expected: str) -> None:
    assert status_line(session) == expected


def test_error_caret_points_at_the_column() -> None:
    with pytest.raises(NotationError) as exc_info:
        parse("R U2 3Rw")
    assert error_caret("R U2 3Rw", exc_info.value) == (
        "R U2 3Rw\n     ^ line 1, column 6: big-cube notation is not supported (3x3 only)"
    )


def test_error_caret_on_a_later_line() -> None:
    with pytest.raises(NotationError) as exc_info:
        parse("R U\nR'2")
    assert error_caret("R U\nR'2", exc_info.value).startswith("R'2\n  ^ line 2, column 3:")


def test_history_text() -> None:
    session = Session.from_moves("F").apply_text(SEXY).apply_text("U // a\nR")
    assert history_text(session) == "start: loaded state\n  1  R U R' U'\n  2  U // a\n     R"
    assert history_text(Session()) == "start: solved"


# The command line.


def test_playground_command_runs_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    runs: list[PlaygroundApp] = []
    monkeypatch.setattr(PlaygroundApp, "run", lambda self: runs.append(self))
    assert main(["playground"]) == 0
    assert len(runs) == 1


def test_cli_loads_textual_only_for_the_playground() -> None:
    code = "import sys, subeventually_tui.cli; print('textual' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "False"


# The app, headless with Textual's test pilot.

type Scenario = Callable[[PlaygroundApp, Pilot[None]], Awaitable[None]]


def run_app(scenario: Scenario) -> PlaygroundApp:
    # Pilot tests are async; asyncio.run keeps them plain pytest tests, with no plugin.
    app = PlaygroundApp()

    async def run() -> None:
        async with app.run_test() as pilot:
            await scenario(app, pilot)

    asyncio.run(run())
    return app


async def submit(pilot: Pilot[None], text: str) -> None:
    # Pressing each key is slow; test_typing_moves_updates_the_net types for real.
    pilot.app.query_one("#prompt", Input).value = text
    await pilot.press("enter")


def shown(app: PlaygroundApp, widget_id: str) -> str:
    # The visual is what is drawn: content after markup, if the widget reads markup.
    visual = app.query_one(f"#{widget_id}", Static).visual
    assert isinstance(visual, Content)
    return visual.plain


def test_starts_solved() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        assert app.query_one("#net", Static).content == colored_net(SOLVED)
        assert shown(app, "status") == "white on top, green in front · solved · 0 moves"
        assert shown(app, "facelets") == to_facelet_string(SOLVED)
        assert app.focused is app.query_one("#prompt", Input)

    run_app(scenario)


def test_typing_moves_updates_the_net() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await pilot.press(*SEXY, "enter")
        state = SOLVED.apply_all(parse(SEXY))
        assert app.query_one("#net", Static).content == colored_net(state)
        assert shown(app, "history") == "start: solved\n  1  R U R' U'"
        assert shown(app, "facelets") == to_facelet_string(state)
        assert "4 moves" in shown(app, "status")
        assert app.query_one("#prompt", Input).value == ""

    run_app(scenario)


def test_invalid_moves_show_the_error_and_keep_the_state() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, "R")
        await submit(pilot, "R U2 3Rw")
        assert shown(app, "message") == (
            "R U2 3Rw\n     ^ line 1, column 6: big-cube notation is not supported (3x3 only)"
        )
        assert app.query_one("#message", Static).has_class("error")
        assert app.session == Session().apply_text("R")
        assert app.query_one("#prompt", Input).value == "R U2 3Rw"

    run_app(scenario)


def test_text_is_shown_as_typed_not_as_markup() -> None:
    # [b] would be a bold tag if the widgets read Textual markup.
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, "[b]R")
        assert shown(app, "message").startswith("[b]R\n^ line 1, column 1: commutator")
        await submit(pilot, "R // [b]pair")
        assert shown(app, "history").endswith("1  R // [b]pair")

    run_app(scenario)


def test_undo_and_redo_keys() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, "U")
        await submit(pilot, SEXY)
        await pilot.press("ctrl+z")
        assert app.session.history == (parse("U"),)
        assert app.query_one("#net", Static).content == colored_net(SOLVED.apply_all(parse("U")))
        await pilot.press("ctrl+y")
        assert app.session == Session().apply_text("U").apply_text(SEXY)

    run_app(scenario)


def test_undo_key_with_empty_history_shows_an_error() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await pilot.press("ctrl+z")
        assert shown(app, "message") == "nothing to undo"
        assert app.session == Session()

    run_app(scenario)


def test_style_key_switches_to_blocks_and_back() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await pilot.press("ctrl+t")
        assert app.query_one("#net", Static).content == colored_net(SOLVED, "blocks")
        await submit(pilot, ":style")
        assert app.query_one("#net", Static).content == colored_net(SOLVED, "letters")

    run_app(scenario)


def test_undo_and_redo_commands() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, "R")
        await submit(pilot, ":undo")
        assert app.session == Session().apply_text("R").undo()
        await submit(pilot, ":redo")
        assert app.session == Session().apply_text("R")

    run_app(scenario)


def test_inverse_returns_to_solved() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, "y R U")
        await submit(pilot, ":inverse")
        assert app.session.state == SOLVED
        assert "· solved ·" in shown(app, "status")
        assert len(app.session.history) == 2

    run_app(scenario)


def test_reset_and_setup() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, ":setup F R")
        assert app.session == Session.from_moves("F R")
        assert shown(app, "history") == "start: loaded state"
        await submit(pilot, ":reset")
        assert app.session == Session()

    run_app(scenario)


def test_setup_error_points_into_the_moves() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, ":setup R'2")
        assert shown(app, "message").startswith("R'2\n  ^ line 1, column 3:")
        assert app.session == Session()

    run_app(scenario)


def test_state_loads_a_facelet_string() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, f":state {AFTER_X}")
        assert app.session.state == SOLVED.apply(X)
        assert shown(app, "status") == "green on top, yellow in front · solved · 0 moves"

    run_app(scenario)


def test_state_rejects_an_invalid_facelet_string() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, ":state UUU")
        assert shown(app, "message") == "facelet string must have 54 characters, got 3"
        assert app.session == Session()

    run_app(scenario)


def test_state_copies_the_facelet_string(monkeypatch: pytest.MonkeyPatch) -> None:
    copied: list[str] = []

    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        monkeypatch.setattr(app, "copy_to_clipboard", copied.append)
        await submit(pilot, "R")
        await submit(pilot, ":state")
        assert shown(app, "message") == "facelet string copied to the clipboard"

    run_app(scenario)
    assert copied == [to_facelet_string(SOLVED.apply_all(parse("R")))]


def test_unknown_command_shows_an_error() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, "R")
        await submit(pilot, ":foo")
        assert shown(app, "message") == "unknown command ':foo', type :help for the list"
        assert app.session == Session().apply_text("R")
        assert app.query_one("#prompt", Input).value == ":foo"

    run_app(scenario)


def test_help() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await pilot.press("f1")
        assert ":inverse" in shown(app, "message")
        await submit(pilot, "R")
        assert shown(app, "message") == ""

    run_app(scenario)


def test_quit_command_exits() -> None:
    async def scenario(app: PlaygroundApp, pilot: Pilot[None]) -> None:
        await submit(pilot, ":quit")
        await pilot.pause()
        assert not app.is_running

    run_app(scenario)
