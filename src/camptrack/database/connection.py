import sqlite3
from pathlib import Path
from contextlib import contextmanager
from camptrack.utils.security import password_hash
from typing import Any, Generator
from importlib.resources import files

def get_schema() -> str:
    """
    Return the packaged SQL schema for CampTrack's SQLite database.
    """
    schema_file = files('camptrack.database') / 'schema.sql'
    with schema_file.open('r', encoding='utf-8') as f:
        return f.read()


def get_db_path() -> Path:
    """
    Get the path to the database file.

    The application maintains persistence by storing its database in the
    .camptrack directory in the user's home directory, a common practice for
    CLI applications.
    """
    dir = Path.home() / '.camptrack'
    # If the directory does not exist, create it. Otherwise, do nothing
    dir.mkdir(exist_ok=True)
    return dir / 'camptrack.db'


def get_db_connection(
    enable_wal: bool = False,
    **kwargs: Any
) -> sqlite3.Connection:
    """
    Get a database connection.
    """
    conn: sqlite3.Connection = sqlite3.connect(str(get_db_path()), **kwargs)
    # Make queries return `Row` objects instead of tuples
    conn.row_factory = sqlite3.Row
    # If requested, enable WAL mode, which is useful for concurrent access
    if enable_wal:
        conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """
    Initialize the database with tables and default data (if not already
    initialized). Raises an exception if database initialization fails.
    """
    conn = get_db_connection()
    try:
        # On success, conn.commit() called. If an exception occurs,
        # conn.rollback() is called and the exception is still raised.
        with conn:
            cursor = conn.cursor()

            # Create tables if they do not exist
            schema = get_schema()
            cursor.executescript(schema)

            # If users were not yet added, add them
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role) VALUES
                    (?, ?, ?), (?, ?, ?), (?, ?, ?), (?, ?, ?), (?, ?, ?)
                """, (
                    'admin', password_hash(''), 'admin',
                    'coordinator', password_hash(''), 'coordinator',
                    'leader1', password_hash(''), 'leader',
                    'leader2', password_hash(''), 'leader',
                    'leader3', password_hash(''), 'leader'
                ))

                # TODO(ed): do we need this?
                from camptrack.database.db_utils import seed_demo_data
                seed_demo_data(cursor)
    finally:
        # Connection object still needs to be closed manually. The connection
        # context manager does not close it.
        conn.close()


# Generalization of the pattern used in init_db()
@contextmanager
def get_db_cursor(
    enable_wal: bool = False,
    **kwargs: Any
) -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager that connects to the database, yields a database cursor on
    enter, commits any statements on exit, and ensures the
    connection is always closed.

    Example:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM users')
    """
    conn = get_db_connection(enable_wal=enable_wal, **kwargs)
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
