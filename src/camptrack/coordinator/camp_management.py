import pandas as pd

from camptrack.database.models import Camp
from camptrack.utils.terminal import clear_screen
from datetime import date, datetime
from camptrack.database.connection import get_db_cursor
from camptrack.coordinator.UI import print_header, print_centered_table, TERMINAL_WIDTH
from camptrack.utils.pagination import get_table_width, center_string

from camptrack.coordinator.utils.location_input import ask_for_location
import asyncio

#---------Helper Functions----------#

#----0: exists in db----#
def exists_in_db(table_name: str, attribute_name: str, attribute_value: str) -> bool:
        """
        Check whether a specific value exists in a given table column.

        Args:
            table_name (str):
                Name of the database table to query.
            attribute_name (str):
                Column name to check for the value.
            attribute_value (str):
                Value too search for in the specified column.

        Returns:
            bool: True if at least on matching row exists, otherwise False.

        Notes:
            - Uses a simple SELECT query annd returns True on the first match.
            - Sae to use for validation such as checking unique camp names, verifiying user IDs, etc.
        """
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {str(attribute_name)} = ?", (attribute_value,))
            for row in cursor: #if there is even one row it will return true
                return True
        return False


#-----1: Camp Name----#
def validated_camp_name()-> str:
    """
    Prompt the user for a camp name and validate it.

    Validation rules:
        - Name cannot be empty.
        - Name must not already exist in the camps table.

    Returns:
        str: A valid, unique camp name.
    """
    while True:
        name = input(">> Enter camp name: ")
        if name.strip() == "":
            print("Camp name cannot be empty. Please try again.")
        elif exists_in_db("camps","name", name):
            print(f"'{name}' is already in use for another camp. Please try again")

        else:
            return name


#-----2: Leader_ID----#

def validated_leader_id() -> int:
    """
    Prompt the user for a leader Id and validate it.

    Validation rules:
        - Empty input returns None (leader unassigned)
        - Must be a positive integer.
        - ID must exist within the 'users' table.

    Returns:
    Optional[int]:  Integar leader ID if  valid, otherwise None.
    """
    while True:
        leader_id = input(">> Enter leader ID (Press enter if unknown): ").strip()
        if leader_id == "":
                return None 
        elif leader_id.isdigit():
            leader_id = int(leader_id)
            if not exists_in_db("users","id", leader_id):
                print(f"'{leader_id}' does not exist in the database. Please try again")
            else:
                return leader_id
        else:
            print("Leader ID must be a valid integer. Please try again.")

#-----3: camp location----#

def validated_camp_location() -> dict:
    return asyncio.run(ask_for_location()) 


#-----4: Camp start date----#
def validated_camp_start_date(created_at_obj) -> date:
    """
    Prompt for and validate the camp start date.

    Validation ruleL
        - cannot be empty
        -Must follow YYYY-MM-DD
        - Cannot be in the past.

    Args:
        created_at_obj (date):
            The current creation date, used to enforce future scheduling.

    Returns:
        date: The valid start date as a datetime.date object
    """
    while True:
        start_date = input(">> Enter camp start date (YYYY-MM-DD): ")
        
        #parsing input into datetime object, validating
        try:
            if start_date.strip() == "":
                print("Camp start date cannot be empty. Please try again.")
                continue
            start_date_object = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError as e:
            print(f"Invalid date format or value. Please use YYYY-MM-DD. Error {e}")
            continue

        #ensuring start_date is in the future by at least one day
        if start_date_object < created_at_obj:
            print("Date cannot be in the past.")
            continue

        return start_date_object

#-----5: Camp end date----#
def validated_camp_end_date(start_date_object) -> date:
    """
    Prompt for and validate the camp end date.

    Validation rule
        - Cannot be empty
        - Must follow YYYY-MM-DD
        - Cannot be earlier than the start date.

    Args:
        start_date_obj (date):
            The already validated camp start date.

    Returns:
        date: The valid start date as a datetime.date object
    """

    while True:
        end_date = input(">> Enter camp end date (YYYY-MM-DD): ")
        if end_date.strip() == "":
            print("Camp end date cannot be empty. Please try again.")
        #parsing input into datetime object, validating
        try:
            end_date_object = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            print(f"Invalid date format or value. Please use DD-MM-YYYY. Error {e}")
            continue

        #ensuring start_date is in the future by at least one day
        if not start_date_object <= end_date_object:
            print("End date cannot be before start date.")
            continue

        return end_date_object

