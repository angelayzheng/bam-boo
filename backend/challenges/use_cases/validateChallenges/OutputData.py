from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidateChallengesFailureData:
    message: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidateChallengesOutputData:
    pass
