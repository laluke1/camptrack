from __future__ import annotations

from typing import Dict,Optional
import pandas as pd

from camptrack.visualisations.data.data import fetch_visualisation_data
from camptrack.visualisations.charts.charts import plot_camp_dashboard
from camptrack.types.cursor import Cursor
from camptrack.utils.terminal import clear_screen
from camptrack.utils.pagination import get_page_data, format_paginated_table, display_pagination_menu, process_pagination_command, TERMINAL_WIDTH,get_table_width, center_string
import time


# -----------------------------------------
# Visualisation menu
# -----------------------------------------
def camp_visualisations_menu(cursor: Cursor) -> None:
    while True:
        clear_screen()

        camp_id = show_camp_selection_menu(cursor)

        if camp_id is None:
            print("Exiting visualisations module.")
            return

        data = fetch_visualisation_data(camp_id, cursor)

        plot_camp_dashboard(
            data["gdf_locations"],
            data["df_attendance"],
            data["df_food"],
            data["df_activities"],
            data["total_campers"],
            data["leaders"],
            camp_id
        )


# -----------------------------------------
# Menu generator
# -----------------------------------------
def show_camp_selection_menu(cursor: Cursor) -> Optional[int]:
    """
    Display camp list plus 'All Camps Summary' at the top.
    Returns a mapping from menu numbers to camp IDs:
      - "1" → 0 (all camps)
      - "N" → camp_id
      - exit option → None
    """
    rows = cursor.execute(
        "SELECT id, name FROM camps ORDER BY id ASC"
    ).fetchall()

    menu_mapping: Dict[str, Optional[int]] = {}
    table_data = [] 
    
    # All Camps Summary option
    menu_mapping["1"] = 0   # 0 means “all camps”
    table_data.append(["1", "All Camps Summary"])

    #iterating through to build the list, not printing inside the loop
    for idx, (camp_id, name) in enumerate(rows, start=2):
        menu_mapping[str(idx)] = int(camp_id)
        table_data.append([f"{idx}", name])

    # Final exit option
    exit_option = len(rows) + 2
    menu_mapping[str(exit_option)] = None

    #pagination
    current_page = 1
    page_size = 5

    while True:
        clear_screen()
        page_data, num_pages = get_page_data(table_data, current_page, page_size)
        
        df_menu = pd.DataFrame(page_data, columns=["Option", "Action"])

        dynamic_width = get_table_width(
            df_menu, 
            headers=["Option", "Action"], 
            tablefmt='fancy_grid'
        )
        
        header_str = (
                f'\n{"═" * dynamic_width}\n'
                f'{center_string("VISUALISATION MODULE OPTIONS")}\n'
                f'{"═" * dynamic_width}\n'
            )
        print(center_string(header_str))

        # Format and Print Table
        print(format_paginated_table(
            df_menu, 
            current_page, 
            num_pages, 
            total_items=len(table_data),
            headers=["Option", "Action"],
            tablefmt='fancy_grid'
        ))

        display_pagination_menu(target_width=dynamic_width)

        option = input("\nNavigate pages, select camp, or press [Q] to return to main menu:  ").strip()

        
        # Check Navigation (P, N, F, L, G, Q)
        if option.upper() == 'Q':
            option = str(exit_option)
            #returning now as otherwise q will bring up the camp that is mapped to q
            return menu_mapping[option]

        new_page, is_nav = process_pagination_command(option, current_page, num_pages)

        if is_nav:
            current_page = new_page
            continue

        # Check Selection
        if option in menu_mapping:
            return menu_mapping[option]
        else:
            print("Invalid selection. Please try again.")
            time.sleep(0.7)
