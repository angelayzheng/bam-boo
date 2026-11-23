from challenges import models as challenge_models
from challenges.use_cases.ports import ChallengeValidationGateway
from challenges.validation import ChallengeDatabaseValidator


class DjangoChallengeValidator(ChallengeValidationGateway):
    def database_errors(self) -> list[str]:
        return ChallengeDatabaseValidator().database_errors()

    def environment_errors(self) -> list[str]:
        return ChallengeDatabaseValidator().environment_errors()

    def challenge_errors(self) -> list[str]:
        validator = ChallengeDatabaseValidator()
        errors = []
        for row in challenge_models.Challenge.objects.all().order_by("slug"):
            errors.extend(validator.challenge_errors(row))
        return errors
