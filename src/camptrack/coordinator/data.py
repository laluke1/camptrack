from camptrack.database.camp_status import get_camp_status
'''
Functions for data retrieval.
'''

def get_camp_data(conn) -> list[dict]:
    """
    Retrieve camp data from the database for the dashboard.
    """
    with conn:
        cur = conn.execute(
            """
            SELECT
                c.id,
                c.coordinator_id,
                u.username AS leader_name,
                c.name,
                c.start_date,
                c.end_date,
                c.type as camp_type,
                c.approved_daily_food_stock,
                c.leader_daily_payment_rate,
                c.daily_food_per_camper,
                COUNT(DISTINCT cp.id) AS n_campers
            FROM camps as c
            LEFT JOIN users AS u ON u.id = c.leader_id
            LEFT JOIN campers AS cp ON c.id = cp.camp_id
            LEFT JOIN notifications AS n ON c.id = n.camp_id
            GROUP BY c.id, c.coordinator_id, u.username, c.name, c.start_date, c.end_date, c.type, c.approved_daily_food_stock, c.leader_daily_payment_rate, c.daily_food_per_camper;
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
    return rows

def get_notifications(conn) -> list[dict]:
    """
    Retrieve notifications from the database for the dashboard.
    """
    with conn:
        cur = conn.execute(
            """
            SELECT
                n.id,
                n.camp_id,
                n.coordinator_id,
                n.type,
                n.message,
                n.is_read,
                n.created_at
            FROM notifications AS n
            ORDER BY n.id ASC;
            """,
        )
        rows = [dict(row) for row in cur.fetchall()]
    return rows