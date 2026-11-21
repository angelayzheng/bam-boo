from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StartChallengeRunInputData:
    challenge_slug: str
    user_id: int | None
    payload: dict


@dataclass(frozen=True, slots=True)
class ChallengeRunInputData:
    run_id: str
    user_id: int | None
    payload: dict = field(default_factory=dict)
