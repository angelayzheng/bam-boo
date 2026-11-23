from contextlib import AbstractContextManager
from typing import Protocol

from play.domain.attempt import Attempt
from play.domain.Run import Run


class UnitOfWork(Protocol):
    def atomic(self) -> AbstractContextManager[None]: ...


class AttemptRepository(Protocol):
    def get_by_submission_id(self, submission_id: str) -> Attempt | None: ...

    def save(self, attempt: Attempt) -> Attempt: ...

    def get_or_create(self, attempt: Attempt) -> tuple[Attempt, bool]: ...

    def list_for_profile(self, profile_id: int) -> list[Attempt]: ...


class RunRepository(Protocol):
    def get_by_id(self, run_id: str, *, for_update: bool = False) -> Run | None: ...

    def create(self, run: Run) -> Run: ...

    def save(self, run: Run) -> Run: ...


class ToneMatcher(Protocol):
    def similarity(self, answer: str, reference_tone: str) -> float: ...
