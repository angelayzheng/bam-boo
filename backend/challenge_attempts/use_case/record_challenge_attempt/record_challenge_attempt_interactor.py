from math import isfinite
from uuid import UUID

from .record_challenge_attempt_data_access_interface import (
    AttemptConflictError,
    RecordChallengeAttemptDataAccessInterface,
)
from .record_challenge_attempt_input_boundary import (
    RecordChallengeAttemptInputBoundary,
)
from .record_challenge_attempt_input_data import RecordChallengeAttemptInputData
from .record_challenge_attempt_output_boundary import (
    RecordChallengeAttemptOutputBoundary,
)


class RecordChallengeAttemptInteractor(RecordChallengeAttemptInputBoundary):
    def __init__(
        self,
        user_data_access_object: RecordChallengeAttemptDataAccessInterface,
        presenter: RecordChallengeAttemptOutputBoundary,
    ):
        self._data_access = user_data_access_object
        self._presenter = presenter

    def execute(self, input_data: RecordChallengeAttemptInputData) -> None:
        if not isinstance(input_data.tone_correct, bool) or not isinstance(
            input_data.action_correct, bool
        ):
            self._presenter.prepare_fail_view(
                "tone_correct and action_correct must be booleans.", 400
            )
            return

        tone_time = input_data.tone_time
        if (
            isinstance(tone_time, bool)
            or not isinstance(tone_time, (int, float))
            or (isinstance(tone_time, float) and not isfinite(tone_time))
            or tone_time < 0
        ):
            self._presenter.prepare_fail_view(
                "tone_time must be a finite, non-negative number of seconds.", 400
            )
            return

        try:
            if not isinstance(input_data.attempt_id, str):
                raise ValueError
            attempt_uuid = str(UUID(input_data.attempt_id))
        except TypeError, ValueError:
            self._presenter.prepare_fail_view(
                "A valid attempt_id UUID and timezone-aware completed_at timestamp "
                "are required.",
                400,
            )
            return

        completed_at = input_data.completed_at
        if (
            completed_at is None
            or completed_at.tzinfo is None
            or completed_at.tzinfo.utcoffset(completed_at) is None
        ):
            self._presenter.prepare_fail_view(
                "A valid attempt_id UUID and timezone-aware completed_at timestamp "
                "are required.",
                400,
            )
            return

        if not self._data_access.challenge_exists(input_data.challenge_slug):
            self._presenter.prepare_fail_view("Challenge not found.", 404)
            return

        score = (
            int(input_data.tone_correct)
            + int(tone_time <= 10)
            + int(input_data.action_correct)
        )

        try:
            output_data = self._data_access.save_attempt_and_update_score(
                user_id=input_data.user_id,
                challenge_slug=input_data.challenge_slug,
                attempt_uuid=attempt_uuid,
                score=score,
                completed_at=completed_at,
            )
        except AttemptConflictError as exc:
            self._presenter.prepare_fail_view(str(exc), 409)
            return

        self._presenter.prepare_success_view(output_data)
