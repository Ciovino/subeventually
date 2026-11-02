"""The cube playground: type moves, watch the net change, undo, reset, inspect the state.

The app only draws a :class:`~subeventually_core.session.Session` and turns input into
session operations. Commands start with ``:``, which never occurs in notation, so a line is
either moves or a command. Command parsing and the status text are pure functions, so they
are tested without running the app.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import ClassVar, Final, Literal, assert_never, get_args

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Input, Static

from subeventually_core.cube import SOLVED
from subeventually_core.facelets import WCA_COLORS, to_facelet_string
from subeventually_core.notation import NotationError
from subeventually_core.session import Session
from subeventually_tui.display import NET_STYLES, NetStyle, colored_net

type CommandName = Literal[
    "undo", "redo", "inverse", "reset", "setup", "state", "style", "help", "quit"
]

COMMAND_NAMES: Final[tuple[CommandName, ...]] = get_args(CommandName.__value__)

# Whether each command takes an argument: never, always or optionally.
_ARGUMENTS: Final[Mapping[CommandName, Literal["none", "required", "optional"]]] = {
    "undo": "none",
    "redo": "none",
    "inverse": "none",
    "reset": "none",
    "setup": "required",
    "state": "optional",
    "style": "none",
    "help": "none",
    "quit": "none",
}

# Typed text to command name; also lets mypy narrow a str to CommandName.
_BY_TEXT: Final[Mapping[str, CommandName]] = {name: name for name in COMMAND_NAMES}

HELP: Final = """\
Type moves and press Enter: each line is one step of the history.
:undo  :redo  :inverse  :reset  :setup <moves>  :style  :help  :quit
:state copies the facelet string, :state <54 letters> loads one
Keys: ctrl+z undo, ctrl+y redo, ctrl+t style, f1 help, ctrl+q quit"""


class CommandError(ValueError):
    """An input line that starts with ``:`` but is not a valid command."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True, slots=True)
class Command:
    """A parsed ``:name argument`` line. ``argument`` is stripped, ``""`` when absent."""

    name: CommandName
    argument: str = ""


def parse_command(text: str) -> Command | None:
    """Return the command on an input line, or ``None`` if the line is moves.

    Raises:
        CommandError: for an unknown command or a wrong argument.
    """
    stripped = text.strip()
    if not stripped.startswith(":"):
        return None
    name, _, argument = stripped[1:].partition(" ")
    argument = argument.strip()
    command_name = _BY_TEXT.get(name)
    if command_name is None:
        raise CommandError(f"unknown command ':{name}', type :help for the list")
    takes = _ARGUMENTS[command_name]
    if takes == "none" and argument:
        raise CommandError(f":{name} takes no argument")
    if takes == "required" and not argument:
        raise CommandError(f":{name} needs moves, for example :{name} R U R' U'")
    return Command(command_name, argument)


def status_line(session: Session) -> str:
    """Return how the cube is held, whether it is solved and the move count of the history."""
    up, front = session.state.held
    solved = "solved" if session.state.is_solved() else "not solved"
    count = session.move_count
    moves = "1 move" if count == 1 else f"{count} moves"
    return f"{WCA_COLORS[up]} on top, {WCA_COLORS[front]} in front · {solved} · {moves}"


def error_caret(text: str, error: NotationError) -> str:
    """Return the line of ``text`` with the error, and a caret under it followed by the error."""
    line = text.split("\n")[error.line - 1]
    return f"{line}\n{' ' * (error.column - 1)}^ {error}"


def history_text(session: Session) -> str:
    """Return the history as numbered lines, after where it started from."""
    start = "start: solved" if session.start == SOLVED else "start: loaded state"
    lines = [start]
    for number, sequence in enumerate(session.history, 1):
        # A comment in the middle of a sequence ends a line; indent what follows.
        lines.append(f"{number:>3}  " + str(sequence).replace("\n", "\n     "))
    return "\n".join(lines)


