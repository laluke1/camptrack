import time
from camptrack.leader.activity_participation import add_activity_participation
from camptrack.leader.camp_assignment import select_camp_to_supervise
from camptrack.leader.camp_assignment import show_assigned_camps
from camptrack.leader.camp_assignment import import_campers_from_csv
from camptrack.leader.camp_assignment import set_food_for_camp
from camptrack.database.models import Camp
from camptrack.leader.daily_log import create_daily_log
from camptrack.leader.dashboard import show_dashboards
from camptrack.utils.terminal import clear_screen
import pandas as pd
from camptrack.coordinator.UI import print_header, print_centered_table

## Option menu presented when leader logs in
def show_leader_menu(leader_id):
    try:
        while True:
            clear_screen()
            print_header('LEADER INTERFACE')
            menu_data = [
                ["[1]","Select a camp to supervise"],
                ["[2]", "Assign campers to my camps"],
                ["[3]", " Assign/Update food units per camper per day"],
                ["[4]", " Add daily log"],
                ["[5]", " Add activity participation"],
                ["[6]", " View dashboard"],
                ["[Q]", " Return to Main Menu"]
            ]
            df_menu = pd.DataFrame(menu_data, columns=["Option", "Action"])
            print_centered_table(df_menu)

            while True:
                choice = input("Enter your choice: ").strip()
                if choice in ("1", "2", "3", "4", "5", "6", "Q", "q"):
                    break
                print("Invalid choice. Please try again.")

            if choice == "1":
                clear_screen()
                camp = select_camp_to_supervise(leader_id)
                if camp is None:
                    continue
                camp.assign_leader(leader_id)
                print("Successfully assigned!")

            elif choice == "2":
                clear_screen()
                while True:
                    camp = show_assigned_camps(leader_id)
                    if camp is None:
                        break

                    choose_another = import_campers_from_csv(camp)
                    if not choose_another:
                        break # user is done or returned to main menu
                    clear_screen()
                    continue

            elif choice == "3":
                clear_screen()
                camp = show_assigned_camps(leader_id)
                if camp is None:
                    continue
                set_food_for_camp(camp)

            elif choice == "4":
                create_daily_log()
                input("Press Enter to return to leader interface.")
            elif choice == "5":
                add_activity_participation()
            elif choice == "6":
                show_dashboards()

            elif choice == "Q" or choice == "q":
                print("Exiting leader interface...")
                time.sleep(2.5)
                return

    except KeyboardInterrupt:
        print("\nExiting Leader Menu. Goodbye.")
