from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RecordChallengeAttemptFailureReason(Enum):
    INVALID_INPUT = "invalid_input"
    CHALLENGE_NOT_FOUND = "challenge_not_found"
    PROFILE_NOT_FOUND = "profile_not_found"
    ATTEMPT_CONFLICT = "attempt_conflict"
    RUN_NOT_FOUND = "run_not_found"
    RUN_INCOMPLETE = "run_incomplete"
    RUN_FORBIDDEN = "run_forbidden"


@dataclass(frozen=True, slots=True)
class RecordChallengeAttemptFailureData:
    reason: RecordChallengeAttemptFailureReason
    message: str


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
