from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from users.useCases.profileData import ProfileData
from users.domain.profile import Profile
from users.domain.profileChanges import ProfileChanges
from users.useCases.getCurrentUser.OutputData import GetCurrentUserOutputData


class ProfileRepository(Protocol):
    def get_by_user_id(
        self, user_id: int, *, for_update: bool = False
    ) -> Profile | None: ...

    def get_by_username(self, username: str) -> Profile | None: ...

    def list_top(self, limit: int) -> Sequence[Profile]: ...

    def save(self, profile: Profile) -> Profile: ...


class ProfileDetailsRepository(Protocol):
    def get_by_user_id(self, user_id: int) -> ProfileData | None: ...

    def get_by_username(
        self, username: str, *, for_update: bool = False
    ) -> ProfileData | None: ...

    def update(
        self, user_id: int, changes: ProfileChanges, *, group_id: int | None
    ) -> ProfileData: ...


class TeamRepository(Protocol):
    def find_by_slug(self, slug: str) -> Sequence[int]: ...


class EmailValidator(Protocol):
    def is_valid(self, email: str) -> bool: ...


class UnitOfWork(Protocol):
    def atomic(self) -> AbstractContextManager[None]: ...


class CurrentAccountGateway(Protocol):
    def current_account(self) -> GetCurrentUserOutputData | None: ...


@dataclass(frozen=True, slots=True)
class AuthenticatedAccount:
    user_id: int
    username: str
    email: str


@dataclass(frozen=True, slots=True)
class AccountCreationResult:
    account: AuthenticatedAccount | None
    errors: dict[str, list[str]]


class AuthenticationGateway(Protocol):
    def create_account(
        self, *, username: str, password: str, email: str, group_id: int | None
    ) -> AccountCreationResult: ...

    def authenticate(
        self, *, username: str, password: str
    ) -> AuthenticatedAccount | None: ...

    def start_session(self, user_id: int) -> None: ...

    def end_session(self) -> None: ...
