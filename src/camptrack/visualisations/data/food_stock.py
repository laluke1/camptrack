from __future__ import annotations

import pandas as pd
from datetime import date
from typing import Any, List, Optional, Protocol, Tuple
from camptrack.types.cursor import Cursor


# -----------------------------------------
# Public wrapper
# -----------------------------------------
def fetch_camp_food_stock(cursor: Cursor, camp_id: int = 0) -> pd.DataFrame:
    """
    Wrapper:
      - camp_id > 0 → full history for a single camp
      - camp_id == 0 → summary for all ongoing camps
    """
    if camp_id > 0:
        return fetch_food_stock_single_camp(cursor, camp_id)
    return fetch_food_stock_summary_all_camps(cursor)


# -----------------------------------------
# Single camp food stock history
# -----------------------------------------
def fetch_food_stock_single_camp(
    cursor: Cursor,
    camp_id: int
) -> pd.DataFrame:
    """
    Return full food stock history for a single camp.
    Columns: ["date", "stock_available"]
    """

    rows = cursor.execute(
        """
        SELECT date, stock_available
        FROM food_stock_history
        WHERE camp_id = ?
        ORDER BY date ASC
        """,
        (camp_id,),
    ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["date", "stock_available"])

    df = pd.DataFrame(rows, columns=["date", "stock_available"])
    df["date"] = pd.to_datetime(df["date"])
    return df


# -----------------------------------------
# Snapshot summary for all ongoing camps
# -----------------------------------------
def fetch_food_stock_summary_all_camps(cursor: Cursor) -> pd.DataFrame:
    """
    Return the most recent food stock value for each ongoing camp
    (where end_date >= today).
    Columns: ["camp_id", "camp_name", "stock_available"]
    """

    today_str = date.today().isoformat()

    query = """
        SELECT f.camp_id, c.name AS camp_name, f.stock_available
        FROM food_stock_history f
        JOIN camps c ON f.camp_id = c.id
        WHERE f.date = (
            SELECT MAX(f2.date)
            FROM food_stock_history f2
            WHERE f2.camp_id = f.camp_id
            AND f2.date <= ?
        )
        AND c.end_date >= ?
        ORDER BY f.camp_id;
    """

    rows = cursor.execute(query, (today_str, today_str)).fetchall()

    if not rows:
        return pd.DataFrame(columns=["camp_id", "camp_name", "stock_available"])

    # Ensure rows are tuples for DataFrame consistency
    safe_rows = [tuple(r) for r in rows]

    df = pd.DataFrame(
        safe_rows,
        columns=["camp_id", "camp_name", "stock_available"]
    )
    return df
