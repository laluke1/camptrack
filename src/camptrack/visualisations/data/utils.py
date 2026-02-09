from __future__ import annotations

from typing import Optional
import pandas as pd


def compute_activity_ratio(
    df_activities: Optional[pd.DataFrame],
    total_campers: int
) -> pd.DataFrame:
    """
    Add a participation ratio column to the activities DataFrame.
    Handles empty/missing data safely.
    """

    # If empty or None → return an empty structured DataFrame
    if df_activities is None or df_activities.empty:
        return pd.DataFrame(
            columns=["activity", "participants", "ratio"]
        )

    df = df_activities.copy()

    # Ensure numeric participants column exists
    if "participants" not in df.columns:
        df["participants"] = 0

    # Compute participation ratio
    if total_campers == 0:
        df["ratio"] = 0
    else:
        df["ratio"] = (
            df["participants"] / total_campers * 100
        ).round(1)

    return df
