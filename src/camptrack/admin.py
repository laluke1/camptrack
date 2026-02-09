"""
Admin Interface for CampTrack
"""
# TODO:
# (a) When there are no more pages to the right or left, instead of writing
# "Invalid command", give a more informative message.

import getpass
import math

import pandas as pd

from camptrack.database import User
from camptrack.utils.terminal import clear_screen
from camptrack.ui import show_header
from tabulate import tabulate  # from pandas[output-formatting] dependency
from typing import Any, Optional


class AdminInterface:
    _TERMINAL_WIDTH = 80

    # Number of items to show per "page" in a listing of users
    _PAGE_SIZE = 5

    def __init__(self, user: User):
        if user.role != 'admin':
            raise ValueError('User must be an admin!')

        self._user = user

    # The only "public" function or attribute of an instance of this class
    def run(self) -> None:
        """
        Main command loop for an admin.
        """
        while True:
            self._show_menu()

            command = input('\n>> Command: ').strip()
            if command == '1':
                self._create_user()                     # [C]reate
            elif command == '2':
                self._list_users()                      # [R]ead
            elif command == '3':
                self._edit_user()                       # [U]pdate
            elif command == '4':
                self._delete_user()                     # [D]elete
            elif command == '5':
                self._toggle_is_disabled()
            elif command == '6':
                clear_screen()
                show_header()
                print('Logging out...\n')
                break
            else:
                self._show_error_prompt_enter(
                    'Invalid command. Please try again.'
                )

    def _show_menu(self) -> None:
        """
        Print the admin menu.
        """
        clear_screen()
        show_header()

        # Admin menu
        columns = ['Command', 'Action']
        df = pd.DataFrame([
            ['1', 'Create user'],
            ['2', 'List users'],
            ['3', 'Edit user'],
            ['4', 'Delete user'],
            ['5', 'Enable/Disable user'],
            ['6', 'Back to Main Menu']
        ],
            columns=columns
        )

        # Print menu in tabular format, centered in _TERMINAL_WIDTH field
        print(f'\n{"═" * self._TERMINAL_WIDTH}')
        print(' ADMIN INTERFACE '.center(self._TERMINAL_WIDTH))
        print(f'{"═" * self._TERMINAL_WIDTH}\n')

        table = tabulate(
            df,  # type: ignore[arg-type]
            showindex=False, headers=columns, tablefmt='fancy_grid'
        )
        self._print_centered(table)

    def _show_message_prompt_enter(self, message: str) -> None:
        """
        Show a message and prompt the user to press Enter to continue.
        """
        print(f"{message}")
        input("Press Enter to continue...")

    def _show_error_prompt_enter(self, message: str) -> None:
        self._show_message_prompt_enter(f'Error: {message}')

    def _show_success_prompt_enter(self, message: str) -> None:
        self._show_message_prompt_enter(f'Success: {message}')

    def _center_string(self, s: str, width: Optional[int] = None) -> str:
        if width is None:
            width = self._TERMINAL_WIDTH

        lines = s.split('\n')
        max_len = max(len(line) for line in lines)
        margin = (width - max_len) // 2
        centered_lines = [f'{" " * margin}{line}' for line in lines]
        return '\n'.join(centered_lines)

    def _print_centered(self, s: str, width: Optional[int] = None) -> None:
        """
        Print a string centered within a field of given `width`.
        """
        print(self._center_string(s, width))

    def _format_users_table(
        self,
        users: list[User],
        num_pages: int,
        page_number: int,
        search_query: str = ''
    ) -> str:
        """
        Return a string representing a formatted table showing a list of
        `users`.

        The remaining arguments are metadata encoding the number of pages
        the `search_query` used to filter all users in the database yielded,
        and the `page_number` the current list of users represents within
        the result set of that query.
        """
        if not users:
            return 'No users.'

        # Create pandas DataFrame
        df_data = []
        for user in users:
            df_data.append({
                'ID': str(user.id),
                'Username': user.username,
                'Role': user.get_role(),
                'Status': self._get_user_status(user)
            })
        df = pd.DataFrame(df_data)

        # Format the DataFrame for pretty-printing
        table = tabulate(
            df,  # type: ignore[arg-type]
            showindex=False,
            headers='keys',
            tablefmt='fancy_grid',
            stralign='left'
        )

        result = []

        ## (a) Construct header

        # Show if results are for all users or for a specific search query
        if search_query:
            results_for = f'Results for: "{search_query}"'
        else:
            results_for= 'Results for: all users'
        # Show current page number of results and total number of pages
        page_numbers = (
            f"Page {page_number}/{num_pages} | Showing {len(users)} users"
        )

        result.append('═' * self._TERMINAL_WIDTH)
        result.append(results_for.center(self._TERMINAL_WIDTH))
        result.append('─' * self._TERMINAL_WIDTH)
        result.append(page_numbers.center(self._TERMINAL_WIDTH))
        result.append('═' * self._TERMINAL_WIDTH)
        result.append('')  # For newline

        ## (b) Center the table
        centered_table = self._center_string(table)
        result.append(centered_table)

        return '\n'.join(result)

    def _show_user_stats(self, users: list[User]) -> None:
        """
        Print basic statistics describing users.
        """
        print(f'\n{"─" * self._TERMINAL_WIDTH}')
        print(' STATISTICS '.center(self._TERMINAL_WIDTH))
        print('─' * self._TERMINAL_WIDTH)
        stats = {
            'Total': len(users),
            'Enabled': sum(1 for u in users if not u.is_disabled),
            'Disabled': sum(1 for u in users if u.is_disabled),
            'Admins': sum(1 for u in users if u.role == 'admin'),
            'Coordinators': sum(1 for u in users if u.role == 'coordinator'),
            'Leaders': sum(1 for u in users if u.role == 'leader')
        }
        self._print_centered(
            tabulate(
                pd.DataFrame([stats]),  # type: ignore[arg-type]
                showindex=False,
                headers='keys',
                tablefmt='simple',
                numalign='center'
            )
        )

    def _search_users(self, query: str) -> list[User]:
        """
        Return a list of users filtered by username and/or role.
        """
        query = query.lower()
        result = []
        for user in User.get_all():
            # Very basic search algorithm, but still very useful
            if (
                query in user.username.lower() or
                query in user.get_role().lower()
            ):
                result.append(user)
        return result

    def _show_list_menu(self, page_number: int, num_pages: int) -> None:
        """
        Show the list-users view's menu for easy navigation.
        """
        print(f"\n{'─' * self._TERMINAL_WIDTH}")

        commands = [
            [f'[P] Previous', f'[N] Next'],
            [f'[F] First', f'[L] Last'],
            [f'[G #] Go to page', f'[S] Search'],
            [f'[C] Clear search', f'[R] Refresh'],
            [f'[B] Back to menu', f'Page {page_number}/{num_pages}']
        ]
        table = tabulate(
            pd.DataFrame(commands),  # type: ignore[arg-type]
            showindex=False,
            tablefmt='plain',
            colalign=('left', 'left')  # Left align columns
        )
        self._print_centered(table)

        print('─' * self._TERMINAL_WIDTH)

    def _create_user(self) -> None:
        """
        Create a new user.
        """
        clear_screen()
        show_header()
        self._print_section_header("CREATE NEW USER")

        # Print the different types of users that can be created
        data = {
            'Role': ['coordinator', 'leader'],
            'Official Title': [
                'Logistics Coordinator', 'Scout Leader'
            ],
            'Description': [
                'Manages camp logistics/resources',
                'Supervises scouts and leads activities'
            ]
        }
        print('\nUser Roles:\n')
        self._print_table(data)

        print('\nEnter their details (blank to cancel):')

        # Prompt for username
        username = input('\n  Username: ').strip()
        if not username:
            self._show_message_prompt_enter('Create User operation cancelled.')
            return

        # Does the user already exist?
        if User.get_by_username(username):
            self._show_error_prompt_enter(f'Username "{username}" exists.')
            return

        # Prompt for type
        role = input('  Type (coordinator/leader): ').strip().lower()
        if role not in ['coordinator', 'leader']:
            self._show_error_prompt_enter('Invalid type.')
            return

        # Prompt for password
        password = getpass.getpass('  Password: ')
        # NOTE: we allow empty passwords here to be consistent with the
        # coursework brief initial users. In a real application, we would not.
        # Prompt for password confirmation
        password_confirmation = getpass.getpass('  Enter password again: ')
        if password != password_confirmation:
            self._show_error_prompt_enter('Nonmatching passwords.')
            return

        try:
            user = User.create(username, password, role)

            # Print user details
            df = pd.DataFrame({
                'Field': ['Username', 'Role', 'Status'],
                'Value': [user.username, user.get_role(), 'Enabled']
            })

            # Print header
            print(f"\n{'─' * 40}")
            print(' User created. '.center(40))
            print('─' * 40)

            # Print table showing user details
            table_lines = tabulate(
                df,  # type: ignore[arg-type]
                showindex=False,
                headers=['Field', 'Value'],
                tablefmt='simple',
            ).split('\n')

            for line in table_lines:
                print(f"  {line}")

            input('\nPress Enter to continue...')

        except Exception:
            # TODO: log the error
            self._show_error_prompt_enter(f'Failed creating user.')

    def _list_users(self) -> None:
        """
        Show a table of all users, with pagination and basic search
        capabilities. A "page" shows at most `self._PAGE_SIZE` users.
        """
        page_number = 1
        search_query = ""
        search_results: list[User] = []

        # List User operation's command loop (an inner command loop)
        while True:
            clear_screen()
            show_header()

            # Get all users or filter only by search query. On the first
            # iteration of this loop, all users will be fetched. If a search
            # command is entered, `users` will represent a filtered subset.
            users = search_results if search_query else User.get_all()

            # Let the user know if there is nothing to show
            if not users:
                print()
                self._print_section_header('USERS')
                print('\nNo users found.\n')
                input('Press Enter to return to the Admin Menu...')
                return

            # Determine number of pages, page number, and users for this page
            num_pages = math.ceil(len(users) / self._PAGE_SIZE)
            page_number = max(1, min(page_number, num_pages))
            start_idx = (page_number - 1) * self._PAGE_SIZE
            end_idx = start_idx + self._PAGE_SIZE
            page_users = users[start_idx : end_idx]

            # Show the table and user statistics
            table = self._format_users_table(
                users=page_users,
                num_pages=num_pages,
                page_number=page_number,
                search_query=search_query
            )
            print(table)
            self._show_user_stats(users)

            ## Command Menu for the List User operation
            print(f"\n{'─' * self._TERMINAL_WIDTH}")
            self._show_list_menu(page_number, num_pages)

            command = input('\n>> Command: ').strip().lower()
            page_number, search_query, search_results, should_continue = \
                self._process_list_command(
                    command, page_number, num_pages, search_query,
                    search_results
                )

            if not should_continue:
                return

    def _process_list_command(
        self,
        command: str,
        page_number: int,
        num_pages: int,
        search_query: str,
        search_results: list[User]
    ) -> tuple[int, str, list[User], bool]:
        """
        Process a command from the list user command loop.

        Returns (new_page_number, new_search_query, new_search_results,
                 should_continue)
        """
        if command == 'p' and page_number > 1:
            # Goto previous page
            return page_number - 1, search_query, search_results, True
        elif command == 'n' and page_number < num_pages:
            # Goto next page
            return page_number + 1, search_query, search_results, True
        elif command == 'f':
            # Goto first page
            return 1, search_query, search_results, True
        elif command == 'l':
            # Goto last page
            return num_pages, search_query, search_results, True
        elif command.startswith('g '):
            # Goto page number
            try:
                input_page_number = int(command[2:])
                if 1 <= input_page_number <= num_pages:
                    return (
                        input_page_number, search_query, search_results, True
                    )
                else:
                    self._show_message_prompt_enter(
                        f"Page number must be between 1 and {num_pages}"
                    )
            except ValueError:
                self._show_message_prompt_enter("Invalid page number")
            return page_number, search_query, search_results, True
        elif command == 's':
            # Search
            query = input('Search (username or role): ').strip()
            if query:
                results = self._search_users(query)
                return 1, query, results, True
            return page_number, "", [], True
        elif command == 'c':
            # Clear search
            return 1, "", [], True
        elif command == 'r':
            # Refresh (in case of database update)
            return page_number, search_query, search_results, True
        elif command == 'b':
            return page_number, search_query, search_results, False
        else:
            self._show_message_prompt_enter("Invalid command")
            return page_number, search_query, search_results, True


    def _edit_user(self) -> None:
        """
        Edit an user's details.
        """
        clear_screen()
        show_header()
        self._print_section_header('EDIT USER')

        user = self._get_user_with_validation('Edit User')
        if not user:
            return

        # Print user details
        print()
        user_details_table = tabulate(
            pd.DataFrame({  # type: ignore[arg-type]
                'Field': ['ID', 'Username', 'Role', 'Status'],
                'Current Value': [
                    user.id,
                    user.username,
                    user.get_role(),
                    self._get_user_status(user)
                ]
            }),
            showindex=False,
            headers='keys',
            tablefmt='rounded_outline',
        )
        self._print_centered(user_details_table)

        # Print menu of possible edit operations
        print()
        options_table = tabulate(
            pd.DataFrame({  # type: ignore[arg-type]
                'Option': ['1', '2', '3', '4'],
                'Action': [
                    'Edit Username',
                    'Change Password',
                    'Change Role',
                    'Cancel'
                ]
            }),
            showindex=False,
            headers='keys',
            tablefmt='simple',
        )
        self._print_centered(options_table)

        command = input('\nEnter command: ').strip()
        if command == '1':  # Change username
            new_username = input('  New username: ').strip()
            if new_username:
                if User.get_by_username(new_username):
                    self._show_error_prompt_enter(
                        f'Username "{new_username}" already exists.'
                    )
                    return
                user.username = new_username
                user.update()
                self._show_success_prompt_enter(
                    f'Username successfully updated to "{new_username}".'
                )
            else:
                self._show_message_prompt_enter('Invalid username.')

        elif command == '2':  # Change password
            # NOTE: we allow empty passwords here to be consistent with the
            # coursework brief initial users. In a real application, we would
            # not.
            new_password = getpass.getpass('  New password: ')
            password_confirmation = getpass.getpass('  Confirm password: ')
            if new_password == password_confirmation:
                user.set_password(new_password)
                user.update()
                self._show_success_prompt_enter(
                    'Password updated successfully.'
                )
            else:
                self._show_error_prompt_enter('Nonmatching passwords.')

        elif command == '3':  # Change user role
            new_type = input(
                '  New role (coordinator/leader): '
            ).strip().lower()
            if new_type in ['coordinator', 'leader'] and new_type != user.role:
                user.role = new_type
                user.update()
                self._show_success_prompt_enter(
                    f'User role successfully updated to {user.get_role()}.'
                )
            else:
                self._show_message_prompt_enter(
                    'The user\'s role was not changed'
                )

        elif command == '4':  # Cancel
            self._show_message_prompt_enter('Edit Operation cancelled.')
        else:
            self._show_error_prompt_enter('Invalid command.')

    def _delete_user(self) -> None:
        """
        Delete a user from the application.
        """
        clear_screen()
        show_header()
        self._print_section_header('DELETE USER')

        user = self._get_user_with_validation('Delete User')
        if not user:
            return

        # Show user details before deleting
        delete_table = tabulate(
            pd.DataFrame({  # type: ignore[arg-type]
                'Field': ['ID', 'Username', 'Role', 'Status'],
                'Value': [
                    user.id,
                    user.username,
                    user.get_role(),
                    self._get_user_status(user)
            ]}),
            showindex=False,
            headers='keys',
            tablefmt='heavy_grid',
        )
        print()
        self._print_centered(delete_table)

        # Confirm deletion
        confirmation = input(
            f'\nEnter "DELETE {user.username}" for confirmation: '
        ).strip()

        if confirmation == f'DELETE {user.username}':
            user.delete()
            self._show_success_prompt_enter(
                f'User "{user.username}" has been successfully deleted.')
        else:
            self._show_message_prompt_enter('Delete User operation cancelled.')

    def _toggle_is_disabled(self) -> None:
        """
        If a user account is disabled, enable it. Otherwise, disable it.
        """
        clear_screen()
        show_header()
        self._print_section_header('DISABLE/ENABLE USER')

        user = self._get_user_with_validation('Toggle Disable/Enable')
        if not user:
            return

        updated_status = 'Enabled' if user.is_disabled else 'Disabled'

        # Show what the change will do to the user
        data = {
            'Field': ['Username', 'Role', 'Current Status', 'New Status'],
            'Value': [
                user.username,
                user.get_role(),
                self._get_user_status(user),
                updated_status,
            ]
        }
        print()
        self._print_table(data)

        # Ask the user for confirmation
        enable_or_disable = 'Enable' if user.is_disabled else 'Disable'
        confirm = input(
            f'\n{enable_or_disable} this user? (y/n): '
        ).strip().lower()
        if confirm == 'y':
            user.is_disabled = not user.is_disabled
            user.update()
            self._show_success_prompt_enter(
                f'User "{user.username}" is now {updated_status}.'
            )
        else:
            self._show_message_prompt_enter(
                'Toggle Disable/Enable Operation cancelled.'
            )

    def _print_section_header(self, title: str) -> None:
        """
        Print a section header with the provided `title`.
        """
        print('═' * self._TERMINAL_WIDTH)
        print(f' {title} '.center(self._TERMINAL_WIDTH))
        print('═' * self._TERMINAL_WIDTH)

    def _get_user_with_validation(self, operation: str) -> Optional[User]:
        # Prompt for user
        username = input('Enter username (blank to cancel): ').strip()
        if not username:
            self._show_message_prompt_enter(
                f'{operation} operation cancelled.'
            )
            return None

        # Get user from database
        user = User.get_by_username(username)
        if not user:
            self._show_error_prompt_enter(f'User "{username}" does not exist.')
            return None

        # Only coordinators or leaders can be modified
        if user.role not in ['coordinator', 'leader']:
            self._show_error_prompt_enter(
                'Only coordinators and leaders can be modified.'
            )
            return None

        return user

    def _create_table(
        self,
        data: dict[str, list[Any]],
        tablefmt: str = 'rounded_outline',
        centered: bool = True,
        **kwargs: Any
    ) -> str:
        """
        Return a formatted table of `data`.
        """
        df = pd.DataFrame(data)
        table = tabulate(
            df,  # type: ignore[arg-type]
            showindex=False,
            headers='keys',
            tablefmt=tablefmt,
            **kwargs
        )
        return self._center_string(table) if centered else table

    def _print_table(
        self,
        data: dict[str, list[Any]],
        tablefmt: str = 'rounded_outline',
        centered: bool = True,
        **kwargs: Any
    ) -> None:
        """
        Print a formatted table of `data`.
        """
        table = self._create_table(data, tablefmt, centered, **kwargs)
        print(table)

    def _get_user_status(self, user: User) -> str:
        return 'Disabled' if user.is_disabled else 'Enabled'
