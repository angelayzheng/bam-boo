from collections.abc import Callable
from dataclasses import dataclass

from challenges.adapters.importChallengePackage.Controller import (
    ImportChallengePackageController,
)
from challenges.adapters.importChallengePackage.Presenter import (
    ImportChallengePackagePresenter,
)
from challenges.adapters.validateChallenges.Controller import (
    ValidateChallengesController,
)
from challenges.adapters.validateChallenges.Presenter import (
    ValidateChallengesPresenter,
)
from challenges.useCases.ports import (
    AudioValidator,
    ChallengeRepository,
    ChallengeValidationGateway,
    MediaStore,
    PackageArchiveExtractor,
    PackageSource,
)
from challenges.useCases.importChallengePackage.Interactor import (
    ImportChallengePackageInteractor,
)
from challenges.useCases.validateChallenges.Interactor import (
    ValidateChallengesInteractor,
)
from play.adapters.manageChallengeRun.Controller import ChallengeRunController
from play.adapters.manageChallengeRun.Presenter import ChallengeRunPresenter
from play.adapters.recordChallengeAttempt.Controller import (
    RecordChallengeAttemptController,
)
from play.adapters.recordChallengeAttempt.Presenter import (
    RecordChallengeAttemptPresenter,
)
from play.useCases.ports import (
    AttemptRepository,
    RunRepository,
    ToneMatcher,
    UnitOfWork,
)
from play.useCases.manageChallengeRun.Interactor import (
    ManageChallengeRunInteractor,
)
from play.useCases.recordChallengeAttempt.Interactor import (
    RecordChallengeAttemptInteractor,
)
from users.adapters.getCurrentUser.Controller import GetCurrentUserController
from users.adapters.getCurrentUser.Presenter import GetCurrentUserPresenter
from users.useCases.getCurrentUser.Interactor import GetCurrentUserInteractor
from users.useCases.ports import CurrentAccountGateway
from tone.useCases.ports import ToneVectorRepository
from users.useCases.ports import ProfileRepository


@dataclass(frozen=True, slots=True)
class GetCurrentUserUseCase:
    controller: GetCurrentUserController
    presenter: GetCurrentUserPresenter


@dataclass(frozen=True, slots=True)
class RecordChallengeAttemptUseCase:
    controller: RecordChallengeAttemptController
    presenter: RecordChallengeAttemptPresenter


@dataclass(frozen=True, slots=True)
class ManageChallengeRunUseCase:
    controller: ChallengeRunController
    presenter: ChallengeRunPresenter


@dataclass(frozen=True, slots=True)
class ImportChallengePackageUseCase:
    controller: ImportChallengePackageController
    presenter: ImportChallengePackagePresenter


