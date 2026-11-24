from contextlib import nullcontext
from datetime import datetime, timezone

from django.test import SimpleTestCase

from play.adapters.recordChallengeAttempt.Presenter import (
    RecordChallengeAttemptPresenter,
)
from play.domain.Run import Run
from play.domain.attempt import Attempt
from play.use_cases.recordChallengeAttempt.InputData import (
    RecordChallengeAttemptInputData,
)
from play.use_cases.recordChallengeAttempt.Interactor import (
    RecordChallengeAttemptInteractor,
)
from play.use_cases.recordChallengeAttempt.OutputData import (
    RecordChallengeAttemptFailureReason,
)
from users.domain.profile import Profile

COMPLETED_AT = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
SUBMISSION_ID = "12345678-1234-5678-1234-567812345678"


class InMemoryRunRepository:
    def __init__(self, runs=()):
        self.records: dict[str, Run] = {run.id: run for run in runs}

    def get_by_id(self, run_id, *, for_update=False):
        return self.records.get(run_id)

    def create(self, run):
        self.records[run.id] = run
        return run

    def save(self, run):
        self.records[run.id] = run
        return run


class InMemoryAttemptRepository:
    def __init__(self):
        self.records: dict[str, Attempt] = {}
        self.get_or_create_calls = 0

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

    def get_or_create(self, attempt):
        self.get_or_create_calls += 1
        existing = self.records.get(attempt.submission_id)
        if existing is not None:
            return existing, False
        return self.save(attempt), True

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
    def build_interactor(self, runs, attempts, profiles, presenter=None):
        presenter = presenter or RecordChallengeAttemptPresenter()
        interactor = RecordChallengeAttemptInteractor(
            runs=runs,
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
        }
        values.update(overrides)
        return RecordChallengeAttemptInputData(**values)

    def completed_run(self, **overrides):
        values = {
            "id": SUBMISSION_ID,
            "challenge_slug": "greeting",
            "current_node": "a1",
            "created_at": datetime(2026, 11, 19, 11, tzinfo=timezone.utc),
            "stage": "completed",
            "user_id": None,
            "score": 3,
            "completed_at": COMPLETED_AT,
        }
        values.update(overrides)
        run = Run.__new__(Run)
        for field, value in values.items():
            setattr(run, field, value)
        return run

    def test_success_records_completed_run_and_prepares_201_view(self):
        interactor, presenter = self.build_interactor(
            InMemoryRunRepository([self.completed_run()]),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 201)
        self.assertEqual(presenter.response_body["attempt"]["score"], 3)
        self.assertEqual(presenter.response_body["total_score"], 3)
        self.assertEqual(presenter.response_body["completed_challenges"], 1)

    def test_repeated_submission_prepares_200_view(self):
        attempts = InMemoryAttemptRepository()
        interactor, presenter = self.build_interactor(
            InMemoryRunRepository([self.completed_run()]),
            attempts,
            InMemoryProfileRepository(),
        )
        interactor.execute(self.input_data())

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(attempts.get_or_create_calls, 2)
        self.assertEqual(len(attempts.records), 1)

    def test_conflicting_submission_prepares_409_view(self):
        attempts = InMemoryAttemptRepository()
        attempts.records[SUBMISSION_ID] = Attempt(
            submission_id=SUBMISSION_ID,
            profile_id=2,
            challenge_slug="greeting",
            score=3,
            completed_at=COMPLETED_AT,
            received_at=COMPLETED_AT,
            record_id=1,
        )
        interactor, presenter = self.build_interactor(
            InMemoryRunRepository([self.completed_run()]),
            attempts,
            InMemoryProfileRepository(),
        )
        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 409)
        self.assertEqual(
            presenter.response_body,
            {
                "detail": "This attempt ID has already been used for a different completion."
            },
        )

    def test_missing_challenge_prepares_404_view(self):
        interactor, presenter = self.build_interactor(
            InMemoryRunRepository(),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 404)
        self.assertEqual(
            presenter.response_body, {"detail": "Completed attempt not found."}
        )

    def test_missing_completion_time_is_rejected(self):
        interactor, presenter = self.build_interactor(
            InMemoryRunRepository(
                [self.completed_run(completed_at=datetime(2026, 11, 19, 12))]
            ),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 409)

    def test_uncompleted_run_is_rejected(self):
        interactor, presenter = self.build_interactor(
            InMemoryRunRepository([self.completed_run(stage="action")]),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
        )

        interactor.execute(self.input_data())

        self.assertEqual(presenter.status_code, 409)
        self.assertEqual(
            presenter.response_body, {"detail": "The attempt is not complete."}
        )

    def test_failure_carries_semantic_reason_without_status_code(self):
        output_boundary = RecordingOutputBoundary()
        interactor, _ = self.build_interactor(
            InMemoryRunRepository(),
            InMemoryAttemptRepository(),
            InMemoryProfileRepository(),
            presenter=output_boundary,
        )

        interactor.execute(self.input_data())

        self.assertEqual(
            output_boundary.failure.reason,
            RecordChallengeAttemptFailureReason.RUN_NOT_FOUND,
        )
        self.assertFalse(hasattr(output_boundary.failure, "status_code"))
