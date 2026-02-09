"""
Authentication for CampTrack.
"""

import getpass
import time

from camptrack.database import User
from camptrack.ui import show_header
from camptrack.utils.terminal import clear_screen
from typing import Optional


def login() -> tuple[Optional[User], User.AuthResult]:
    """
    Prompt the user for their username and password.

    Return a `User` object if the credentials are valid and the account is
    not disabled. Otherwise, return `None`.
    """
    print('=== Login ===')
    print('Enter your credentials...\n')

    username = input('Username: ').strip()
    password = getpass.getpass('Password: ')

    user, auth_result = User.authenticate(username, password)

    clear_screen()
    show_header()

    if auth_result == User.AuthResult.SUCCESS:
        print(f'Welcome, {user.username}. ', end='')
        print(f'You are logged in as {user.get_role_with_article()}.\n')
        return user, auth_result
    elif auth_result == User.AuthResult.DISABLED:
        print('Login failed. Your account is disabled.')
    else:
        print('Login failed. Invalid username or password.')

    return None, auth_result


def logout(user: User) -> None:
    clear_screen()
    show_header()
    print('Logging out...')
    time.sleep(0.75)
    print(f'Goodbye, {user.username}!\n')
    time.sleep(0.5)
