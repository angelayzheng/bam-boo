from collections.abc import Callable
from dataclasses import dataclass

from challenges.adapters.getChallenge.Controller import GetChallengeController
from challenges.adapters.getChallenge.Presenter import GetChallengePresenter
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
from challenges.useCases.getChallenge.Interactor import GetChallengeInteractor
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
from users.useCases.ports import (
    EmailValidator,
    ProfileDetailsRepository,
    TeamRepository,
)
from users.adapters.viewProfile.Controller import ViewProfileController
from users.adapters.viewProfile.Presenter import ViewProfilePresenter
from users.adapters.updateProfile.Controller import UpdateProfileController
from users.adapters.updateProfile.Presenter import UpdateProfilePresenter
from users.adapters.signUp.Controller import SignUpController
from users.adapters.signUp.Presenter import SignUpPresenter
from users.adapters.logIn.Controller import LogInController
from users.adapters.logIn.Presenter import LogInPresenter
from users.adapters.logOut.Controller import LogOutController
from users.adapters.logOut.Presenter import LogOutPresenter
from users.useCases.viewProfile.Interactor import ViewProfileInteractor
from users.useCases.updateProfile.Interactor import UpdateProfileInteractor
from users.useCases.ports import AuthenticationGateway
from users.useCases.signUp.Interactor import SignUpInteractor
from users.useCases.logIn.Interactor import LogInInteractor
from users.useCases.logOut.Interactor import LogOutInteractor


@dataclass(frozen=True, slots=True)
class GetCurrentUserUseCase:
    controller: GetCurrentUserController
    presenter: GetCurrentUserPresenter


@dataclass(frozen=True, slots=True)
class SignUpUseCase:
    controller: SignUpController
    presenter: SignUpPresenter


@dataclass(frozen=True, slots=True)
class LogInUseCase:
    controller: LogInController
    presenter: LogInPresenter


@dataclass(frozen=True, slots=True)
class LogOutUseCase:
    controller: LogOutController
    presenter: LogOutPresenter


@dataclass(frozen=True, slots=True)
class GetChallengeUseCase:
    controller: GetChallengeController
    presenter: GetChallengePresenter


@dataclass(frozen=True, slots=True)
class RecordChallengeAttemptUseCase:
    controller: RecordChallengeAttemptController
    presenter: RecordChallengeAttemptPresenter


@dataclass(frozen=True, slots=True)
class ManageChallengeRunUseCase:
    controller: ChallengeRunController
    presenter: ChallengeRunPresenter


@dataclass(frozen=True, slots=True)
class ViewProfileUseCase:
    controller: ViewProfileController
    presenter: ViewProfilePresenter


@dataclass(frozen=True, slots=True)
class UpdateProfileUseCase:
    controller: UpdateProfileController
    presenter: UpdateProfilePresenter


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
    profile_details: ProfileDetailsRepository | None = None
    teams: TeamRepository | None = None
    email_validator: EmailValidator | None = None

    def build_get_current_user_use_case(
        self, *, accounts: CurrentAccountGateway, csrf_token: Callable[[], str]
    ) -> GetCurrentUserUseCase:
        presenter = GetCurrentUserPresenter(csrf_token)
        interactor = GetCurrentUserInteractor(accounts=accounts, presenter=presenter)
        return GetCurrentUserUseCase(GetCurrentUserController(interactor), presenter)

    def build_sign_up_use_case(
        self, *, authentication: AuthenticationGateway, csrf_token: Callable[[], str]
    ) -> SignUpUseCase:
        presenter = SignUpPresenter(csrf_token)
        interactor = SignUpInteractor(
            authentication=authentication, presenter=presenter
        )
        return SignUpUseCase(SignUpController(interactor), presenter)

    def build_log_in_use_case(
        self, *, authentication: AuthenticationGateway, csrf_token: Callable[[], str]
    ) -> LogInUseCase:
        presenter = LogInPresenter(csrf_token)
        interactor = LogInInteractor(authentication=authentication, presenter=presenter)
        return LogInUseCase(LogInController(interactor), presenter)

    def build_log_out_use_case(
        self, *, authentication: AuthenticationGateway
    ) -> LogOutUseCase:
        presenter = LogOutPresenter()
        interactor = LogOutInteractor(
            authentication=authentication, presenter=presenter
        )
        return LogOutUseCase(LogOutController(interactor), presenter)

    def build_get_challenge_use_case(self) -> GetChallengeUseCase:
        presenter = GetChallengePresenter()
        interactor = GetChallengeInteractor(
            challenges=self.challenges,
            presenter=presenter,
        )
        return GetChallengeUseCase(
            controller=GetChallengeController(interactor),
            presenter=presenter,
        )

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

    def build_view_profile_use_case(self) -> ViewProfileUseCase:
        if self.profile_details is None:
            raise RuntimeError("Profile details repository is required.")
        presenter = ViewProfilePresenter()
        interactor = ViewProfileInteractor(
            profiles=self.profile_details, presenter=presenter
        )
        return ViewProfileUseCase(ViewProfileController(interactor), presenter)

    def build_update_profile_use_case(self) -> UpdateProfileUseCase:
        if (
            self.profile_details is None
            or self.teams is None
            or self.email_validator is None
        ):
            raise RuntimeError("Profile update dependencies are required.")
        presenter = UpdateProfilePresenter()
        interactor = UpdateProfileInteractor(
            profiles=self.profile_details,
            teams=self.teams,
            email_validator=self.email_validator,
            unit_of_work=self.unit_of_work,
            presenter=presenter,
        )
        return UpdateProfileUseCase(
            UpdateProfileController(interactor, presenter), presenter
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
    profile_details: ProfileDetailsRepository | None = None,
    teams: TeamRepository | None = None,
    email_validator: EmailValidator | None = None,
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
        profile_details=profile_details,
        teams=teams,
        email_validator=email_validator,
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
    from users.adapters.emailValidator import DjangoEmailValidator
    from users.adapters.repositories import (
        DjangoProfileDetailsRepository,
        DjangoProfileRepository,
        DjangoTeamRepository,
    )

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
        profile_details=DjangoProfileDetailsRepository(),
        teams=DjangoTeamRepository(),
        email_validator=DjangoEmailValidator(),
    )


def get_container() -> ApplicationContainer:
    global _container
    if _container is None:
        _container = build_django_container()
    return _container
