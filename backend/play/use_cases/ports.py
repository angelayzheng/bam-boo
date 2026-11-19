from contextlib import AbstractContextManager
from typing import Protocol

from play.domain.attempt import Attempt


class UnitOfWork(Protocol):
    def atomic(self) -> AbstractContextManager[None]: ...


class AttemptRepository(Protocol):
    def get_by_submission_id(self, submission_id: str) -> Attempt | None: ...

    def save(self, attempt: Attempt) -> Attempt: ...

    def list_for_profile(self, profile_id: int) -> list[Attempt]: ...


class ToneMatcher(Protocol):
    def similarity(self, answer: str, reference_tone: str) -> float: ...
