from datetime import datetime
from camptrack.database.connection import get_db_cursor
from camptrack.utils import session
from camptrack.utils.terminal import clear_screen
from camptrack.coordinator.UI import print_header, print_centered_table, TERMINAL_WIDTH
import pandas as pd

def create_daily_log() -> None:
    """Display messages in command line for creating daily logs"""
    clear_screen()
    print_header("DAILY LOG")
    print("\nYou are now creating a new daily log.")

    # Fetch all current and previous camps
    camps = fetch_camps_for_logs()

    if not camps:
        print("No camps available for logging. Returning to menu...")
        return None

    print("\nAVAILABLE CAMPS:")
    display_camps_table(camps)
    try:

        # Get selection
        while True:
            cmd = input("Please choose a camp to create a log for: ").strip()
            if cmd == "q" or cmd == "Q":
                print("\n\n🚫 Operation cancelled by user. Returning to menu...")
                break

            if not cmd.isdigit() or not 1 <= int(cmd) <= len(camps):
                print("Invalid camp chosen. Please try again")
                continue

            selection_idx = int(cmd)
            selected_camp = camps[selection_idx - 1]

            print(f"\nYou are now creating a log for {selected_camp['name']} [{selected_camp['start_date']} - {selected_camp['end_date']}].")
            try:

                # Fill in details for camp
                log_details = record_daily_log_details()
                # Save log to db
                inserted_id = save_log(selected_camp, log_details)
                print(f"\n✅ Log successfully created! Activity ID: {inserted_id}")
                break
            except Exception as e:
                print(f"\n❌ Log could not be created. Details: {e}")

    except KeyboardInterrupt:
        print("\n\n🚫 Operation cancelled by user. Returning to menu...")
        return None

    return None


def fetch_camps_for_logs():
    """To fetch all past and current camps"""
    curr_user = session.get_user()

    with get_db_cursor() as cursor:
        cursor.execute(
                """
                SELECT id, name, start_date, end_date
                FROM camps
                WHERE start_date <= date('now')
                AND leader_id = ?
                """, (curr_user.id,)
            )
        camps = cursor.fetchall()

    return camps

def display_camps_table(camps_data) -> None:
    """Prints the camp data as pandas table."""
    # """Prints the camp data in a custom CLI table using + and -."""

    rows = []
    for index, camp in enumerate(camps_data, start=1):
        end_date_display = camp['end_date'] if camp['end_date'] else "N/A"

        rows.append([
            index,
            camp['name'],
            camp['start_date'],
            end_date_display
        ])

    df = pd.DataFrame(
        rows, 
        columns=["No.", "Camp Name", "Start Date", "End Date"]
    )
    print_centered_table(df)


def record_daily_log_details() -> dict:
    """To get all user input on daily log details"""
    # TODO: Allow user to quit at any time

    log_details = {}

    # Get and validate activity date
    while True:
        date_input = input("1. Enter activity date (YYYY-MM-DD): ").strip()
        try:
            activity_date_parsed = datetime.strptime(date_input, "%Y-%m-%d").date()
            log_details['activity_date'] = activity_date_parsed
            # TODO: Check if date is within the range of camp dates
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2025-01-30).")

    # Get and validate activity name
    # TODO: Possibly standardise activities to choose from rather than free text
    while True:
        name_input = input("2. Enter activity name: ").strip()
        if name_input:
            log_details['activity_name'] = name_input
            break
        else:
            print("❌ Activity name cannot be empty. Please try again.")

    # Get and validate incident count
    while True:
        count_input = input("3. Enter incident count: ").strip()
        try:
            count = int(count_input)
            log_details['incident_count'] = count
            break
        except ValueError:
            print("❌ Invalid count. Please use a number.")

    # Get and validate notes
    notes_input = input("4. Enter notes (e.g. special achievements): ").strip()
    log_details['notes'] = notes_input # can be null

    # TODO: Add attendance for activity to calculate participation rate

    return log_details

def save_log(selected_camp: dict, log_details: dict) -> bool:
    """
    Save log details to activities table
    """
    with get_db_cursor() as cursor:
        cursor.execute(
                """
                INSERT INTO activities (
                    camp_id, activity_date, activity_name, incident_count, notes
                ) VALUES
                (?, ?, ?, ?, ?)
                """, (selected_camp['id'], log_details['activity_date'], log_details['activity_name'], log_details['incident_count'], log_details['notes'])
            )

        inserted_id = cursor.lastrowid

    return inserted_id
