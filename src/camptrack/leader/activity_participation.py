import sqlite3
from camptrack.database.connection import get_db_cursor
from camptrack.utils import session
from camptrack.coordinator.UI import print_header, print_centered_table, TERMINAL_WIDTH   
from camptrack.utils.terminal import clear_screen
from camptrack.utils.pagination import get_table_width, center_string
import pandas as pd

def add_activity_participation() -> None:
    """Display messages in command line for adding activity participation"""
    clear_screen()
    print_header("ACTIVITY PARTICIPATION LOG")
    print("\nYou are now adding activity participation for activities.")

    # Fetch & display all activities
    activities_data = fetch_activities()

    if not activities_data:
        print("No activities available for logging.")
        input("Press enter to continue: ")
        return None

    print("\nAVAILABLE ACTIVITIES:")
    display_activities(activities_data)
    try:
        while True:
            available_activity_ids = set(activity['id'] for activity in activities_data)
            cmd = input("Please choose an activity ID to log participation for: ").strip()

            if cmd == "q" or cmd == "Q":
                print("\n\n🚫 Participation logging cancelled. Returning to menu...")
                break

            if not cmd.isdigit() or int(cmd) not in available_activity_ids:
                print("Invalid activity chosen. Please try again.")
                continue

            # Find selected activity from id
            selected_activity = None
            for activity in activities_data:
                if activity['id'] == int(cmd):
                    selected_activity = activity

            if selected_activity:
                print(f"You are now adding participation for {selected_activity['activity_name']} from {selected_activity['camp_name']} on {selected_activity['activity_date']}.")
                print("Please indicate 'Y / N ' for each camper's participation in this activity.")

                # Fetch campers from chosen activity
                campers = fetch_activity_campers(selected_activity['id'])

                # Mark participation for each camper
                mark_participation(selected_activity['id'], campers)
                input("\nPress Enter to return to leader interface.")
                break

    except KeyboardInterrupt:
        print("\n\n🚫 Participation logging cancelled. Returning to menu...")
        return None



def fetch_activities() -> list[sqlite3.Row]:
    """Fetches all activities logged by current scout leader"""

    curr_user = session.get_user()

    with get_db_cursor() as cursor:
        cursor.execute(
                """
                SELECT a.id, a.activity_date, a.activity_name, c.name as camp_name
                FROM activities a
                LEFT JOIN camps c ON a.camp_id = c.id
                WHERE c.leader_id = ?
                """, (curr_user.id,)
            )
        activities = cursor.fetchall()

    return activities

def display_activities(activities_data) -> None:
    """Prints the activities data in a custom CLI table using + and -."""
    NAME_WIDTH = 24
    CAMP_NAME_WIDTH = 15

    rows = []
    if activities_data:
        for activity in activities_data:
            act_name = activity['activity_name'][:NAME_WIDTH].strip()
            camp_name = activity['camp_name'][:CAMP_NAME_WIDTH].strip()

            rows.append([
                activity['id'],
                activity['activity_date'],
                act_name,
                camp_name
            ])

    df = pd.DataFrame(
        rows, 
        columns=["ID", "Activity Date", "Activity Name", "Camp Name"]
    )
    clear_screen()
    dynamic_width = get_table_width(df)
    header_str = (
                f'\n{"═" * max(TERMINAL_WIDTH, dynamic_width)}\n'
                f'{center_string("ACTIVITY PARTICIPATION LOG")}\n'
                f'{"═" * max(TERMINAL_WIDTH, dynamic_width)}\n'
            )
    print(center_string(header_str))
    print("\nYou are now adding activity participation for activities.")
    print_centered_table(df)


def fetch_activity_campers(activity_id: int) -> list[sqlite3.Row]:
    """Fetches all participants for a given activity_id"""

    with get_db_cursor() as cursor:
        cursor.execute(
                """
                SELECT c.name, c.id
                FROM campers c
                INNER JOIN activities a ON a.camp_id = c.camp_id
                WHERE a.id = ?
                """, (activity_id,)
            )
        campers = cursor.fetchall()

        return campers

def mark_participation(activity_id: int, campers: list[sqlite3.Row]) -> None:
    """Loops through given campers list to allow marking of participation in given activity"""

    participated_ids = set() # To store id of campers marked "Y"/"y"
    valid_inputs = ["y", "Y", "n", "N"]

    # Get participation for each camper
    for idx, camper in enumerate(campers):
        while True:
            check = input(f"{idx + 1}. {camper['name']}: ").strip()
            if check not in valid_inputs:
                print("Invalid input, please try again.")
                continue
            if check == "Y" or check == "y":
                participated_ids.add(camper['id'])
            break

    # Record participation in DB
    errors = []
    with get_db_cursor() as cursor:
        for camper_id in participated_ids:
            try:
                cursor.execute(
                        """
                        INSERT INTO activity_campers (activity_id, camper_id)
                        VALUES (?, ?)
                        """, (activity_id, camper_id)
                    )
            except sqlite3.IntegrityError:
                camper_name = [c['name'] for c in campers if c['id'] == camper_id][0]
                errors.append(f"Camper {camper_name} (ID: {camper_id}) already logged for this activity.")
            except Exception as e:
                errors.append(f"Database Error for ID {camper_id}: {e}")

    if not errors:
        print(f"\n✅ Participation successfully logged for Activity {activity_id}!")
    else:
        print(f"\n⚠️ Participation logged with {len(errors)} issues for Activity {activity_id}:")
        for error in errors:
            print(f"   - {error}")
