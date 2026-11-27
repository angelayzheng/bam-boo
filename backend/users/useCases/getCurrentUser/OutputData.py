from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetCurrentUserOutputData:
    user_id: int
    username: str
    email: str
