from camptrack.coordinator.data import get_camp_data
from camptrack.database.connection import get_db_connection
from camptrack.utils.session import get_user
from datetime import date

'''
Helper functions for main coordinator dash.
'''
def set_daily_payment_rate(camp_id: int, new_rate: float) -> None:
    """
    Function to set daily payment rate for any existing camp.
    """
    # [Additional] Rate is conditional on number of campers.
    # take a third parameter. Decide a max rate per camper

    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                UPDATE camps
                SET leader_daily_payment_rate = ?
                WHERE id = ?
            """, (new_rate, camp_id))
    finally:
        conn.close()

    
def top_up_food_stock(camp_id: int, additional_stock: int) -> None:
    """
    Function to top up food stock for any existing camp.
    """
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                UPDATE camps
                SET approved_daily_food_stock = approved_daily_food_stock + ?
                WHERE id = ?
            """, (additional_stock, camp_id))
    finally:
        conn.close()

def change_notification_status(notification_id: int, status: int) -> None:
    """
    Function to change notification status for a camp.
    """
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                UPDATE notifications
                SET is_read = ?
                WHERE id = ?
""", (status, notification_id))
    finally:
        conn.close()

def days_left(camp_id: int) -> int:
    """
    Function to calculate days left until camp ends. Always returns at least 1.
    """
    conn = get_db_connection()
    try:
        camp = next((c for c in get_camp_data(conn) if c.get('id') == camp_id), None)
        if camp is None:
            return 1

        end_date = date.fromisoformat(camp['end_date'])
        days_remaining = (end_date - date.today()).days
        return days_remaining if days_remaining >= 1 else 1
    finally:
        conn.close()


def nofification_generator() -> None:
    """
    Function to generate notifications from the dataset.
    Avoids creating duplicate unread notifications for the same camp and type.
    """
    conn = get_db_connection()
    try:
        camps = get_camp_data(conn)

        for camp in camps:

            food_type = 'not_enough_food'
            food_msg = f"Camp '{camp['name']}' may run out of food stock before the camp ends."
            money_type = 'low_daily_payment_rate'
            money_msg = f"Camp '{camp['name']}' has a low daily payment rate for the leader."

            # Check and insert "not enough food" notification if needed and not already present (unread)
            if camp['approved_daily_food_stock'] < camp['daily_food_per_camper'] * camp['n_campers'] * days_left(camp['id']):
                with conn:
                    cur = conn.execute(
                        "SELECT COUNT(1) AS cnt FROM notifications WHERE camp_id = ? AND type = ? AND is_read = 0",
                        (camp['id'], food_type)
                    )
                    if cur.fetchone()[0] == 0:
                        conn.execute(
                            """
                            INSERT INTO notifications (camp_id, coordinator_id, type, message, is_read)
                            VALUES (?, 1, ?, ?, 0)
                            """,
                            (camp['id'], food_type, food_msg)
                        )

            # Check and insert "low daily payment rate" notification if needed and not already present (unread)
            elif camp['leader_daily_payment_rate'] < (20 * camp['n_campers']):
                with conn:
                    cur = conn.execute(
                        "SELECT COUNT(1) AS cnt FROM notifications WHERE camp_id = ? AND type = ? AND is_read = 0",
                        (camp['id'], money_type)
                    )
                    if cur.fetchone()[0] == 0:
                        conn.execute(
                            """
                            INSERT INTO notifications (camp_id, coordinator_id, type, message, is_read)
                            VALUES (?, 1, ?, ?, 0)
                            """,
                            (camp['id'], money_type, money_msg)
                        )
    finally:
        conn.close()
 
