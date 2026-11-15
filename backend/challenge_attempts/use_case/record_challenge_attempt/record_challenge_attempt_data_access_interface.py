from datetime import datetime
from typing import Protocol

from .record_challenge_attempt_output_data import RecordChallengeAttemptOutputData


class AttemptConflictError(ValueError):
    pass


class RecordChallengeAttemptDataAccessInterface(Protocol):
    def challenge_exists(self, challenge_slug: str) -> bool: ...

    def save_attempt_and_update_score(
        self,
        *,
        user_id: int,
        challenge_slug: str,
        attempt_uuid: str,
        score: int,
        completed_at: datetime,
    ) -> RecordChallengeAttemptOutputData: ...
