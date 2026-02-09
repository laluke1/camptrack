import pandas as pd
from tabulate import tabulate

from camptrack.coordinator.camp_management import create_camp_process
from camptrack.utils.terminal import clear_screen
from camptrack.visualisations.camp_visualisations import camp_visualisations_menu
from camptrack.database.connection import get_db_cursor
from camptrack.coordinator.UI import print_header, print_centered_table, TERMINAL_WIDTH
from camptrack.coordinator.coord import coordinator_dash


def present_coord_options(coord_id):

    while True:
        clear_screen()

        print_header('COORDINATOR INTERFACE')

        #MENU options table
        menu_data = [
        ["[1]", "Create New Camp"],
        ["[2]", "View Dashboard"],
        ["[3]", "View Camp Visualisations"],
        ["[4]", "Return to Main Menu"]
        ]

        df_menu = pd.DataFrame(menu_data, columns=["Option", "Action"])
        print_centered_table(df_menu)
            
        try:
            user_input = input(f"\n{' ' * ((TERMINAL_WIDTH // 2) -6)}Your input: ").strip()
            
            if not user_input.isdigit():
                print("Please enter a valid number.")
                continue

            user_input = int(user_input)
            
            if user_input == 1:
                create_camp_process(coord_id)
                input("Return to Coordinator Menu [Any key]: ")
            elif user_input == 2:
                coordinator_dash()
            elif user_input == 3:
                print("Entering visualisations module...")
                with get_db_cursor() as cursor:
                    camp_visualisations_menu(cursor)
            elif user_input == 4:
                print("Logging out...")
                return
            else:
                print("Invalid operation.")
        except ValueError:
            print("Please enter a valid opertation. e.g. '1'")
            continue
