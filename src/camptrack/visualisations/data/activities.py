from __future__ import annotations

import pandas as pd
from typing import List, Optional, Tuple, Protocol, Any
from camptrack.types.cursor import Cursor


# -----------------------------------------
# Public API
# -----------------------------------------
def fetch_activity_engagement(cursor: Cursor, camp_id: int) -> pd.DataFrame:
    """
    Wrapper that returns activity engagement for either:
    - A specific camp (camp_id > 0)
    - All camps combined (camp_id == 0)
    """
    if camp_id == 0:
        return fetch_all_camp_activity_engagement(cursor)
    else:
        return fetch_single_camp_activity_engagement(cursor, camp_id)


# -----------------------------------------
# Single camp
# -----------------------------------------
def fetch_single_camp_activity_engagement(
    cursor: Cursor,
    camp_id: int
) -> pd.DataFrame:
    """
    Returns participants per activity for ONE specific camp.
    """

    rows = cursor.execute(
        """
        SELECT a.activity_name, COUNT(ac.camper_id) AS participants
        FROM activities a
        LEFT JOIN activity_campers ac
            ON a.id = ac.activity_id
        WHERE a.camp_id = ?
        GROUP BY a.id, a.activity_name
        ORDER BY a.activity_date ASC;
        """,
        (camp_id,),
    ).fetchall()

    if not rows:
        # Preserve stable schema for callers
        return pd.DataFrame(columns=["activity", "participants"])

    # rows: List[Tuple[str, int]]
    return pd.DataFrame(rows, columns=["activity", "participants"])


# -----------------------------------------
# All camps
# -----------------------------------------
def fetch_all_camp_activity_engagement(cursor: Cursor) -> pd.DataFrame:
    """
    Returns total participants per activity across ALL camps.
    """

    rows = cursor.execute(
        """
        SELECT a.activity_name, COUNT(ac.camper_id) AS participants
        FROM activities a
        LEFT JOIN activity_campers ac
            ON a.id = ac.activity_id
        GROUP BY a.activity_name
        ORDER BY a.activity_name ASC;
        """
    ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["activity", "participants"])

    return pd.DataFrame(rows, columns=["activity", "participants"])



