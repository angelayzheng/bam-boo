from typing import Protocol

from .OutputData import ViewProfileOutputData


class ViewProfileOutputBoundary(Protocol):
    def prepare_success_view(self, output_data: ViewProfileOutputData) -> None: ...

    def prepare_fail_view(self) -> None: ...
