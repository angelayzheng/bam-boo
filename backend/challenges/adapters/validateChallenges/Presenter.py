from dataclasses import dataclass

from challenges.use_cases.validateChallenges.OutputBoundary import (
    ValidateChallengesOutputBoundary,
)
from challenges.use_cases.validateChallenges.OutputData import (
    ValidateChallengesFailureData,
    ValidateChallengesOutputData,
)


@dataclass(frozen=True, slots=True)
class ValidateChallengesViewModel:
    success: bool
    message: str
    errors: tuple[str, ...] = ()


class ValidateChallengesPresenter(ValidateChallengesOutputBoundary):
    def __init__(self):
        self.view_model = ValidateChallengesViewModel(success=False, message="")

    def prepare_success_view(self, output_data: ValidateChallengesOutputData) -> None:
        self.view_model = ValidateChallengesViewModel(success=True, message="OK")

    def prepare_fail_view(self, failure: ValidateChallengesFailureData) -> None:
        self.view_model = ValidateChallengesViewModel(
            success=False, message=failure.message, errors=failure.errors
        )
