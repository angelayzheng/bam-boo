from datetime import datetime, timezone

from django.test import SimpleTestCase

from play.adapters.record_challenge_attempt.record_challenge_attempt_presenter import (
    RecordChallengeAttemptPresenter,
)
from play.domain.attempt import Attempt
from play.use_cases.record_challenge_attempt.record_challenge_attempt_data_access_interface import (
    AttemptConflictError,
    RecordedChallengeAttempt,
)
from play.use_cases.record_challenge_attempt.record_challenge_attempt_input_data import (
    RecordChallengeAttemptInputData,
)
from play.use_cases.record_challenge_attempt.record_challenge_attempt_interactor import (
    RecordChallengeAttemptInteractor,
)
from users.domain.profile import Profile

COMPLETED_AT = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
SUBMISSION_ID = "12345678-1234-5678-1234-567812345678"


class InMemoryChallengeAttemptDataAccess:
    def __init__(self, valid_slugs=()):
        self.valid_slugs = set(valid_slugs)
        self.records: dict[str, Attempt] = {}

    def challenge_exists(self, challenge_slug: str) -> bool:
        return challenge_slug in self.valid_slugs

    def record(self, attempt: Attempt) -> RecordedChallengeAttempt:
        existing = self.records.get(attempt.submission_id)
        if existing is not None and not existing.matches_completion(
            attempt.profile_id,
            attempt.challenge_slug,
            attempt.score,
            attempt.completed_at,
        ):
            raise AttemptConflictError(
                "This attempt ID has already been used for a different completion."
            )
        created = existing is None
        if created:
            self.records[attempt.submission_id] = attempt
        recorded = Attempt(
            submission_id=attempt.submission_id,
            profile_id=attempt.profile_id,
            challenge_slug=attempt.challenge_slug,
            score=attempt.score,
            completed_at=attempt.completed_at,
            received_at=COMPLETED_AT,
            record_id=1,
        )
        profile = Profile(
            user_id=attempt.profile_id,
            username="tester",
            scores={attempt.challenge_slug: attempt.score},
        )
        return RecordedChallengeAttempt(
            attempt=recorded,
            profile=profile,
            created=created,
        )


class RecordChallengeAttemptInteractorTests(SimpleTestCase):
    def build_interactor(self, data_access):
        presenter = RecordChallengeAttemptPresenter()
        interactor = RecordChallengeAttemptInteractor(data_access, presenter)
        return interactor, presenter

    def input_data(self, **overrides):
        values = {
            "user_id": 1,
            "challenge_slug": "greeting",
            "attempt_id": SUBMISSION_ID,
            "tone_correct": True,
            "action_correct": True,
            "tone_time": 3.5,
            "completed_at": COMPLETED_AT,
        }
        values.update(overrides)
        return RecordChallengeAttemptInputData(**values)

    def test_success_scores_with_domain_rules_and_prepares_201_view(self):
        data_access = InMemoryChallengeAttemptDataAccess(valid_slugs={"greeting"})
        interactor, presenter = self.build_interactor(data_access)

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 201)
        self.assertEqual(presenter.response_body["attempt"]["score"], 3)
        self.assertEqual(presenter.response_body["total_score"], 3)
        self.assertEqual(presenter.response_body["completed_challenges"], 1)

    def test_repeated_submission_prepares_200_view(self):
        data_access = InMemoryChallengeAttemptDataAccess(valid_slugs={"greeting"})
        interactor, presenter = self.build_interactor(data_access)
        interactor.execute(self.input_data())

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(len(data_access.records), 1)

    def test_conflicting_submission_prepares_409_view(self):
        data_access = InMemoryChallengeAttemptDataAccess(valid_slugs={"greeting"})
        interactor, presenter = self.build_interactor(data_access)
        interactor.execute(self.input_data())

        interactor.execute(self.input_data(action_correct=False))

        self.assertEqual(presenter.status_code, 409)
        self.assertEqual(
            presenter.response_body,
            {
                "detail": "This attempt ID has already been used for a different completion."
            },
        )

    def test_missing_challenge_prepares_404_view(self):
        interactor, presenter = self.build_interactor(
            InMemoryChallengeAttemptDataAccess(valid_slugs=set())
        )

        interactor.execute(self.input_data(challenge_slug="unknown"))

        self.assertEqual(presenter.status_code, 404)
        self.assertEqual(presenter.response_body, {"detail": "Challenge not found."})

    def test_naive_completion_time_prepares_400_view(self):
        interactor, presenter = self.build_interactor(
            InMemoryChallengeAttemptDataAccess(valid_slugs={"greeting"})
        )

        interactor.execute(self.input_data(completed_at=datetime(2026, 11, 19, 12)))

        self.assertEqual(presenter.status_code, 400)
