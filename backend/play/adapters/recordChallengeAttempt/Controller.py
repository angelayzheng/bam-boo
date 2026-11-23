from datetime import datetime

from play.use_cases.recordChallengeAttempt.InputBoundary import (
    RecordChallengeAttemptInputBoundary,
)
from play.use_cases.recordChallengeAttempt.InputData import (
    RecordChallengeAttemptInputData,
)


class RecordChallengeAttemptController:
    def __init__(self, interactor: RecordChallengeAttemptInputBoundary):
        self._interactor = interactor

    def execute(
        self,
        *,
        user_id: int,
        challenge_slug: str,
        attempt_id: str,
        tone_correct: bool,
        action_correct: bool,
        tone_time: float,
        completed_at: datetime | None,
    ) -> None:
        self._interactor.execute(
            RecordChallengeAttemptInputData(
                user_id=user_id,
                challenge_slug=challenge_slug,
                attempt_id=attempt_id,
                tone_correct=tone_correct,
                action_correct=action_correct,
                tone_time=tone_time,
                completed_at=completed_at,
            )
        )
