from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, Union, Any

from camptrack.visualisations.geo_support import HAS_GEO, gpd
from camptrack.utils.logging_config import get_logger
from camptrack.visualisations.charts.empty_plot import render_empty

logger = get_logger(__name__)

# --------------------------------------
# Type alias: DataFrame or GeoDataFrame
# --------------------------------------
GeoDF = Union[pd.DataFrame, "gpd.GeoDataFrame"]


def plot_activity_table(
    df: pd.DataFrame,
    camp_id: int,
    ax: Optional[Axes] = None
) -> Optional[Axes]:

    if df.empty:
        message = (
            f"No activity data for Camp {camp_id}"
            if camp_id != 0 else "No activity data available"
        )
        return render_empty(ax, message)

    # --- PREVIEW SETTINGS ---
    MAX_PREVIEW_ROWS = 6
    preview_df = df.head(MAX_PREVIEW_ROWS).copy()

    if len(df) > MAX_PREVIEW_ROWS:
        preview_df.loc[MAX_PREVIEW_ROWS] = [
            "…",
            "…",
            f"{len(df) - MAX_PREVIEW_ROWS} more →"
        ]

    # --- Truncate long activity names ---
    MAX_NAME_LEN = 14
    preview_df["activity"] = preview_df["activity"].apply(
        lambda x: x[:MAX_NAME_LEN] + "…" if isinstance(x, str) and len(x) > MAX_NAME_LEN else x
    )

    if ax is None:
        fig, ax = plt.subplots(figsize=(4, 3))

    # Build table
    table_data = [["Activity", "Participants", "Ratio (%)"]] + \
                 preview_df[["activity", "participants", "ratio"]].values.tolist()

    table = ax.table(cellText=table_data, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.8, 1.6)

    # Cell padding
    for _, cell in table.get_celld().items():
        cell.PAD = 0.35

    ax.set_axis_off()

    title = (
        "Activity (Preview)"
        if camp_id == 0
        else f"Activity (Preview) – Camp {camp_id}"
    )
    ax.set_title(title, pad=8)

    # --- Add hint text ---
    ax.text(
        0.5, -0.15,
        "Double-click to view full activity list",
        ha="center", va="top",
        fontsize=7, color="gray",
        transform=ax.transAxes
    )

    # Attach fullscreen handler
    _attach_fullscreen_activity_table(ax, df, camp_id)

    return ax


def _attach_fullscreen_activity_table(ax: Axes, df: pd.DataFrame, camp_id: int):

    def open_fullscreen(event):
        if event.inaxes is not ax or not event.dblclick:
            return

        # Create fullscreen figure
        fig_full = plt.figure(figsize=(10, min(1 + 0.4 * len(df), 20)))

        try:
            mng = fig_full.canvas.manager
            if hasattr(mng, "window"):
                mng.window.showMaximized()
        except Exception:
            fig_full.set_size_inches(10, min(1 + 0.4 * len(df), 20))

        ax_full = fig_full.add_subplot(1, 1, 1)

        # Full table
        table_data = [["Activity", "Participants", "Ratio (%)"]] + \
                     df[["activity", "participants", "ratio"]].values.tolist()

        table = ax_full.table(cellText=table_data, loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)

        ax_full.set_axis_off()

        title = "All Activities" if camp_id == 0 else f"All Activities – Camp {camp_id}"
        ax_full.set_title(title, pad=12)

        def close_fullscreen(ev):
            if ev.inaxes is ax_full and ev.dblclick:
                plt.close(fig_full)

        fig_full.canvas.mpl_connect("button_press_event", close_fullscreen)
        plt.show()

    ax.figure.canvas.mpl_connect("button_press_event", open_fullscreen)


def plot_leaders_table(
    df: pd.DataFrame,
    camp_id: int,
    ax: Optional[Axes] = None
) -> Optional[Axes]:
    """
    Show a compact preview of the leaders table inside a subplot.
    Double-click opens a fullscreen readable table.
    Shows ONLY camp_id, camp_name, leader_name.
    """

    if df.empty:
        message = (
            f"No leaders found for Camp {camp_id}"
            if camp_id != 0 else "No leader data available"
        )
        return render_empty(ax, message)

    # --- PREVIEW SETTINGS ---
    MAX_PREVIEW_ROWS = 6
    preview_df = df.head(MAX_PREVIEW_ROWS).copy()

    if len(df) > MAX_PREVIEW_ROWS:
        preview_df.loc[MAX_PREVIEW_ROWS] = [
            "…",
            f"{len(df) - MAX_PREVIEW_ROWS} more",
            "…"
        ]

    # Truncate long text
    MAX_NAME_LEN = 15
    preview_df["camp_name"] = preview_df["camp_name"].apply(
        lambda x: x[:MAX_NAME_LEN] + "…" if isinstance(x, str) and len(x) > MAX_NAME_LEN else x
    )
    preview_df["leader_name"] = preview_df["leader_name"].apply(
        lambda x: x[:MAX_NAME_LEN] + "…" if isinstance(x, str) and len(x) > MAX_NAME_LEN else x
    )

    # Create axis
    if ax is None:
        fig, ax = plt.subplots(figsize=(4, 3))

    # Build preview table
    table_data = [["Camp ID", "Camp Name", "Leader"]] + \
                 preview_df[["camp_id", "camp_name", "leader_name"]].values.tolist()

    table = ax.table(cellText=table_data, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.8, 1.6)

    # Padding
    for _, cell in table.get_celld().items():
        cell.PAD = 0.35

    ax.set_axis_off()

    # Hint
    ax.text(
        0.5, -0.15,
        "Double-click to view full leader list",
        ha="center", va="top",
        fontsize=7, color="gray",
        transform=ax.transAxes
    )

    # Title
    title = (
        "Leaders - All Camps"
        if camp_id == 0
        else f"Leaders - Camp {camp_id}"
    )
    ax.set_title(title, pad=8)

    # Enable fullscreen
    _attach_fullscreen_leader_table(ax, df, camp_id)

    return ax


def _attach_fullscreen_leader_table(ax: Axes, df: pd.DataFrame, camp_id: int):
    """
    Double-click to open fullscreen table (camp_id, camp_name, leader_name).
    """
    def open_fullscreen(event):
        if event.inaxes is not ax or not event.dblclick:
            return

        fig_full = plt.figure(figsize=(10, min(1 + 0.4 * len(df), 20)))

        try:
            mng = fig_full.canvas.manager
            if hasattr(mng, "window"):
                mng.window.showMaximized()
        except Exception:
            pass

        ax_full = fig_full.add_subplot(1, 1, 1)

        table_data = [["Camp ID", "Camp Name", "Leader"]] + \
            df[["camp_id", "camp_name", "leader_name"]].values.tolist()

        table = ax_full.table(cellText=table_data, loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)

        ax_full.set_axis_off()

        title = (
            "All Camp Leaders"
            if camp_id == 0
            else f"All Leaders for Camp {camp_id}"
        )
        ax_full.set_title(title, pad=12)

        def close_fullscreen(ev):
            if ev.inaxes is ax_full and ev.dblclick:
                plt.close(fig_full)

        fig_full.canvas.mpl_connect("button_press_event", close_fullscreen)
        plt.show()

    ax.figure.canvas.mpl_connect("button_press_event", open_fullscreen)