from play.use_cases.recordChallengeAttempt.OutputBoundary import (
    RecordChallengeAttemptOutputBoundary,
)
from play.use_cases.recordChallengeAttempt.OutputData import (
    RecordChallengeAttemptFailureData,
    RecordChallengeAttemptFailureReason,
    RecordChallengeAttemptOutputData,
)


class RecordChallengeAttemptPresenter(RecordChallengeAttemptOutputBoundary):
    _FAILURE_STATUS_CODES = {
        RecordChallengeAttemptFailureReason.INVALID_INPUT: 400,
        RecordChallengeAttemptFailureReason.CHALLENGE_NOT_FOUND: 404,
        RecordChallengeAttemptFailureReason.PROFILE_NOT_FOUND: 404,
        RecordChallengeAttemptFailureReason.ATTEMPT_CONFLICT: 409,
    }

    def __init__(self):
        self.response_body: dict = {}
        self.status_code: int = 200

    def prepare_success_view(
        self, output_data: RecordChallengeAttemptOutputData
    ) -> None:
        self.response_body = {
            "user_id": output_data.user_id,
            "username": output_data.username,
            "avatar": output_data.avatar,
            "total_score": output_data.total_score,
            "completed_challenges": output_data.completed_challenges,
            "scores": output_data.scores,
            "attempt": {
                "id": output_data.attempt.id,
                "attempt_id": output_data.attempt.attempt_id,
                "challenge_slug": output_data.attempt.challenge_slug,
                "score": output_data.attempt.score,
                "completed_at": output_data.attempt.completed_at.isoformat(),
                "received_at": output_data.attempt.received_at.isoformat(),
            },
        }
        self.status_code = 201 if output_data.created else 200

    def prepare_fail_view(self, failure: RecordChallengeAttemptFailureData) -> None:
        self.response_body = {"detail": failure.message}
        self.status_code = self._FAILURE_STATUS_CODES[failure.reason]