@dataclass(frozen=True, slots=True)
class ValidateChallengesUseCase:
    controller: ValidateChallengesController
    presenter: ValidateChallengesPresenter


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    challenges: ChallengeRepository
    attempts: AttemptRepository
    runs: RunRepository
    profiles: ProfileRepository
    unit_of_work: UnitOfWork
    packages: PackageSource
    archives: PackageArchiveExtractor
    audio: AudioValidator
    media: MediaStore
    validation: ChallengeValidationGateway
    tone_matcher: ToneMatcher | None = None
    tone_vectors: ToneVectorRepository | None = None

    def build_get_current_user_use_case(
        self, *, accounts: CurrentAccountGateway, csrf_token: Callable[[], str]
    ) -> GetCurrentUserUseCase:
        presenter = GetCurrentUserPresenter(csrf_token)
        interactor = GetCurrentUserInteractor(accounts=accounts, presenter=presenter)
        return GetCurrentUserUseCase(GetCurrentUserController(interactor), presenter)

    def build_record_challenge_attempt_use_case(self) -> RecordChallengeAttemptUseCase:
        presenter = RecordChallengeAttemptPresenter()
        interactor = self._build_record_challenge_attempt_interactor(presenter)
        return RecordChallengeAttemptUseCase(
            controller=RecordChallengeAttemptController(interactor),
            presenter=presenter,
        )

    def _build_record_challenge_attempt_interactor(self, presenter):
        return RecordChallengeAttemptInteractor(
            runs=self.runs,
            attempts=self.attempts,
            profiles=self.profiles,
            unit_of_work=self.unit_of_work,
            presenter=presenter,
        )

    def build_manage_challenge_run_use_case(self) -> ManageChallengeRunUseCase:
        presenter = ChallengeRunPresenter()
        attempt_recorder = self._build_record_challenge_attempt_interactor(
            RecordChallengeAttemptPresenter()
        )
        interactor = ManageChallengeRunInteractor(
            challenges=self.challenges,
            runs=self.runs,
            attempt_recorder=attempt_recorder,
            unit_of_work=self.unit_of_work,
            tone_matcher=self.tone_matcher,
            presenter=presenter,
        )
        return ManageChallengeRunUseCase(
            controller=ChallengeRunController(interactor),
            presenter=presenter,
        )

    def build_import_challenge_package_use_case(self) -> ImportChallengePackageUseCase:
        presenter = ImportChallengePackagePresenter()
        interactor = ImportChallengePackageInteractor(
            challenges=self.challenges,
            packages=self.packages,
            archives=self.archives,
            audio=self.audio,
            media=self.media,
            unit_of_work=self.unit_of_work,
            presenter=presenter,
        )
        return ImportChallengePackageUseCase(
            controller=ImportChallengePackageController(interactor),
            presenter=presenter,
        )

    def build_validate_challenges_use_case(self) -> ValidateChallengesUseCase:
        presenter = ValidateChallengesPresenter()
        interactor = ValidateChallengesInteractor(
            validation=self.validation,
            presenter=presenter,
        )
        return ValidateChallengesUseCase(
            controller=ValidateChallengesController(interactor),
            presenter=presenter,
        )


def build_container(
    *,
    challenges: ChallengeRepository,
    attempts: AttemptRepository,
    runs: RunRepository,
    profiles: ProfileRepository,
    unit_of_work: UnitOfWork,
    packages: PackageSource,
    archives: PackageArchiveExtractor,
    audio: AudioValidator,
    media: MediaStore,
    validation: ChallengeValidationGateway,
    tone_matcher: ToneMatcher | None = None,
    tone_vectors: ToneVectorRepository | None = None,
) -> ApplicationContainer:
    """Collect infrastructure ports at the application composition boundary."""
    return ApplicationContainer(
        challenges=challenges,
        attempts=attempts,
        runs=runs,
        profiles=profiles,
        unit_of_work=unit_of_work,
        packages=packages,
        archives=archives,
        audio=audio,
        media=media,
        validation=validation,
        tone_matcher=tone_matcher,
        tone_vectors=tone_vectors,
    )


_container: ApplicationContainer | None = None


def build_django_container() -> ApplicationContainer:
    from challenges.adapters.archives import ZipPackageArchiveExtractor
    from challenges.adapters.audioValidator import FfprobeAudioValidator
    from challenges.adapters.challengeValidator import DjangoChallengeValidator
    from challenges.adapters.mediaStore import FileSystemMediaStore
    from challenges.adapters.packageSource import FileSystemPackageSource
    from challenges.adapters.repositories import DjangoChallengeRepository
    from play.adapters.repositories import DjangoAttemptRepository, DjangoRunRepository
    from play.adapters.unitOfWork import DjangoUnitOfWork
    from play.adapters.vectorToneMatcher import VectorToneMatcher
    from users.adapters.repositories import DjangoProfileRepository

    return build_container(
        challenges=DjangoChallengeRepository(),
        attempts=DjangoAttemptRepository(),
        runs=DjangoRunRepository(),
        profiles=DjangoProfileRepository(),
        unit_of_work=DjangoUnitOfWork(),
        packages=FileSystemPackageSource(),
        archives=ZipPackageArchiveExtractor(),
        audio=FfprobeAudioValidator(),
        media=FileSystemMediaStore(),
        validation=DjangoChallengeValidator(),
        tone_matcher=VectorToneMatcher(),
    )


def get_container() -> ApplicationContainer:
    global _container
    if _container is None:
        _container = build_django_container()
    return _container
