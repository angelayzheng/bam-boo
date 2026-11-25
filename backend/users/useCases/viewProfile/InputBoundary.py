from typing import Protocol

from .InputData import ViewProfileInputData


class ViewProfileInputBoundary(Protocol):
    def execute(self, input_data: ViewProfileInputData) -> None: ...
