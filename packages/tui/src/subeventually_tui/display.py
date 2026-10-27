"""Drawing cube states in the terminal with Rich.

Both styles draw on a fixed dark backdrop, so white and yellow stay readable whatever the
terminal's own background is. Without a color terminal, the plain-text net of the core is
printed instead.
"""

from collections.abc import Mapping
from typing import Final, Literal, get_args

from rich.console import Console
from rich.text import Text

from subeventually_core.cube import CubeState
from subeventually_core.facelets import WCA_COLORS, net, to_net

type NetStyle = Literal["letters", "blocks"]

NET_STYLES: Final[tuple[NetStyle, ...]] = get_args(NetStyle.__value__)
"""The styles of :func:`colored_net`; the first is the default."""

BACKDROP: Final = "#1c1c1c"
"""The background of the whole net."""

# Per core color name: the letter shown, its color in the letters style (bright enough for
# bold text on the backdrop), and the cell color in the blocks style. Rich downgrades the
# colors to what the terminal supports (256 or 16 colors).
LETTERS: Final[Mapping[str, str]] = {
    "white": "W",
    "yellow": "Y",
    "green": "G",
    "blue": "B",
    "red": "R",
    "orange": "O",
}
FOREGROUNDS: Final[Mapping[str, str]] = {
    "white": "#f2f2f2",
    "yellow": "#ffd500",
    "green": "#1fd65f",
    "blue": "#5c9dff",
    "red": "#ff4d4d",
    "orange": "#ff9933",
}
BACKGROUNDS: Final[Mapping[str, str]] = {
    "white": "#ffffff",
    "yellow": "#ffd500",
    "green": "#009b48",
    "blue": "#0046ad",
    "red": "#b71234",
    "orange": "#ff5800",
}

# Per style: (text of a sticker cell, gap between stickers, gap between faces).
# The outer padding is a face gap on each side and a blank row above and below.
_LAYOUT: Final[dict[NetStyle, tuple[int, str, str]]] = {
    "letters": (1, " ", "  "),
    "blocks": (2, "", " "),
}


def colored_net(state: CubeState, style: NetStyle = "letters") -> Text:
    """Return the net of ``state`` on the backdrop, one styled span per sticker.

    ``letters`` shows each sticker as its color letter (W, Y, G, B, R, O) in bold and in its
    color; ``blocks`` shows it as a two-character cell of its color.
    """
    cell_width, sticker_gap, face_gap = _LAYOUT[style]
    text = Text(style=f"on {BACKDROP}")
    rows = net(state)
    width = 12 * cell_width + 8 * len(sticker_gap) + 3 * len(face_gap) + 2 * len(face_gap)
    text.append(" " * width + "\n")
    for row in rows:
        text.append(face_gap)
        for col, cell in enumerate(row):
            if col:
                text.append(face_gap if col % 3 == 0 else sticker_gap)
            if cell is None:
                text.append(" " * cell_width)
            elif style == "letters":
                color = WCA_COLORS[cell]
                text.append(LETTERS[color], style=f"bold {FOREGROUNDS[color]}")
            else:
                text.append(" " * cell_width, style=f"on {BACKGROUNDS[WCA_COLORS[cell]]}")
        text.append(face_gap + "\n")
    text.append(" " * width)
    return text


def print_net(state: CubeState, console: Console, style: NetStyle = "letters") -> None:
    """Print the net of ``state``: in ``style`` on a color terminal, else the plain-text net."""
    if console.is_terminal and console.color_system is not None and not console.no_color:
        console.print(colored_net(state, style), soft_wrap=True)
    else:
        # A Text, not a str, so Rich applies no markup or highlighting.
        console.print(Text(to_net(state)), soft_wrap=True)
