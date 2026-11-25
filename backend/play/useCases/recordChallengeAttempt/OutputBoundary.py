from typing import Protocol

from .OutputData import (
    RecordChallengeAttemptFailureData,
    RecordChallengeAttemptOutputData,
)


class RecordChallengeAttemptOutputBoundary(Protocol):
    def prepare_success_view(
        self, output_data: RecordChallengeAttemptOutputData
    ) -> None: ...

    def prepare_fail_view(self, failure: RecordChallengeAttemptFailureData) -> None: ...
