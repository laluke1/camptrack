import math
import pandas as pd
from tabulate import tabulate
from typing import Any, List, Tuple, Union


TERMINAL_WIDTH = 80
DEFAULT_PAGE_SIZE = 5

def get_page_data(data: List[Any], page_number: int, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[Any], int]:
    """
    Slices the data list based on the current page number and page size.
    Returns the sliced data and the total number of pages.
    """
    if not data:
        return [], 0

    num_pages = math.ceil(len(data) / page_size)
    # Ensure page number is within valid bounds
    current_page = max(1, min(page_number, num_pages))
    
    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    
    return data[start_idx:end_idx], num_pages

def center_string(s: str, width: int = TERMINAL_WIDTH) -> str:
    """Centers a multiline string within a specific width."""
    lines = s.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    margin = (width - max_len) // 2
    centered_lines = [f'{" " * margin}{line}' for line in lines]
    return '\n'.join(centered_lines)

def get_table_width(df: pd.DataFrame, headers = 'keys', tablefmt = 'fancy_grid') -> int:
    """
    Calculates the width of a given Dataframe
    """
    if df.empty:
        return TERMINAL_WIDTH
    table_str = tabulate(df, showindex=False, headers=headers, tablefmt=tablefmt)
    lines = table_str.split('\n')
    width =  max(len(line) for line in lines) 
    return width if width >TERMINAL_WIDTH else TERMINAL_WIDTH

def format_paginated_table(
    df: pd.DataFrame, 
    page_number: int, 
    num_pages: int, 
    total_items: int, 
    headers: Union[str, List[str]] = 'keys',
    tablefmt: str = 'fancy_grid'
) -> str:
    """
    Formats a dataframe, with a dynamically generated header.
    """

    #Generate the Table string
    table_str = tabulate(
        df, 
        showindex=False, 
        headers=headers, 
        tablefmt=tablefmt, 
        stralign='left'
    )

    lines = table_str.split('\n')
    table_width = max(len(line) for line in lines) if lines else TERMINAL_WIDTH
    
    #table header
    result = []
    
    page_info = f"Page {page_number}/{num_pages} | Showing {len(df)} items (Total: {total_items})"

    result.append('═' * max(table_width,TERMINAL_WIDTH))
    result.append(center_string(page_info))
    result.append('═' *  max(table_width,TERMINAL_WIDTH))
    result.append('') 

    #table body
    result.append(center_string(table_str))
   
    return '\n'.join(result)

def display_pagination_menu(target_width: int = TERMINAL_WIDTH) -> None:
    """
    Prints the standardised navigation menu.
    """
    commands = [
        [f'[P] Previous', f'[N] Next'],
        [f'[F] First', f'[L] Last'],
        [f'[G #] Go to page', '']
    ]
    menu_str = tabulate(
        pd.DataFrame(commands), 
        showindex=False, 
        tablefmt='plain', 
        colalign=('left', 'left')
    )

    menu_lines = menu_str.split('\n')
    menu_width = max(len(line) for line in menu_lines)
    final_width = max(target_width, menu_width)
    
    separator = '─' * final_width

    print(center_string('\n' + separator))
    print(center_string(menu_str))
    print(center_string(separator))

def process_pagination_command(
    command: str, 
    current_page: int, 
    num_pages: int
) -> Tuple[int, bool]:
    """
    Processes standard pagination commands (P, N, F, L, G).
    
    Returns:
        (new_page_number, is_pagination_command)
        
    If is_pagination_command is True, the caller should refresh the page.
    If False, the caller should handle the input as a custom command (e.g. selection).
    """
    cmd = command.lower().strip()
    
    if cmd == 'p' and current_page > 1:
        return current_page - 1, True
    elif cmd == 'n' and current_page < num_pages:
        return current_page + 1, True
    elif cmd == 'f':
        return 1, True
    elif cmd == 'l':
        return num_pages, True
    elif cmd.startswith('g'):
        try:
            val = int(cmd[1:])
            if 1 <= val <= num_pages:
                return val, True
            else:
                print(f"Page number must be between 1 and {num_pages}")
                input("Press Enter to continue...")
                return current_page, True
        except ValueError:
            pass
    return current_page, False