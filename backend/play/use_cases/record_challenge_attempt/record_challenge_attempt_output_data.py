from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AttemptOutputData:
    id: int
    attempt_id: str
    challenge_slug: str
    score: int
    completed_at: datetime
    received_at: datetime


@dataclass(frozen=True, slots=True)
class RecordChallengeAttemptOutputData:
    user_id: int
    username: str
    avatar: str
    total_score: int
    completed_challenges: int
    scores: dict[str, int]
    attempt: AttemptOutputData
    created: bool
