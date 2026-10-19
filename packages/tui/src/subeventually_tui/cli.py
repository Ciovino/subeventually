"""Command-line entry point for the ``subeventually`` command."""

import argparse
from collections.abc import Sequence

from subeventually_tui import __version__


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the app. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog="subeventually",
        description="A cubing assistant for speedcubers.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args(argv)
    return 0
