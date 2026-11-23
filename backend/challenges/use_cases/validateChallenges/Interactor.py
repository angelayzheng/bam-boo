from challenges.use_cases.ports import ChallengeValidationGateway

from .InputBoundary import ValidateChallengesInputBoundary
from .InputData import ValidateChallengesInputData
from .OutputBoundary import ValidateChallengesOutputBoundary
from .OutputData import (
    ValidateChallengesFailureData,
    ValidateChallengesFailureReason,
    ValidateChallengesOutputData,
)


class ValidateChallengesInteractor(ValidateChallengesInputBoundary):
    def __init__(
        self,
        *,
        validation: ChallengeValidationGateway,
        presenter: ValidateChallengesOutputBoundary,
    ):
        self._validation = validation
        self._presenter = presenter

    def execute(self, input_data: ValidateChallengesInputData) -> None:
        errors: list[str] = []
        try:
            errors.extend(self._validation.database_errors())
            errors.extend(self._validation.environment_errors())
            if not errors:
                errors.extend(self._validation.challenge_errors())
        except Exception as exc:
            self._fail(
                ValidateChallengesFailureReason.VALIDATOR_ERROR,
                f"Could not validate challenges: {exc}",
            )
            return

        if errors:
            self._fail(
                ValidateChallengesFailureReason.VALIDATION_FAILED,
                "Challenge validation failed.",
                tuple(errors),
            )
            return

        self._presenter.prepare_success_view(ValidateChallengesOutputData())

    def _fail(
        self,
        reason: ValidateChallengesFailureReason,
        message: str,
        errors: tuple[str, ...] = (),
    ) -> None:
        self._presenter.prepare_fail_view(
            ValidateChallengesFailureData(reason=reason, message=message, errors=errors)
        )
