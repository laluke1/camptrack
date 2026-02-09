"""
Terminal utilities.
"""

import os
import sys

def clear_screen() -> None:
    """
    Clear the terminal screen.
    """
    os.system('clear' if os.name != 'nt' else 'cls')

def logout() -> None:
    clear_screen()
    print("Logging out...")
    sys.exit(0)
