from __future__ import annotations

from typing import Optional, Union

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.text import Annotation
import pandas as pd

from camptrack.visualisations.geo_support import HAS_GEO, gpd
from camptrack.utils.logging_config import get_logger
from camptrack.visualisations.charts.empty_plot import render_empty

logger = get_logger(__name__)

# --------------------------------------
# Type alias: DataFrame or GeoDataFrame
# --------------------------------------
GeoDF = Union[pd.DataFrame, "gpd.GeoDataFrame"]


# ============================================================
# CAMP LOCATION MAP
# ============================================================

def plot_camp_locations_auto(
    df: GeoDF,
    ax: Optional[Axes] = None,
) -> Axes:
    """
    Plot camp locations on a world map.

    If GeoPandas is available, use a GeoDataFrame + world geometry.
    Otherwise, fall back to Cartopy-based plotting.

    Behaviour:
    - Stacked left/right labels around the map edges.
    - Scroll-to-zoom around the cursor.
    - Click-and-drag pan.
    - Double-click to open a fullscreen map window
      (and double-click again inside fullscreen to close).
    """
    # -----------------------------------------
    # Graceful empty-case
    # -----------------------------------------
    if df is None or df.empty:
        return render_empty(ax, "No camp location data available")
    
    required = {"lat", "lon", "name"}
    if not required.issubset(df.columns):
        return render_empty(ax, "Camp location data is incomplete")
    
    if HAS_GEO:
        try:
            from shapely.geometry import Point

            # Ensure GeoDataFrame
            if not hasattr(df, "geometry"):
                df = gpd.GeoDataFrame(
                    df,
                    geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])],
                    crs="EPSG:4326",
                )

            # Load world geometry
            world = gpd.read_file(
                "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
                "master/geojson/ne_110m_admin_0_countries.geojson"
            )

            # Create axis if needed
            if ax is None:
                fig, ax = plt.subplots(figsize=(26, 14))
                ax.autoscale(False)

            # Base map + camp points
            world.plot(ax=ax, color="lightgray", edgecolor="white")
            df.plot(ax=ax, color="blue", markersize=100, alpha=0.7)

            # ==========================================
            # STACKED LEFT/RIGHT LABELS (NO OVERLAP)
            # ==========================================

            # Map boundaries
            min_x, max_x = -180, 180
            min_y, max_y = -90, 90

            label_margin_x = 8
            label_margin_y = 32  # vertical spacing between labels

            # Split camps into left or right depending on longitude
            left_labels: list[tuple[float, float, str]] = []
            right_labels: list[tuple[float, float, str]] = []

            for x, y, label in zip(df.geometry.x, df.geometry.y, df["name"]):
                if x < 0:
                    left_labels.append((x, y, label))
                else:
                    right_labels.append((x, y, label))

            # Sort labels vertically to avoid crossing arrows
            left_labels.sort(key=lambda t: t[1], reverse=True)
            right_labels.sort(key=lambda t: t[1], reverse=True)

            # Vertical start positions for labels
            left_start_y = max_y - 5
            right_start_y = max_y - 5

            # Draw left side labels
            for idx, (x, y, label) in enumerate(left_labels):
                text_y = left_start_y - idx * label_margin_y
                text_x = min_x - label_margin_x

                ax.annotate(
                    label,
                    xy=(x, y),
                    xytext=(text_x, text_y),
                    arrowprops=dict(
                        arrowstyle="-",
                        lw=0.8,
                        color="black",
                        relpos=(1, 0.5),
                    ),
                    fontsize=9,
                    ha="right",
                    va="center",
                )

            # Draw right side labels
            for idx, (x, y, label) in enumerate(right_labels):
                text_y = right_start_y - idx * label_margin_y
                text_x = max_x + label_margin_x

                ax.annotate(
                    label,
                    xy=(x, y),
                    xytext=(text_x, text_y),
                    arrowprops=dict(
                        arrowstyle="-",
                        lw=0.8,
                        color="black",
                        relpos=(0, 0.5),
                    ),
                    fontsize=9,
                    ha="left",
                    va="center",
                )

            # Final axis config
            ax.set_xlim(-180, 180)
            ax.set_ylim(-90, 90)
            ax.set_axis_off()
            ax.set_title("Camp Location")

            # Interaction hint
            hint = ax.text(
                0.5, -0.08,
                "Double-click to view full map",
                ha="center", va="top",
                fontsize=9, color="gray",
                transform=ax.transAxes
            )

            # STORE THE HINT SO REDRAW() KNOWS NOT TO DELETE IT
            ax._map_hint = hint

            # Interactivity: scroll + drag pan + label restacking
            enable_interactive_zoom(ax, df)

            # Double-click fullscreen handler
            _attach_fullscreen_handler(ax, world, df)

            return ax

        except Exception as e:  # pragma: no cover - fallback path
            logger.warning(f"GeoPandas path failed, falling back to Cartopy:: {e}")

    # Fallback
    return plot_camp_locations_no_geo(df, ax=ax)


