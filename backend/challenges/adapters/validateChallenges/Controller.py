from challenges.use_cases.validateChallenges.InputBoundary import (
    ValidateChallengesInputBoundary,
)
from challenges.use_cases.validateChallenges.InputData import (
    ValidateChallengesInputData,
)


class ValidateChallengesController:
    def __init__(self, interactor: ValidateChallengesInputBoundary):
        self._interactor = interactor

    def execute(self) -> None:
        self._interactor.execute(ValidateChallengesInputData())
