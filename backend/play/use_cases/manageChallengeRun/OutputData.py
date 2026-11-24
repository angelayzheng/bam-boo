from dataclasses import dataclass
from enum import Enum

from challenges.domain.challenge import Challenge
from play.domain.Run import Run


class PlayFailureReason(Enum):
    INVALID_INPUT = "invalid_input"
    CHALLENGE_NOT_FOUND = "challenge_not_found"
    CHALLENGE_UNAVAILABLE = "challenge_unavailable"
    RUN_NOT_FOUND = "run_not_found"
    RUN_FORBIDDEN = "run_forbidden"
    INVALID_STAGE = "invalid_stage"
    UNKNOWN_TONE_ANSWER = "unknown_tone_answer"
    TONE_UNAVAILABLE = "tone_unavailable"
    PROFILE_NOT_FOUND = "profile_not_found"
    ATTEMPT_CONFLICT = "attempt_conflict"


@dataclass(frozen=True, slots=True)
class PlayFailureData:
    reason: PlayFailureReason
    message: str


@dataclass(frozen=True, slots=True)
class PlaySuccessData:
    run: Run
    challenge: Challenge
    status_code: int = 200
