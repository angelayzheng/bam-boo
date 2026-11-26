from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class GetChallengeOutputData:
    name: str
    slug: str
    challenge_date: date
    difficulty: int
    category: str


@dataclass(frozen=True, slots=True)
class GetChallengeFailureData:
    message: str
