from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Any, List, Optional, Protocol, Tuple
from camptrack.types.cursor import Cursor


# =======================================================
# TOP-LEVEL SEEDER
# =======================================================
def seed_demo_data(cursor: Cursor) -> None:
    reset_all_seeded_tables(cursor)
    
    seed_camps(cursor)
    seed_campers(cursor)
    seed_assign_leaders(cursor)
    seed_food_stock_history(cursor)
    seed_attendance_rota(cursor)
    seed_activities(cursor)
    seed_notifications(cursor)


# =======================================================
# CAMPS
# =======================================================
def seed_camps(cursor: Cursor) -> None:
    """
    Initial DB population with sample camps that are ongoing.
    """

    today = date.today()
    camp_a_start = today - timedelta(days=2)
    camp_a_end = today + timedelta(days=1)
    camp_b_start = today - timedelta(days=5)
    camp_b_end = today + timedelta(days=2)

    camps = [
        (
            2, "Riverbend Expedition Camp", "Timbuktu", 16.7666, -3.0026,
            camp_a_start.isoformat(), camp_a_end.isoformat(),
            "overnight", 15, 100.00, 5
        ),
        (
            2, "Sunset Valley Camp", "Sunset Valley", 34.0522, -118.2437,
            camp_b_start.isoformat(), camp_b_end.isoformat(),
            "overnight", 10, 80.00, 3
        ),

        (
            2, 'Mountain Expedition', 'The Alps', 46.8200, 8.2300,
            '2025-11-28', '2025-11-30',
            'overnight', 5, 100.00, 5
        ),
        (
            2, 'Desert Trek', 'The Sahara', 23.4162, 25.6628,
            '2025-12-16', '2025-12-20',
            'overnight', 5, 150.00, 5
        ),
        (
            2, 'Summer Adventure', 'Mountain Base', 42.6689, 0.0000,
            '2025-07-01', '2025-07-07',
            'expedition', 5, 200.00, 2
        ),
        (
            2, 'Forest Expo', 'Greenwood Park', 39.7817, -89.6501,
            '2025-12-10', '2025-12-15',
            'expedition', 5, 150.00, 3
        ),
        (
            2, 'Day Camp', 'Thetford Park', 52.4655, 0.7772,
            '2025-08-10', '2025-08-15',
            'overnight', 12, 10.00, 2
        ),
        (
            2, 'Forest Exploration', 'Greenwood Park', 39.8000, -89.6200,
            '2026-08-10', '2026-08-15',
            'day_camp', 5, 400.00, 2
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO camps (
            coordinator_id, name, location, latitude, longitude,
            start_date, end_date, type, approved_daily_food_stock,
            leader_daily_payment_rate, daily_food_per_camper
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        camps
    )


# =======================================================
# ACTIVITIES
# =======================================================
def seed_activities(cursor: Cursor) -> None:
    random.seed(42)
    example_activities = ["Archery", "Canoeing", "Hiking", "Campfire", "Swimming"]

    cursor.execute("SELECT id, start_date FROM camps ORDER BY id ASC")
    camps = cursor.fetchall()

    today = date.today()

    for camp_id, start_str in camps:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()

        cursor.execute("SELECT id FROM campers WHERE camp_id=?", (camp_id,))
        camper_rows = cursor.fetchall()
        camper_ids = [row[0] for row in camper_rows]
        if not camper_ids:
            continue

        activity_ids: List[int] = []

        # Create activities
        for offset, name in enumerate(example_activities):
            activity_date = start_date + timedelta(days=offset)
            if activity_date > today:
                break
            cursor.execute(
                """
                INSERT INTO activities (camp_id, activity_date, activity_name, notes)
                VALUES (?, ?, ?, ?)
                """,
                (camp_id, activity_date.isoformat(), name, f"Notes for {name}")
            )
            activity_ids.append(cursor.lastrowid)

        # Assign participants
        for act_id in activity_ids:
            rate = random.uniform(0.7, 0.9)
            num = max(1, int(len(camper_ids) * rate))
            participants = random.sample(camper_ids, num)

            for camper_id in participants:
                cursor.execute(
                    """
                    INSERT INTO activity_campers (activity_id, camper_id)
                    VALUES (?, ?)
                    """,
                    (act_id, camper_id)
                )

# =======================================================
# LEADERS
# =======================================================
def seed_assign_leaders(cursor: Cursor) -> None:
    """
    Assign each camp a leader by cycling through all users 
    who have role='leader' and are not disabled.
    """

    # Fetch active leaders
    leader_rows = cursor.execute(
        "SELECT id FROM users WHERE role = 'leader' AND is_disabled = 0"
    ).fetchall()

    if not leader_rows:
        return  # No leaders → nothing to assign

    leader_ids = [row[0] for row in leader_rows]

    # Fetch camps
    camps = cursor.execute(
        "SELECT id FROM camps ORDER BY id ASC"
    ).fetchall()

    if not camps:
        return

    # Assign leaders in round-robin pattern
    for i, (camp_id,) in enumerate(camps):
        leader_id = leader_ids[i % len(leader_ids)]
        cursor.execute(
            "UPDATE camps SET leader_id = ? WHERE id = ?;",
            (leader_id, camp_id)
        )


# =======================================================
# CAMPERS
# =======================================================
def seed_campers(cursor: Cursor) -> List[Tuple[Any, ...]]:
    cursor.execute("DELETE FROM campers")

    campers: List[Tuple[Any, ...]] = [
        (1, "Alice Pickles", "2005-04-12"),
        (1, "Ben Turner", "2006-01-23"),
        (2, "Chloe Adams", "2005-11-02"),
        (2, "Daniel Bright", "2007-03-15"),
        (2, "Ella Winters", "2006-07-08"),
        (1, "Finn Cooper", "2005-09-30"),
        (2, "Grace Holloway", "2006-12-19"),
        (2, "Harry Kingston", "2007-02-27"),
        (2, "Isla Matthews", "2005-05-21"),
        (1, "Jack Rivers", "2006-08-14"),

      # --- Teammate’s static campers (assigned to camps 3–8) ---
        # Camp 3: Mountain Expedition
        (3, 'Alice Johnson',  '2012-04-11'),
        (3, 'Ben Thompson',   '2011-09-23'),
        (3, 'Chloe Smith',    '2013-06-05'),
        (3, 'David Williams', '2010-12-19'),

        # Camp 4: Desert Trek
        (4, 'Ella Fitzgerald', '2011-02-28'),
        (4, 'George Wilson',   '2012-10-14'),
        (4, 'Hannah Knight',   '2013-03-17'),

        # Camp 5: Summer Adventure
        (5, 'Isla Peterson',   '2010-08-09'),
        (5, 'Jack Robinson',   '2011-01-30'),
        (5, 'Katie Daniels',   '2012-05-22'),
        (5, 'Leo Martinez',    '2013-11-11'),

        # Camp 6: Forest Expo (2025)
        (6, 'Mia Carter',      '2012-07-01'),
        (6, 'Noah Adams',      '2011-04-04'),
        (6, 'Olivia Brooks',   '2013-09-15'),

        # Camp 7: Day Camp
        (7, 'Peter Wallace',   '2014-02-20'),
        (7, 'Quinn Hughes',    '2013-12-03'),

        # Camp 8: Forest Exploration (2026)
        (8, 'Ruby Evans',      '2011-06-18'),
        (8, 'Samuel Turner',   '2012-11-27'),
        (8, 'Tia Williams',    '2014-01-08'),
    ]

    cursor.executemany(
        """
        INSERT INTO campers (camp_id, name, date_of_birth)
        VALUES (?, ?, ?)
        """,
        campers
    )

    cursor.execute("SELECT * FROM campers")
    return cursor.fetchall()


# =======================================================
# ATTENDANCE
# =======================================================
def seed_attendance_rota(cursor: Cursor) -> None:
    random.seed(42)

    cursor.execute("SELECT * FROM campers")
    cursor.fetchall()  # We only need to verify existence; rows unused

    cursor.execute("SELECT id, start_date, end_date FROM camps ORDER BY id ASC")
    camps = cursor.fetchall()

    attendance_rows: List[Tuple[int, int, str, str]] = []

    for camp_id, start_str, end_str in camps:
        cursor.execute("SELECT id FROM campers WHERE camp_id=?", (camp_id,))
        campers = [r[0] for r in cursor.fetchall()]
        if not campers:
            continue

        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

        today = date.today()
        if start_date > today:
            continue  # don’t generate attendance for future camps

        end_date = min(end_date, today)

        total_days = (end_date - start_date).days + 1

        for offset in range(total_days):
            day = start_date + timedelta(days=offset)
            day_str = day.isoformat()

            for camper_id in campers:
                status = random.choices(
                    ["present", "absent"],
                    weights=[0.75, 0.25]
                )[0]
                attendance_rows.append((camp_id, camper_id, day_str, status))

    cursor.executemany(
        """
        INSERT INTO attendance_records (camp_id, camper_id, date, status)
        VALUES (?, ?, ?, ?)
        """,
        attendance_rows
    )


# =======================================================
# FOOD STOCK
# =======================================================
def seed_food_stock_history(cursor: Cursor) -> None:
    cursor.execute("DELETE FROM food_stock_history")

    camps = cursor.execute(
        """
        SELECT id, start_date, end_date, approved_daily_food_stock
        FROM camps;
        """
    ).fetchall()

    today = date.today()

    for camp_id, start_str, end_str, daily_stock in camps:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)

        # Skip camps that haven't started yet
        if start > today:
            continue

        # --- IMPORTANT: calculate full camp length for initial stock ---
        full_camp_days = (end - start).days + 1
        initial_stock = daily_stock * full_camp_days
        running_stock = initial_stock

        # Insert initial allocation as-is (even for future-ending camps)
        cursor.execute(
            """
            INSERT INTO food_stock_history
            (camp_id, date, stock_available, change_reason, change_amount)
            VALUES (?, ?, ?, ?, ?)
            """,
            (camp_id, start.isoformat(), initial_stock, "initial allocation", initial_stock)
        )

        # --- Clamp daily usage to today ---
        last_day_to_seed = min(end, today)
        days_to_seed = (last_day_to_seed - start).days + 1

        # Daily stock usage ONLY up to today
        for i in range(days_to_seed):
            current = start + timedelta(days=i)
            running_stock -= daily_stock

            cursor.execute(
                """
                INSERT INTO food_stock_history
                (camp_id, date, stock_available, change_reason, change_amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    camp_id,
                    current.isoformat(),
                    running_stock,
                    "daily usage",
                    -daily_stock
                )
            )


# =======================================================
# NOTIFICATIONS
# =======================================================
def seed_notifications(cursor: Cursor) -> None:
    cursor.execute("DELETE FROM notifications")

    notifications = [
        # CAMP 1: Riverbend Expedition Camp (originally CAMP A)
        (
            1, 2, 'not_enough_food',
            'Food stock for Riverbend Expedition Camp has fallen below the approved daily level.',
            0
        ),
        (
            1, 2, 'low_daily_payment_rate',
            'Leader daily payment rate for Riverbend Expedition Camp is below the recommended threshold.',
            1
        ),

        # CAMP 5: Summer Adventure
        (
            5, 2, 'not_enough_food',
            'Summer Adventure camp will not have enough food if registrations continue to increase.',
            0
        ),
        (
            5, 2, 'low_daily_payment_rate',
            'Leader daily payment rate for Summer Adventure is low compared to similar expeditions.',
            1
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO notifications (camp_id, coordinator_id, type, message, is_read)
        VALUES (?, ?, ?, ?, ?)
        """,
        notifications
    )


# =======================================================
# RESET SEED DATA
# =======================================================
def reset_all_seeded_tables(cursor: Cursor) -> None:
    tables = [
        "attendance_records",
        "activity_campers",
        "activities",
        "food_stock_history",
        "campers",
        "camps",
        "notifications"
    ]
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
