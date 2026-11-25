from play.useCases.manageChallengeRun.InputBoundary import (
    ManageChallengeRunInputBoundary,
)
from play.useCases.manageChallengeRun.InputData import (
    ChallengeRunInputData,
    StartChallengeRunInputData,
)


class ChallengeRunController:
    def __init__(self, interactor: ManageChallengeRunInputBoundary):
        self._interactor = interactor

    def reject_input(self, message):
        self._interactor.reject_input(message)

    def start_challenge(self, slug, user_id, payload):
        self._interactor.start_challenge(
            StartChallengeRunInputData(
                challenge_slug=slug,
                user_id=user_id,
                payload=payload,
            )
        )

    def get_run(self, run_id, user_id):
        self._interactor.get_run(ChallengeRunInputData(run_id, user_id))

    def submit_tone(self, run_id, user_id, payload):
        self._interactor.submit_tone(ChallengeRunInputData(run_id, user_id, payload))

    def choose_response(self, run_id, user_id, payload):
        self._interactor.choose_response(
            ChallengeRunInputData(run_id, user_id, payload)
        )

    def continue_conversation(self, run_id, user_id, payload):
        self._interactor.continue_conversation(
            ChallengeRunInputData(run_id, user_id, payload)
        )

    def submit_action(self, run_id, user_id, payload):
        self._interactor.submit_action(ChallengeRunInputData(run_id, user_id, payload))
