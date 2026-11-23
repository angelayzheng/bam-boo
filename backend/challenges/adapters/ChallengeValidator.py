from challenges import models as challenge_models
from challenges.domain.challenge import Challenge
from challenges.use_cases.ports import ChallengeValidationGateway
from challenges.validation import ChallengeDatabaseValidator


class DjangoChallengeValidator(ChallengeValidationGateway):
    def database_errors(self) -> list[str]:
        return ChallengeDatabaseValidator().database_errors()

    def environment_errors(self) -> list[str]:
        return ChallengeDatabaseValidator().environment_errors()

    def challenge_errors(self, challenge: Challenge) -> list[str]:
        row = challenge_models.Challenge.objects.filter(slug=challenge.slug).first()
        if row is None:
            return [f"{challenge.slug}: challenge row is missing."]
        return ChallengeDatabaseValidator().challenge_errors(row)
