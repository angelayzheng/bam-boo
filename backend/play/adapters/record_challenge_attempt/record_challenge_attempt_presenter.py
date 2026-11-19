from play.use_cases.record_challenge_attempt.record_challenge_attempt_output_boundary import (
    RecordChallengeAttemptOutputBoundary,
)
from play.use_cases.record_challenge_attempt.record_challenge_attempt_output_data import (
    RecordChallengeAttemptOutputData,
)


class RecordChallengeAttemptPresenter(RecordChallengeAttemptOutputBoundary):
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

    def prepare_fail_view(self, error_message: str, status_code: int) -> None:
        self.response_body = {"detail": error_message}
        self.status_code = status_code
