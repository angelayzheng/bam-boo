from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RecordChallengeAttemptInputData:
    user_id: int
    challenge_slug: str
    attempt_id: str
    tone_correct: bool
    action_correct: bool
    tone_time: float
    completed_at: datetime
