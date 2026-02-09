
import pandas as pd
from tabulate import tabulate

TERMINAL_WIDTH = 80

def print_header(title: str) -> None:
    """
    Prints a double-lined header centered in teh terminal.
    """

    print(f'\n{"═" * TERMINAL_WIDTH}')
    print(f' {title.upper()} '.center(TERMINAL_WIDTH))
    print(f'{"═" * TERMINAL_WIDTH}\n')

def print_centered_table(df: pd.DataFrame, headers='keys', tablefmt='fancy_grid') -> None:
    """
    Formats a Pandas DataFrame uusing tabulate and prints it centere in the terminal.

    Args:
        df (pd.DataFrame): The data to display.
        headers (str to list): 'keys' to use coolumn names, or a list of custom header.
        tablefmt (str): TThe tabulate syle 
    """

    if df.empty:
        print("No data available.".center(TERMINAL_WIDTH))
        return

    table_str = tabulate(df, showindex=False, headers=headers, tablefmt=tablefmt)

    lines = table_str.split('\n')
    max_len = max(len(line) for line in lines)
    margin = max(0, (TERMINAL_WIDTH - max_len) // 2)

    for line in lines:
        print(f"{' ' * margin}{line}")

def print_centered_text(text: str) -> None:
    """
    Prints a simple string centered in tteh terminal.
    """
    print(text.center(TERMINAL_WIDTH))

def get_centered_input_prompt() -> str:
    """
    Returns a srting of spaces to center an input prompt visually 
    (approximate, based on half width).
    """
    return ' ' * ((TERMINAL_WIDTH // 2) - 10)