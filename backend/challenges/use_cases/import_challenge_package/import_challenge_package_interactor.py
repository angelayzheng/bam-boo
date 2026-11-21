from contextlib import ExitStack
from dataclasses import dataclass

from challenges.domain.challenge import Challenge
from challenges.domain.challenge_package import (
    AudioValidationError,
    ChallengePackageError,
    challenge_from_package,
)
from challenges.use_cases.ports import (
    AudioValidator,
    ChallengeRepository,
    LoadedChallengePackage,
    MediaStore,
    PackageArchiveExtractor,
    PackageSource,
)
from play.use_cases.ports import UnitOfWork

from .import_challenge_package_input_boundary import (
    ImportChallengePackageInputBoundary,
)
from .import_challenge_package_input_data import ImportChallengePackageInputData
from .import_challenge_package_output_boundary import (
    ImportChallengePackageOutputBoundary,
)
from .import_challenge_package_output_data import (
    ImportChallengePackageFailureData,
    ImportChallengePackageFailureReason,
    ImportChallengePackageOutputData,
    ImportChallengePackageResultData,
)


@dataclass(frozen=True, slots=True)
class _PreparedPackage:
    challenge: Challenge
    source: LoadedChallengePackage


class ImportChallengePackageInteractor(ImportChallengePackageInputBoundary):
    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        packages: PackageSource,
        archives: PackageArchiveExtractor,
        audio: AudioValidator,
        media: MediaStore,
        unit_of_work: UnitOfWork,
        presenter: ImportChallengePackageOutputBoundary,
    ):
        self._challenges = challenges
        self._packages = packages
        self._archives = archives
        self._audio = audio
        self._media = media
        self._unit_of_work = unit_of_work
        self._presenter = presenter

    def execute(self, input_data: ImportChallengePackageInputData) -> None:
        with ExitStack() as stack:
            prepared: list[_PreparedPackage] = []
            for location in input_data.locations:
                try:
                    folder = location.folder
                    if location.archive is not None:
                        folder = stack.enter_context(
                            self._archives.extract(location.archive)
                        )
                    prepared.append(self._prepare(folder))
                except (ChallengePackageError, AudioValidationError) as exc:
                    self._fail(
                        ImportChallengePackageFailureReason.INVALID_PACKAGE, str(exc)
                    )
                    return

            duplicate = self._find_duplicate(prepared)
            if duplicate is not None:
                self._fail(
                    ImportChallengePackageFailureReason.INVALID_PACKAGE, duplicate
                )
                return

            selected: list[_PreparedPackage] = []
            skipped: set[int] = set()
            replaced: dict[int, bool] = {}
            for index, item in enumerate(prepared):
                existing = self._challenges.get_by_slug(item.challenge.slug)
                replaced[index] = existing is not None
                if existing is not None and not input_data.replace:
                    if input_data.skip_existing:
                        skipped.add(index)
                        continue
                    self._fail(
                        ImportChallengePackageFailureReason.ALREADY_EXISTS,
                        f"Challenge {item.challenge.slug!r} already exists; "
                        "select Replace to update it.",
                    )
                    return
                selected.append(item)

            if selected:
                try:
                    with self._unit_of_work.atomic():
                        for item in selected:
                            self._challenges.save(item.challenge)
                        self._media.install(selected, replace=input_data.replace)
                except ChallengePackageError as exc:
                    self._fail(
                        ImportChallengePackageFailureReason.INVALID_PACKAGE, str(exc)
                    )
                    return

            results = tuple(
                ImportChallengePackageResultData(
                    slug=item.challenge.slug,
                    name=item.challenge.name,
                    challenge_date=item.challenge.challenge_date,
                    turn_count=item.source.turn_count,
                    replaced=replaced[index] and index not in skipped,
                    skipped=index in skipped,
                )
                for index, item in enumerate(prepared)
            )

        self._presenter.prepare_success_view(ImportChallengePackageOutputData(results))

    def _prepare(self, folder) -> _PreparedPackage:
        try:
            source = self._packages.load(folder)
        except (OSError, TypeError, ValueError) as exc:
            raise ChallengePackageError(f"Invalid challenge package: {exc}") from exc

        try:
            challenge = challenge_from_package(
                source.metadata, source.conversation_tree
            )
        except ChallengePackageError as exc:
            raise ChallengePackageError(
                f"Invalid challenge package {folder.name}: {exc}"
            ) from exc

        try:
            self._validate_audio(source)
        except AudioValidationError as exc:
            raise ChallengePackageError(
                f"Invalid challenge package {folder.name}: {exc}"
            ) from exc
        return _PreparedPackage(challenge=challenge, source=source)

    def _validate_audio(self, source: LoadedChallengePackage) -> None:
        for relative in sorted(source.files):
            if not relative.startswith("audio/"):
                continue
            try:
                self._audio.validate(source.folder, relative)
            except AudioValidationError as exc:
                raise AudioValidationError(f"{relative}: {exc}") from exc

    def _find_duplicate(self, prepared: list[_PreparedPackage]) -> str | None:
        for field in ("name", "slug"):
            seen = set()
            for item in prepared:
                value = getattr(item.challenge, field)
                if value in seen:
                    return f"Selected challenges have a duplicate {field}: {value}"
                seen.add(value)
        return None

    def _fail(self, reason: ImportChallengePackageFailureReason, message: str) -> None:
        self._presenter.prepare_fail_view(
            ImportChallengePackageFailureData(reason=reason, message=message)
        )
