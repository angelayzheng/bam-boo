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
    ) -> None:
        self._interactor.execute(
            RecordChallengeAttemptInputData(
                user_id=user_id,
                challenge_slug=challenge_slug,
                attempt_id=attempt_id,
            )
        )
