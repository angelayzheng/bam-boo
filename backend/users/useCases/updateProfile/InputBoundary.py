from typing import Protocol

from .InputData import UpdateProfileInputData


class UpdateProfileInputBoundary(Protocol):
    def execute(self, input_data: UpdateProfileInputData) -> None: ...
