from typing import Protocol

from .OutputData import UpdateProfileFailureData, UpdateProfileOutputData


class UpdateProfileOutputBoundary(Protocol):
    def prepare_success_view(self, output_data: UpdateProfileOutputData) -> None: ...

    def prepare_fail_view(self, failure: UpdateProfileFailureData) -> None: ...
