from typing import Protocol

from .InputData import ValidateChallengesInputData


class ValidateChallengesInputBoundary(Protocol):
    def execute(self, input_data: ValidateChallengesInputData) -> None: ...
