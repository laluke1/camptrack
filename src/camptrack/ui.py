"""
User Interface (UI) helpers.
"""

import math
import re
import shutil

from camptrack import __version__

from functools import lru_cache


# ASCII art generated from https://patorjk.com/software/taag
LOGO = r"""
  ____                    _____               _
 / ___|__ _ _ __ ___  _ _|_   _| __ __ _  ___| | __
| |   / _` | '_ ` _ \| '_ \| || '__/ _` |/ __| |/ /
| |__| (_| | | | | | | |_) | || | | (_| | (__|   <
 \____\__,_|_| |_| |_| .__/|_||_|  \__,_|\___|_|\_\
                     |_|
""".rstrip()

TAGLINE = "A Scout Camp Management System"


def show_header(*, center: bool = False, center_width: int = 80) -> None:
    if center:
        # Center the LOGO within a `center_width` character field
        lines = LOGO.splitlines()

        width = max(len(line) for line in lines)     # Width of the logo
        left_padding = (center_width - width) // 2   # Padding needed per side

        for line in lines:
            print(" " * max(left_padding, 0) + line)
    else:
        print(LOGO)
    print(f'\n{TAGLINE}')
    print(f'Version: {__version__}\n')


class Ansi:
    """
    Selected ANSI escape sequences for terminal colors and control
    """

    # Used to start a new color for text
    RED = '\033[38;5;196m'
    BLUE = '\033[38;5;39m'
    GREEN = '\033[38;5;42m'
    PURPLE = '\033[38;5;177m'
    LIME = '\033[38;5;190m'
    GRAY = '\033[38;5;248m'

    BOLD = '\033[1m'

    # Used to deactivate the current color (i.e. back to default)
    END = '\033[0m'

    # Control
    MOVE_CURSOR_UP = '\033[A'  # Move the cursor up a line
    CLEAR_LINE = '\033[2K'     # Clear current line


@lru_cache(maxsize=1)  # Cache so it's only compiled once
def _get_ansi_compiled_regex() -> re.Pattern[str]:
    return re.compile(r'\033\[[0-9;]*m')


def center(s: str, width: int = 80) -> str:
    """
    Analagous to `str.center()`, but accounts for ANSI escape codes.
    """
    # Length of string if we strip ANSI escape codes
    strlen_no_ansi = len(_get_ansi_compiled_regex().sub('', s))

    # Cannot center within `width` if this is the case
    if strlen_no_ansi >= width:
        return s

    # Calculate the padding needed on each side and apply it
    padding = width - strlen_no_ansi
    left_padding = padding // 2
    right_padding = padding - left_padding

    return f"{' ' * left_padding}{s}{' ' * right_padding}"


def clear_terminal_lines(text: str) -> None:
    """
    Clear terminal lines that the given `text` fills, based on calculations
    of the current terminal width.
    """
    try:
        terminal_width = shutil.get_terminal_size().columns
    except Exception:  # Use 80 as a reasonable fallback
        terminal_width = 80

    # Determine the number of lines the text wrapped to based on the width
    total_lines = max(math.ceil(len(text) / terminal_width), 1)

    # For each line, move the cursor up one line and clear the line
    for _ in range(total_lines):
        print(f"{Ansi.MOVE_CURSOR_UP}{Ansi.CLEAR_LINE}", end='')
