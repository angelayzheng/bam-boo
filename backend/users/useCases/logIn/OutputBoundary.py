from typing import Protocol

from .OutputData import LogInOutputData


class LogInOutputBoundary(Protocol):
    response_body: dict
    status_code: int

    def present(self, output: LogInOutputData) -> None: ...
