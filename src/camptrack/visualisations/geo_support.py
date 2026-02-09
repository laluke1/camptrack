from __future__ import annotations

import sys
from typing import Any, Optional

HAS_GEO: bool = sys.version_info < (3, 14)

if HAS_GEO:
    import geopandas as gpd
    from shapely.geometry import Point
else:
    gpd = None
    Point = None