#-----6: Camp Type----#
def validated_camp_type(start_date_object, end_date_object) -> str:
    """
    Prompt for and validate the camp type.

    Valid types:
        - 'day camp'
        - 'overnight'
        - 'expedition'

    Additional rules:
        - Input cannot be empty.
        - Overnight camps require start and end dates to be different.

    Args:
        start_date_object (date): Valdated start date.
        end_date_object: validated end date.

    Returns:
        str: Valid camp type in lowercase.

    """
    while True:
        type = input(">> Enter camp type ('day_camp' / 'overnight' / 'expedition') : ").strip().lower()
        if type == "":
            print("Camp type cannot be empty. Please try again.")
        elif type not in ('day_camp', 'overnight', 'expedition'):
            print("Camp type must be one of the following options: 'day_camp', 'overnight', 'expedition' ")
        elif type == "overnight" and start_date_object == end_date_object:
            print("Overnight camps cannot occur if the start date is the same date as the end date.")
        else:  
            return type

#-----7: Camp Capacity----#
def validated_capacity() -> int:
    """
    Prompt for and validate the camp capacity.

    Valiidation rulesL
        - Must be a valid integer.
        - Must be greaer than zero.

    returns:
        int: The validated camp capacity.
    """
    while True:
        try:
            capacity = input(">> Enter camp capacity: ")
            
            if capacity.isdigit():
                capacity = int(capacity)
                if capacity <= 0:
                    print("Capcity must be greater than 0")
                else:
                    return capacity
            else:
                print("Please provide a valid integer.")
        except ValueError:
            print("Camp capacity must be a valid integer. Please try again.")

#-----8: Daily Food Allowance-----#
def validated_daily_food_allowance() -> int:
    """
    Prompt for and validate the appproved daily food stock.

    Validation rules:
        - Must be a whole, non negative number

    Returns:
        int: The validated approved daily food stock.
    """
    while True:
        approved_daily_food_stock = input(">> Enter approved daily food stock: ")
        try:
            approved_daily_food_stock = int(approved_daily_food_stock)
            if approved_daily_food_stock >= 0:
                return approved_daily_food_stock
            else:
                print("Approved daily food stock cannot be a negative value")
        except ValueError:
            print("Approved daily food stock must be a valid whole number. Please try again."),

#-----9: Leader daily rate----#

def validated_leader_daily_rate() -> float:
    """
    Prompt for and validate the leader's daily payment rate.

    Validation rules:
        - Must be numeric
        - Min £100

    Returns:
        float: The daily rate in quid
    """
    MIN_RATE = 100.00
    while True:
        try:
            leader_daily_payment_rate = float(input(">> Enter leader daily rate: £"))
            if leader_daily_payment_rate >= MIN_RATE:
                return float(leader_daily_payment_rate)
            else:
                print(f"The minimum leader rate is £{MIN_RATE} per day. Please try again.")
        except ValueError:
            print("Leader daily rate must be a valid number. Please try again.")
        except Exception as e:
            print(f"Error: {e}: Please try again")


def create_camp_instance(coord_id: int) -> Camp:
    """
    Prompts user for all required camp details and returns a camp instance.

    Args:
        coord_id (int): The ID of the cuurrently logged-in user (coordinator).

    Returns:
        Camp: A Camp object populated with validate user input.
    """

    #campid auto-incremented by the database
    #test coordinator_id, needs to be set automatically to the user's id
    #coordinator_id = 1234
    created_at_obj= datetime.now().date()
    form_data= {
        "Name": "...",
        "Leader ID": "...",
        "Location": "...",
        "Start Date":"...",
        "End Date": "...",
        "Type": "...",
        "Capacity":"...",
        "Food Stock":"...",
        "Leader Daily Rate":"...",
        }
    
    def show_form_progress(current_step_name):
        clear_screen()

        df = pd.DataFrame(list(form_data.items()), columns=["Field", "Current Input"])
        dynamic_width = get_table_width(df)
        
        header_str = (
            f'\n{"═" * dynamic_width}\n'
            f'{center_string("CAMP SUMMARY DASHBOARD")}\n'
            f'{"═" * dynamic_width}\n'
        )
        print(center_string(header_str))

        print_centered_table(df, tablefmt="rounded_outline")
        print(f"\n[Step: {current_step_name}]")

    show_form_progress("Camp Name")
    name = validated_camp_name()
    form_data["Name"] = name

    show_form_progress("Leader ID")
    leader_id= validated_leader_id()
    form_data["Leader ID"] = leader_id if leader_id is not None else "Unassigned"

    show_form_progress("Location")
    selected_location = validated_camp_location()
    location = selected_location["name"]
    latitude = selected_location["lat"]
    longitude = selected_location["lon"]
    form_data["Location"] = location

    show_form_progress("Start Date")
    start_date = validated_camp_start_date(created_at_obj)
    form_data["Start Date"] = start_date

    show_form_progress("End Date")
    end_date = validated_camp_end_date(start_date)
    form_data["End Date"] = end_date

    show_form_progress("Type")
    camp_type = validated_camp_type(start_date, end_date)
    form_data["Type"] = camp_type

    show_form_progress("Capacity")
    camp_capacity = validated_capacity()
    form_data["Capacity"] = camp_capacity

    show_form_progress("Food Stock")
    camp_food_stock = validated_daily_food_allowance()
    form_data["Food Stock"] = camp_food_stock

    show_form_progress("Leader Daily Rate")
    leader_rate = validated_leader_daily_rate()
    form_data["leader_rate"] = leader_rate 

    coordinator_id = coord_id
    name = name
    leader_id = leader_id
    location = location
    start_date=start_date
    end_date = end_date
    type = camp_type
    capacity =  camp_capacity
    approved_daily_food_stock = camp_food_stock
    leader_daily_payment_rate = leader_rate


    return Camp(
        name=name,
        coordinator_id=coordinator_id,
        leader_id=leader_id,
        location=location,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        type=type,
        approved_daily_food_stock=approved_daily_food_stock,
        leader_daily_payment_rate=leader_daily_payment_rate,
        capacity=capacity,
    )

