import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import pandas as pd
from typing import Optional

def plot_leaders_overall_trends(df: pd.DataFrame) -> None:
    """Combine all plots into single dashboard"""
    fig, axes = plt.subplots(2, 3, figsize=(18,8))

    plot_money_earned(df, ax=axes[0, 0])
    plot_total_campers(df, ax=axes[0, 1])
    plot_avg_participation_rates(df, ax=axes[0, 2])
    plot_incident_count(df, ax=axes[1,0])
    plot_food_resources(df, ax=axes[1, 1])

    axes[1, 2].axis('off') # Hide unused plot panel

    plt.tight_layout()
    plt.show()

def plot_money_earned(df: pd.DataFrame, ax: Optional[Axes] = None) -> Optional[Axes]:

    if df.empty:
        print("No records for money earned.")
        return ax

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(df["camp_name"], df["money_earned"], color="green")
    ax.set_xlabel("Camp")
    ax.set_ylabel("Amount ($)")
    ax.set_title("Money Earned from Past Camps")

    max_value = df["money_earned"].max()
    top_limit = max_value * 1.1 if max_value > 0 else 1.0
    ax.set_ylim(0, top_limit)
    for i, v in enumerate(df["money_earned"]):
        offset = top_limit * 0.01
        ax.text(i, v + offset, str(v), ha="center", va="bottom")

    return ax

def plot_total_campers(df: pd.DataFrame, ax: Optional[Axes] = None) -> Optional[Axes]:

    if df.empty:
        print("No records for total campers.")
        return ax

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(df["camp_name"], df["total_campers_led"], color="gold")
    ax.set_xlabel("Camp")
    ax.set_ylabel("No. of Campers")
    ax.set_title("Number of Campers Led")

    max_value = df["total_campers_led"].max()
    top_limit = max_value * 1.1 if max_value > 0 else 1.0
    ax.set_ylim(0, top_limit)
    for i, v in enumerate(df["total_campers_led"]):
        offset = top_limit * 0.01
        ax.text(i, v + offset, str(v), ha="center", va="bottom")

    return ax

def plot_avg_participation_rates(df: pd.DataFrame, ax: Optional[Axes] = None) -> Optional[Axes]:

    if df.empty:
        print("No records for participation rates.")
        return ax

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(df["camp_name"], df["avg_participation_rate"], color="skyblue")
    ax.set_xlabel("Camp")
    ax.set_ylabel("Rate (%)")
    ax.set_title("Average Participation Rate")

    max_value = df["avg_participation_rate"].max()
    top_limit = max_value * 1.1 if max_value > 0 else 1.0
    ax.set_ylim(0, top_limit)
    for i, v in enumerate(df["avg_participation_rate"]):
        label = f"{v * 100:.2f}"
        offset = top_limit * 0.01
        ax.text(i, v + offset, label, ha="center", va="bottom")

    return ax

def plot_incident_count(df: pd.DataFrame, ax: Optional[Axes] = None) -> Optional[Axes]:

    if df.empty:
        print("No records for incident counts.")
        return ax

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(df["camp_name"], df["total_incident_count"], color="orange")
    ax.set_xlabel("Camp")
    ax.set_ylabel("No. of incidents")
    ax.set_title("Total Incident Counts")

    max_value = df["total_incident_count"].max()
    top_limit = max_value * 1.1 if max_value > 0 else 1.0
    ax.set_ylim(0, top_limit)
    for i, v in enumerate(df["total_incident_count"]):
        offset = top_limit * 0.01
        ax.text(i, v + offset, str(v), ha="center", va="bottom")

    return ax

def plot_food_resources(df: pd.DataFrame, ax: Optional[Axes] = None) -> Optional[Axes]:

    if df.empty:
        print("No records for food resources used.")
        return ax

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(df["camp_name"], df["food_resources_used"], color="beige")
    ax.set_xlabel("Camp")
    ax.set_ylabel("Units of Food")
    ax.set_title("Food Resources Used")

    max_value = df["food_resources_used"].max()
    top_limit = max_value * 1.1 if max_value > 0 else 1.0
    ax.set_ylim(0, top_limit)
    for i, v in enumerate(df["food_resources_used"]):
        offset = top_limit * 0.01
        ax.text(i, v + offset, str(v), ha="center", va="bottom")

    return ax
