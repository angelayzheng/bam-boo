from typing import Protocol

from .OutputData import SignUpOutputData


class SignUpOutputBoundary(Protocol):
    response_body: dict
    status_code: int

    def present(self, output: SignUpOutputData) -> None: ...
