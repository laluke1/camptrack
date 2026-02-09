from camptrack.database.connection import get_db_connection
from camptrack.utils.terminal import clear_screen
from camptrack.coordinator.data import get_camp_data, get_notifications
from camptrack.coordinator.helper import set_daily_payment_rate, top_up_food_stock, change_notification_status, days_left, nofification_generator
from camptrack.coordinator.UI import print_header, print_centered_table, TERMINAL_WIDTH, print_centered_text
from camptrack.utils.pagination import get_page_data, format_paginated_table, display_pagination_menu, process_pagination_command, TERMINAL_WIDTH,get_table_width, center_string

import pandas as pd
import time
import datetime
"""
Implementation of the coordinator dashboard.
"""

###################################### MAIN DASHBOARD FUNCTION ######################################
def coordinator_dash() -> None:
    """
    Display the coordinator dashboard.
    """
    conn = get_db_connection()
    try:
        current_page = 1
        page_size =5
        while True:
            #getting data
            camp_data = get_camp_data(conn)
            nofification_generator()    # scan db for notifications to load on dashboard
            notifications_data = get_notifications(conn)    # get all notifications from db
            unread_notifications = [n for n in notifications_data if n['is_read'] == 0]

            # Camp summary & pagination
            paged_camps, num_pages = get_page_data(camp_data, current_page, page_size)

            table_data = []
            for camp in paged_camps:
                select_key = f"[{camp['id']}]"
                table_data.append([
                    select_key,
                    camp['name'],
                    camp['camp_type'].replace('_', ' ').title(),
                    f"{camp['start_date']} to {camp['end_date']}",
                    camp['leader_name'] or 'Unassigned'
                ])
            df_camps = pd.DataFrame(table_data, columns=["Select", "Camp Name", "Type", "Dates", "Leader"])
            dynamic_width = get_table_width(df_camps)

            #display header
            clear_screen()

            header_str = (
                f'\n{"═" * dynamic_width}\n'
                f'{center_string("CAMP SUMMARY DASHBOARD")}\n'
                f'{"═" * dynamic_width}\n'
            )
            print(center_string(header_str))

            # Notification messages
            if not unread_notifications:
                notification_text ="  You have no new notifications.\n"
            elif len(unread_notifications) == 1:
                notification_text = f"  You have {len(unread_notifications)} new notification. Press [V] to view\n"
            elif len(unread_notifications) > 1:
                notification_text =f"  You have {len(unread_notifications)} new notifications. Press [V] to view\n"

            print(center_string(notification_text, dynamic_width))

            #camp table
            table_str = format_paginated_table(
                df_camps,
                current_page,
                num_pages,
                total_items=len(camp_data),
            )
            print(table_str)

            display_pagination_menu(target_width = dynamic_width)

            #user input
            if camp_data and unread_notifications:
                prompt = "\nPress [V] to view your notifications, select a camp to view, navigate pages, \n" \
                "or [Q] to return to main menu: "
            elif camp_data:
                prompt = "\nSelect a camp to view, navigate pages, or press [Q] to return to main menu: "
            else:
                print('\nNo camps active at the moment, no new notifications.\n Press Q to return to main menu.\n')
                prompt = "\nPress [Q] to return to main menu: "

            option = input(prompt).strip()

            if option.upper() == 'Q':
                return

            if not option:
                continue

            if option.upper() == 'V':
                if unread_notifications:
                    notifications_view(conn)
                else:
                    print("No notifications to view.")
                continue
            new_page, is_nav = process_pagination_command(option, current_page, num_pages)
            if is_nav:
                current_page = new_page
                continue

            # Check Camp Selection
            if option.isdigit() and int(option) in [c['id'] for c in camp_data]:
                show_camp_details(int(option))

                continue

            if not is_nav and option.upper() != 'V':
                print("Invalid option or page command.")
                time.sleep(1)
    finally:
        conn.close()



