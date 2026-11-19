from datetime import datetime
from math import isfinite
from uuid import UUID

from play.domain.attempt import Attempt
from play.domain.star_rules import StarRules

from .record_challenge_attempt_data_access_interface import (
    AttemptConflictError,
    RecordChallengeAttemptDataAccessInterface,
    RecordedChallengeAttempt,
)
from .record_challenge_attempt_input_boundary import (
    RecordChallengeAttemptInputBoundary,
)
from .record_challenge_attempt_input_data import RecordChallengeAttemptInputData
from .record_challenge_attempt_output_boundary import (
    RecordChallengeAttemptOutputBoundary,
)
from .record_challenge_attempt_output_data import (
    AttemptOutputData,
    RecordChallengeAttemptOutputData,
)


class RecordChallengeAttemptInteractor(RecordChallengeAttemptInputBoundary):
    def __init__(
        self,
        data_access: RecordChallengeAttemptDataAccessInterface,
        presenter: RecordChallengeAttemptOutputBoundary,
        star_rules: StarRules | None = None,
    ):
        self._data_access = data_access
        self._presenter = presenter
        self._star_rules = star_rules or StarRules()

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

        score = self._star_rules.score(
            input_data.tone_correct, tone_time, input_data.action_correct
        )
        completed_at = input_data.completed_at
        if not isinstance(completed_at, datetime) or completed_at.utcoffset() is None:
            self._presenter.prepare_fail_view(
                "A valid attempt_id UUID and timezone-aware completed_at timestamp "
                "are required.",
                400,
            )
            return
        try:
            if not isinstance(input_data.attempt_id, str):
                raise ValueError
            submission_id = str(UUID(input_data.attempt_id))
            attempt = Attempt(
                submission_id=submission_id,
                profile_id=input_data.user_id,
                challenge_slug=input_data.challenge_slug,
                score=score,
                completed_at=completed_at,
            )
        except TypeError, ValueError:
            self._presenter.prepare_fail_view(
                "A valid attempt_id UUID and timezone-aware completed_at timestamp "
                "are required.",
                400,
            )
            return

        if not self._data_access.challenge_exists(attempt.challenge_slug):
            self._presenter.prepare_fail_view("Challenge not found.", 404)
            return

        try:
            recorded = self._data_access.record(attempt)
        except AttemptConflictError as exc:
            self._presenter.prepare_fail_view(str(exc), 409)
            return

        self._presenter.prepare_success_view(self._build_output_data(recorded))

    def _build_output_data(
        self, recorded: RecordedChallengeAttempt
    ) -> RecordChallengeAttemptOutputData:
        attempt = recorded.attempt
        profile = recorded.profile
        if attempt.record_id is None or attempt.received_at is None:
            raise ValueError("A recorded attempt must have an ID and receipt time.")
        return RecordChallengeAttemptOutputData(
            user_id=profile.user_id,
            username=profile.username,
            avatar=profile.avatar,
            total_score=profile.total_score,
            completed_challenges=len(profile.scores),
            scores=dict(profile.scores),
            attempt=AttemptOutputData(
                id=attempt.record_id,
                attempt_id=attempt.submission_id,
                challenge_slug=attempt.challenge_slug,
                score=attempt.score,
                completed_at=attempt.completed_at,
                received_at=attempt.received_at,
            ),
            created=recorded.created,
        )
