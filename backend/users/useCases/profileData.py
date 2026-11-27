from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProfileData:
    user_id: int
    username: str
    name: str
    email: str
    team: str
    avatar: str
    scores: dict[str, int]
    total_score: int
    login_days: list[str]
