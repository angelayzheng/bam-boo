from dataclasses import dataclass
from datetime import date
from enum import Enum


class ImportChallengePackageFailureReason(Enum):
    INVALID_INPUT = "invalid_input"
    INVALID_PACKAGE = "invalid_package"
    ALREADY_EXISTS = "already_exists"


@dataclass(frozen=True, slots=True)
class ImportChallengePackageFailureData:
    reason: ImportChallengePackageFailureReason
    message: str


@dataclass(frozen=True, slots=True)
class ImportChallengePackageResultData:
    slug: str
    name: str
    challenge_date: date
    turn_count: int
    replaced: bool
    skipped: bool = False


@dataclass(frozen=True, slots=True)
class ImportChallengePackageOutputData:
    results: tuple[ImportChallengePackageResultData, ...]
