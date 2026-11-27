from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SignUpInputData:
    username: str
    password: str
    email: str = ""
    group_id: int | None = None
