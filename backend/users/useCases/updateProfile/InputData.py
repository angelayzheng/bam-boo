from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateProfileInputData:
    username: str
    user_id: int | None
    payload: dict | None
    parsing_error: str | None = None
