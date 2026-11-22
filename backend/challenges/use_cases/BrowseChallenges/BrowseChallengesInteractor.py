"""Interactor for the browse-challenges use case.

Holds the business logic: builds one CalendarDay for each day of the month and
decides its status (completed, available, upcoming, missed, or none). Depends only
on the boundaries and the data access interface, never on Django, so it can be
tested with fakes.
"""

import calendar
from datetime import date
from typing import Callable

from .BrowseChallengesDataAccessInterface import (
    BrowseChallengesDataAccessInterface,
    ChallengeRecord,
)
from .BrowseChallengesInputBoundary import BrowseChallengesInputBoundary
from .BrowseChallengesInputData import BrowseChallengesInputData
from .BrowseChallengesOutputBoundary import BrowseChallengesOutputBoundary
from .BrowseChallengesOutputData import BrowseChallengesOutputData, CalendarDay
from challenges.domain.calendar_clock import calendar_today


class BrowseChallengesInteractor(BrowseChallengesInputBoundary):
    def __init__(
        self,
        data_access: BrowseChallengesDataAccessInterface,
        presenter: BrowseChallengesOutputBoundary,
        today: Callable[[], date] = calendar_today,
    ):
        self._data_access = data_access
        self._presenter = presenter
        self._today = today

    def execute(self, input_data: BrowseChallengesInputData) -> None:
        if not 1 <= input_data.month <= 12:
            self._presenter.prepare_fail_view("Month must be between 1 and 12.")
            return

        records = self._data_access.challenges_in_month(
            input_data.year, input_data.month
        )
        by_date = {r.challenge_date: r for r in records}
        scores = (
            self._data_access.best_scores(input_data.user_id, [r.id for r in records])
            if input_data.user_id is not None
            else {}
        )

        today = self._today()
        days_in_month = calendar.monthrange(input_data.year, input_data.month)[1]
        days = []
        for number in range(1, days_in_month + 1):
            day = date(input_data.year, input_data.month, number)
            record = by_date.get(day)
            if record is None:
                days.append(self._day(day, "none", None, None))
            elif record.id in scores:
                days.append(self._day(day, "completed", scores[record.id], record))
            elif day == today:
                days.append(self._day(day, "available", None, record))
            elif day > today:
                days.append(self._day(day, "upcoming", None, record))
            else:
                days.append(self._day(day, "missed", None, record))

        self._presenter.prepare_success_view(
            BrowseChallengesOutputData(input_data.year, input_data.month, days)
        )

    @staticmethod
    def _day(
        day: date,
        status: str,
        stars: int | None,
        record: ChallengeRecord | None,
    ) -> CalendarDay:
        return CalendarDay(
            date=day,
            status=status,
            stars=stars,
            slug=record.slug if record else None,
            name=record.name if record else None,
            difficulty=record.difficulty if record else None,
            category=record.category if record else None,
        )
