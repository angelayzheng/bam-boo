from typing import Protocol

from .OutputData import GetChallengeFailureData, GetChallengeOutputData


class GetChallengeOutputBoundary(Protocol):
    def prepare_success_view(self, output_data: GetChallengeOutputData) -> None: ...

    def prepare_fail_view(self, failure: GetChallengeFailureData) -> None: ...
