from camptrack.database.models import Camp
from camptrack.database.models import Camper
import csv   
from camptrack.utils.terminal import clear_screen
from camptrack.database.camp_status import get_camp_statuses, CampStatus
from camptrack.coordinator.UI import print_header, print_centered_table, TERMINAL_WIDTH
from camptrack.utils.pagination import get_table_width, center_string
import pandas as pd

#========== SELECT A CAMP TO SUPERVISE ================
## Check for conflicts with selected camp ##
def validate_camp_choice(leader_id, selected_camp):
    assigned_camps = Camp.get_assigned_camps(leader_id)

    for camp in assigned_camps:
        if (selected_camp.start_date <= camp.end_date and camp.start_date <= selected_camp.end_date):
            print("\nDate conflict detected!")
            print(f"You are already supervising: {camp.name} ({camp.start_date} -> {camp.end_date})")
            print(f"which overlaps with {selected_camp.name} ({selected_camp.start_date} -> {selected_camp.end_date})")
            return False
        
    return True 

## Flow for choosing a camp to supervise ##
def select_camp_to_supervise(leader_id):
    while True:
        clear_screen()
        unassigned = Camp.get_unassigned()

        if not unassigned:
            print("Sorry there are no available camps at the moment.")
            input("Press enter to return to menu: ")
            return None
        
        camp_data = []
        for index, camp in enumerate(unassigned, start=1):
            date_range = f"{camp.start_date} -> {camp.end_date}"
            camp_data.append([
                f"[{index}]",
                f"{camp.name} ({camp.location})",
                camp.type,
                camp.capacity,
                date_range
            ])

        df_camps = pd.DataFrame(
            camp_data, 
            columns=["Option", "Camp Name", "Type", "Capacity", "Dates"]
        )
        dynamic_width = get_table_width(df_camps)
        header_str = (
                    f'\n{"═" * max(TERMINAL_WIDTH, dynamic_width)}\n'
                    f'{center_string("AVAILABLE CAMPS TO SUPERVISE")}\n'
                    f'{"═" * max(TERMINAL_WIDTH, dynamic_width)}\n'
                )
        print(center_string(header_str))
        print_centered_table(df_camps)

        while True:
            choice = input("Select a camp by number (or type Q to cancel): ").strip().upper()

            if choice == "Q":
                print("\nReturning to leader menu...")
                return None
            
            # Validate numeric input
            if not choice.isdigit() or not (1<= int(choice) <= len(unassigned)):
                print("Invalid choice. Please try again.")
                continue

            break
        
        selected_camp = unassigned[int(choice) - 1]

        # Check for conflicts
        if validate_camp_choice(leader_id, selected_camp):
            print(f"\nNo conflicts! You can supervise {selected_camp.name}.")
            input("Press enter to return to leader menu")
            return selected_camp
        
        while True:
            retry = input("\nWould you like to select a different camp? (y/n): ").strip().lower()
            if retry == "n":
                input("Press enter to return to leader menu")
                return None
            elif retry == "y":
                break
            print("Invalid choice. Please enter 'y' or 'n")