class PlaygroundApp(App[None]):
    """The playground app. ``session`` is the whole state; assigning it redraws the screen."""

    TITLE = "subeventually playground"
    ENABLE_COMMAND_PALETTE = False
    CSS = """
    #top { height: 1fr; }
    #net { width: auto; height: auto; }
    #history-panel { width: 1fr; border-left: solid $panel; padding: 0 1; }
    #status, #facelets, #message { height: auto; padding: 0 1; }
    #message { color: $text-muted; }
    #message.error { color: $error; }
    """
    # Priority bindings are checked before the focused Input, which gets every other key.
    # Plain letters are moves, so only ctrl and function keys are bound.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+z", "undo", "Undo", priority=True),
        Binding("ctrl+y", "redo", "Redo", priority=True),
        Binding("ctrl+t", "toggle_style", "Style", priority=True),
        Binding("f1", "help", "Help", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),  # Textual's own, shown in the footer
    ]

    # init=False: the widgets don't exist before compose, so on_mount draws the first time.
    session: reactive[Session] = reactive(Session, init=False)
    style: reactive[NetStyle] = reactive[NetStyle](NET_STYLES[0], init=False)

    def compose(self) -> ComposeResult:
        """Build the widget tree: net and history on top, then status, input and keys."""
        with Horizontal(id="top"):
            yield Static(id="net")
            with VerticalScroll(id="history-panel"):
                yield Static(id="history", markup=False)
        yield Static(id="status", markup=False)
        yield Static(id="facelets", markup=False)
        yield Static(id="message", markup=False)
        yield Input(placeholder="moves, or :help", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        """Draw the solved cube and put the cursor in the input line."""
        self._draw()
        self.query_one("#prompt", Input).focus()

    def watch_session(self) -> None:
        """Redraw after every change of session."""
        self._draw()

    def watch_style(self) -> None:
        """Redraw the net in the new style."""
        self._draw()

    def _draw(self) -> None:
        state = self.session.state
        self.query_one("#net", Static).update(colored_net(state, self.style))
        self.query_one("#history", Static).update(history_text(self.session))
        self.query_one("#status", Static).update(status_line(self.session))
        self.query_one("#facelets", Static).update(to_facelet_string(state))

    def _say(self, text: str, *, error: bool = False) -> None:
        message = self.query_one("#message", Static)
        message.update(text)
        message.set_class(error, "error")

    def _change(self, operation: Callable[[Session], Session], source: str = "") -> bool:
        # Replace the session with operation(session). On error, show it and keep the session.
        # ``source`` is the notation text the operation parses, to point at a parse error.
        try:
            session = operation(self.session)
        except NotationError as error:
            self._say(error_caret(source, error), error=True)
            return False
        except ValueError as error:
            self._say(str(error), error=True)
            return False
        self.session = session
        self._say("")
        return True

    @on(Input.Submitted)
    def submitted(self, event: Input.Submitted) -> None:
        """Run the line as moves or as a command; clear it only if that worked."""
        text = event.value
        try:
            command = parse_command(text)
        except CommandError as error:
            self._say(error.message, error=True)
            return
        if command is None:
            done = self._change(lambda session: session.apply_text(text), text)
        else:
            done = self._run(command)
        if done:
            event.input.clear()

    def _run(self, command: Command) -> bool:
        argument = command.argument
        match command.name:
            case "undo":
                return self._change(Session.undo)
            case "redo":
                return self._change(Session.redo)
            case "inverse":
                return self._change(Session.invert)
            case "reset":
                return self._change(Session.reset)
            case "setup":
                return self._change(lambda _: Session.from_moves(argument), argument)
            case "state" if argument:
                return self._change(lambda _: Session.from_facelets(argument))
            case "state":
                self.copy_to_clipboard(to_facelet_string(self.session.state))
                self._say("facelet string copied to the clipboard")
                return True
            case "style":
                self.action_toggle_style()
                return True
            case "help":
                self.action_help()
                return True
            case "quit":
                self.exit()
                return True
            case _:
                assert_never(command.name)

    def action_undo(self) -> None:
        """Undo the last line."""
        self._change(Session.undo)

    def action_redo(self) -> None:
        """Redo the last undone line."""
        self._change(Session.redo)

    def action_toggle_style(self) -> None:
        """Switch the net between letters and blocks."""
        self.style = NET_STYLES[(NET_STYLES.index(self.style) + 1) % len(NET_STYLES)]

    def action_help(self) -> None:
        """Show the commands and keys."""
        self._say(HELP)
