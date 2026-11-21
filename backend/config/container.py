from dataclasses import dataclass

from challenges.use_cases.ports import ChallengeRepository, MediaStore
from play.adapters.manage_challenge_run.controller import ChallengeRunController
from play.adapters.manage_challenge_run.presenter import ChallengeRunPresenter
from play.adapters.record_challenge_attempt.record_challenge_attempt_controller import (
    RecordChallengeAttemptController,
)
from play.adapters.record_challenge_attempt.record_challenge_attempt_presenter import (
    RecordChallengeAttemptPresenter,
)
from play.use_cases.ports import (
    AttemptRepository,
    RunRepository,
    ToneMatcher,
    UnitOfWork,
)
from play.use_cases.manage_challenge_run.interactor import (
    ManageChallengeRunInteractor,
)
from play.use_cases.record_challenge_attempt.record_challenge_attempt_interactor import (
    RecordChallengeAttemptInteractor,
)
from tone.use_cases.ports import ToneVectorRepository
from users.use_cases.ports import AuthGateway, GroupRepository, ProfileRepository


@dataclass(frozen=True, slots=True)
class RecordChallengeAttemptUseCase:
    controller: RecordChallengeAttemptController
    presenter: RecordChallengeAttemptPresenter


@dataclass(frozen=True, slots=True)
class ManageChallengeRunUseCase:
    controller: ChallengeRunController
    presenter: ChallengeRunPresenter


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    challenges: ChallengeRepository
    attempts: AttemptRepository
    runs: RunRepository
    profiles: ProfileRepository
    unit_of_work: UnitOfWork
    media: MediaStore | None = None
    tone_matcher: ToneMatcher | None = None
    tone_vectors: ToneVectorRepository | None = None
    auth: AuthGateway | None = None
    groups: GroupRepository | None = None

    def build_record_challenge_attempt_use_case(self) -> RecordChallengeAttemptUseCase:
        presenter = RecordChallengeAttemptPresenter()
        interactor = RecordChallengeAttemptInteractor(
            challenges=self.challenges,
            attempts=self.attempts,
            profiles=self.profiles,
            unit_of_work=self.unit_of_work,
            presenter=presenter,
        )
        return RecordChallengeAttemptUseCase(
            controller=RecordChallengeAttemptController(interactor),
            presenter=presenter,
        )

    def build_manage_challenge_run_use_case(self) -> ManageChallengeRunUseCase:
        presenter = ChallengeRunPresenter()
        interactor = ManageChallengeRunInteractor(
            challenges=self.challenges,
            runs=self.runs,
            attempts=self.attempts,
            profiles=self.profiles,
            unit_of_work=self.unit_of_work,
            tone_matcher=self.tone_matcher,
            presenter=presenter,
        )
        return ManageChallengeRunUseCase(
            controller=ChallengeRunController(interactor),
            presenter=presenter,
        )


def build_container(
    *,
    challenges: ChallengeRepository,
    attempts: AttemptRepository,
    runs: RunRepository,
    profiles: ProfileRepository,
    unit_of_work: UnitOfWork,
    media: MediaStore | None = None,
    tone_matcher: ToneMatcher | None = None,
    tone_vectors: ToneVectorRepository | None = None,
    auth: AuthGateway | None = None,
    groups: GroupRepository | None = None,
) -> ApplicationContainer:
    """Collect infrastructure ports at the application composition boundary."""
    return ApplicationContainer(
        challenges=challenges,
        attempts=attempts,
        runs=runs,
        profiles=profiles,
        unit_of_work=unit_of_work,
        media=media,
        tone_matcher=tone_matcher,
        tone_vectors=tone_vectors,
        auth=auth,
        groups=groups,
    )


_container: ApplicationContainer | None = None


def build_django_container() -> ApplicationContainer:
    from challenges.adapters.repositories import DjangoChallengeRepository
    from play.adapters.repositories import DjangoAttemptRepository, DjangoRunRepository
    from play.adapters.unit_of_work import DjangoUnitOfWork
    from play.adapters.vector_tone_matcher import VectorToneMatcher
    from users.adapters.repositories import DjangoProfileRepository

    return build_container(
        challenges=DjangoChallengeRepository(),
        attempts=DjangoAttemptRepository(),
        runs=DjangoRunRepository(),
        profiles=DjangoProfileRepository(),
        unit_of_work=DjangoUnitOfWork(),
        tone_matcher=VectorToneMatcher(),
    )


def get_container() -> ApplicationContainer:
    global _container
    if _container is None:
        _container = build_django_container()
    return _container
