from dataclasses import dataclass
from typing import Protocol

from play.domain.attempt import Attempt
from users.domain.profile import Profile


class AttemptConflictError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RecordedChallengeAttempt:
    attempt: Attempt
    profile: Profile
    created: bool


class RecordChallengeAttemptDataAccessInterface(Protocol):
    def challenge_exists(self, challenge_slug: str) -> bool: ...

    def record(self, attempt: Attempt) -> RecordedChallengeAttempt: ...
