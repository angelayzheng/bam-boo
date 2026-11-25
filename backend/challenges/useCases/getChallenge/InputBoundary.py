from typing import Protocol

from .InputData import GetChallengeInputData


class GetChallengeInputBoundary(Protocol):
    def execute(self, input_data: GetChallengeInputData) -> None: ...
