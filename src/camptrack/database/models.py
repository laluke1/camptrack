from dataclasses import dataclass, asdict
from typing import Optional
from .connection import get_db_cursor
from camptrack.utils.security import password_verify, password_hash
from typing import Optional
from datetime import datetime, timezone, date
from enum import Enum
import sqlite3


@dataclass  # See https://docs.python.org/3/library/dataclasses.html
class User:
    id: Optional[int] = None
    username: str = ''
    password_hash: str = ''
    role: str = ''
    is_disabled: bool = False

    # Maps role value stored in database to something more readable
    _ROLE_PUBLIC = {
        'admin': 'Admin',
        'coordinator': 'Logistics Coordinator',
        'leader': 'Scout Leader'
    }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'User':
        return cls(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash'],
            role=row['role'],
            is_disabled=bool(row['is_disabled'])
        )

    class AuthResult(Enum):
        SUCCESS = "success"
        BAD_CREDENTIALS = "bad_credentials"
        DISABLED = "disabled"

    @classmethod
    def authenticate(
        cls,
        username: str,
        password: str
    ) -> tuple[Optional['User'], 'User.AuthResult']:
        """
        Return a tuple of (`User` object or `None`, `AuthResult` enum).
        The first element is a `User` object if the provided credentials
        are valid, and the user is not disabled. Otherwise, it is `None`.
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users
                WHERE username = ?
            """, (username,))
            row = cursor.fetchone()

        if not row:
            # User does not exist
            return None, User.AuthResult.BAD_CREDENTIALS

        if not password_verify(password, row['password_hash']):
            # User exists but wrong password
            return None, User.AuthResult.BAD_CREDENTIALS

        if row['is_disabled']:
            # Account is disabled
            return None, User.AuthResult.DISABLED

        return cls.from_row(row), User.AuthResult.SUCCESS

    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """
        Return a `User` with the provided `username`.
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            )
            row = cursor.fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_id(cls, id: int) -> Optional['User']:
        """
        Return a `User` with the provided `id`.
        """
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
            row = cursor.fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def get_all(cls, is_disabled_only: bool = False) -> list['User']:
        """
        Return a list of all `User`s.

        If `is_disabled_only` is `True`, return only disabled users. Otherwise,
        return all users.
        """
        with get_db_cursor() as cursor:
            if is_disabled_only:
                cursor.execute("""
                    SELECT * FROM users
                    WHERE is_disabled = 1
                    ORDER BY username
                """)
            else:
                cursor.execute("SELECT * FROM users ORDER BY username")
            rows = cursor.fetchall()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def create(
        cls, username: str, password: str, role: str, is_disabled: bool = False
    ) -> 'User':
        """
        Create a new user in the database.

        Raises `RuntimeError` if the user could not be created, or if the
        user was created but could not be subsequently retrieved.
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, is_disabled)
                VALUES (?, ?, ?, ?)
            """,
                (username, password_hash(password), role, int(is_disabled))
            )
            id = cursor.lastrowid

        if id is None:
            raise RuntimeError(f'Failed to create new user {username}')

        user = cls.get_by_id(id)
        if user is None:
            raise RuntimeError(f'Failed to get new user {username}')

        return user

    def update(self) -> None:
        """
        Update the user in the database.
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET username = ?, password_hash = ?, role = ?, is_disabled = ?
                WHERE id = ?
            """,
                (self.username, self.password_hash, self.role,
                 int(self.is_disabled), self.id)
            )

    def delete(self) -> None:
        """
        Delete the user from the database.
        """
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = ?", (self.id,))

    def set_password(self, password: str) -> None:
        """
        Set the user's password to `password`.

        Does not update the database. Call `self.update()` if you need to.
        """
        self.password_hash = password_hash(password)

    def get_role(self) -> str:
        """
        Return the user's official role title.

        For example, 'Admin', 'Logistics Coordinator', or 'Scout Leader'.
        """
        return self._ROLE_PUBLIC.get(self.role, self.role)

    def get_role_with_article(self) -> str:
        """
        Return the user's official role title prefixed with an article.

        For example, 'an Admin', 'a Logistics Coordinator', or
        'a Scout Leader'.
        """
        VOWELS = 'aeiou'
        role = self._ROLE_PUBLIC[self.role]
        article = 'an' if role[0].lower() in VOWELS else 'a'
        return f'{article} {role}'


@dataclass
class Camp:
    id: Optional[int] = None
    name: str = ''
    coordinator_id: int = None
    leader_id: int = None
    location: str = ''
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    type: str = ''
    approved_daily_food_stock: int = 0
    leader_daily_payment_rate: float=0.0
    capacity: int = 0
    created_at: Optional[date] = None
    daily_food_per_camper: int = 0

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Camp':
        """Retrieve a Camp instance from a database row."""
        return cls(
            id=row['id'],
            name=row['name'],
            coordinator_id=row['coordinator_id'],
            leader_id=row['leader_id'],
            location=row['location'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            type=row['type'],
            approved_daily_food_stock=row['approved_daily_food_stock'],
            leader_daily_payment_rate=float(row['leader_daily_payment_rate']),
            created_at=row['created_at'],
            capacity=row['capacity'],
            daily_food_per_camper=row['daily_food_per_camper'],
        )

    #want save separate, so can ask to confirm if all details are correct
    #potentally ask what specific details need to change before saving

    def save(self) -> None:
        """Save the camp instance to the database.

        If the instance has no ID, a new record is inserted."""

        #if self.id is None, insert new record
        if self.id is None:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO camps (name, coordinator_id, leader_id, location, 
                               latitude, longitude, start_date, end_date, type,
                               approved_daily_food_stock, leader_daily_payment_rate, capacity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (self.name, self.coordinator_id, self.leader_id, self.location, 
                          self.latitude, self.longitude, self.start_date,
                        self.end_date, self.type, self.approved_daily_food_stock, self.leader_daily_payment_rate,
                        self.capacity,))

        #TODO: add else block if self.id is not none i.e. updating an existing row



    def display_details(self):
        """Prints Camps Details in user friendly format."""

        data = asdict(self)

        print("\n======= NEW CAMP DETAILS =======" \
        f"\n[1] Name:                   {data['name']}" \
        f"\n[2] Leader ID:              {data['leader_id'] if data['leader_id'] is not None else 'Unassigned'}" \
        f"\n[3] Location:               {data['location']}" \
        f"\n[4] Start Date:             {data['start_date']}" \
        f"\n[5] End Date:               {data['end_date']}" \
        f"\n[6] Type:                   {data['type']}" \
        f"\n[7] Capacity:               {data['capacity']}" \
        f"\n[8] Initial Food Stock:     {data['approved_daily_food_stock']}" \
        f"\n[9] Leader Daily Rate:      £{data['leader_daily_payment_rate']:.2f}" \
        f"\n=====================================")

    ## ----FOR LEADER FUNCTIONALITIES----
    ## Fetch camps that don't have a leader assigned to them yet
    @classmethod
    def get_unassigned(cls):
        with get_db_cursor() as cursor:
            today = date.today() # to only display camps that are not passed their start date 

            cursor.execute('SELECT * FROM camps WHERE leader_id IS NULL AND start_date>= ?', (today,))
            rows = cursor.fetchall()
        
        camps = []
        for row in  rows:
            camp = cls.from_row(row)
            camps.append(camp)

        return camps
    
    ## Fetch camps that a specific leader is assigned to
    @classmethod
    def get_assigned_camps(cls, leader_id):
        with get_db_cursor() as cursor:
            cursor.execute('SELECT * FROM camps WHERE leader_id = ?', (leader_id,))
            rows = cursor.fetchall()

        camps = []
        for row in rows:
            camp = cls.from_row(row)
            camps.append(camp)

        return camps
    
    ## Update existing camp in DB with the new leader assignment 
    def assign_leader(self, leader_id):
        if self.id is None:
            raise ValueError("Cannot assign leader to a camp with no id")
        
        self.leader_id = leader_id

        with get_db_cursor() as cursor:
            cursor.execute("UPDATE camps SET leader_id = ? WHERE id = ?", (self.leader_id, self.id))
    
    ## Determine what the occupancy of a camp is 
    def get_current_occupancy(self):
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM campers WHERE camp_id=?", (self.id,))
            (count,) = cursor.fetchone()
        
        return count

    ## Leader: Update daily food units required per camper for a camp
    def update_daily_food_per_camper(self, units: int):
        self.daily_food_per_camper = units

        with get_db_cursor() as cursor:
            cursor.execute("UPDATE camps SET daily_food_per_camper = ? WHERE id = ?", (units, self.id))



   
@dataclass
class Camper:
    id: Optional[int] = None
    camp_id: int = None
    name: str = ''
    date_of_birth: str=''
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(
            id = row['id'],
            camp_id = row['camp_id'],
            name = row['name'],
            date_of_birth = row['date_of_birth'],
            created_at = row['created_at']
        )
    
    @classmethod
    def bulk_import(cls, camp_id: int, campers: list[tuple]):
        # campers: list of name, dob
        with get_db_cursor() as cursor:
            cursor.executemany("""
                INSERT OR IGNORE INTO campers (camp_id, name, date_of_birth)
                VALUES (?, ?, ?)
                """, [(camp_id, name, dob) for name, dob in campers])
            

    ### Helper method for importing campers
    # Return true if camper already exists in any other camp, to prevent assigning the same campers in multiple camps
    @classmethod
    def camper_exists_globally(cls, name: str, dob: str) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1 FROM campers WHERE name=? AND date_of_birth=? LIMIT 1", (name, dob))

            return cursor.fetchone() is not None 
        