def show_camp_details(camp_id: int) -> None:
    """
    Display detailed information for a chosen, specific camp.
    """
    conn = get_db_connection()

    try:
        while True:
            clear_screen()
            camp_data = get_camp_data(conn)
            camp = next(camp for camp in camp_data if camp['id'] == camp_id)
            today = datetime.date.today()

            print_header(f"CAMP DETAILS: {camp['name'].upper()}")
            details_data = [
                ["Camp Name", camp['name']],
                ["Camp Type", camp['camp_type'].replace("_", " ").capitalize()],
                ["Camp Start Date", camp['start_date']],
                ["Camp End Date", camp['end_date']],
                ["Leader",camp['leader_name'] or 'Unassigned'],
                ["Daily Payment Rate", f"£{round(camp['leader_daily_payment_rate'], 2)}"],
                ["Current Food Stock Level",f"{camp['approved_daily_food_stock']} units"],
                ["Number of Campers", camp['n_campers']],
                ["Daily Food per Camper", f"{camp['daily_food_per_camper']} units"],
            ]
            df_details = pd.DataFrame(details_data, columns=["Field", "Value"])
            print_centered_table(df_details, headers=["Field", "Value"], tablefmt="rounded_outline")
            print("\n")

            if camp['end_date'] < today.isoformat():
                input("This camp has ended. Press Enter to return to the dashboard...")
                return

            #action menu
            menu_data = [
                ["[A]", "Set Daily Payment Rate"],
                ["[B]", "Top up Food Stock"],
                ["[Q]", "Return to Dashboard"]
            ]
            df_menu = pd.DataFrame(menu_data, columns=["Option", "Action"])
            print_centered_table(df_menu, tablefmt="simple")
            option = input("Select an option: ")
            if option.upper() == 'A':
                while True:
                    try:
                        new_rate = float(input("Enter new daily payment rate: £"))
                        if new_rate < 0:
                            print("Please enter a non-negative value for the payment rate.")
                            continue
                        break
                    except ValueError:
                        print("Invalid input. Please enter a valid number for the payment rate.")
                set_daily_payment_rate(camp_id, new_rate)
                print(f"Daily payment rate for {camp['name']} updated to £{round(new_rate, 2)}")
                time.sleep(1.5)
                continue
            elif option.upper() == 'B':
                while True:
                    try:
                        additional_stock = int(input("Enter additional food stock to add: "))
                        if additional_stock < 0:
                            print("Please enter a non-negative integer for food stock.")
                            continue
                        break
                    except ValueError:
                        print("Invalid input. Please enter a valid integer for food stock.")
                top_up_food_stock(camp_id, additional_stock)
                print(f"Food stock topped up by {additional_stock} units.")
                time.sleep(1.5)
                continue
            elif option.upper() == 'Q':
                print("Returning to dashboard...")
                time.sleep(1.5)
                return
            else:
                print("Invalid option. Please try again.")
                continue
    finally:
        conn.close()


