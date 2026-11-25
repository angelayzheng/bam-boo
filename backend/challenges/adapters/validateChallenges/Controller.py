from challenges.useCases.validateChallenges.InputBoundary import (
    ValidateChallengesInputBoundary,
)
from challenges.useCases.validateChallenges.InputData import (
    ValidateChallengesInputData,
)


class ValidateChallengesController:
    def __init__(self, interactor: ValidateChallengesInputBoundary):
        self._interactor = interactor

    def execute(self) -> None:
        self._interactor.execute(ValidateChallengesInputData())
