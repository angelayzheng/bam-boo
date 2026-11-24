"""Data access interface for the browse-challenges use case.

Declares what the interactor needs from storage (the challenges in a month and a
user's best scores) without saying how they are stored. The Django ORM adapter
implements it, so this file must not import Django or any model.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ChallengeRecord:
    id: int
    name: str
    challenge_date: date
    slug: str | None
    difficulty: int | None
    category: str | None


class BrowseChallengesDataAccessInterface(ABC):
    @abstractmethod
    def challenges_in_month(self, year: int, month: int) -> list[ChallengeRecord]: ...

    @abstractmethod
    def best_scores(self, user_id: int, challenge_ids: list[int]) -> dict[int, int]:
        """Map of challenge id to the user's best score."""
