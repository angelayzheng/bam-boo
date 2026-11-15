from typing import Protocol

from .record_challenge_attempt_input_data import RecordChallengeAttemptInputData


class RecordChallengeAttemptInputBoundary(Protocol):
    def execute(self, input_data: RecordChallengeAttemptInputData) -> None: ...
