from camptrack import __version__
from camptrack.chat import MessagingInterface
from camptrack.database import init_db, User
from camptrack.leader.leader_menu import show_leader_menu
from camptrack.utils import session
from camptrack.utils.terminal import clear_screen
from camptrack.ui import show_header
from camptrack.auth import login, logout
from camptrack.admin import AdminInterface
from camptrack.coordinator.coordinator_options import present_coord_options
from camptrack.utils.logging_config import init_logging, get_logger
from tabulate import tabulate

import pandas as pd

import argparse
import logging
import sys
import time


logger = get_logger(__name__)

MENU_WIDTH = 80


def show_main_menu(user: User) -> str:
    clear_screen()
    show_header()

    logger.debug(f'Show main menu to user {user.username} (role: {user.role})')

    print('═' * MENU_WIDTH)
    print(f' Main Menu - {user.username} ({user.get_role()}) '
          .center(MENU_WIDTH))
    print('═' * MENU_WIDTH)
    print()

    menu = []
    match user.role:
        case 'admin':
            menu.append(
                ('1', 'Admin Interface', 'Manage users')
            )
        case 'coordinator':
            menu.append(
                ('1', 'Coordinator Interface', 'Manage camp logistics')
            )
        case 'leader':
            menu.append(
                ('1', 'Leader Interface', 'Manage scouts and camp activities')
            )
        case _:
            logger.error(f'Unrecognized user type: {user.role}')
            print('Error: unrecognized user type')
            sys.exit(1)

    menu.extend((
        ('2', 'Messages', 'Direct chat messaging system'),
        ('3', 'Logout', 'Exit CampTrack')
    ))

    df = pd.DataFrame(menu, columns=['Command', 'Function', 'Description'])
    table = tabulate(
        df,
        showindex=False,
        headers='keys',
        tablefmt='fancy_grid'
    )

    for line in table.split('\n'):
        print(line.center(MENU_WIDTH))
    print()

    return input('Enter command (1-3): ').strip()


def run_user_session(user: User) -> None:
    logger.info(f'Starting user session for {user.username}')

    while True:
        command = show_main_menu(user)
        try:
            match command:
                case '1':
                    logger.debug(
                        f'User ({user.username}) accessing their role '
                        f'interface'
                    )

                    if user.role == 'admin':
                        AdminInterface(user).run()
                    elif user.role == 'coordinator':
                        present_coord_options(coord_id=user.id)
                    elif user.role == 'leader':
                        show_leader_menu(leader_id=user.id)
                    else:
                        logger.error(f'Unrecognized user type: {user.role}')

                        print('Error: unrecognized user type')
                        sys.exit(1)
                case '2':
                    logger.debug(f'User ({user.username}) accessing messages')

                    MessagingInterface(user).run()
                case '3':
                    logger.info(f'User {user.username} logging out')

                    logout(user)
                    break
                case _:
                    logger.warning(f'Invalid command entered: {command}')

                    print('Invalid command. Please try again')
                    input('Press Enter to continue...')
        except Exception as e:
            logger.exception(f'Error in user session ({user.username}): {e}')
            print('\nAn error occurred.')
            print('Returning to the main menu...')
            time.sleep(2.5)


def main() -> None:
    # Parse command-line arguments for debugging
    parser = argparse.ArgumentParser(description='CampTrack CLI')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output to console'
    )
    args = parser.parse_args()
    init_logging(
        console_level=logging.DEBUG if args.debug else None,
        file_level=logging.DEBUG
    )

    logger.info('=' * 80)
    logger.info('CampTrack application starting')
    logger.info(f'Version: {__version__}')
    logger.info('=' * 80)

    clear_screen()
    show_header()

    # If not already done, create tables and default data (e.g. users)
    try:
        logger.info('Initializing database...')
        init_db()
        logger.info('Database initialized...')
    except Exception as e:
        logger.critical(f'Failed initializing database: {e}', exc_info=True)
        sys.exit(1)

    # Attempt login
    user = None
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):

        user, auth_result = login()
        if user:
            break

        if auth_result == User.AuthResult.DISABLED:
            sys.exit(1)

        #login failed
        remaining = max_attempts - attempt
        logger.warning('Login - invalid credentials or account is disabled' \
        '\nAttempt %d / %d' % (attempt, max_attempts))
        if remaining > 0:
            print('Invalid credentials. You have %d attempt(s) remaining.' \
            '\nRedirecting to login...'  % (remaining))
            time.sleep(3)
            clear_screen()
            show_header()
        else:
            print('\nMaximum login attempts reached. System closing.')
            sys.exit(1)

    logger.info(f'User {user.username} logged in successfully')
    session.set_user(user)

    try:
        run_user_session(user)
    except KeyboardInterrupt:
        logger.info(f'User {user.username} interrupted session (Ctrl+C)')
        logout(user)
    except Exception as e:
        logger.critical(
            f'Unhandled exception in user session: {e}', exc_info=True
        )
        raise
    finally:
        logger.info('CampTrack is shutting down...')


if __name__ == '__main__':
    main()
