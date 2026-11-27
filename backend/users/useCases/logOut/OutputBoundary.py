from typing import Protocol

from .OutputData import LogOutOutputData


class LogOutOutputBoundary(Protocol):
    response_body: dict
    status_code: int

    def present(self, output: LogOutOutputData) -> None: ...
