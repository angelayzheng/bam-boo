from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecordChallengeAttemptInputData:
    user_id: int
    challenge_slug: str
    attempt_id: str
