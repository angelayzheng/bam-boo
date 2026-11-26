from challenges.useCases.getChallenge.InputBoundary import GetChallengeInputBoundary
from challenges.useCases.getChallenge.InputData import GetChallengeInputData


class GetChallengeController:
    def __init__(self, interactor: GetChallengeInputBoundary):
        self._interactor = interactor

    def execute(self, slug: str) -> None:
        self._interactor.execute(GetChallengeInputData(slug=slug))
