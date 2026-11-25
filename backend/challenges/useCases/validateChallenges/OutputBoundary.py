from typing import Protocol

from .OutputData import (
    ValidateChallengesFailureData,
    ValidateChallengesOutputData,
)


class ValidateChallengesOutputBoundary(Protocol):
    def prepare_success_view(
        self, output_data: ValidateChallengesOutputData
    ) -> None: ...

    def prepare_fail_view(self, failure: ValidateChallengesFailureData) -> None: ...
