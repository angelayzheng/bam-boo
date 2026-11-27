from dataclasses import dataclass

from users.useCases.ports import AuthenticatedAccount


@dataclass(frozen=True, slots=True)
class SignUpOutputData:
    status_code: int
    account: AuthenticatedAccount | None = None
    errors: dict[str, list[str]] | None = None
