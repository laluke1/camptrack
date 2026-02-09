"""
CLI for CampTrack Development Utilities.
"""

import sys
from camptrack.database.connection import get_db_path, init_db


def db_path() -> None:
    path = get_db_path()
    print(f'SQLite database path: {path}')


def delete_db() -> bool:
    """
    Return `True` if deleting the database succeeds, or if it does not exist.
    Otherwise, return `False`.
    """
    path = get_db_path()
    if path.exists():
        try:
            path.unlink()
            print(f'Database ({path}) deletion succeeded')
            return True
        except Exception as e:
            print(f'Database ({path}) deletion failed: {e}')
            return False
    else:
        print(f'Database ({path}) does not exist')
        return True


def reset_db() -> bool:
    """
    Delete the database and reinitialize it to its default state (e.g. default
    users).

    Return `True` if the database was successfully reset. Otherwise, return
    `False`.
    """
    if delete_db():
        try:
            init_db()
            print(
                f'Database ({get_db_path()}) was reset to its default state'
            )
            return True
        except Exception as e:
            print(
                f'Database ({get_db_path()}) failed to reinitialize: {e}'
            )
            return False
    return False


def help_message() -> None:
    print('Usage: camptrack-dev <command>')
    print('Commands:')
    print('    delete    - Delete the database')
    print('    reset     - Delete then reset the database to its default state'
          ' (e.g. default users)')
    print('    path      - Get the path to the SQLite database')


def main() -> None:
    if len(sys.argv) < 2:
        help_message()
        sys.exit(1)

    commands = {
        'delete': delete_db,
        'reset': reset_db,
        'path': db_path,
        'help': help_message,
    }

    command = sys.argv[1].lower()
    if command in commands:
        commands[command]()
    else:
        print(f'Unknown argument: {command}')
        print(f'Run "camptrack-dev help"')
        sys.exit(1)


if __name__ == '__main__':
    main()
