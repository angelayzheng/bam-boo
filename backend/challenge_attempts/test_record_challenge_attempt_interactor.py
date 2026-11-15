from datetime import datetime, timezone
from unittest import TestCase

from challenge_attempts.interface_adapter.record_challenge_attempt.record_challenge_attempt_presenter import (
    RecordChallengeAttemptPresenter,
)
from challenge_attempts.use_case.record_challenge_attempt.record_challenge_attempt_data_access_interface import (
    AttemptConflictError,
    RecordChallengeAttemptDataAccessInterface,
)
from challenge_attempts.use_case.record_challenge_attempt.record_challenge_attempt_input_data import (
    RecordChallengeAttemptInputData,
)
from challenge_attempts.use_case.record_challenge_attempt.record_challenge_attempt_interactor import (
    RecordChallengeAttemptInteractor,
)
from challenge_attempts.use_case.record_challenge_attempt.record_challenge_attempt_output_data import (
    AttemptOutputData,
    RecordChallengeAttemptOutputData,
)


class InMemoryChallengeAttemptDAO(RecordChallengeAttemptDataAccessInterface):
    def __init__(self, valid_slugs=None):
        self.valid_slugs = set(valid_slugs or [])
        self.records = {}

    def challenge_exists(self, challenge_slug: str) -> bool:
        return challenge_slug in self.valid_slugs

    def save_attempt_and_update_score(
        self, *, user_id, challenge_slug, attempt_uuid, score, completed_at
    ) -> RecordChallengeAttemptOutputData:
        existing = self.records.get(attempt_uuid)
        if existing is not None:
            if existing != (user_id, challenge_slug, score, completed_at):
                raise AttemptConflictError(
                    "This attempt ID has already been used for a different completion."
                )
            created = False
        else:
            self.records[attempt_uuid] = (user_id, challenge_slug, score, completed_at)
            created = True

        return RecordChallengeAttemptOutputData(
            user_id=user_id,
            username="tester",
            avatar="panda",
            total_score=score,
            completed_challenges=1,
            scores={challenge_slug: score},
            attempt=AttemptOutputData(
                id=1,
                attempt_id=attempt_uuid,
                challenge_slug=challenge_slug,
                score=score,
                completed_at=completed_at,
                received_at=completed_at,
            ),
            created=created,
        )


class RecordChallengeAttemptInteractorTests(TestCase):
    def test_success_prepares_201_view_without_django(self):
        dao = InMemoryChallengeAttemptDAO(valid_slugs={"greeting"})
        presenter = RecordChallengeAttemptPresenter()
        interactor = RecordChallengeAttemptInteractor(
            user_data_access_object=dao, presenter=presenter
        )

        interactor.execute(
            RecordChallengeAttemptInputData(
                user_id=1,
                challenge_slug="greeting",
                attempt_id="12345678-1234-5678-1234-567812345678",
                tone_correct=True,
                action_correct=True,
                tone_time=3.5,
                completed_at=datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc),
            )
        )

        self.assertEqual(presenter.status_code, 201)
        self.assertEqual(presenter.response_body["attempt"]["score"], 3)

    def test_missing_challenge_prepares_404_view(self):
        dao = InMemoryChallengeAttemptDAO(valid_slugs=set())
        presenter = RecordChallengeAttemptPresenter()
        interactor = RecordChallengeAttemptInteractor(
            user_data_access_object=dao, presenter=presenter
        )

        interactor.execute(
            RecordChallengeAttemptInputData(
                user_id=1,
                challenge_slug="unknown",
                attempt_id="12345678-1234-5678-1234-567812345678",
                tone_correct=True,
                action_correct=False,
                tone_time=12.0,
                completed_at=datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc),
            )
        )

        self.assertEqual(presenter.status_code, 404)
        self.assertEqual(presenter.response_body, {"detail": "Challenge not found."})
