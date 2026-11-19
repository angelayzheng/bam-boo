from contextlib import nullcontext
from datetime import date, datetime, timezone

from django.test import SimpleTestCase

from challenges.domain.challenge import Challenge
from play.adapters.record_challenge_attempt.record_challenge_attempt_presenter import (
    RecordChallengeAttemptPresenter,
)
from play.domain.attempt import Attempt
from play.use_cases.record_challenge_attempt.record_challenge_attempt_input_data import (
    RecordChallengeAttemptInputData,
)
from play.use_cases.record_challenge_attempt.record_challenge_attempt_interactor import (
    RecordChallengeAttemptInteractor,
)
from play.use_cases.record_challenge_attempt.record_challenge_attempt_output_data import (
    RecordChallengeAttemptFailureReason,
)
from users.domain.profile import Profile

COMPLETED_AT = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
SUBMISSION_ID = "12345678-1234-5678-1234-567812345678"


class InMemoryChallengeRepository:
    def __init__(self, valid_slugs=()):
        self.slugs = set(valid_slugs)

    def list(self):
        return [self._challenge(slug) for slug in self.slugs]

    def get_by_slug(self, slug):
        return self._challenge(slug) if slug in self.slugs else None

    def get_by_date(self, challenge_date):
        return None

    def save(self, challenge):
        self.slugs.add(challenge.slug)
        return challenge

    def _challenge(self, slug):
        return Challenge(
            name=slug,
            slug=slug,
            challenge_date=date(2026, 11, 19),
            difficulty=1,
            category="work",
            tone="calm",
            required_action="reply",
        )


class InMemoryAttemptRepository:
    def __init__(self):
        self.records: dict[str, Attempt] = {}

    def get_by_submission_id(self, submission_id):
        return self.records.get(submission_id)

    def save(self, attempt):
        record = Attempt(
            submission_id=attempt.submission_id,
            profile_id=attempt.profile_id,
            challenge_slug=attempt.challenge_slug,
            score=attempt.score,
            completed_at=attempt.completed_at,
            received_at=COMPLETED_AT,
            record_id=len(self.records) + 1,
        )
        self.records[attempt.submission_id] = record
        return record

    def list_for_profile(self, profile_id):
        return [
            record
            for record in self.records.values()
            if record.profile_id == profile_id
        ]


class InMemoryProfileRepository:
    def __init__(self, user_id=1, username="tester"):
        self.profile = Profile(user_id=user_id, username=username)

    def get_by_user_id(self, user_id, *, for_update=False):
        return self.profile if self.profile.user_id == user_id else None

    def get_by_username(self, username):
        return self.profile if self.profile.username == username else None

    def list_top(self, limit):
        return [self.profile][:limit]

    def save(self, profile):
        self.profile = profile
        return profile


class InMemoryUnitOfWork:
    def atomic(self):
        return nullcontext()


class RecordingOutputBoundary:
    def __init__(self):
        self.success = None
        self.failure = None

    def prepare_success_view(self, output_data):
        self.success = output_data

    def prepare_fail_view(self, failure):
        self.failure = failure


class RecordChallengeAttemptInteractorTests(SimpleTestCase):
    def build_interactor(self, challenges, attempts, profiles, presenter=None):
        presenter = presenter or RecordChallengeAttemptPresenter()
        interactor = RecordChallengeAttemptInteractor(
            challenges=challenges,
            attempts=attempts,
            profiles=profiles,
            unit_of_work=InMemoryUnitOfWork(),
            presenter=presenter,
        )
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
        interactor, presenter = self.build_interactor(
            InMemoryChallengeRepository({"greeting"}),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 201)
        self.assertEqual(presenter.response_body["attempt"]["score"], 3)
        self.assertEqual(presenter.response_body["total_score"], 3)
        self.assertEqual(presenter.response_body["completed_challenges"], 1)

    def test_repeated_submission_prepares_200_view(self):
        interactor, presenter = self.build_interactor(
            InMemoryChallengeRepository({"greeting"}),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )
        interactor.execute(self.input_data())

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 200)

    def test_conflicting_submission_prepares_409_view(self):
        interactor, presenter = self.build_interactor(
            InMemoryChallengeRepository({"greeting"}),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )
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
            InMemoryChallengeRepository(),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )

        interactor.execute(self.input_data(challenge_slug="unknown"))

        self.assertEqual(presenter.status_code, 404)
        self.assertEqual(presenter.response_body, {"detail": "Challenge not found."})

    def test_naive_completion_time_prepares_400_view(self):
        interactor, presenter = self.build_interactor(
            InMemoryChallengeRepository({"greeting"}),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )

        interactor.execute(self.input_data(completed_at=datetime(2026, 11, 19, 12)))

        self.assertEqual(presenter.status_code, 400)

    def test_failure_carries_semantic_reason_without_status_code(self):
        output_boundary = RecordingOutputBoundary()
        interactor, _ = self.build_interactor(
            InMemoryChallengeRepository(),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
            presenter=output_boundary,
        )

        interactor.execute(self.input_data())

        self.assertEqual(
            output_boundary.failure.reason,
            RecordChallengeAttemptFailureReason.CHALLENGE_NOT_FOUND,
        )
        self.assertFalse(hasattr(output_boundary.failure, "status_code"))
