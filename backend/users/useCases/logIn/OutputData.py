from dataclasses import dataclass

from users.useCases.ports import AuthenticatedAccount


@dataclass(frozen=True, slots=True)
class LogInOutputData:
    status_code: int
    account: AuthenticatedAccount | None = None
