from typing import Protocol

from .InputData import LogInInputData


class LogInInputBoundary(Protocol):
    def execute(self, data: LogInInputData) -> None: ...
