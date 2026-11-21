from typing import Protocol

from .output_data import PlayFailureData, PlaySuccessData


class ManageChallengeRunOutputBoundary(Protocol):
    def prepare_success_view(self, output_data: PlaySuccessData) -> None: ...

    def prepare_fail_view(self, failure: PlayFailureData) -> None: ...
