from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ViewProfileInputData:
    user_id: int | None = None
    username: str | None = None
