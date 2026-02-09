from typing import Optional

from camptrack.database.models import User
current_user: Optional[User] = None

def set_user(user):
    global current_user
    current_user = user

def get_user():
    if current_user is None:
        raise Exception("No user logged in.")
    return current_user
