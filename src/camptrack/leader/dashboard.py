import pandas as pd
import sqlite3
from camptrack.database.connection import get_db_cursor
from camptrack.leader.plot import plot_leaders_overall_trends
from camptrack.utils.session import get_user
from camptrack.coordinator.UI import print_header, print_centered_table, TERMINAL_WIDTH
from camptrack.utils.terminal import clear_screen
import pandas as pd

def show_dashboards() -> None:
    """Show all available leader dashboards"""
    try:
        while True:
            clear_screen()
            print_header("DASHBOARDS")
            camp_data =  [
            ["[1]"," Overall Statistics (Table)"],
            ["[2]"," Overall Trends (Charts)"],
            ["[Q]","Quit"]
            ]
            df_camps = pd.DataFrame(
                    camp_data, 
                    columns=["Option", "Dashboard Type"]
                )
            print_centered_table(df_camps)
            cmd = input("Please choose a dashboard to view from above: ").strip()

            if cmd == "1":
                show_overall_statistics()
            elif cmd == "2":
                show_overall_trends()
            elif cmd == "Q" or cmd == "q":
                print("Exiting Dashboards...")
                break
            else:
                print("Invalid dashboard choice, please try again.")
                continue

    except KeyboardInterrupt:
        print("\n\n🚫 Participation logging cancelled. Returning to menu...")
        return None

def show_overall_statistics() -> None:
    """
    Displays overall statistics for all led camps in table form:
        - Total camps led
        - $ earned
        - Total campers led
        - Average participation rates across all activities
        - Total Incident count
        - Total food resources used
    """
    clear_screen()
    stats = get_overall_statistics()

    stats = get_overall_statistics()

    print_header("OVERALL STATISTICS")

    # List of tuples (Label, Value, Format String)
    display_data = [
        ("Total Camps Led", stats.get('total_camp_count', 0), ""),
        ("$ Earned", stats.get('total_money_earned', 0.0), "${:,.2f}"),
        ("Total Campers Led", stats.get('total_campers_led', 0), ""),
        ("Total Incident Count", stats.get('total_incident_count', 0), ""),
        ("Total Food Resources Used", stats.get('total_food_resources', 0.0), "{:,.1f} units"),
        ("Avg Participation Rate", stats.get('avg_participation_rate', 0.0), "{:.1%}")
    ]

    rows = []
    for label, raw_value, fmt_str in display_data:
        safe_value = raw_value if raw_value is not None else 0
        if fmt_str:
            formatted_value = fmt_str.format(safe_value)
        else:
            formatted_value = str(safe_value)
        
        rows.append([label, formatted_value])
    
    df = pd.DataFrame(rows, columns=["Statistic", "Value"])
    print_centered_table(df)
    input("Press Enter to return to Dashboard Menu: ")

def get_overall_statistics() -> dict:
    """Queries and returns required overall statistics"""
    stats = {}

    with get_db_cursor() as cursor:
        curr_user = get_user()

        cursor.execute(
                """
                SELECT
                COUNT(c.id) AS total_camp_count,
                SUM(
                    (julianday(c.end_date) - julianday(c.start_date) + 1) * c.leader_daily_payment_rate
                ) AS total_money_earned
                FROM camps c
                WHERE c.leader_id = ? AND c.start_date <= date('now')
                """, (curr_user.id,)
            )
        res = cursor.fetchone()
        stats['total_camp_count'] = res['total_camp_count']
        stats['total_money_earned'] = res['total_money_earned']

        cursor.execute(
            """
            SELECT COUNT(cr.id) AS total_campers_led
            FROM campers cr
            INNER JOIN camps c ON cr.camp_id = c.id
            WHERE c.leader_id = ? AND c.start_date <= date('now')
            """, (curr_user.id,)
        )
        res = cursor.fetchone()
        stats['total_campers_led'] = res['total_campers_led']

        cursor.execute(
                """
                SELECT SUM(a.incident_count) AS total_incident_count
                FROM activities a
                INNER JOIN camps c ON c.id = a.camp_id
                WHERE c.leader_id = ? AND c.start_date <= date('now')
                """, (curr_user.id,)
            )
        res = cursor.fetchone()
        stats['total_incident_count'] = res['total_incident_count']

        cursor.execute(
                """
                SELECT
                ABS(SUM(fsh.change_amount)) AS total_food_resources
                FROM food_stock_history fsh
                JOIN camps c ON c.id = fsh.camp_id
                WHERE c.leader_id = ?
                AND c.start_date <= date('now')
                AND fsh.change_amount < 0;
                """, (curr_user.id,)
            )
        res = cursor.fetchone()
        stats['total_food_resources'] = res['total_food_resources']

        cursor.execute(
            """
            SELECT
                CAST(SUM(p.actual_participants) AS REAL) / SUM(p.potential_participants) AS avg_participation_rate
            FROM
            (
                SELECT
                    a.id AS activity_id,
                    COUNT(ac.camper_id) AS actual_participants,
                    (
                        SELECT COUNT(ca.id) FROM campers ca WHERE ca.camp_id = a.camp_id
                    ) AS potential_participants
                FROM
                    activities a
                INNER JOIN
                    camps c ON a.camp_id = c.id
                LEFT JOIN
                    activity_campers ac ON a.id = ac.activity_id
                WHERE
                    c.leader_id = ? AND c.start_date <= date('now')
                GROUP BY
                    a.id
            ) AS p;
            """, (curr_user.id,)
        )
        res = cursor.fetchone()
        stats['avg_participation_rate'] = res['avg_participation_rate']

    return stats

