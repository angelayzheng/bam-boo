from dataclasses import dataclass
from enum import Enum


class ValidateChallengesFailureReason(Enum):
    VALIDATION_FAILED = "validation_failed"
    VALIDATOR_ERROR = "validator_error"


@dataclass(frozen=True, slots=True)
class ValidateChallengesFailureData:
    reason: ValidateChallengesFailureReason
    message: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidateChallengesOutputData:
    errors: tuple[str, ...] = ()
