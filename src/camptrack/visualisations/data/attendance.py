from __future__ import annotations

import pandas as pd
from datetime import date
from typing import List, Optional, Tuple, Any, Protocol
from camptrack.types.cursor import Cursor


# -----------------------------------------
# Public Wrapper
# -----------------------------------------
def fetch_camp_attendance(cursor: Cursor, camp_id: int) -> pd.DataFrame:
    """
    Wrapper: fetch a single camp or summary depending on camp_id.
    """
    if camp_id > 0:
        return fetch_single_camp_attendance(cursor, camp_id)
    return fetch_all_camps_attendance_summary(cursor)


# -----------------------------------------
# Single Camp Attendance
# -----------------------------------------
def fetch_single_camp_attendance(
    cursor: Cursor,
    camp_id: int
) -> pd.DataFrame:
    """
    Fetch attendance records for a single camp.
    Returns DataFrame with columns: ["camper_id", "date", "status"]
    """

    rows = cursor.execute(
        """
        SELECT camper_id, date, status
        FROM attendance_records
        WHERE camp_id = ?
        """,
        (camp_id,),
    ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["camper_id", "date", "status"])

    # rows: List[Tuple[int, str, str]]
    df = pd.DataFrame(rows, columns=["camper_id", "date", "status"])
    df["date"] = pd.to_datetime(df["date"])
    return df


# -----------------------------------------
# All Camps Attendance Summary
# -----------------------------------------
def fetch_all_camps_attendance_summary(cursor: Cursor) -> pd.DataFrame:
    """
    Fetch today's attendance summary for all ongoing camps.
    Returns DataFrame with columns:
      ["camp_name", "present", "absent", "pending"]
    """

    today_str = date.today().isoformat()

    # Find ongoing camps
    rows = cursor.execute(
        """
        SELECT id, name
        FROM camps
        WHERE end_date >= ?
        """,
        (today_str,),
    ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["camp_name", "present", "absent", "pending"])

    data: List[List[Any]] = []

    for camp_id_val, camp_name in rows:
        counts = cursor.execute(
            """
            SELECT status, COUNT(*)
            FROM attendance_records
            WHERE camp_id = ? AND date = ?
            GROUP BY status
            """,
            (camp_id_val, today_str),
        ).fetchall()

        # Initialize expected keys with 0
        count_dict = {"present": 0, "absent": 0, "pending": 0}

        for status, cnt in counts:
            count_dict[status] = cnt

        data.append([
            camp_name,
            count_dict["present"],
            count_dict["absent"],
            count_dict["pending"],
        ])

    return pd.DataFrame(
        data,
        columns=["camp_name", "present", "absent", "pending"]
    )