def show_overall_trends() -> None:
    """Displays statistical trends of all camps led in charts"""

    df = get_trends_dataframe()
    plot_leaders_overall_trends(df)

def get_trends_dataframe() -> pd.DataFrame:
    """
    Fetches the following statistics grouped by camp_id:
        - $ earned
        - Number of campers led
        - Average participation rates across all activities
        - Incident count
        - Food resources used

    Returns as unified dataframe
    """

    with get_db_cursor() as cursor:
        curr_user = get_user()

        # Similar to above SQL queries but with GROUP BY
        # 1. Get total camps, money earned and campers led
        cursor.execute(
                """
                SELECT
                    c.id AS camp_id,
                    c.name AS camp_name,
                    -- 1. $ Earned
                    (julianday(c.end_date) - julianday(c.start_date) + 1) * c.leader_daily_payment_rate AS money_earned,
                    -- 2. Number of Campers Led
                    TotalCampers.campers_count AS total_campers_led,
                    -- 3. Food Resources Used
                    FoodUsage.actual_used AS food_resources_used
                FROM camps c
                INNER JOIN
                    (
                        -- Subquery to get camper count per camp
                        SELECT camp_id, COUNT(id) AS campers_count
                        FROM campers
                        GROUP BY camp_id
                    ) AS TotalCampers ON c.id = TotalCampers.camp_id
                LEFT JOIN
                    (
                        SELECT
                            camp_id,
                            ABS(SUM(change_amount)) AS actual_used
                        FROM food_stock_history
                        WHERE change_amount < 0
                        GROUP BY camp_id
                    ) AS FoodUsage ON c.id = FoodUsage.camp_id
                WHERE
                    c.leader_id = ? AND c.start_date <= date('now')
                GROUP BY
                    -- Need to group by all other columns in group aggregation
                    c.id, c.name, TotalCampers.campers_count, c.leader_daily_payment_rate, c.approved_daily_food_stock
                ORDER BY c.id ASC;
                """, (curr_user.id,)
            )
        df_base = pd.DataFrame(
            cursor.fetchall(),
            columns=['camp_id', 'camp_name', 'money_earned', 'total_campers_led', 'food_resources_used']
        )

        # 2. Get incident count
        cursor.execute(
                """
                SELECT
                    c.id AS camp_id,
                    SUM(a.incident_count) AS total_incident_count
                FROM camps c
                INNER JOIN activities a ON c.id = a.camp_id
                WHERE c.leader_id = ? AND c.start_date <= date('now')
                GROUP BY c.id
                ORDER BY c.id ASC;
                """, (curr_user.id,)
            )
        df_incidents = pd.DataFrame(
            cursor.fetchall(),
            columns=['camp_id', 'total_incident_count']
        )

        # 3. Gets weighted average participation rate
        cursor.execute(
            """
            SELECT
                c.id AS camp_id,
                c.name AS camp_name,
                CAST(SUM(p.actual_participants) AS REAL) / SUM(p.potential_participants) AS avg_participation_rate
            FROM
            (
                -- P: Subquery calculates ACTUAL and POTENTIAL participation PER ACTIVITY
                SELECT
                    a.camp_id,
                    a.id AS activity_id,
                    COUNT(ac.camper_id) AS actual_participants,
                    (
                        SELECT COUNT(ca.id) FROM campers ca WHERE ca.camp_id = a.camp_id
                    ) AS potential_participants
                FROM activities a
                LEFT JOIN activity_campers ac ON a.id = ac.activity_id
                GROUP BY a.id, a.camp_id -- Must group by camp_id here to prevent errors
            ) AS p
            INNER JOIN camps c ON p.camp_id = c.id
            WHERE c.leader_id = ? AND c.start_date <= date('now')
            GROUP BY c.id, c.name
            ORDER BY c.id ASC;
            """, (curr_user.id,)
        )
        df_participation = pd.DataFrame(
            cursor.fetchall(),
            columns=['camp_id', 'camp_name', 'avg_participation_rate']
        )

        final_df = merge_trends_dataframes(df_base, df_incidents, df_participation)

    return final_df

def merge_trends_dataframes(df_base: pd.DataFrame, df_incidents: pd.DataFrame, df_participation: pd.DataFrame) -> pd.DataFrame:
    """Merge output of get_trends_data"""

    final_df = df_base.copy()

    final_df = final_df.merge(
        df_incidents[['camp_id', 'total_incident_count']],
        on='camp_id',
        how='left'
    )

    final_df = final_df.merge(
        df_participation[['camp_id', 'avg_participation_rate']],
        on='camp_id',
        how='left'
    )

    # Replace any NaN values generated by the LEFT JOINs
    columns_to_fill_zero = ['total_incident_count', 'avg_participation_rate']
    final_df[columns_to_fill_zero] = final_df[columns_to_fill_zero].fillna(0)

    return final_df
