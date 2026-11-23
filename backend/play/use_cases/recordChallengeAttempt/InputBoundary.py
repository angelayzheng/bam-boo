from typing import Protocol

from .InputData import RecordChallengeAttemptInputData


class RecordChallengeAttemptInputBoundary(Protocol):
    def execute(self, input_data: RecordChallengeAttemptInputData) -> None: ...
