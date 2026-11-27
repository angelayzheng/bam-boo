from typing import Protocol

from .OutputData import GetCurrentUserOutputData


class GetCurrentUserOutputBoundary(Protocol):
    def prepare_success_view(self, output_data: GetCurrentUserOutputData) -> None: ...

    def prepare_fail_view(self) -> None: ...
