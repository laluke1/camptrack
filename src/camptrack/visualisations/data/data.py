from __future__ import annotations

import pandas as pd
from datetime import date
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union

from camptrack.visualisations.geo_support import HAS_GEO, gpd
from camptrack.types.cursor import Cursor
from camptrack.utils.logging_config import get_logger

logger = get_logger(__name__)

# Type alias: GeoDataFrame OR DataFrame
GeoDF = Union[pd.DataFrame, "gpd.GeoDataFrame"]


# External imports
from camptrack.visualisations.data.food_stock import fetch_camp_food_stock
from camptrack.visualisations.data.attendance import fetch_camp_attendance
from camptrack.visualisations.data.activities import fetch_activity_engagement


# -----------------------------------------
# Fetch set of visualisation data
# -----------------------------------------
def fetch_visualisation_data(
    camp_id: int,
    cursor: Cursor
) -> Dict[str, Any]:
    """
    Fetch all data needed for a camp's visualisations.
    """

    df_food = fetch_camp_food_stock(cursor, camp_id)
    df_attendance = fetch_camp_attendance(cursor, camp_id)
    leaders = fetch_camp_leaders(cursor, camp_id)
    gdf_locations = fetch_camp_locations_auto(cursor, camp_id=camp_id)
    df_activities = fetch_activity_engagement(cursor, camp_id)
    total_campers = fetch_total_campers(cursor, camp_id)

    return {
        "df_food": df_food,
        "df_attendance": df_attendance,
        "leaders": leaders,
        "gdf_locations": gdf_locations,
        "df_activities": df_activities,
        "total_campers": total_campers,
    }


# -----------------------------------------
# Leaders
# -----------------------------------------
def fetch_camp_leaders(cursor: Cursor, camp_id: int) -> pd.DataFrame:
    """
    Fetch leaders for a specific camp or all camps.

    Returns DataFrame with:
        ["camp_id", "camp_name", "leader_name"]
    """

    base_query = """
        SELECT 
            c.id AS camp_id,
            c.name AS camp_name,
            u.username AS leader_name
        FROM camps c
        LEFT JOIN users u ON u.id = c.leader_id
    """

    # Fetch all or single camp
    if camp_id == 0:
        rows = cursor.execute(base_query).fetchall()
    else:
        rows = cursor.execute(
            base_query + " WHERE c.id = ?",
            (camp_id,)
        ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["camp_id", "camp_name", "leader_name"])

    return pd.DataFrame(rows, columns=["camp_id", "camp_name", "leader_name"])


# -----------------------------------------
# Camp Locations (Auto)
# -----------------------------------------
def fetch_camp_locations_auto(cursor: Cursor, camp_id: Optional[int] = None) -> GeoDF:
    """
    Return camp locations as GeoDataFrame (if geopandas available)
    or as plain pandas DataFrame otherwise.
    """
    if HAS_GEO:
        try:
            from shapely.geometry import Point

            if camp_id:
                rows = cursor.execute(
                    """
                    SELECT name, location, latitude, longitude
                    FROM camps
                    WHERE id = ?
                    """,
                    (camp_id,),
                ).fetchall()
            else:
                rows = cursor.execute(
                    """
                    SELECT name, location, latitude, longitude
                    FROM camps
                    """
                ).fetchall()

            if not rows:
                return gpd.GeoDataFrame(
                    columns=["name", "location", "lat", "lon", "geometry"],
                    crs="EPSG:4326",
                )

            df = pd.DataFrame(rows, columns=["name", "location", "lat", "lon"])

            gdf = gpd.GeoDataFrame(
                df,
                geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])],
                crs="EPSG:4326",
            )
            return gdf

        except Exception as e:
            logger.warning(f"Geo fetch failed, falling back to non-geo: {e}")

    return fetch_camp_locations_no_geo(cursor, camp_id)


# -----------------------------------------
# Camp Locations (No Geo)
# -----------------------------------------
def fetch_camp_locations_no_geo(
    cursor: Cursor,
    camp_id: Optional[int] = None
) -> pd.DataFrame:
    """
    Return non-geo location data with columns:
    ["name", "location", "lat", "lon"]
    """

    if camp_id:
        rows = cursor.execute(
            """
            SELECT name, location, latitude, longitude
            FROM camps
            WHERE id = ?
            """,
            (camp_id,),
        ).fetchall()
    else:
        rows = cursor.execute(
            """
            SELECT name, location, latitude, longitude
            FROM camps
            """
        ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["name", "location", "lat", "lon"])

    df = pd.DataFrame(rows, columns=["name", "location", "lat", "lon"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df


# -----------------------------------------
# Total Campers
# -----------------------------------------
def fetch_total_campers(cursor: Cursor, camp_id: int) -> int:
    if camp_id == 0:
        total = cursor.execute(
            """
            SELECT COUNT(DISTINCT camper_id)
            FROM attendance_records
            WHERE status = 'present';
            """
        ).fetchone()[0]
    else:
        total = cursor.execute(
            """
            SELECT COUNT(DISTINCT camper_id)
            FROM attendance_records
            WHERE camp_id = ? AND status = 'present';
            """,
            (camp_id,),
        ).fetchone()[0]

    return int(total)
