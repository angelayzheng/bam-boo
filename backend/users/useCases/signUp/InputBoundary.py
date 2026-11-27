from typing import Protocol

from .InputData import SignUpInputData


class SignUpInputBoundary(Protocol):
    def execute(self, data: SignUpInputData) -> None: ...
