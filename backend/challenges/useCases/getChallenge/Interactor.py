from challenges.useCases.ports import ChallengeRepository

from .InputBoundary import GetChallengeInputBoundary
from .InputData import GetChallengeInputData
from .OutputBoundary import GetChallengeOutputBoundary
from .OutputData import GetChallengeFailureData, GetChallengeOutputData


class GetChallengeInteractor(GetChallengeInputBoundary):
    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        presenter: GetChallengeOutputBoundary,
    ):
        self._challenges = challenges
        self._presenter = presenter

    def execute(self, input_data: GetChallengeInputData) -> None:
        challenge = self._challenges.get_by_slug(input_data.slug)
        if challenge is None:
            self._presenter.prepare_fail_view(
                GetChallengeFailureData(message="Challenge not found.")
            )
            return
        self._presenter.prepare_success_view(
            GetChallengeOutputData(
                name=challenge.name,
                slug=challenge.slug,
                challenge_date=challenge.challenge_date,
                difficulty=challenge.difficulty,
                category=challenge.category,
            )
        )
