import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional

def render_empty(ax: Optional[Axes], message: str) -> Axes:
    """Render a clean placeholder box when a subplot has no data."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(4, 3))

    ax.set_axis_off()

    ax.text(
        0.5, 0.5,
        message,
        ha="center", va="center",
        fontsize=10, color="gray",
        transform=ax.transAxes,
    )

    return ax
