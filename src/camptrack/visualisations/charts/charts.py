from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, Union, Any
import matplotlib.dates as mdates
from datetime import date

from camptrack.visualisations.geo_support import HAS_GEO, gpd
from camptrack.visualisations.data.utils import compute_activity_ratio

from camptrack.utils.logging_config import get_logger
from camptrack.visualisations.charts.map_plot import plot_camp_locations_auto

from camptrack.visualisations.charts.empty_plot import render_empty
from camptrack.visualisations.charts.tables import plot_activity_table, plot_leaders_table

logger = get_logger(__name__)

# --------------------------------------
# Type alias: DataFrame or GeoDataFrame
# --------------------------------------
GeoDF = Union[pd.DataFrame, "gpd.GeoDataFrame"]


# ============================================================
# Dashboard
# ============================================================
def plot_camp_dashboard(
    gdf_locations: GeoDF,
    df_attendance: pd.DataFrame,
    df_food: pd.DataFrame,
    df_activities: pd.DataFrame,
    total_campers: int,
    df_leaders: pd.DataFrame,
    camp_id: int
) -> None:
    """
    Combine all plots into a 2x4 dashboard.
    """
    df_activities = compute_activity_ratio(df_activities, total_campers)
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))

    # Row 1
    plot_camp_locations_auto(gdf_locations, ax=axes[0, 0])
    plot_camp_attendance(df_attendance, camp_id, ax=axes[0, 1])
    plot_food_stock(df_food, camp_id, ax=axes[0, 2])
    plot_leaders_table(df_leaders, camp_id, ax=axes[0, 3])

    # Row 2
    plot_activity_bar(df_activities, camp_id, ax=axes[1, 0])
    plot_activity_table(df_activities, camp_id, ax=axes[1, 1])
    plot_participation_ratio(df_activities, total_campers, camp_id, ax=axes[1, 2])
    plot_leaders_distribution(df_leaders, ax=axes[1, 3])

    plt.tight_layout()
    plt.show()


# ============================================================
# PLOTS (Bar, Table, Ratio, Attendance, Leaders)
# ============================================================

def plot_activity_bar(
    df: pd.DataFrame,
    camp_id: int,
    ax: Optional[Axes] = None
) -> Optional[Axes]:

    # --- Handle empty data gracefully ---
    if df.empty:
        message = (
            f"No activity data for Camp {camp_id}"
            if camp_id != 0 else "No activity data available"
        )
        return render_empty(ax, message)

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))

    x_pos = range(len(df))
    ax.bar(x_pos, df["participants"], color="skyblue")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df["activity"], rotation=45, ha="right")
    ax.set_ylabel("Participants")

    title = (
        f"Activity Engagement - Camp {camp_id}"
        if camp_id != 0
        else "Activity Engagement - All Camps"
    )
    ax.set_title(title)

    plt.tight_layout()
    return ax


def plot_camp_attendance(
    df: pd.DataFrame,
    camp_id: int,
    ax: Optional[Axes] = None
) -> Optional[Axes]:
    if df.empty:
        message = (
            f"No attendance records for Camp {camp_id}"
            if camp_id != 0 else "No attendance data available"
        )
        return render_empty(ax, message)

    if camp_id > 0:
        df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        counts = df.groupby(["date_str", "status"]).size().unstack(fill_value=0)

        for status in ["present", "absent"]:
            if status not in counts:
                counts[status] = 0

        if ax is None:
            fig, ax = plt.subplots(figsize=(9, 5))

        counts[["present", "absent"]].plot(
            kind="bar",
            stacked=True,
            ax=ax,
            color=["#4ECDC4", "#FF6B6B"]
        )

        ax.set_xlabel("Date")
        ax.set_ylabel("Number of campers")
        ax.set_title(f"Camp {camp_id} Attendance vs Absence")
        ax.set_xticklabels(
            ax.get_xticklabels(),
            rotation=45,
            ha="right",
            fontsize=9
        )
        ax.grid(axis="y", linestyle="--", alpha=0.7)

    else:
        if ax is None:
            fig, ax = plt.subplots(figsize=(9, 5))

        df.plot(
            kind="bar",
            stacked=True,
            ax=ax,
            x="camp_name",
            y=["present", "absent", "pending"],
            color=["#4ECDC4", "#FF6B6B", "#FFD166"]
        )

        ax.set_xlabel("Camp")
        ax.set_ylabel("Number of campers")
        ax.set_title("Camper Distribution Across Ongoing Camps (Today)")
        ax.set_xticklabels(df["camp_name"], rotation=45, ha="right", fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

    if ax.figure:
        plt.tight_layout()

    return ax


def plot_food_stock(
    df: pd.DataFrame,
    camp_id: int = 0,
    ax: Optional[Axes] = None
) -> Optional[Axes]:

    if df.empty:
        message = (
            f"No food stock history for Camp {camp_id}"
            if camp_id > 0 else "No food stock data available"
        )
        return render_empty(ax, message)

    # Ensure the x-axis data is DATE ONLY (no time component)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date   # strip to pure date

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))

    # ===== Camp-specific timeseries =====
    if camp_id > 0:
        ax.plot(df["date"], df["stock_available"], marker="o")

        # Format x-axis as DATE ONLY
        ax.xaxis.set_major_locator(mdates.DayLocator())             # one tick per day
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))  # no hours ever

        ax.set_xlabel("Date")
        ax.set_ylabel("Stock Available")
        ax.set_title(f"Camp {camp_id} Food Stock Over Time")
        ax.grid(True)
        ax.tick_params(axis="x", rotation=45)

    # ===== Summary bar chart =====
    else:
        ax.bar(df["camp_name"], df["stock_available"], color="skyblue")
        ax.set_xlabel("Camp")
        ax.set_ylabel("Current Stock Available")
        ax.set_title("Current Food Stock Across Ongoing Camps")
        ax.tick_params(axis="x", rotation=45)

        # Add labels above bars
        for i, v in enumerate(df["stock_available"]):
            ax.text(i, v + 0.5, str(v), ha="center", va="bottom")

    plt.tight_layout()
    return ax


def plot_leaders_distribution(
    df: pd.DataFrame,
    ax: Optional[Axes] = None
) -> Optional[Axes]:
    if df.empty:
        return render_empty(ax, "No leader distribution data available")

    counts = df.groupby("camp_name").size().sort_values(ascending=True)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, max(4, 0.5 * len(counts))))

    counts.plot(kind="barh", ax=ax, color="skyblue")

    ax.set_xlabel("Number of Leaders")
    ax.set_ylabel("Camp")
    ax.set_title("Leader Allocation Across Camps")

    for i, v in enumerate(counts):
        ax.text(v + 0.1, i, str(v), va="center")

    plt.tight_layout()

    return ax


def plot_participation_ratio(
    df: pd.DataFrame,
    total_campers: int,
    camp_id: int = 0,
    ax: Optional[Axes] = None
) -> Optional[Axes]:
    if df.empty:
        return render_empty(ax, "No participation data available")

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))

    df["participation_ratio"] = (
        (df["participants"] / total_campers * 100).round(1)
    )

    ax.bar(range(len(df)), df["participation_ratio"], color="lightgreen")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["activity"], rotation=45, ha="right")
    ax.set_xlabel("Activity")
    ax.set_ylabel("% of Campers")

    title = (
        "Participation Ratio (%)"
        if camp_id != 0
        else "Participation Ratio (%) - All Camps"
    )
    ax.set_title(title)

    return ax