def plot_camp_locations_no_geo(
    df: pd.DataFrame,
    ax: Optional[Axes] = None,
) -> Axes:
    """
    Plot camps on a simple world map using Cartopy (no GeoPandas).

    This does NOT include stacked labels or custom interactivity.
    """
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.geoaxes import GeoAxes

    # Replace or create ax
    if ax is None:
        fig = plt.figure(figsize=(14, 8))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    else:
        if not isinstance(ax, GeoAxes):
            fig = ax.figure
            ss = ax.get_subplotspec()
            gs = ss.get_gridspec()

            row_slice = ss.rowspan.start
            row_stop = ss.rowspan.stop
            col_slice = ss.colspan.start
            col_stop = ss.colspan.stop

            ax.remove()
            ax = fig.add_subplot(
                gs[row_slice:row_stop, col_slice:col_stop],
                projection=ccrs.PlateCarree(),
            )

    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.BORDERS, linewidth=0.4)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.4)

    ax.scatter(
        df["lon"],
        df["lat"],
        s=100,
        color="blue",
        alpha=0.7,
        transform=ccrs.PlateCarree(),
    )

    for x, y, label in zip(df["lon"], df["lat"], df["name"]):
        ax.text(
            x,
            y,
            label,
            fontsize=9,
            ha="right",
            va="bottom",
            transform=ccrs.PlateCarree(),
        )

    ax.set_global()
    ax.set_title("Camp Location")
    return ax


# ============================================================
# INTERACTION: ZOOM + PAN + LABEL RESTACK
# ============================================================

def enable_interactive_zoom(ax: Axes, df: GeoDF | None = None) -> None:
    """
    Attach scroll-zoom and click-drag pan to an axis.

    Behaviour is exactly as in your working version:
    - Scroll wheel zooms in/out around the cursor.
    - Left mouse button drag pans the map.
    - After each zoom/pan, stacked labels are redrawn.
    """
    fig = ax.figure
    pan_state = {"pressed": False, "x": None, "y": None}

    # -------------------------------
    # Helper to redraw labels
    # -------------------------------
    def redraw() -> None:
        if df is None:
            return
        
        hint = getattr(ax, "_map_hint", None)

        # Remove existing text/annotation objects
        for artist in list(ax.texts) + [
            c for c in ax.get_children() if isinstance(c, Annotation)
        ]:
            if artist is hint:       # <-- DO NOT REMOVE HINT
                continue
            try:
                artist.remove()
            except Exception:
                # Non-fatal; continue removing the rest
                pass

        redraw_labels_for_zoom(ax, df)

    # -------------------------------
    # Scroll zoom
    # -------------------------------
    def on_scroll(event) -> None:
        if event.inaxes is not ax:
            return

        scale = 1.2 if event.button == "up" else 1 / 1.2
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        xc, yc = event.xdata, event.ydata

        ax.set_xlim(
            [
                xc - (xc - xlim[0]) * scale,
                xc + (xlim[1] - xc) * scale,
            ]
        )
        ax.set_ylim(
            [
                yc - (yc - ylim[0]) * scale,
                yc + (ylim[1] - yc) * scale,
            ]
        )

        redraw()
        fig.canvas.draw_idle()

    # -------------------------------
    # PAN START (mouse press)
    # -------------------------------
    def on_press(event) -> None:
        if event.inaxes is not ax or event.button != 1:
            return
        pan_state["pressed"] = True
        pan_state["x"], pan_state["y"] = event.x, event.y  # pixel coords

    # -------------------------------
    # PAN END
    # -------------------------------
    def on_release(event) -> None:
        pan_state["pressed"] = False

    # -------------------------------
    # PAN MOVE (mouse drag)
    # -------------------------------
    def on_motion(event) -> None:
        if not pan_state["pressed"] or event.inaxes is not ax:
            return

        dx_pixels = event.x - pan_state["x"]
        dy_pixels = event.y - pan_state["y"]

        # Convert pixel movement → data movement
        inv = ax.transData.inverted()
        p0 = inv.transform((0, 0))
        p1 = inv.transform((dx_pixels, dy_pixels))

        dx_data = p0[0] - p1[0]
        dy_data = p0[1] - p1[1]

        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()

        ax.set_xlim(x0 + dx_data, x1 + dx_data)
        ax.set_ylim(y0 + dy_data, y1 + dy_data)

        # Store new pixel position
        pan_state["x"], pan_state["y"] = event.x, event.y

        redraw()
        fig.canvas.draw_idle()

    # Attach events
    fig.canvas.mpl_connect("scroll_event", on_scroll)
    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)


