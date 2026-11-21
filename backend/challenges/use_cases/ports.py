from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import date
from pathlib import Path
from typing import BinaryIO, Protocol

from challenges.domain.challenge import Challenge


class ChallengeRepository(Protocol):
    def list(self) -> Sequence[Challenge]: ...

    def get_by_slug(self, slug: str) -> Challenge | None: ...

    def get_by_date(self, challenge_date: date) -> Challenge | None: ...

    def save(self, challenge: Challenge) -> Challenge: ...


class LoadedChallengePackage(Protocol):
    folder: Path
    slug: str
    metadata: Mapping[str, object]
    conversation_tree: Mapping[str, object]
    files: frozenset[str]
    turn_count: int


class PreparedChallengePackage(Protocol):
    challenge: Challenge
    source: LoadedChallengePackage


class PackageSource(Protocol):
    def load(self, folder: Path) -> LoadedChallengePackage: ...


class PackageArchiveExtractor(Protocol):
    def extract(self, archive: BinaryIO) -> AbstractContextManager[Path]: ...


class AudioValidator(Protocol):
    def validate(self, folder: Path, relative_path: str) -> None: ...


class MediaStore(Protocol):
    def install(
        self, packages: Sequence[PreparedChallengePackage], *, replace: bool
    ) -> None: ...
