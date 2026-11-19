from play.domain.attempt import Attempt
from play.use_cases.ports import AttemptRepository
from users.models import ChallengeAttempt


def _to_domain(row: ChallengeAttempt) -> Attempt:
    return Attempt(
        submission_id=row.submission_id,
        profile_id=row.profile_id,
        challenge_slug=row.challenge_id,
        score=row.score,
        completed_at=row.completed_at,
        received_at=row.received_at,
        record_id=row.pk,
    )


class DjangoAttemptRepository(AttemptRepository):
    def get_by_submission_id(self, submission_id: str) -> Attempt | None:
        row = ChallengeAttempt.objects.filter(submission_id=submission_id).first()
        return None if row is None else _to_domain(row)

    def save(self, attempt: Attempt) -> Attempt:
        row = ChallengeAttempt.objects.create(
            submission_id=attempt.submission_id,
            profile_id=attempt.profile_id,
            challenge_id=attempt.challenge_slug,
            score=attempt.score,
            completed_at=attempt.completed_at,
        )
        return _to_domain(row)

    def list_for_profile(self, profile_id: int) -> list[Attempt]:
        return [
            _to_domain(row)
            for row in ChallengeAttempt.objects.filter(profile_id=profile_id)
        ]
