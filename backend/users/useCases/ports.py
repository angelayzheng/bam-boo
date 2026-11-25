from collections.abc import Sequence
from contextlib import AbstractContextManager
from typing import Protocol

from users.useCases.profileData import ProfileData
from users.domain.profile import Profile


class ProfileRepository(Protocol):
    def get_by_user_id(
        self, user_id: int, *, for_update: bool = False
    ) -> Profile | None: ...

    def get_by_username(self, username: str) -> Profile | None: ...

    def list_top(self, limit: int) -> Sequence[Profile]: ...

    def save(self, profile: Profile) -> Profile: ...


class AuthGateway(Protocol):
    def sign_up(
        self,
        username: str,
        password: str,
        email: str = "",
        group_id: int | None = None,
    ) -> int: ...

    def log_in(self, username: str, password: str) -> int | None: ...

    def log_out(self) -> None: ...

    def current_user_id(self) -> int | None: ...


class GroupRepository(Protocol):
    def list_groups(self) -> Sequence[tuple[int, str]]: ...


class ProfileDetailsRepository(Protocol):
    def get_by_user_id(self, user_id: int) -> ProfileData | None: ...

    def get_by_username(
        self, username: str, *, for_update: bool = False
    ) -> ProfileData | None: ...

    def update(self, user_id: int, changes: dict) -> ProfileData: ...


class TeamRepository(Protocol):
    def find_by_slug(self, slug: str) -> Sequence[int]: ...


class EmailValidator(Protocol):
    def is_valid(self, email: str) -> bool: ...


class UnitOfWork(Protocol):
    def atomic(self) -> AbstractContextManager[None]: ...
