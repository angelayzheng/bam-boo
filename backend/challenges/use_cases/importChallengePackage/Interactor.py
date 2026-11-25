from contextlib import ExitStack
from dataclasses import dataclass

from challenges.domain.challenge import Challenge
from challenges.domain.challengePackage import (
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

from .InputBoundary import (
    ImportChallengePackageInputBoundary,
)
from .InputData import ImportChallengePackageInputData
from .OutputBoundary import (
    ImportChallengePackageOutputBoundary,
)
from .OutputData import (
    ImportChallengePackageFailureData,
    ImportChallengePackageFailureReason,
    ImportChallengePackageOutputData,
    ImportChallengePackageResultData,
)


@dataclass(frozen=True, slots=True)
class _PreparedPackage:
    challenge: Challenge
    source: LoadedChallengePackage

    @property
    def turn_count(self) -> int:
        return self.source.turn_count


@dataclass(frozen=True, slots=True)
class _SkippedPackage:
    challenge: Challenge
    turn_count: int


_ImportPackage = _PreparedPackage | _SkippedPackage


def _turn_count(tree) -> int:
    if tree is None:
        return 0
    return 1 + sum(_turn_count(child) for child in tree.children)


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
            packages: list[_ImportPackage] = []
            for location in input_data.locations:
                try:
                    folder = location.folder
                    if location.archive is not None:
                        folder = stack.enter_context(
                            self._archives.extract(location.archive)
                        )
                    if input_data.skip_existing and not input_data.replace:
                        existing = self._challenges.get_by_slug(folder.name)
                        if existing is not None:
                            packages.append(
                                _SkippedPackage(
                                    challenge=existing,
                                    turn_count=_turn_count(existing.conversation_tree),
                                )
                            )
                            continue
                    packages.append(self._prepare(folder))
                except (ChallengePackageError, AudioValidationError) as exc:
                    self._fail(
                        ImportChallengePackageFailureReason.INVALID_PACKAGE, str(exc)
                    )
                    return

            prepared = [item for item in packages if isinstance(item, _PreparedPackage)]
            duplicate = self._find_duplicate(prepared)
            if duplicate is not None:
                self._fail(
                    ImportChallengePackageFailureReason.INVALID_PACKAGE, duplicate
                )
                return

            selected: list[_PreparedPackage] = []
            replaced_slugs: set[str] = set()
            for item in prepared:
                existing = self._challenges.get_by_slug(item.challenge.slug)
                if existing is not None and not input_data.replace:
                    self._fail(
                        ImportChallengePackageFailureReason.ALREADY_EXISTS,
                        f"Challenge {item.challenge.slug!r} already exists; "
                        "select Replace to update it.",
                    )
                    return
                if existing is not None:
                    replaced_slugs.add(item.challenge.slug)

                existing_name = self._challenges.get_by_name(item.challenge.name)
                if (
                    existing_name is not None
                    and existing_name.slug != item.challenge.slug
                ):
                    self._fail(
                        ImportChallengePackageFailureReason.INVALID_PACKAGE,
                        f"Challenge name {item.challenge.name!r} is already used "
                        f"by {existing_name.slug!r}.",
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
                    turn_count=item.turn_count,
                    replaced=isinstance(item, _PreparedPackage)
                    and item.challenge.slug in replaced_slugs,
                    skipped=isinstance(item, _SkippedPackage),
                )
                for item in packages
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
        for field in ("name", "slug", "challenge_date"):
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
