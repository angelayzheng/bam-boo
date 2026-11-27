from collections.abc import Sequence
from typing import Protocol

from users.domain.profile import Profile
from users.useCases.getCurrentUser.OutputData import GetCurrentUserOutputData


class ProfileRepository(Protocol):
    def get_by_user_id(
        self, user_id: int, *, for_update: bool = False
    ) -> Profile | None: ...

    def get_by_username(self, username: str) -> Profile | None: ...

    def list_top(self, limit: int) -> Sequence[Profile]: ...

    def save(self, profile: Profile) -> Profile: ...


class CurrentAccountGateway(Protocol):
    def current_account(self) -> GetCurrentUserOutputData | None: ...
