"""Output data for the browse-challenges use case.

The result the interactor hands to the presenter: one CalendarDay per day of the
month, with its challenge, status, and stars. Plain dataclasses only, so the use
case stays independent of the web framework and of how the data is displayed.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CalendarDay:
    date: date
    status: str  # "completed", "missed", "available", "upcoming", "none"
    stars: int | None
    slug: str | None
    name: str | None
    difficulty: int | None
    category: str | None


@dataclass(frozen=True)
class BrowseChallengesOutputData:
    year: int
    month: int
    days: list[CalendarDay]
