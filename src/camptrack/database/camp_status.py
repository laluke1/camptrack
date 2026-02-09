from enum import Enum
from datetime import datetime, date
from .connection import get_db_cursor
from typing import Optional


# Minimum number of campers needed for a camp to run
MIN_CAMPERS = 1


class CampStatus(Enum):
    """
    Each camp has a status that can be determined dynamically based on the
    current date and information available.

    PLANNED:
        Future camp, no leader yet.

    NO_CAMPERS:
        Future camp, has leader, but no campers yet.

    INSUFFICIENT_FOOD:
        Future camp, has leader and campers, but insufficient food.

    READY:
        Future camp, has leader, campers, and sufficient food.

    IN_PROGRESS:
        The camp is running.

    COMPLETED:
        Today > end_date, had leader, campers, and sufficient food.

    CANCELLED:
        A camp is considered cancelled if it did not reach the SUFFICIENT 
        status before its start date.
    """
    PLANNED = 'planned'
    NO_CAMPERS = 'no_campers'
    INSUFFICIENT_FOOD = 'insufficient_food'
    READY = 'ready'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


# Date string format used in the database
DATE_FORMAT = '%Y-%m-%d'  # 'YYYY-MM-DD'


def get_camp_status(camp_id: int) -> CampStatus:
    """
    Return the status of the camp with the provided ID.
    """
    return get_camp_statuses([camp_id])[camp_id]


def get_camp_statuses(
    camp_ids: Optional[list[int]] = None
) -> dict[int, CampStatus]:
    """
    If `camp_ids` is `None`, return the status of all camps in the database.
    Otherwise, return the status of all camps in `camp_ids`.
    """
    # TODO: this function needs tests
    with get_db_cursor() as cursor:
        if camp_ids is None:
            cursor.execute("""
                SELECT c.*, COUNT(DISTINCT campers.id) as n_campers
                FROM camps c
                LEFT JOIN campers ON c.id = campers.camp_id
                GROUP BY c.id
            """)
        else:
            cursor.execute(f"""
                SELECT c.*, COUNT(DISTINCT campers.id) as n_campers
                FROM camps c
                LEFT JOIN campers ON c.id = campers.camp_id
                WHERE c.id IN ({','.join('?' * len(camp_ids))})
                GROUP BY c.id
            """, camp_ids)

        camps = cursor.fetchall()

    result = {}

    today = date.today()
    for camp in camps:
        s_date = datetime.strptime(camp['start_date'], DATE_FORMAT).date()
        e_date = datetime.strptime(camp['end_date'], DATE_FORMAT).date()
        has_leader = camp['leader_id'] is not None
        n_campers = camp['n_campers'] or 0
        food_needed = camp['daily_food_per_camper'] * n_campers
        food_sufficient = food_needed <= camp['approved_daily_food_stock']

        result[camp['id']] = determine_status(
            today=today,
            s_date=s_date,
            e_date=e_date,
            has_leader=has_leader,
            n_campers=n_campers,
            food_sufficient=food_sufficient
        )

    return result


def determine_status(
    today: date,
    s_date: date,
    e_date: date,
    has_leader: bool,
    n_campers: int,
    food_sufficient: bool
) -> CampStatus:
    """
    Determine the status of a camp using the provided state.
    """
    # Past camp
    if e_date < today:
        if has_leader and n_campers >= MIN_CAMPERS and food_sufficient:
            return CampStatus.COMPLETED
        else:
            return CampStatus.CANCELLED
    # Camp that is potentially in progress
    elif s_date <= today <= e_date:
        if has_leader and n_campers >= MIN_CAMPERS and food_sufficient:
            return CampStatus.IN_PROGRESS
        else:
            return CampStatus.CANCELLED
    # Future camp
    else:
        if not has_leader:
            return CampStatus.PLANNED
        elif n_campers < MIN_CAMPERS:
            return CampStatus.NO_CAMPERS
        elif not food_sufficient:
            return CampStatus.INSUFFICIENT_FOOD
        else:
            return CampStatus.READY
