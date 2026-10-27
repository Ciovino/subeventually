"""Command-line entry point for the ``subeventually`` command."""

import argparse
from collections.abc import Sequence

from rich.console import Console

from subeventually_core.cube import SOLVED
from subeventually_core.notation import NotationError, parse
from subeventually_tui import __version__
from subeventually_tui.display import NET_STYLES, print_net


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the app. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog="subeventually",
        description="A cubing assistant for speedcubers.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    show = commands.add_parser(
        "show",
        help="show a cube after some moves",
        description="Print the net of a solved cube (white on top, green in front) after MOVES.",
    )
    show.add_argument("moves", metavar="MOVES", help="moves in WCA notation, e.g. \"R U R' U'\"")
    show.add_argument(
        "--style",
        choices=NET_STYLES,
        default=NET_STYLES[0],
        help="color letters (default) or colored blocks; ignored without a color terminal",
    )
    args = parser.parse_args(argv)

    if args.command == "show":
        try:
            moves = parse(args.moves)
        except NotationError as error:
            show.error(str(error))
        print_net(SOLVED.apply_all(moves), Console(), args.style)
    return 0