#============ ASSIGN CAMPERS TO CAMP =================
## Bulk assign campers ##
def import_campers_from_csv(camp):
    # Check capacity limit
    occupied = camp.get_current_occupancy()
    available = camp.capacity - occupied

    if available <= 0 :
        print("\nThis camp is already full. Cannot import more campers.")
        while True:
            user_input = input("Would you like to select another camp? (y/n): ").strip().lower()
            if user_input == "n":
                print("\nReturning to leader menu...")
                return False
            elif user_input == "y":
                return True
            print("Invalid choice. Please enter 'y' or 'n'")
                

    clear_screen()
    print(f"\n--- Bulk assigning campers to {camp.name}. ---\n")

    # Ask for csv file and validate
    while True:
        path = input("Please enter the path to the csv file: ").strip()
        try:
            with open(path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                required = {"first_name", "last_name", "date_of_birth"}

                # Check if CSV is empty or missing a header row -> fieldnames will be None
                if reader.fieldnames is None:
                    print("\nInvalid CSV format.")
                    print("The CSV file appears to be empty or missing a header row.")
                    print("Required headers: first_name, last_name, date_of_birth")
                    print("Please try again.")
                    continue 

                # Check if anything is missing and inform the user
                missing = required - set(reader.fieldnames)

                if missing:
                    print("\nInvalid CSV format.")
                    print("The following required fields are missing from the CSV: ")
                    for field in missing:
                        print(f"    - {field}")
                    print("\nYour CSV must contain all of these: first_name, last_name, date_of_birth")
                    print("Please try again.")
                    continue
                
                campers = []
                skipped = {
                    "missing_fields":0,
                    "already_assigned":0
                }

                for row in reader:
                    # To skip blank rows 
                    if not row or any(v is None for v in row.values()):
                        skipped["missing_fields"] += 1
                        continue

                    first = row.get("first_name", "").strip()
                    last = row.get("last_name","").strip() 
                    dob = row.get("date_of_birth","").strip()

                    # Check if missing essential fields
                    if not first or not last or not dob:
                        skipped["missing_fields"] += 1
                        continue

                    name = f"{first} {last}"

                    # Camper already exists globally. To prevent from having campers join two overlapping camps.
                    if Camper.camper_exists_globally(name,dob):
                        skipped["already_assigned"] += 1
                        continue

                    campers.append((name, dob))
                break

        except FileNotFoundError:
            print("File not found. Please check the path again.")
            continue

    # Inform the user of any skipped campers
    total_skipped = skipped["missing_fields"] + skipped["already_assigned"]
    if total_skipped > 0:
        print(f"\n{total_skipped} campers were skipped while processing the file:")
        
        if skipped["missing_fields"] > 0:
            print(f" - {skipped['missing_fields']} are missing required fields")

        if skipped["already_assigned"] > 0:
            print(f" - {skipped['already_assigned']} are already assigned to another camp")
    else:
        print("\nNo campers were skipped while processing the file.")

    print(f"\nAvailable campers contained in the CSV: {len(campers)}") # Only shows campers who are available to be imported
    print(f"Camp capacity: {camp.capacity}")
    print(f"Currently occupied: {occupied}")
    

    if not campers:
        print("\nThere are no campers avaialable to be added to this camp.")
        print("\nReturning to leader menu...")
        return False
    
    max_import = min(len(campers), available)
    # Ask user how many campers to import
    while True:
        amount = input(f"\nHow many campers would you like to import? (1 to {max_import}): ").strip()

        if not amount.isdigit():
            print("Invalid number. Please enter a number between 1 and {max_import}.")
            continue

        amount = int(amount)

        if 1 <= amount <= max_import:
            break

        print(f"Number must be between 1 and {max_import}. Please try again.")


    # Import only the chosen number 
    Camper.bulk_import(camp.id, campers[:amount])

    print(f"\nSuccessfully imported {amount} campers into {camp.name}!")
    print("\nReturning to leader menu...")
    return False



## Display camps leader is assigned to ##
def show_assigned_camps(leader_id):
    assigned_camps = Camp.get_assigned_camps(leader_id)
    if not assigned_camps:
        print("You don't have any camps assigned to you at the moment.")
        return None
    
    camp_ids = [camp.id for camp in assigned_camps]
    statuses = get_camp_statuses(camp_ids)

    valid_camps = [camp for camp in assigned_camps if statuses[camp.id] not in {CampStatus.COMPLETED, CampStatus.CANCELLED}]

    if not valid_camps:
        print("You don't have any active camps assigned to you at the moment.")
        return None

    camp_data = []
    for index, camp in enumerate(valid_camps, start=1):
        occupancy = camp.get_current_occupancy()
        
        # Format strings for cleaner table display
        capacity_display = f"{camp.capacity} (Occ: {occupancy})"
        date_range = f"{camp.start_date} -> {camp.end_date}"

        camp_data.append([
            f"[{index}]",
            f"{camp.name} ({camp.location})",
            camp.type,
            capacity_display,
            camp.daily_food_per_camper,
            date_range
        ])

    df_my_camps = pd.DataFrame(
        camp_data,
        columns=["Option", "Camp Name", "Type", "Capacity", "Food/Day", "Dates"]
    )
    dynamic_width = get_table_width(df_my_camps)
    header_str = (
                f'\n{"═" * dynamic_width}\n'
                f'{center_string("CAMP SUMMARY DASHBOARD")}\n'
                f'{"═" * dynamic_width}\n'
            )
    print(center_string(header_str))
    print_centered_table(df_my_camps)

    while True:
        choice = input("Select a camp by number (or type Q to return): ").strip().upper()

        if choice == "Q":
            print("\nReturning to leader menu...")
            return None
        
        if not choice.isdigit() or not (1<= int(choice) <= len(valid_camps)):
            print("Invalid choice. Please try again.")
            continue

        chosen_camp = valid_camps[int(choice)-1]

        return chosen_camp
    

#============= SET DAILY FOOD STOCK ===============
## Set daily food stock per camper ## 
def set_food_for_camp(camp):
    clear_screen()
    print_header(f"Setting food units for {camp.name}")
    print(f"Current food units per camper per day: {camp.daily_food_per_camper}")

    while True:
        units = input("\nEnter food units required per camper per day (e.g. 2): ").strip()

        if not units.isdigit():
            print("Invalid number. Please try again.")
            continue

        units = int(units)
        break

    camp.update_daily_food_per_camper(units)
    print(f"\nSuccessfully set daily food stock per camper to {units} for {camp.name}!")
    input("Press Enter to return to leader menu: ")
    return