from collections.abc import Mapping, Sequence
from datetime import date
from typing import Protocol

from challenges.domain.challenge import Challenge


class ChallengeRepository(Protocol):
    def list(self) -> Sequence[Challenge]: ...

    def get_by_slug(self, slug: str) -> Challenge | None: ...

    def get_by_date(self, challenge_date: date) -> Challenge | None: ...

    def save(self, challenge: Challenge) -> Challenge: ...


class MediaStore(Protocol):
    def read_text(self, challenge_slug: str, filename: str) -> str: ...

    def write_package(
        self, challenge_slug: str, files: Mapping[str, bytes]
    ) -> None: ...

    def delete_package(self, challenge_slug: str) -> None: ...