def redraw_labels_for_zoom(ax: Axes, df: GeoDF) -> None:
    """
    Redraw stacked labels for the current zoomed/panned view.

    Behaviour:
    - Margins scale with the current view extents.
    - Labels are split left/right by current visible midpoint.
    """
    min_x, max_x = ax.get_xlim()
    min_y, max_y = ax.get_ylim()

    label_margin_x = (max_x - min_x) * 0.00001
    label_margin_y = (max_y - min_y) * 0.2

    left_labels: list[tuple[float, float, str]] = []
    right_labels: list[tuple[float, float, str]] = []

    midpoint = (min_x + max_x) / 2.0

    for x, y, label in zip(df.geometry.x, df.geometry.y, df["name"]):
        (left_labels if x < midpoint else right_labels).append((x, y, label))

    left_labels.sort(key=lambda t: t[1], reverse=True)
    right_labels.sort(key=lambda t: t[1], reverse=True)

    left_start_y = max_y - label_margin_y
    right_start_y = max_y - label_margin_y

    for idx, (x, y, label) in enumerate(left_labels):
        ax.annotate(
            label,
            xy=(x, y),
            xytext=(min_x - label_margin_x, left_start_y - idx * label_margin_y),
            ha="right",
            va="center",
                 arrowprops=dict(
                        arrowstyle="-",
                        lw=0.8,
                        color="black",
                        relpos=(1, 0.5),
                    ),
            
        )

    for idx, (x, y, label) in enumerate(right_labels):
        ax.annotate(
            label,
            xy=(x, y),
            xytext=(max_x + label_margin_x, right_start_y - idx * label_margin_y),
            ha="left",
            va="center",
                 arrowprops=dict(
                        arrowstyle="-",
                        lw=0.8,
                        color="black",
                        relpos=(0, 0.5),
                    ),
        )


def redraw_labels_for_fullscreen(ax: Axes, df: GeoDF) -> None:
    """
    Draw labels for the fullscreen view.
    Uses fixed margins and full-world extents.
    """
    min_x, max_x = -180, 180
    min_y, max_y = -90, 90

    label_margin_x = 10
    label_margin_y = 35

    left_labels: list[tuple[float, float, str]] = []
    right_labels: list[tuple[float, float, str]] = []

    # Split by longitude
    for x, y, label in zip(df.geometry.x, df.geometry.y, df["name"]):
        (left_labels if x < 0 else right_labels).append((x, y, label))

    # Sort vertically (top → bottom)
    left_labels.sort(key=lambda t: t[1], reverse=True)
    right_labels.sort(key=lambda t: t[1], reverse=True)

    left_start_y = max_y - 5
    right_start_y = max_y - 5

    # Left side labels
    for idx, (x, y, label) in enumerate(left_labels):
        ax.annotate(
            label,
            xy=(x, y),
            xytext=(min_x - label_margin_x, left_start_y - idx * label_margin_y),
            ha="right",
            va="center",
                    arrowprops=dict(
                        arrowstyle="-",
                        lw=0.8,
                        color="black",
                        relpos=(1, 0.5),
                    ),
        )

    # Right side labels
    for idx, (x, y, label) in enumerate(right_labels):
        ax.annotate(
            label,
            xy=(x, y),
            xytext=(max_x + label_margin_x, right_start_y - idx * label_margin_y),
            ha="left",
            va="center",
                    arrowprops=dict(
                        arrowstyle="-",
                        lw=0.8,
                        color="black",
                        relpos=(0, 0.5),
                    ),
        )


# ============================================================
# FULLSCREEN HANDLER
# ============================================================

def _attach_fullscreen_handler(
    ax: Axes,
    world: "gpd.GeoDataFrame",
    df: GeoDF,
) -> None:
    """
    Attach a double-click handler to `ax` that opens a fullscreen map.

    Fullscreen behaviour:
    - Double-click on the original map → open fullscreen figure.
    - Double-click inside fullscreen map → close it.
    """
    def open_fullscreen_map(event) -> None:
        if event.inaxes is not ax or not event.dblclick:
            return

        # Create fullscreen map window
        fig_full = plt.figure(figsize=(20, 12))

        try:
            mng = fig_full.canvas.manager
            # QtAgg on macOS / Linux
            if hasattr(mng, "window"):
                mng.window.showMaximized()   # preferred behaviour
        except Exception:
            # Some backends do not support this; it's safe to ignore.
            fig_full.set_size_inches(20, 12)
            pass

        ax_full = fig_full.add_subplot(1, 1, 1)

        # Draw map + data
        world.plot(ax=ax_full, color="lightgray", edgecolor="white")
        df.plot(ax=ax_full, color="blue", markersize=120, alpha=0.8)

        # Labels
        redraw_labels_for_fullscreen(ax_full, df)

        ax_full.set_xlim(-180, 180)
        ax_full.set_ylim(-90, 90)
        ax_full.set_axis_off()
        ax_full.set_title("Camp Location", fontsize=18)

        # -----------------------------
        # DOUBLE CLICK TO CLOSE WINDOW
        # -----------------------------
        def close_fullscreen(e) -> None:
            if e.inaxes is ax_full and e.dblclick:
                plt.close(fig_full)

        fig_full.canvas.mpl_connect("button_press_event", close_fullscreen)
        plt.show()

    ax.figure.canvas.mpl_connect("button_press_event", open_fullscreen_map)
