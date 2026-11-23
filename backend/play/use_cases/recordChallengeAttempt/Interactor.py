from datetime import datetime
from math import isfinite
from uuid import UUID

from challenges.use_cases.ports import ChallengeRepository
from play.domain.attempt import Attempt
from play.domain.star_rules import StarRules
from play.use_cases.ports import AttemptRepository, UnitOfWork
from users.domain.profile import Profile
from users.use_cases.ports import ProfileRepository

from .InputBoundary import (
    RecordChallengeAttemptInputBoundary,
)
from .InputData import RecordChallengeAttemptInputData
from .OutputBoundary import (
    RecordChallengeAttemptOutputBoundary,
)
from .OutputData import (
    AttemptOutputData,
    RecordChallengeAttemptFailureData,
    RecordChallengeAttemptFailureReason,
    RecordChallengeAttemptOutputData,
)


class RecordChallengeAttemptInteractor(RecordChallengeAttemptInputBoundary):
    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        attempts: AttemptRepository,
        profiles: ProfileRepository,
        unit_of_work: UnitOfWork,
        presenter: RecordChallengeAttemptOutputBoundary,
        star_rules: StarRules | None = None,
    ):
        self._challenges = challenges
        self._attempts = attempts
        self._profiles = profiles
        self._unit_of_work = unit_of_work
        self._presenter = presenter
        self._star_rules = star_rules or StarRules()

    def execute(self, input_data: RecordChallengeAttemptInputData) -> None:
        if not isinstance(input_data.tone_correct, bool) or not isinstance(
            input_data.action_correct, bool
        ):
            self._fail(
                RecordChallengeAttemptFailureReason.INVALID_INPUT,
                "tone_correct and action_correct must be booleans.",
            )
            return

        tone_time = input_data.tone_time
        if (
            isinstance(tone_time, bool)
            or not isinstance(tone_time, (int, float))
            or (isinstance(tone_time, float) and not isfinite(tone_time))
            or tone_time < 0
        ):
            self._fail(
                RecordChallengeAttemptFailureReason.INVALID_INPUT,
                "tone_time must be a finite, non-negative number of seconds.",
            )
            return

        score = self._star_rules.score(
            input_data.tone_correct, tone_time, input_data.action_correct
        )
        completed_at = input_data.completed_at
        if not isinstance(completed_at, datetime) or completed_at.utcoffset() is None:
            self._fail(
                RecordChallengeAttemptFailureReason.INVALID_INPUT,
                "A valid attempt_id UUID and timezone-aware completed_at timestamp "
                "are required.",
            )
            return
        try:
            if not isinstance(input_data.attempt_id, str):
                raise ValueError
            submission_id = str(UUID(input_data.attempt_id))
        except TypeError, ValueError:
            self._fail(
                RecordChallengeAttemptFailureReason.INVALID_INPUT,
                "A valid attempt_id UUID and timezone-aware completed_at timestamp "
                "are required.",
            )
            return

        with self._unit_of_work.atomic():
            profile = self._profiles.get_by_user_id(input_data.user_id, for_update=True)
            if profile is None:
                self._fail(
                    RecordChallengeAttemptFailureReason.PROFILE_NOT_FOUND,
                    "Profile not found.",
                )
                return
            attempt = Attempt(
                submission_id=submission_id,
                profile_id=profile.record_id or profile.user_id,
                challenge_slug=input_data.challenge_slug,
                score=score,
                completed_at=completed_at,
            )
            if self._challenges.get_by_slug(attempt.challenge_slug) is None:
                self._fail(
                    RecordChallengeAttemptFailureReason.CHALLENGE_NOT_FOUND,
                    "Challenge not found.",
                )
                return

            stored, created = self._attempts.get_or_create(attempt)
            if not stored.matches_completion(
                attempt.profile_id,
                attempt.challenge_slug,
                attempt.score,
                attempt.completed_at,
            ):
                self._fail(
                    RecordChallengeAttemptFailureReason.ATTEMPT_CONFLICT,
                    "This attempt ID has already been used for a different "
                    "completion.",
                )
                return

            profile.add_score(attempt.challenge_slug, attempt.score)
            saved_profile = self._profiles.save(profile)
            output_data = self._build_output_data(stored, saved_profile, created)

        self._presenter.prepare_success_view(output_data)

    def _fail(self, reason: RecordChallengeAttemptFailureReason, message: str) -> None:
        self._presenter.prepare_fail_view(
            RecordChallengeAttemptFailureData(reason=reason, message=message)
        )

    def _build_output_data(
        self, attempt: Attempt, profile: Profile, created: bool
    ) -> RecordChallengeAttemptOutputData:
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
            created=created,
        )