def notifications_view(conn) -> None:
    """
    Display notifications page.
    """
    while True:
        clear_screen()
        print_header("NOTIFICATIONS")


        camp_data = get_camp_data(conn)
        notifications_data = get_notifications(conn)    # get all notifications from db

        unread_notifications = [n for n in notifications_data if n['is_read'] == 0]
        read_notifications = [n for n in notifications_data if n['is_read'] == 1]

        # ------------------------------------- Display Unread Notifications -------------------------------------
        table_data = []

        for n in unread_notifications:
            table_data.append([
                f"[{n['id']}]",
                next(camp['name'] for camp in camp_data if camp['id'] == n['camp_id']),
                n['type'].replace('_', ' ').title(),
                n['created_at']
            ])

        df_notifs = pd.DataFrame(table_data, columns=["Select", "Camp", "Issue", "Date Created"])
        print_centered_table(df_notifs, tablefmt="fancy_grid")
        print("\n")

        if not unread_notifications:
            print_centered_text("No unread notifications to display.\n")

        print_centered_text("Press [Q] to go back\n")


        notification_option = input("\nWhat notification would you like to act on? Press [R] to see 'Read' notifications. ").strip()

        if notification_option.upper() == 'Q':
                return
        if not notification_option:
            # Empty input -> show the menu again
            continue



        # --------------------------------- Read Notifications ---------------------------------
        if notification_option.upper() == 'R':
            # Show read notifications
            clear_screen()
            print_header("READ NOTIFICATIONS")

            if not read_notifications:
                print_centered_text("No read notifications to display.\n")
            else:
                table_data = []
                for n in read_notifications:
                    table_data.append([
                        f"[{n['camp_id']}]",
                        next(camp['name'] for camp in camp_data if camp['id'] == n['camp_id']),
                        n['type'].replace('_', ' ').title(),
                        n['created_at']
                    ])

                df_read_notifs = pd.DataFrame(table_data, columns=["Select", "Camp", "Issue","Date Created"])
                print_centered_table(df_read_notifs, tablefmt="fancy_grid")
                print("\n")

            input("Press Enter to return to unread notifications...")
            continue
        # -------------------------------- Act on Notification ---------------------------------
        if notification_option.isdigit() and int(notification_option) in [n['id'] for n in unread_notifications]:
                notification_id = int(notification_option)
                notification_camp_id = [n['camp_id'] for n in unread_notifications if n['id'] == notification_id][0]   #check: this should be of type int
                camp = [camp for camp in camp_data if camp['id'] == notification_camp_id][0]


                # Action depends on type of notification
                type_food = [n for n in unread_notifications if n['id'] == notification_id and n['type'] == 'not_enough_food']
                type_money = [n for n in unread_notifications if n['id'] == notification_id and n['type'] == 'low_daily_payment_rate']


                days_remaining = days_left(notification_camp_id) # TODO: check over this line and the next
                reccomended_food_top_up = (camp['daily_food_per_camper'] * camp['n_campers'] * days_remaining) - camp['approved_daily_food_stock'] if type_food else 0


                if type_food:
                    while True:
                        top_up_option = input('Would you like to top up now? [y/n] \n')

                        if not top_up_option.isalpha() or top_up_option.upper() not in ['Y', 'N']:
                            print('Please enter Y or N')
                            time.sleep(1)
                            clear_screen()
                            continue

                        if top_up_option.upper() == 'N':
                            return

                        if top_up_option.upper() == 'Y':
                            clear_screen()
                            print('Press [Q] to go back.')
                            print_header('Top Up Food Stock')
                            while True:
                                    try:
                                        details_data = [
                                            ["Current Food Stock", camp['approved_daily_food_stock']],
                                            ["Number of Campers", camp['n_campers']],
                                            ["Food Needed Per Day", camp['daily_food_per_camper'] * camp['n_campers']],
                                            ["Days Remaining", days_remaining],
                                            ["Recommended Top-Up", reccomended_food_top_up],
                                        ]

                                        df_details = pd.DataFrame(details_data, columns=["Field", "Value"])
                                        print_centered_table(df_details, headers=[camp['name'], ""], tablefmt="rounded_outline")
                                        print("\n")
                                        message = [n['message'] for n in unread_notifications if n['id'] == notification_id][0]
                                        print(f"Message: {message}")

                                        top_up_option = input('\nEnter additional food stock to add: ')

                                        if top_up_option.upper() == 'Q':
                                            return
                                        if not top_up_option:
                                            continue
                                        if int(top_up_option) < 0:
                                            print("Please enter a non-negative integer for food stock.")
                                            continue
                                        if int(top_up_option) + camp['approved_daily_food_stock'] < camp['daily_food_per_camper'] * camp['n_campers'] * days_remaining:
                                            print(f"That will not be enough to last the remaining days. Please top up at least {reccomended_food_top_up} units.")
                                            continue
                                        break
                                    except ValueError:
                                        print('Invalid Input. Please enter a valid integer')

                            top_up_food_stock(notification_camp_id, int(top_up_option))   # top up food stock             TODO: these are not working?
                            change_notification_status(notification_id, 1)           # mark notification as read

                            print(f"Food stock topped up by {top_up_option} units. Stock levels are now {camp['approved_daily_food_stock'] + int(top_up_option)} units.")
                            time.sleep(2)
                            break



                elif type_money:
                    while True:
                        set_rate_option = input('Would you like to set a new rate now? [y/n] ')

                        if not set_rate_option.isalpha() or set_rate_option.upper() not in ['Y', 'N']:
                            print('Please enter Y or N')
                            continue

                        if set_rate_option.upper() == 'N':
                            return

                        if set_rate_option.upper() == 'Y':
                            clear_screen()
                            print('Press [Q] to go back.')
                            print_header('Set New Daily Payment Rate')
                            while True:
                                    try:
                                        details_data = [
                                            ["Current Daily Payment Rate", f"£{camp['leader_daily_payment_rate']}"],
                                            ["Number of Campers", camp['n_campers']],
                                            ["Days Remaining", days_remaining],
                                            ["Recommended Daily Rate", f"£{round(20 * camp['n_campers'], 2)}"],
                                        ]

                                        df_details = pd.DataFrame(details_data, columns=["Field", "Value"])
                                        print_centered_table(df_details, headers=[camp['name'], ""], tablefmt="rounded_outline")
                                        print("\n")

                                        rate_option = input('Enter new daily payment rate:£')

                                        if rate_option.upper() == 'Q':
                                            return
                                        if not rate_option:
                                            continue
                                        if float(rate_option) < 0:
                                            print("Please enter a non-negative amount for daily payment rate. ")
                                            continue
                                        break
                                    except ValueError:
                                        print('Invalid Input. Please enter a valid value')

                        print(f"Daily payment rate for {camp['name']} updated to £{float(rate_option)}")
                        set_daily_payment_rate(notification_camp_id, float(rate_option))
                        change_notification_status(notification_id, 1)
                        time.sleep(2)
                        break

        else:
            print('Please select a valid option. ')