def create_camp_process(coord_id):
    """
    Man process loop for creating a new camp, including input, confirmation, editing, and saving the data.

    Args:
        coord_id (int): The ID of the currently logged-in user (coordinator).
    """

    while True:
        clear_screen()
        print(f'\n{"═" * TERMINAL_WIDTH}')
        print(' NEW CAMP CREATION '.center(TERMINAL_WIDTH))
        print(f'{"═" * TERMINAL_WIDTH}\n')

        #getting user input & creating camp instance6

        today = date.today()
        new_camp_instance = create_camp_instance(coord_id)

        #inner loop for confirmation and editing
        while True:
            clear_screen()
            print_header('CONFIRM DETAILS')
            data = [
                ["1", "Name", new_camp_instance.name],
                ["2", "LeaderID", new_camp_instance.leader_id or "Unassigned"],
                ["3", "Location", new_camp_instance.location.title()],
                ["4", "Start Date", new_camp_instance.start_date],
                ["5", "End Date", new_camp_instance.end_date],
                ["6", "Type", new_camp_instance.type],
                ["7", "Capacity", new_camp_instance.capacity],
                ["8", "Food Stock", new_camp_instance.approved_daily_food_stock],
                ["9", "Daily Rate", "£"+str(new_camp_instance.leader_daily_payment_rate)],
            ]
            df = pd.DataFrame(data, columns=['Command', 'Field', 'Value'])
            print_centered_table(df, headers=['Command', 'Field', 'Value'], tablefmt="fancy_grid")

            #confirm values
            confirm_input = input("\nAre the details above correct? (y/n): " ).lower().strip()

            if confirm_input in ('y', 'yes'):
                new_camp_instance.save()
                print("\nCamp saved sucessfully.\n")
                return #exits camp_create_process

            elif confirm_input in ('n', 'no'):
                edit_option = input("Edit Menu:\nType 'r' to restart, 'q' to quit, or the line number to edit(e.g. '2'): ").lower().strip()
                if edit_option == "r":
                    print("\n...Restarting Camp Creation...")
                    break #breaks inner loop to restart creation

                #---- Editing Logic ---#
                elif edit_option == "q":
                    #doesn't save data to the database and exits create_camp_process
                    return
                elif edit_option == "1":
                    new_camp_instance.name = validated_camp_name()
                elif edit_option == "2":
                    new_camp_instance.leader_id = validated_leader_id()
                elif edit_option == "3":
                    new_loc_data = validated_camp_location()
                    new_camp_instance.location = new_loc_data["name"]
                    new_camp_instance.latitude = new_loc_data["lat"]
                    new_camp_instance.longitude = new_loc_data["lon"]
                elif edit_option in ("4", "5", "6"):
                    #updating any date, means start, end, and type, all have to be updated as they are dependent on each other
                    print("\nAs you are editing a date or camp type, the start date, end date, and type must all be updated.")
                    start_obj = validated_camp_start_date(today)
                    new_camp_instance.start_date = start_obj

                    end_obj = validated_camp_end_date(start_obj)
                    new_camp_instance.end_date = end_obj

                    new_camp_instance.type = validated_camp_type(start_obj, end_obj)

                elif edit_option == "7":
                    new_camp_instance.capacity = validated_capacity()
                elif edit_option == "8":
                    new_camp_instance.approved_daily_food_stock = validated_daily_food_allowance()
                elif edit_option == "9":
                    new_camp_instance.leader_daily_payment_rate = validated_leader_daily_rate()


                else:
                    print("Invalid input. Please try again.")
            else:
                print("Invalid input.  Please enter 'y'or 'n'.")
