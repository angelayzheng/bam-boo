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
from challenges.use_cases.ports import (
    AudioValidator,
    ChallengeRepository,
    ChallengeValidationGateway,
    MediaStore,
    PackageArchiveExtractor,
    PackageSource,
)
from challenges.use_cases.importChallengePackage.Interactor import (
    ImportChallengePackageInteractor,
)
from challenges.use_cases.validateChallenges.Interactor import (
    ValidateChallengesInteractor,
)
from play.adapters.record_challenge_attempt.record_challenge_attempt_controller import (
    RecordChallengeAttemptController,
)
from play.adapters.record_challenge_attempt.record_challenge_attempt_presenter import (
    RecordChallengeAttemptPresenter,
)
from play.use_cases.ports import AttemptRepository, ToneMatcher, UnitOfWork
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
    profiles: ProfileRepository
    unit_of_work: UnitOfWork
    packages: PackageSource
    archives: PackageArchiveExtractor
    audio: AudioValidator
    media: MediaStore
    validation: ChallengeValidationGateway
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
            challenges=self.challenges,
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
    profiles: ProfileRepository,
    unit_of_work: UnitOfWork,
    packages: PackageSource,
    archives: PackageArchiveExtractor,
    audio: AudioValidator,
    media: MediaStore,
    validation: ChallengeValidationGateway,
    tone_matcher: ToneMatcher | None = None,
    tone_vectors: ToneVectorRepository | None = None,
    auth: AuthGateway | None = None,
    groups: GroupRepository | None = None,
) -> ApplicationContainer:
    """Collect infrastructure ports at the application composition boundary."""
    return ApplicationContainer(
        challenges=challenges,
        attempts=attempts,
        profiles=profiles,
        unit_of_work=unit_of_work,
        packages=packages,
        archives=archives,
        audio=audio,
        media=media,
        validation=validation,
        tone_matcher=tone_matcher,
        tone_vectors=tone_vectors,
        auth=auth,
        groups=groups,
    )


_container: ApplicationContainer | None = None


def build_django_container() -> ApplicationContainer:
    from challenges.adapters.archives import ZipPackageArchiveExtractor
    from challenges.adapters.AudioValidator import FfprobeAudioValidator
    from challenges.adapters.ChallengeValidator import DjangoChallengeValidator
    from challenges.adapters.MediaStore import FileSystemMediaStore
    from challenges.adapters.PackageSource import FileSystemPackageSource
    from challenges.adapters.repositories import DjangoChallengeRepository
    from play.adapters.repositories import DjangoAttemptRepository
    from play.adapters.unit_of_work import DjangoUnitOfWork
    from users.adapters.repositories import DjangoProfileRepository

    return build_container(
        challenges=DjangoChallengeRepository(),
        attempts=DjangoAttemptRepository(),
        profiles=DjangoProfileRepository(),
        unit_of_work=DjangoUnitOfWork(),
        packages=FileSystemPackageSource(),
        archives=ZipPackageArchiveExtractor(),
        audio=FfprobeAudioValidator(),
        media=FileSystemMediaStore(),
        validation=DjangoChallengeValidator(),
    )


def get_container() -> ApplicationContainer:
    global _container
    if _container is None:
        _container = build_django_container()
    return _container
