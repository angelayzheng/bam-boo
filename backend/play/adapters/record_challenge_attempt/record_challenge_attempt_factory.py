from dataclasses import dataclass

from play.use_cases.record_challenge_attempt.record_challenge_attempt_interactor import (
    RecordChallengeAttemptInteractor,
)

from .django_challenge_attempt_data_access import DjangoChallengeAttemptDataAccess
from .record_challenge_attempt_controller import RecordChallengeAttemptController
from .record_challenge_attempt_presenter import RecordChallengeAttemptPresenter


@dataclass(frozen=True, slots=True)
class RecordChallengeAttemptUseCase:
    controller: RecordChallengeAttemptController
    presenter: RecordChallengeAttemptPresenter


def build_record_challenge_attempt_use_case() -> RecordChallengeAttemptUseCase:
    presenter = RecordChallengeAttemptPresenter()
    interactor = RecordChallengeAttemptInteractor(
        data_access=DjangoChallengeAttemptDataAccess(),
        presenter=presenter,
    )
    return RecordChallengeAttemptUseCase(
        controller=RecordChallengeAttemptController(interactor),
        presenter=presenter,
    )
