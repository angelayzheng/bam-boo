from challenges.useCases.getChallenge.OutputBoundary import GetChallengeOutputBoundary
from challenges.useCases.getChallenge.OutputData import (
    GetChallengeFailureData,
    GetChallengeOutputData,
)


class GetChallengePresenter(GetChallengeOutputBoundary):
    def __init__(self):
        self.response_body: dict = {}
        self.status_code = 200

    def prepare_success_view(self, output_data: GetChallengeOutputData) -> None:
        self.response_body = {
            "name": output_data.name,
            "slug": output_data.slug,
            "challenge_date": output_data.challenge_date.isoformat(),
            "difficulty": output_data.difficulty,
            "category": output_data.category,
        }
        self.status_code = 200

    def prepare_fail_view(self, failure: GetChallengeFailureData) -> None:
        self.response_body = {"detail": failure.message}
        self.status_code = 404
