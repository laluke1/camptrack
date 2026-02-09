"""
Unit tests for the `camp_status` module.
"""

from camptrack.database.camp_status import (
    determine_status, CampStatus, MIN_CAMPERS
)
from datetime import date
import unittest


class TestDetermineStatus(unittest.TestCase):
    def setUp(self) -> None:
        self.today = date(1969, 7, 21)  # Apollo 11 moon landing

        self.past_start = date(1969, 7, 10)
        self.past_end = date(1969, 7, 15)

        self.curr_start = date(1969, 7, 16)
        self.curr_end = date(1969, 7, 26)

        self.future_start = date(1969, 8, 1)
        self.future_end = date(1969, 8, 7)

    def test_future_planned(self) -> None:
        # Future camp, no leader yet
        status = determine_status(
            today=self.today,
            s_date=self.future_start,
            e_date=self.future_end,
            has_leader=False,
            n_campers=0,
            food_sufficient=False
        )
        self.assertEqual(status, CampStatus.PLANNED)

    def test_future_no_campers(self) -> None:
        # Future camp, has leader, but no campers yet
        status = determine_status(
            today=self.today,
            s_date=self.future_start,
            e_date=self.future_end,
            has_leader=True,
            n_campers=0,
            food_sufficient=False
        )
        self.assertEqual(status, CampStatus.NO_CAMPERS)

    def test_future_insufficient(self) -> None:
        # Future camp, has leader and campers, but insufficient food
        status = determine_status(
            today=self.today,
            s_date=self.future_start,
            e_date=self.future_end,
            has_leader=True,
            n_campers=MIN_CAMPERS,
            food_sufficient=False
        )
        self.assertEqual(status, CampStatus.INSUFFICIENT_FOOD)

    def test_future_sufficient(self) -> None:
        # Future camp, has leader, campers, and sufficient food
        status = determine_status(
            today=self.today,
            s_date=self.future_start,
            e_date=self.future_end,
            has_leader=True,
            n_campers=MIN_CAMPERS,
            food_sufficient=True
        )
        self.assertEqual(status, CampStatus.READY)

    def test_in_progress(self) -> None:
        # Camp went from sufficient to in progress
        status = determine_status(
            today=self.today,
            s_date=self.curr_start,
            e_date=self.curr_end,
            has_leader=True,
            n_campers=MIN_CAMPERS,
            food_sufficient=True
        )
        self.assertEqual(status, CampStatus.IN_PROGRESS)

    def test_completed(self) -> None:
        # Today > end_date, had leader, campers, and sufficient food
        status = determine_status(
            today=self.today,
            s_date=self.past_start,
            e_date=self.past_end,
            has_leader=True,
            n_campers=MIN_CAMPERS,
            food_sufficient=True
        )
        self.assertEqual(status, CampStatus.COMPLETED)

    def test_cancelled(self) -> None:
        # Camp that could potentially be in progress, but requirements were
        # never satisfied
        status = determine_status(
            today=self.today,
            s_date=self.curr_start,
            e_date=self.curr_end,
            has_leader=False,
            n_campers=0,
            food_sufficient=False
        )
        self.assertEqual(status, CampStatus.CANCELLED)

        status = determine_status(
            today=self.today,
            s_date=self.curr_start,
            e_date=self.curr_end,
            has_leader=True,
            n_campers=0,
            food_sufficient=False
        )
        self.assertEqual(status, CampStatus.CANCELLED)

        status = determine_status(
            today=self.today,
            s_date=self.curr_start,
            e_date=self.curr_end,
            has_leader=True,
            n_campers=MIN_CAMPERS,
            food_sufficient=False
        )
        self.assertEqual(status, CampStatus.CANCELLED)
