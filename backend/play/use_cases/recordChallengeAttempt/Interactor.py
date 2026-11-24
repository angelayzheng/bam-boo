from datetime import datetime
from uuid import UUID

from play.domain.attempt import Attempt
from play.use_cases.ports import (
    AttemptRecordingError,
    AttemptRepository,
    RunRepository,
    UnitOfWork,
)
from users.domain.profile import Profile
from users.use_cases.ports import ProfileRepository

from .InputBoundary import RecordChallengeAttemptInputBoundary
from .InputData import RecordChallengeAttemptInputData
from .OutputBoundary import RecordChallengeAttemptOutputBoundary
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
        runs: RunRepository,
        attempts: AttemptRepository,
        profiles: ProfileRepository,
        unit_of_work: UnitOfWork,
        presenter: RecordChallengeAttemptOutputBoundary,
    ):
        self._runs = runs
        self._attempts = attempts
        self._profiles = profiles
        self._unit_of_work = unit_of_work
        self._presenter = presenter

    def execute(self, input_data: RecordChallengeAttemptInputData) -> None:
        try:
            if not isinstance(input_data.attempt_id, str):
                raise ValueError
            attempt_id = str(UUID(input_data.attempt_id))
        except TypeError, ValueError:
            self._fail(
                RecordChallengeAttemptFailureReason.INVALID_INPUT,
                "attempt_id must be a valid UUID.",
            )
            return

        try:
            with self._unit_of_work.atomic():
                run = self._runs.get_by_id(attempt_id, for_update=True)
                if run is None or run.challenge_slug != input_data.challenge_slug:
                    self._reject(
                        RecordChallengeAttemptFailureReason.RUN_NOT_FOUND,
                        "Completed attempt not found.",
                    )
                if run.stage != "completed":
                    self._reject(
                        RecordChallengeAttemptFailureReason.RUN_INCOMPLETE,
                        "The attempt is not complete.",
                    )
                if not self._valid_completion(run):
                    self._reject(
                        RecordChallengeAttemptFailureReason.RUN_INCOMPLETE,
                        "The attempt is not complete.",
                    )
                if run.user_id not in (None, input_data.user_id):
                    self._reject(
                        RecordChallengeAttemptFailureReason.RUN_FORBIDDEN,
                        "This completed attempt belongs to another account.",
                    )

                if run.user_id is None:
                    run.user_id = input_data.user_id
                    self._runs.save(run)
                attempt, profile, created = self.record_completed_run(run)
                output_data = self._build_output_data(attempt, profile, created)
        except _RecordFailure as exc:
            self._presenter.prepare_fail_view(exc.failure)
            return
        except AttemptRecordingError as exc:
            self._fail(RecordChallengeAttemptFailureReason(exc.reason), exc.message)
            return

        self._presenter.prepare_success_view(output_data)

    def record_completed_run(self, run):
        """Persist an authenticated completed run within the caller's transaction."""
        if run.user_id is None:
            raise AttemptRecordingError(
                RecordChallengeAttemptFailureReason.PROFILE_NOT_FOUND.value,
                "A completed run must belong to a user to be recorded.",
            )
        if run.stage != "completed" or not self._valid_completion(run):
            raise AttemptRecordingError(
                RecordChallengeAttemptFailureReason.RUN_INCOMPLETE.value,
                "The attempt is not complete.",
            )
        profile = self._profiles.get_by_user_id(run.user_id, for_update=True)
        if profile is None:
            raise AttemptRecordingError(
                RecordChallengeAttemptFailureReason.PROFILE_NOT_FOUND.value,
                "Profile not found.",
            )
        attempt = Attempt(
            submission_id=run.id,
            profile_id=profile.record_id or profile.user_id,
            challenge_slug=run.challenge_slug,
            score=run.score,
            completed_at=run.completed_at,
        )
        stored, created = self._attempts.get_or_create(attempt)
        if not stored.matches_completion(
            attempt.profile_id,
            attempt.challenge_slug,
            attempt.score,
            attempt.completed_at,
        ):
            raise AttemptRecordingError(
                RecordChallengeAttemptFailureReason.ATTEMPT_CONFLICT.value,
                "This attempt ID has already been used for a different completion.",
            )
        profile.add_score(run.challenge_slug, run.score)
        return stored, self._profiles.save(profile), created

    @staticmethod
    def _valid_completion(run) -> bool:
        return (
            isinstance(run.completed_at, datetime)
            and run.completed_at.utcoffset() is not None
            and isinstance(run.score, int)
            and not isinstance(run.score, bool)
            and run.score >= 0
        )

    def _fail(self, reason: RecordChallengeAttemptFailureReason, message: str) -> None:
        self._presenter.prepare_fail_view(
            RecordChallengeAttemptFailureData(reason=reason, message=message)
        )

    @staticmethod
    def _reject(reason: RecordChallengeAttemptFailureReason, message: str) -> None:
        raise _RecordFailure(
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


class _RecordFailure(Exception):
    def __init__(self, failure: RecordChallengeAttemptFailureData):
        super().__init__(failure.message)
        self.failure = failure
