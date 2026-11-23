"""Input data for the browse-challenges use case.

A plain, immutable record of what the caller is asking for: the year, the month,
and the user (None for guests). Contains no Django or request objects.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BrowseChallengesInputData:
    year: int
    month: int
    user_id: int | None = None  # None for guests
